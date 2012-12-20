zenoss-pagerduty-sync
=====================

zenoss-pagerduty-sync

This script creates a tight linkage between Zenoss and PagerDuty by synchronizing states between the two tools, 
and by replicating PagerDuty data in the Zenoss Event Console details.  It has been tested against Zenoss 3.2.1, but
may require further modifcation to work with Zenoss 4.x.


Usage: zenpagerduty.py [options] arg

Options:
  -h, --help            show this help message and exit
  -z ZENHOST, --zenhost=ZENHOST
                        Zenoss Server hostname
  -u ZENUSER, --zenuser=ZENUSER
                        Zenoss admin username
  -p ZENPASS, --zenpass=ZENPASS
                        Zenoss admin password
  -e EVID, --evid=EVID  Zenoss Event ID
  -V, --zenver          True if Zenoss version >= 4
  -H PDHOST, --pdhost=PDHOST
                        Pagerduty hostname
  -T PDTOKEN, --pdtoken=PDTOKEN
                        Pagerduty token
  -U PDUSER, --pduser=PDUSER
                        Pagerduty User Key (for tracking auto updates)
  -S SERVICEKEY, --servicekey=SERVICEKEY
                        Pagerduty Service Key
  -a ACTION, --action=ACTION
                        one of [create|update]
  -v, --verbose         Show additional output


The script has 2 modes:  a "create" mode intended to be run as an Zenoss "event command" or "trigger", and an "update"
mode intended to be run via cron.


The event command/trigger should look something like:

$DIR/pagerduty/zenpagerduty.py -a "create" -z "ZENOSS_SERVER" -u "ZENOSS_ADMIN" -p "ZENOSS_PASSWORD" -H "PAGERDUTY_HOSTNAME" -T "PAGERDUTY_API_TOKEN" -U "PAGERDUTY_USER" -e "${evt/evid}" -S "PAGERDUTY_SERVICEKEY"


while the cron entry should look like:

bash -lc "/opt/zenoss/libexec/pagerduty/zenpagerduty.py -a update -z ZENOSS_SERVER -u ZENOSS_ADMIN -p ZENOSS_PASSWORD -H PAGERDUTY_HOSTNAME -T PAGERDUTY_API_TOKEN -U PAGERDUTY_USER >/dev/null 2>&1"


The script performs the following functions:

- The "zenpagerduty.py" script can take the place of the "curl" command per PagerDuty's Integration guide
- Each event command (associated with a PagerDuty Service) will be the same except for the "-S" (Sservice key) flag
- PagerDuty manages the alerting methods and escalations for each alert (PagerDuty refers to them as “Incidents”)
- Events/Incidents can be dealt with (acknowledged or resolved) in either Zenoss or PagerDuty. Changes in one are replicated to the other.
- At each update, Pagerduty Incidents and Zenoss events are compared.  Whichever was last updated "wins" and its state is changed in the other.
- At each update, Zenoss' Event Console is updated with PagerDuty Incident History details
- During creation, the script polls the target PagerDuty service for its current state.
- Services in a Maintenance Window will be automatically acknowledged and amended with details about the maintenance window (start/end times, who created it, and description if available.  
- Disabled Services are left open in the Zenoss console, but the log is amended with details about the disabled Service (who disabled, when, etc).


Some known/suspected issues:

- At the time of this writing, some bugs exist in the Zenoss 4.x JSON API that may prevent this script from working at all (not yet tested).
- May need further development to be fully Zenoss 4.x compatible.  At present, the script will resolve any PagerDuty incidents that are not in the Zenoss console.  This is done in order to avoid an expensive query of Zenoss Event History table (which has changed in 4.x), but may need to be changed somewhat.
- Key parts of the script rely on parsing date/time/timezone information from both Zenoss and Pagerduty. The script attempts to convert all time data to epoch prior to comparison, but it's likely that the methods used here are inadequate to the task or possible .
- Performance under load conditions are unknown and may require some readjustment
- The "synchronization" may need to be handled a different way after a large number of PagerDuty incidents exist.


The script has been "functionally" tested, but not yet used in a "production" environment.  Any suggestions or observations are most welcome. 


