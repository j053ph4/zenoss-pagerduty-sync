from HTTPHandler import HTTPHandler

class ZenossHandler():
    """
    """
    def __init__(self,host,username,password,verbose=False):
        """
        """
        self.routers = {
                        'MessagingRouter': 'messaging',
                        'EventsRouter': 'evconsole',
                        'ProcessRouter': 'process',
                        'ServiceRouter': 'service',
                        'DeviceRouter': 'device',
                        'NetworkRouter': 'network',
                        'TemplateRouter': 'template',
                        'DetailNavRouter': 'detailnav',
                        'ReportRouter': 'report',
                        'MibRouter': 'mib',
                        'ZenPackRouter': 'zenpack' 
                        }
        
        self.host = host
        self.username = username
        self.password = password
        self.baseurl = "http://%s:8080" % self.host
        self.login = {
                      "__ac_name": self.username,
                      "__ac_password": self.password,
                      "submitted": "true",
                      "came_from": "%s/zport/dmd" % self.baseurl
                      }
        self.http = HTTPHandler()
        self.http.verbose = verbose
        self.http.persist("%s/zport/acl_users/cookieAuthHelper/login" % self.baseurl ,self.login)

    def request(self,router,method,data=[]):
        """
            Handle HTTP GET / POST operations against Zenoss API
        """
        self.http.headers['Content-type'] = 'application/json; charset=utf-8'
        self.http.connect("%s/zport/dmd/%s_router" % (self.baseurl,self.routers[router]))
        data = {
                "action": router,
                "method": method,
                "data": data,
                "type": 'rpc',
                "tid" : self.http.counter
                }
        self.http.transact(data)
        return self.http.response
        
    def getEvents(self):
        """
            retrieve current console events
        """
        data = dict(start=0, limit=100, dir='DESC', sort='severity')
        data['params'] = dict(severity=[5,4,3,2,1,0])
        return self.request('EventsRouter','query',[data])["result"]
    
    def manageEventStatus(self,evids=[],action="acknowledge"):
        """
            manage event status
            action = [acknowledge|close]
        """
        data = [{"evids": evids}]
        return self.request('EventsRouter',action,data)
    
    def addEventMessage(self,evid,message):
        """
            manage event open/close/acknowledge status
        """
        data = {
                'evid': evid,
                'message':message
                }
        return self.request('EventsRouter','write_log',[data])
      
    def getEventDetails(self,evid):
        """
            manage event open/close/acknowledge status
        """
        data = {
                'evid': evid,
                }
        return self.request('EventsRouter','detail',[data])

    def getDevices(self, deviceClass='/zport/dmd/Devices/Server/Linux'):
        return self.request('DeviceRouter', 'getDevices', data=[{'uid': deviceClass, 'params': {} }])["result"]
