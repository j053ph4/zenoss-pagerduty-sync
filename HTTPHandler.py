import urllib,urllib2
try:
    import json
except ImportError:
    import simplejson as json

class HTTPHandler():
    """
    """
    def __init__(self):
        """
        """
        self.headers = {} #'Content-type':'application/json; charset=utf-8''
        self.verbose = False
             
    def persist(self,uri,params={}):
        """
            Handle persistent connections used by Zenoss
        """
        params = urllib.urlencode(params)
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        self.opener.open(uri, params)
        self.counter = 1

    def connect(self, uri):
        """
            Create urllib2.Request object with headers
        """
        self.session = urllib2.Request(uri)
        self.session.headers = self.headers

    def jsonify(self,data):
        """
            convert given data to JSON and add to session
        """
        data = json.dumps(data)
        self.session.add_data(data)
        if self.verbose == True:
            print "JSON data: %s" % data
    
    def post(self, data):
        """
            convert given data to JSON and add to session
        """
        self.jsonify(data)
 
    def put(self, data):
        """
            support HTTP PUT method
        """
        self.jsonify(data)
        self.session.get_method = lambda: "PUT"
        
    def delete(self, data):
        """
            support HTTP DELETE method
        """
        self.jsonify(data)
        self.session.get_method = lambda: "DELETE"

    def transact(self,data):
        """
            Conduct HTTP transaction against persistent session (Zenoss)
        """
        data = json.dumps([data])
        if self.verbose == True:
            print "JSON data: %s" % data
        self.response = json.loads(self.opener.open(self.session, data).read())
        if self.verbose == True:
            print "RESPONSE",self.response
        self.counter += 1

    def submit(self):
        if self.verbose == True:
            self.info()
        self.output = urllib2.urlopen(self.session)
        self.response = {}
        try:
            self.response = json.loads(self.output.read())
        except urllib2.URLError as e:
            if hasattr(e, 'reason'):
                self.response["reason"] = e.reason
            elif hasattr(e, 'code'):
                self.response["code"] = e.code
        if self.verbose == True:
            print "RESPONSE",self.response
                
    def info(self):
        """
            Print session data debug/troubleshooting
        """
        print "---SESSION DETAILS---"
        print "URL",self.session.get_full_url()
        print "HEADERS",self.session.header_items()
        print "METHOD",self.session.get_method()
        print "DATA",self.session.get_data()
        #print "TYPE",self.session.get_type()
        #print "SELECTOR",self.session.get_selector()
        print "---------------------"

