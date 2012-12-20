#!/usr/bin/env python

import datetime,time
from optparse import OptionParser
from HTTPHandler import HTTPHandler
from ZenossHandler import ZenossHandler
from PagerDutyHandler import PagerDutyHandler
from MessageHandler import MessageHandler

# optionally populate below or supply via command line
ZENOSS_HOST = ''
ZENOSS_USERNAME = ''
ZENOSS_PASSWORD = ''
EVID = ''

PAGERDUTY_TOKEN = ''
PAGERDUTY_HOST = ''
PAGERDUTY_SERVICE  = ''
PAGERDUTY_SERVICEKEY = ''
PAGERDUTY_USER = ''


ZENOSS_HOST = 'fpmon001.na.atxglobal.com'
ZENOSS_USERNAME = 'admin'
ZENOSS_PASSWORD = 'z3n055'
EVID = 'baf0c32b-6f97-472e-8017-d3d987b266eb'

PAGERDUTY_TOKEN = 'Z2FMKyrbF1xdSUPVDisL'
PAGERDUTY_HOST = 'agero.pagerduty.com'
PAGERDUTY_SERVICE  = 'PJ9LKSP'
PAGERDUTY_SERVICEKEY = '552ff32011800130648822000af81c0e'
PAGERDUTY_USER = "PFX83CI"


        
    
