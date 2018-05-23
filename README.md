# trackerapp
<img src="/imgs/logo.png" style="border: solid green 2px;" width="40"> IoT Tracker App (uses Kivy, PythonForAndroid, Device Cloud) 


## Getting Started
App tracks the mobile device (typically an IoT device connected to cloud services). The app is pre-configured with the following:
1. Recipient cell number (would be notified when App starts; device is home or away).
2. Latitude and Longitude values of the home address.
3. Google App Key for MapService - used to map the address to the lat/lng markers.

[App can be configured remotely from the cloud at runtime]


### Pre-requisites
The config files required by the App:
1. "iot-tracker.cfg" - IoT Device Cloud configuration
2. "app.cfg" - Recipient, home address configuration

## Installing


## Build tools

Note: App uses Python3.6 and needs some modifications to the Kivy VM from buildozer team to compile. One of the issues is to get SSL working with Crystax NDK - thanks to the P4A team for fixing it. However, at this time the fix is not available in the P4A master.

## Screenshots
<p>
<figure>
<figcaption><b>Application starts up:</b></figcaption>
<img src="/imgs/app_start.png" title="Application starts up" width="200">
</figure>
<br>
<figure>
<figcaption><b>Device at home:</b></figcaption>
<img src="/imgs/device_at_home.png" title="Device at home" width="200">
</figure>
<br>
<figure>
<figcaption><b>Device is away:</b></figcaption>
<img src="/imgs/device_is_away.png" title="Device is away" width="200">
</figure>
<br>
<figure>
<figcaption><b>Device is approaching or leaving the home:</b></figcaption>
<img src="/imgs/device_approaching_or_leaving_home.png" title="Device approaching or leaving home" width="200">
</figure>
</p>
