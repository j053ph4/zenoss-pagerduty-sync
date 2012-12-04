zenoss-pagerduty-sync
=====================

zenoss-pagerduty-sync

This script creates a tight linkage between Zenoss and PagerDuty by synchronizing states between the two tools, 
and by replicating PagerDuty data in the Zenoss Event Console details.

The script has 2 modes:  a "create" mode intended to be run as an Zenoss "event command" or "trigger", and an "update"
mode intended 