class Main():
    """
        Either:
            1) Create Pagerduty Incident based on new Zenoss event
            2) Synchronize Zenoss and Pagerduty Events and Incidents
    """
    def __init__(self):
        """
        """
        self.getOptions()
        #self.options.verbose = True
        self.zenoss = ZenossHandler(self.options.zenhost, self.options.zenuser, self.options.zenpass, self.options.verbose)
        self.pagerduty = PagerDutyHandler(self.options.pdhost, self.options.pdtoken, self.options.verbose)
        # dictionary of corresponding event/incident states
        self.statusData = {
                           "ack":{"zenoss":"Acknowledged","pagerduty":"acknowledged","zenaction":"acknowledge","num":1},
                           "close":{"zenoss":"Closed","pagerduty":"resolved","zenaction":"close","num":2},
                           "open":{"zenoss":"New","pagerduty":"triggered","zenaction":"unacknowledge","num":0},
                           }
        if self.options.zenver == True:
            self.statusData["open"]["zenaction"] = "reopen"
            
        self.messenger = MessageHandler()
        self.statusDict = {}
              
    def lastDisabled(self,service):
        """
            return PagerDuty newest disabled entry
        """
        message = ""
        details = self.pagerduty.getServiceLog(service["id"])["log_entries"]
        last = 0
        lastentry = None
        for d in details:
            if d["maintenance_window"]["type"] == "disable":
                starttime = self.messenger.getLocalTime(d["maintenance_window"]["time"])
                start = self.messenger.getTimestamp(starttime)
                if start > last:
                    lastentry = d
                    last = start
        return lastentry
        
    def getMaintenanceWindows(self,service):
        """
            return list of maintenance windows (ongoing) for a given service
        """
        output = []
        windows = self.pagerduty.getMaintenanceWindows()["maintenance_windows"]
        for w in windows:
            services = w["services"]
            for s in services:
                if s["id"] == service["id"]:
                    beg = self.messenger.getLocalTime(w["start_time"])
                    fin = self.messenger.getLocalTime(w["end_time"])
                    
                    start = self.messenger.getTimestamp(beg)
                    end = self.messenger.getTimestamp(fin) 
                    now = time.time()
                    if start <= now and now <=end:
                        output.append(w)
        return output
    
    def createIncidentDetails(self,evid):
        """
            Retrieve event detail from Zenoss and format it 
            for PagerDuty incident creation
        """
        
        self.incidentData = {
                "service_key": self.options.servicekey,
                "incident_key": self.options.evid
                }
        details = self.zenoss.getEventDetails(evid)["result"]["event"][0]["properties"]
        
        self.statusDict[evid] = {}
        self.statusDict[evid]["target"] = "open"
        data = {}
        status = 0
        dev = None
        comp = None
        summ = None
        for d in details:
            k = d["key"]
            v = d["value"]
            data[k] = v
            if k == "device": dev=v
            if k == "component": comp = v
            if k == "summary": summ = v
            if k == "eventState": status = v
        self.incidentData["details"] = data
        self.incidentData["description" ] = "%s | %s | %s" % (dev, comp, summ)
        
        if status == 0:
            self.statusDict[evid]["current"] = "open"
        elif status == 1:
            self.statusDict[evid]["current"] = "ack"
        elif status == 2:
            self.statusDict[evid]["current"] = "close"
        
        return status

    def createPagerDutyIncident(self):
        """
        1) check whether the destination service is in a maintenance window.  
            a) If so, ack the local alert in zenoss 
            b) and add a "in maintenance window" log message to the Zenoss event details.

        2) if it is not in maintenance, proceed with the event submission. as usual
            a) send event to pagerduty
            b) update Zenoss console with submit status info
            c) update Zenoss Event with incident details (incident URL, service URL, oncall)
        3) check issues in Zenoss w/pagerduty incidents:
            a) if acked in Zenoss, ack in PagerDuty
            b) if closed in Zenoss, resolve in PagerDuty
        """
        status = self.createIncidentDetails(self.options.evid)
        
        if status == 0:
            # first find the appropriate PD service definition
            service = self.pagerduty.findService(self.options.servicekey)
            if service:
                 # in maintenance, so ack the zenoss alert but note the window detail
                if self.pagerduty.inMaintenance(service) == True:
                    self.statusDict[self.options.evid]["target"] = "ack"
                    mws = self.getMaintenanceWindows(service) 
                    for mw in mws:
                        self.messenger.serviceInMaintenance(self.options.evid, "Acknowledged", service, mw, self.pagerduty.weburl)
    
                # disabled, so leave event unacked in Zenoss, but that service is disabled    
                elif self.pagerduty.isDisabled(service) == True: 
                    self.messenger.serviceIsDisabled(self.options.evid, "No Incident created", service, self.lastDisabled(service), self.pagerduty.weburl)
                
                # assuming service is enabled, create PD incident, note output in zenoss event console.
                else: 
                    output = self.pagerduty.manageIncident(self.incidentData,"trigger")
                    try:
                        self.messenger.serviceIncidentCreated(self.options.evid, service, self.pagerduty.weburl, output["errors"])
                    except KeyError:
                        self.messenger.serviceIncidentCreated(self.options.evid, service, self.pagerduty.weburl)
    
            else:
                self.messenger.serviceNotFound(self.options.evid, self.options.servicekey)
        else:
           self.statusDict[self.options.evid]["target"] = self.statusDict[self.options.evid]["current"]
         
    def correlateByZenoss(self):
        """
            build dictionary of Zenoss events matched to PagerDuty incidents
            1) get list of zenoss events
            2) get list of pagerduty incidents based on date range of zenoss events
            3) match them by evid - incident_key
        """
        if self.options.verbose == True:
            print "CORRELATING ZENOSS EVENTS AND PAGERDUTY INCIDENTS"
        #incidents = self.pagerduty.getIncidentList()["incidents"]
        events = self.zenoss.getEvents()["events"]
        self.pairs = []
        
        for e in events:
            data = {"id": e["evid"], 'pagerduty': None, 'zenoss': e}
            try:
                data["pagerduty"]= self.pagerduty.getIncidentByKey(e["evid"])
            except:
                pass
            self.pairs.append(data)
    
    def correlateByPagerDuty(self):
        """
            build dictionary of Zenoss events matched to PagerDuty incidents
            1) get list of zenoss events
            2) get list of pagerduty incidents based on date range of zenoss events
            3) match them by evid - incident_key
        """
        if self.options.verbose == True:
            print "CORRELATING ZENOSS EVENTS AND PAGERDUTY INCIDENTS"
        incidents = self.pagerduty.getIncidentList()["incidents"]
        events = self.zenoss.getEvents()["events"]
        self.pairs = []
        for i in incidents:
            data = {"id": i["incident_key"], 'pagerduty': i, 'zenoss': None}
            for e in events:
                if i["incident_key"] == e["evid"]:
                    data['zenoss'] = e
            self.pairs.append(data)
        
    def synchronize(self):
        """
            update pagerduty based on Zenoss event console activities (acknowledge, resolve, etc)

            4) if acked in one, ack in the other
            5) if closed in one, close in the other
        """
        if self.options.verbose == True:
            print "SYNCHRONIZING ZENOSS AND PAGERDUTY EVENT/INCIDENT STATES"
        for p in self.pairs:
            id = p["id"]
            zen = p["zenoss"]
            pd = p["pagerduty"]
            self.messenger.newId(id)
            self.statusDict[id] = {}
            # if pagerduty event is open, but not listed in zenoss, then close it (for Zenoss 3.x, to avoid querying event history)
            if zen == None:
                #if self.options.zenver == False:
                self.statusDict[id]["target"] = "close"
            else:
                # set up console messages
                self.messenger.incidentCreated(id, pd)
                #self.messenger.incidentAssigned(id, pd)
                details = self.pagerduty.getIncidentDetail(pd["id"])["log_entries"]
                self.messenger.incidentLogs(id, details, self.pagerduty.weburl)
                for k,v in self.statusData.items():
                    if v["zenoss"] == zen["eventState"]: self.statusDict[id]["current"] = k
                # determine whether Zenoss or Pagerduty has authority
                self.compare(zen, pd)
       
    def compare(self,event,incident):
        """
            determine target state based on event vs. incident last updated
        """
        if self.options.verbose == True:
            print "COMPARING EVENT AND INCIDENT FOR ID:%s" % event["evid"]

        evupdated = None
        evdetails = details = self.zenoss.getEventDetails(event["evid"])["result"]["event"][0]["properties"]
        for e in evdetails:
            k = e["key"]
            v = e["value"]
            if k == "stateChange": eupdated = v
        iupdated = incident["last_status_change_on"]
        
        zt = self.messenger.getZenossTime(eupdated)
        pt = self.messenger.getUTCTime(iupdated)
        
        zentime = self.messenger.getTimestamp(zt)
        pdtime = self.messenger.getTimestamp(pt)
        
        zenstate = event['eventState']
        pdstate = incident['status']
        if self.options.verbose == True:
            print "EVENT ID %s IS %s IN ZENOSS, %s IN PAGERDUTY" % (event["evid"],zenstate,pdstate)
        zentarget = None
        pdtarget = None

        for k,v in self.statusData.items():
            if v["zenoss"] == zenstate:
                zentarget = k
            if v["pagerduty"] == pdstate:
                pdtarget = k

        if zentime >= pdtime:
            if self.options.verbose == True:
                print "ZENOSS %s NEWER THAN PAGERDUTY %s" % (zenstate,pdstate)
            self.statusDict[event["evid"]]["target"] = zentarget
        else:
            if self.options.verbose == True:
                print "PAGERDUTY %s NEWER THAN ZENOSS %s" % (pdstate,zenstate)
            self.statusDict[event["evid"]]["target"] = pdtarget
        
    def getIncidentLogs(self,id,evid):
        details = self.pagerduty.getIncidentDetail(id)["log_entries"]
        self.messenger.incidentLogs(evid, details, self.pagerduty.weburl)
    
    def updatePagerDuty(self):
        """
            update PagerDuty incident status
        """
        if self.options.verbose == True:
            print "UPDATING PAGERDUTY"
        updates = {"incidents": [], "requester_id": self.options.pduser}
        
        for p in self.pairs:
            id = p["id"]
            pd = p["pagerduty"]
            target = self.statusDict[id]["target"]
            if pd["status"] != self.statusData[target]["pagerduty"]:
                if self.options.verbose == True:
                    print "INCIDENT %s IS %s; SHOULD BE %s" % (pd["id"],pd["status"],self.statusData[target]["pagerduty"])
                pdData = {"id": pd["id"], "status":  self.statusData[target]["pagerduty"]} 
                updates["incidents"].append(pdData)
                
        if len(updates["incidents"]) > 0:
            self.pagerduty.updateStatus(updates)

    def updateZenoss(self):
        """
            update Zenoss console
            
        """
        if self.options.verbose == True:
            print "UPDATING ZENOSS"
        for p in self.pairs:
            id = p["id"]
            zen = p["zenoss"]
            if p["zenoss"] != None:
                self.updateZenossMessages(id)
                
        for p in self.pairs:
            id = p["id"]
            zen = p["zenoss"]
            if p["zenoss"] != None:
                self.updateZenossStatus(id)
                                     
    def updateZenossStatus(self,evid):
        """
            update Zenoss event status if target is not current
        """
        
        current = self.statusDict[evid]["current"]
        target = self.statusDict[evid]["target"]
        if current != target:
            if self.options.verbose == True:
                print "CHANGING STATUS %s IN ZENOSS TO %s" % (evid,target)
            self.zenoss.manageEventStatus([evid], self.statusData[target]['zenaction'])
    
    def updateZenossMessages(self,evid):
        """
            update Zenoss event console with messages if they don't exist
        """
        eventlog = self.zenoss.getEventDetails(evid)["result"]["event"][0]["log"]
        logs = []
        for e in eventlog:
            logs.append(e[-1])
        for msg in self.messenger.messages[evid]:
            if msg not in logs:
                self.zenoss.addEventMessage(evid,msg)
             
    def getOptions(self):
        """
            Command line runtime arguments
        """
        usage = "usage: %prog [options] arg"
        parser = OptionParser(usage)
        # options for Zenoss
        parser.add_option("-z", "--zenhost", dest="zenhost", help="Zenoss Server hostname", default=ZENOSS_HOST)
        parser.add_option("-u", "--zenuser", dest="zenuser", help="Zenoss admin username", default=ZENOSS_USERNAME)
        parser.add_option("-p", "--zenpass", dest="zenpass", help="Zenoss admin password", default=ZENOSS_PASSWORD)
        parser.add_option("-e", "--evid", dest="evid", help="Zenoss Event ID", default=EVID)
        parser.add_option("-V", "--zenver", dest="zenver", help="True if Zenoss version >= 4", action="store_false")
        
        # options for Pagerduty 
        parser.add_option("-H", "--pdhost", dest="pdhost", help="Pagerduty hostname", default=PAGERDUTY_HOST)
        parser.add_option("-T", "--pdtoken", dest="pdtoken", help="Pagerduty token", default=PAGERDUTY_TOKEN)
        parser.add_option("-U", "--pduser", dest="pduser", help="Pagerduty User Key (for tracking auto updates)", default=PAGERDUTY_USER)
        parser.add_option("-S", "--servicekey", dest="servicekey", help="Pagerduty Service Key", default=PAGERDUTY_SERVICEKEY)
        
        # action to be performed
        parser.add_option("-a", "--action", dest="action", help="one of [create|update]", default="update")
        parser.add_option("-v", "--verbose", dest="verbose", help="Show additional output", action="store_true")
        # options for zenoss interaction
        (self.options, self.args) = parser.parse_args()

    def run(self):
        """
            control script execution
        """
        if self.options.action == 'create':
            self.messenger.newId(self.options.evid)
            self.createPagerDutyIncident()
            self.updateZenossMessages(self.options.evid)
            self.updateZenossStatus(self.options.evid)
            
        if self.options.action == 'update':
            self.correlateByPagerDuty()
            self.synchronize()
            self.updatePagerDuty()
            self.updateZenoss()

if __name__ == "__main__":
    u = Main()
    u.run()    
