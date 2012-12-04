import datetime,time

class MessageHandler():
    """
        Standardize messages to pass between systems
    """
    def __init__(self):
        self.messages = {}

    def newId(self,id):
        self.messages[id] = []

    def serviceIncidentCreated(self, id, service, baseurl, error=None):
        """
            initial PagerDuty Incident creation status
        """
        if error is None:
            self.messages[id].append("Incident created for <a href=\"%s%s\">%s</a>" % (baseurl, service["service_url"], service["name"]))
        else:
            self.messages[id].append("Failed to create incident for <a href=\"%s%s\">%s</a> with output: %s" % (
                baseurl, 
                service["service_url"], 
                service["name"],
                error
                ))

    def incidentCreated(self, id, incident):
        """
            message for new PagerDuty Incident
        """
        self.messages[id].append("Incident <a href=\"%s\">%s</a> created under <a href=\"%s\">%s</a>" % (
                incident["html_url"],
                incident["id"],
                incident["service"]["html_url"],
                incident["service"]["name"]
                ))
        
    def incidentAssigned(self, id, incident):
        """
            message for new PagerDuty Incident
        """
        self.messages[id].append("Incident <a href=\"%s\">%s</a> Assigned to <a href=\"%s\">%s</a>" % (
                incident["html_url"],
                incident["id"],
                incident["assigned_to_user"]["html_url"],
                incident["assigned_to_user"]["name"]
                ))

    def incidentStatusChange(self, id, incident):
        """
            message for PagerDuty Incident status changes
        """
        message = "%s: Incident <a href=\"%s\">%s</a> %s by <a href=\"%s\">%s</a>" % (
                self.getUTCTime(incident["created_on"]),
                incident["html_url"],
                incident["id"],
                incident["status"], 
                incident["last_status_change_by"]["html_url"], 
                incident["last_status_change_by"]["name"]
                )
        self.messages[id].append(message)

    def incidentLogs(self,id,logs,baseurl):
        """
            reformat incident log data
        """
        for d in logs:
            created = self.getLocalTime(d["created_at"])
            type = d["type"]
            if type == "notify":
                self.messages[id].append("%s: Notification %s via %s to %s " % (created,
                                                                                d["notification"]["status"],
                                                                                d["notification"]["type"],
                                                                                d["notification"]["address"] ))
            elif type == "acknowledge":
                url = "<a href=\"%s%s\">%s</a>" % (baseurl,d["agent"]["user_url"],d["agent"]["name"])
                self.messages[id].append("%s: Acknowledged by %s via %s" % (created,
                                                                            url,
                                                                            d["channel"]["type"]))
            elif type == "unacknowledge":
                self.messages[id].append("%s: Unacknowledged due to %s" % (created,
                                                                           d["channel"]["type"]))
            elif type == "resolve":
                url = "<a href=\"%s%s\">%s</a>" % (baseurl,d["agent"]["user_url"],d["agent"]["name"])
                self.messages[id].append("%s: Resolved by %s via %s" % (created,
                                                                            url,
                                                                            d["channel"]["type"]))
            elif type == "assign":
                url = "<a href=\"%s%s\">%s</a>" % (baseurl,d["assigned_user"]["user_url"],d["assigned_user"]["name"])
                self.messages[id].append("%s: Assigned to %s" % (created,url))
            else:
                
                continue
        
    def serviceInMaintenance(self, id, action, svc, mw, baseurl):
        """
            message with PagerDuty Maintenance Window details
        """
        self.messages[id].append("%s due to %s maintenance window <a href=\"%s\">%s</a> starting: %s ending: %s" % (
                action,
                "<a href=\"%s%s\">%s</a>" % (baseurl, svc["service_url"], svc["name"]),                                                                                  
                "%s/maintenance_windows#/show/%s" % (baseurl,mw["id"]),
                mw["description"],
                self.getLocalTime(mw["start_time"]),
                self.getLocalTime(mw["end_time"]),
                ))
    
    def serviceIsDisabled(self, id, action, svc, svcdetail, baseurl):
        """
            message for PagerDuty Service disabled
        """
        self.messages[id].append("%s because %s disabled by %s at %s" % (
                action,
                "<a href=\"%s%s\">%s</a>" % (baseurl, svc["service_url"], svc["name"]),
                "<a href=\"%s%s\">%s</a>" % (baseurl, svcdetail["user"]["user_url"], svcdetail["user"]["name"]),
                self.getLocalTime(svcdetail["maintenance_window"]["time"]),
                ))

    def serviceNotFound(self, id, key):
        """
        """
        self.messages[id].append("PagerDuty Service not found with KEY: %s" % key)

    def getAge(self, timestring):
        time_tuple = time.strptime(timestring, "%Y-%m-%dT%H:%M:%SZ")
        then = time.mktime(time_tuple)
        now = time.time() + 6*60*60 # improve this to calculate local offset
        delta = now - then
        return delta
    
    def getPagerDutyTime(self,ts):
        dt = datetime.datetime.strptime(ts,'%Y-%m-%dT%H:%M:%SZ')
        dt = dt - datetime.timedelta(seconds=time.timezone)
        return time.mktime(dt.timetuple())
    
    def getUTCTime(self,ts):
        """
            return datetime from PagerDuty UTC
        """
        dt = datetime.datetime.strptime(ts,'%Y-%m-%dT%H:%M:%SZ') - datetime.timedelta(seconds=time.timezone)
        return dt

    def getLocalTime(self,ts):
        sub = ts[:-6]
        return datetime.datetime.strptime(sub,'%Y-%m-%dT%H:%M:%S')

    def getZenossTime(self, ts):
        sub = ts[:-4]
        dt = datetime.datetime.strptime(sub,'%Y/%m/%d %H:%M:%S')
        return dt
        #return self.getTimeStamp(dt)        
        
    def getTimestamp(self,dt):
        """
            return seconds given a datetime object
        """
        return time.mktime(dt.timetuple())
