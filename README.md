# trackerapp
IoT Tracker App (uses Kivy, PythonForAndroid, Device Cloud)

The app tracks the mobile device (typically an IoT device connected to cloud services). The app is pre-configured with the following:
1. SMS of the recipient (would be notified when App starts; device arrives or departs the point of interest).
2. Latitude and Longitude values of the point of interest.

[TODO: Above should be configurable from the cloud at runtime]

Note: App uses Python3.6 and needs some modifications to the Kivy VM from buildozer team to compile. One of the issues is to get SSL working with Crystax NDK - thanks to the P4A team for fixing it. However, at this time the fix is not available in the P4A master.

The config files required by the App:
1. "iot-tracker.cfg" - IoT cloud configuration
2. "app.cfg" - Recipient, point of interest configuration
