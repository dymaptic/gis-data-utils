import requests
import pymsteams
import keyring
import json

teamsWebHook = r"WEBHOOK_URL_FROM_TEAMS"

monitorServer = r"https://YOUR_MONITOR_SERVER"

#first get a token to monitor

tokenUrl = r"{}/rest/api/auth/token".format(monitorServer)
alertUrl = r"{}/rest/api/monitor/alerts?token=".format(monitorServer)

#used keyring to save the account to log into ArcGIS Monitor
postData = {"username":"Site","password":keyring.get_password("monitor","Site")}

responseJson = requests.post(tokenUrl,data=postData,verify=False).json()
token = responseJson['token']

from datetime import datetime,timedelta
#getAlerts
endTime = datetime.now()
startTime = endTime - timedelta(hours=1)

endTimeEpoch = int(endTime.timestamp()) * 1000
startTimeEpoch = int(startTime.timestamp()) * 1000

#from the last hour
postData = { "where": {"startTime": startTimeEpoch, "endTime": endTimeEpoch } }
alertUrl = r"{}/rest/api/monitor/alerts?token={}".format(monitorServer,token)

alerts = requests.post(alertUrl,data=json.dumps(postData),verify=False).json()

teamsMessage = ""

#this is the business logic to parse the alerts.
for alert in alerts['data']:
    if alert['hasAlerts']:
        teamsMessage = "The following Items are alerting:<br>"
        for alertingView in alert['alertingViews']:
            teamsMessage += "<b>{}</b><br>".format(alertingView["name"])
            print(alertingView["name"])
            for counter in alertingView['countersWithAlerts']:

                for counterAlert in counter['alerts']:
                    teamsMessage += "&nbsp;&nbsp;&nbsp;&nbsp;<i>{}</i> {} {}<br>".format(counter['counterInstance'],counter['counterName'],counterAlert['note'])

        teamsMessage += "<br>"
    else:
        teamsMessage = "Nothing is alerting at the moment."

teamsMessageWebHook = pymsteams.connectorcard(teamsWebHook)
teamsMessageWebHook.title("ArcGIS Monitor Hourly Updates")
teamsMessageWebHook.text(teamsMessage)
teamsMessageWebHook.addLinkButton("ArcGIS Monitor Administrator",monitorServer)
teamsMessageWebHook.send()