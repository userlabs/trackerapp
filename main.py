#!/usr/bin/env python

"""
Tracker app uses Kivy, Plyer APIs for location of a mobile device and
an IoT system APIs to (Device Cloud) to demonstrate tracking of a device
in the field.
"""
import json
from os import getcwd,path

from kivy.lang import Builder
from plyer import gps
from plyer import uniqueid
from plyer import sms
from kivy.app import App
from kivy.properties import StringProperty
from kivy.clock import mainthread
from math import cos, asin, sqrt
import device_cloud as iot


kv = '''
BoxLayout:
    orientation: 'vertical'

    Label:
        text: app.gps_location

    Label:
        text: app.gps_status

    Label:
        text: app.gps_distance

    Label:
        text: app.gps_location_status

    BoxLayout:
        size_hint_y: None
        height: '48dp'
        padding: '4dp'

        ToggleButton:
            text: 'Start' if self.state == 'normal' else 'Stop'
            on_state:
                app.start(2000, 5) if self.state == 'down' else \
                app.stop()
'''


class Gps(App):

    gps_distance = StringProperty()
    gps_location = StringProperty()
    gps_status = StringProperty('Click start for location updates')
    gps_location_status = StringProperty('location_status=unknown')

    def init_device_cloud(self):
        self.count=0
        self.app_config={}
        self.reached=False
        self.lastDist=0

        config_dir = getcwd() +'/'
        app_config_file = "app.cfg"
        app_config_path = path.join(config_dir, app_config_file)
        config = open(app_config_path, "r")
        self.app_config.update(json.load(config))

        # Initialize client
        app_id = "tracker_app"
        self.client = iot.Client(app_id)

        # Use the iot-tracker.cfg iot application config file 
        config_file = "iot-tracker.cfg"
        self.client.config.config_file = config_file
        self.client.config.config_dir = config_dir
        self.client.initialize()

        # Connect to Device Cloud
        if self.client.connect(timeout=10) != iot.STATUS_SUCCESS:
            self.client.error("Failed")
        
        # Identify the device using the android unique ID
        self.client.attribute_publish('id', uniqueid.id or 'unknown')
        # Send an SMS when app starts
        sms.send(recipient=self.app_config["recipient"], message="Tracker app started "+self.client.config.key)

    def build(self):
        self.init_device_cloud()
        try:
            gps.configure(on_location=self.on_location,
                          on_status=self.on_status)
        except NotImplementedError:
            self.gps_status = 'GPS implementation issue on your platform'
        return Builder.load_string(kv)

    def start(self, minTime, minDistance):
        gps.start(minTime, minDistance)

    def stop(self):
        gps.stop()

    @mainthread
    def on_location(self, **kwargs):
        self.count = self.count+1 # count the number of gps updates 
        self.gps_location = '\n'.join([
            '{}={}'.format(k, v) for k, v in kwargs.items()])
        for k, v in kwargs.items():
            if k == 'lat':
                self.lat = v
            if k == 'lon':
                self.lon = v
            if k == 'speed':
                self.speed = v
            if k == 'bearing':
                self.bearing = v #heading and bearing are not exactly the same.. but assuming them to be the same for now 
            if k == 'altitude':
                self.altitude = v
        if self.client.is_alive():
            toPublish=self.checkDistance(self.lat, self.lon)
            if toPublish:
                self.client.log(iot.LOGINFO, "Publishing Location info")
                self.client.location_publish(self.lat, self.lon, self.bearing, self.altitude)

    def checkDistance(self, newLat, newLon):
        lat1 = self.app_config["marker"]["lat"]
        lon1 = self.app_config["marker"]["lon"]
        lat2 = round(newLat, 6)
        lon2 = round(newLon, 6) 
        # Using Haversine formula
        p = 0.017453292519943295     #Pi/180
        a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
        dist = 12742000 * asin(sqrt(a)) #2*R*asin...
        self.gps_distance = 'distance={}-{}\n'.format(dist, self.count)
        if dist < 10: # arrived when closer than 10m to the marked point
            if self.reached == False:
                self.reached=True 
                self.client.telemetry_publish('arrive', 1)
                sms.send(recipient=self.app_config["recipient"], message=' arrived')
                self.gps_location_status = 'location_status={}\n'.format('ARRIVED')
                return True
        elif dist > 100: # departed when longer than 100m from the marked point
            if self.reached == True:
                self.reached=False
                self.client.telemetry_publish('depart', 1)
                sms.send(recipient=self.app_config["recipient"], message=' departed')
                self.gps_location_status = 'location_status={}\n'.format('DEPARTED')
                return True
        # notify distance remaining if moved more than 20m
        if self.lastDist > 0 and abs(self.lastDist - dist) > 20: 
            self.lastDist = dist
            self.client.telemetry_publish('distance', dist)
        return False

    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}\n{}'.format(stype, status)

    def on_pause(self):
        gps.stop()
        return True

    def on_resume(self):
        gps.start(2000, 5)
        pass


if __name__ == '__main__':
    Gps().run()
