# Dymaptic Monitor 2 Teams
This script is setup as a Windows task that will pull Monitor Alerts and push them via a webhook to the Teams Channel of your choice.

Microsoft Teams has a connector called Incoming Webhook.  Add this to the Teams Channel of your Choice. When you configure the webhook you can add a custom image and a custom Name. We recommend ArcGIS Monitor Notifications.
You will then be provided a URL to send your notifications to. Be sure to copy and save that URL, you’ll need it in another step.

In order to get the notifications to Teams we have to use an intermediary. In this case we used a python script setup in Windows Task Scheduler to run once an hour.
 
The next step is to configure your python script to write to the webhook.  You will have to install the pymsteams python module: https://pypi.org/project/pymsteams/
It makes sending the Teams notifications very simple.
 
In the python script we also must connect to the ArcGIS Monitor API service, grab a token and request the alerts.
Once you have connected and received the token you can make calls to the alerts rest endpoint.

If you would like help building these notifications, let us know at info@dymaptic.com!


**dymaptic** (di-map-tick) www.dymaptic.com is an innovative, woman-owned GIS services provider and trusted Esri Partner with the know-how to handle all your needs for GIS consulting services and custom software development. Our team has collectively spent decades in the industry and counts many different types of organizations among our customers. These include Fortune 500 companies, non-profits, and large municipal governments. Our ability to provide precisely what our clients need has led those clients back to us again and again.

Our team’s software toolset is virtually limitless. We have proven experience in all aspects of project management, software engineering, and systems implementation across a wide range of technologies. Our team members take pride in their adaptability and breadth of knowledge, so we always seek the best solution for the task at hand regardless of what technologies that might mean. As an Esri Partner, we offer an exceptional level of expertise with GIS and have remarkably deep experience with the Esri platform. A few of the many services we provide are web, mobile, and desktop app development; database design and deployment; custom widget implementation; and server, database, and GIS configuration and administration.

We at dymaptic also put our expertise to use by building commercial off-the-shelf products. We will soon release infomaptic, which is a sleek, modern web app that generates beautiful, real-time reports from your ArcGIS data. Setting up pixel-perfect reports with infomaptic is simple and flexible with its interactive editor. Reports can include data values, maps, charts, graphs, and more, and are made accessible by URL. With infomaptic, a high-quality report for any ArcGIS feature is only a click away.
If there’s a task that intersects the worlds of GIS and software development, chances are the dymaptic team has done it and done it well. If you’re looking for a team of dedicated GIS software professionals who can deliver exactly what you need, look no further.

