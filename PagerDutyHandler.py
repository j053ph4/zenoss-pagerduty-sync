from HTTPHandler import HTTPHandler
import urllib

class PagerDutyHandler():
    """
    """
    def __init__(self, host, token,verbose=False):
        """
        """
        self.host = host
        self.token = token
        self.incidentEndpoint = "https://events.pagerduty.com/generic/2010-04-15/create_event.json"
        self.weburl = "https://%s" % self.host
        self.baseurl = "https://%s/api/v1" % self.host
        self.http = HTTPHandler()
        self.http.verbose = verbose
        self.http.headers['Content-type'] = 'application/json'
    
    def request(self, endpoint, data=None, token=True, method="GET"): # data should be list of dicts
        """
            Handle HTTP GET / POST operations against PagerDuty API
        """
        if data and method=="GETARG":
            endpoint += '?%s' % urllib.urlencode(data)

        if token == True:
            self.http.headers['Authorization'] = 'Token token=%s' % self.token

        self.http.connect(endpoint)

        if data:
            if method == "POST":
                self.http.post(data)
            if method == "PUT":
                self.http.put(data)
            if method == "GET":
                self.http.session.add_data(json.dumps(data))
                
        self.http.submit()
        return self.http.response
        
    def manageIncident(self,data,action="trigger"): 
        """
            action = [trigger|acknowledge|resolve] 
            Manage PagerDuty Incidents
        """
        data["event_type"] = action
        output = self.request(self.incidentEndpoint,data,token=False,method="POST")
        return output 
    
    def updateStatus(self,data): 
        """
            action = [trigger|acknowledge|resolved] 
            Manage PagerDuty Incidents
        """
        return self.request("%s/incidents" % self.baseurl, data, token=True, method="PUT")
    
    def getServiceList(self):
        """
        """
        return self.request("%s/services" % self.baseurl)
    
    def getServiceDetail(self,id):
        """
        """
        return self.request("%s/services/%s" % (self.baseurl,id))
    
    def getServiceLog(self,id):
        """
        """
        return self.request("%s/services/%s/log" % (self.baseurl,id))
    
    def getIncidentList(self):
        """
        """
        return self.request("%s/incidents" % self.baseurl)

    def getIncidentByKey(self,key):
        """
            Retrieve incident by its incident key
        """
        data = {"incident_key":key}
        return self.request("%s/incidents" % self.baseurl,data,token=True,method="GETARG")
    
    def getIncidentDetail(self,id):
        """
        """
        return self.request("%s/incidents/%s/log_entries" % (self.baseurl,id))
    
    def getIncidentLog(self,id):
        """
        """
        return self.request("%s/incidents/%s/log" % (self.baseurl,id))
    
    def getMaintenanceWindows(self):
        #data = {"type":"ongoing"}
        return self.request("%s/maintenance_windows" % self.baseurl)
    
    def findService(self,serviceKey):
        """
            find service info for given key
        """
        services = self.getServiceList()
        for s in services["services"] :
            if s["service_key"] == serviceKey:
                return s
        return None
        
    def getServiceStatus(self,data):
        return data["status"]
        
    def inMaintenance(self, data):
        """
        """
        if self.getServiceStatus(data) == 'maintenance':
            return True
        return False
    
    def isDisabled(self, data):
        """
        """
        if self.getServiceStatus(data) == 'disabled':
            return True
        return False
    
    def isActive(self, data):
        """
        """
        if self.getServiceStatus(data) == 'active':
            return True
        return False

