#!/usr/bin/env python

"""
Tracker app uses Kivy, Plyer APIs for location of a mobile device and
an IoT system APIs to (Device Cloud) to demonstrate tracking of a device
in the field.
"""
import json
import requests
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
        canvas.before:
            Color:
                rgb: (0,1,0)
            Rectangle:
                size: self.size
                pos: self.pos 
        text: "Tracker"
        font_size: "50sp"
        bold: True
        underline: True
            
    GridLayout:
        cols: 2
        rows: 5
        row_default_height: "60sp"
        row_force_default: True
        spacing_vertical: "2sp"
        Label:
            text: "Home:"
            font_size: "20sp"
            halign: "left"
            valign: "bottom"
        Label:
            text: app.location_home
            font_size: "10sp"
            halign: "left"
            valign: "bottom"
        Label:
            text: "Location status:"
            font_size: "20sp"
            halign: "left"
            valign: "bottom"
        Label:
            text: app.location_status
            font_size: "20sp"
            halign: "left"
            valign: "bottom"
        Label:
            text: "Distance(m):"
            font_size: "20sp"
            halign: "left"
            valign: "bottom"
        Label:
            text: app.distance
            font_size: "20sp"
            halign: "left"
            valign: "bottom"
        Label:
            text: "Location updates:"
            font_size: "20sp"
            halign: "left"
            valign: "bottom"
        Label:
            text: app.location_updates
            font_size: "20sp"
            halign: "left"
            valign: "bottom"
        Label:
            text: "Location"
            font_size: "20sp"
            halign: "left"
            valign: "bottom"
        Label:
            text: app.location_current
            font_size: "10sp"
            halign: "left"
            valign: "top"
            
    Label:
        text: ""
    Label:
        text: app.gps_status
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

    config_dir = getcwd() +'/'
    app_config_file = "app.cfg"
    app_id = "tracker_app"
    config_file = "iot-tracker.cfg"
    
    distance = StringProperty()
    location_home = StringProperty()
    location_current = StringProperty()
    gps_status = StringProperty('Click start for location updates')
    location_status = StringProperty('UNKNOWN')
    location_updates = StringProperty('0')

    def init_device_cloud(self):
        self.count=0
        self.app_config={}
        self.reached=False
        self.lastDist=0.0

        app_config_path = path.join(self.config_dir, self.app_config_file)
        # open the file in write mode (may need to update the geoCodes)
        app_config_file_handle = open(app_config_path, "r+")
        self.app_config.update(json.load(app_config_file_handle))

        # Initialize client
        self.client = iot.Client(self.app_id)

        # Use the iot-tracker.cfg iot application config file 
        self.client.config.config_file = self.config_file
        self.client.config.config_dir = self.config_dir
        self.client.initialize()
        self.client.action_register_callback("start", self.remote_start)
        self.client.action_register_callback("stop", self.remote_stop)
        self.client.action_register_callback("configure", self.remote_configure)

        # Connect to Device Cloud
        if self.client.connect(timeout=10) != iot.STATUS_SUCCESS:
            self.client.error("Failed")

        # At startup if only home address is configured get the geoCodes
        if self.app_config["home"]["address"] is not None and \
                self.app_config["home"]["lat"] is None or self.app_config["home"]["lon"] is None:
            geoCodes = self.getGeoCodes(self.app_config["home"]["address"])
            self.app_config["home"]["lat"]=geoCodes["lat"]
            self.app_config["home"]["lon"]=geoCodes["lng"]
            json.dump(self.app_config, app_config_file_handle)
        self.location_home = "{}\nlat:{},lon:{}".format(self.app_config["home"]["address"],
                                                        self.app_config["home"]["lat"],
                                                        self.app_config["home"]["lon"])

        # Identify the device using the android unique ID
        self.client.attribute_publish('id', uniqueid.id or "unavailable")
        # Send an SMS when app starts
        sms.send(recipient=self.app_config["recipient"], message="Tracking started for "+self.client.config.key)

    def remote_configure(self, client, params, user_data, request):
        isRecipientChanged = False
        isHomeLocationChanged = False
        if params["recipient"] is not None:
            isRecipientChanged = True
            self.app_config["recipient"]=params["recipient"]
        if params["address"] is None:
            if params["lat"] is not None:
                isHomeLocationChanged = True
                self.app_config["home"]["lat"]=params["lat"]
            if params["lon"] is not None:
                isHomeLocationChanged = True
                self.app_config["home"]["lon"]=params["lon"]
        else:
            geoCodes = self.getGeoCodes(params["address"])
            self.app_config["home"]["address"]=params["address"]
            self.app_config["home"]["lat"]=geoCodes["lat"]
            self.app_config["home"]["lon"]=geoCodes["lng"]
            isHomeLocationChanged = True
        if isHomeLocationChanged == True:
           self.location_home = "{}\nlat:{},lon:{}".format(self.app_config["home"]["address"],
                                                            self.app_config["home"]["lat"],
                                                            self.app_config["home"]["lon"])
        if isRecipientChanged == True or isHomeLocationChanged == True:
            app_config_path = path.join(self.config_dir, self.app_config_file)
            app_config_file_handle = open(app_config_path, "w")
            json.dump(self.app_config, app_config_file_handle)
            self.location_status = "UNKNOWN"
            self.root_widget.do_layout()
        return (iot.STATUS_SUCCESS, "")

    def build(self):
        self.init_device_cloud()
        try:
            gps.configure(on_location=self.on_location,
                          on_status=self.on_status)
        except NotImplementedError:
            self.gps_status = 'GPS implementation issue on your platform'
        self.root_widget = Builder.load_string(kv)
        return self.root_widget

    def start(self, minTime, minDistance):
        gps.start(minTime, minDistance)
        self.gps_status = "Starting location service..."

    def stop(self):
        gps.stop()
        self.gps_status = "Click start for location updates"

    def remote_start(self, client, params, user_data, request): # minTime, minDistance):
        gps.start(params["minTime"], params["minDistance"])

    def remote_stop(self, client, params, user_data, request):
        gps.stop()

    def getGeoCodes(self, address):
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {'sensor': 'false', 'address': address, 'key': self.app_config["appKey"]}
        r = requests.get(url, params=params)
        results = r.json()['results']
        status = r.json()['status']
        if status == 'OK':
            return results[0]['geometry']['location']
        else:
            return { "lat": 0, "lng": 0 }

    @mainthread
    def on_location(self, **kwargs):
        self.count = self.count+1 # count the number of gps updates 
        self.location_current = '\n'.join([
            '{}={}'.format(k, round(v, 6)) for k, v in kwargs.items() if k == 'lat' or k == 'lon'])
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
        lat1 = self.app_config["home"]["lat"]
        lon1 = self.app_config["home"]["lon"]
        lat2 = round(newLat, 6)
        lon2 = round(newLon, 6) 
        # Using Haversine formula
        p = 0.017453292519943295     #Pi/180
        a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
        dist = 12742000 * asin(sqrt(a)) #2*R*asin...
        self.distance = '{}'.format(round(dist, 2))
        self.location_updates = '{}'.format(self.count)
        if dist < 15: # home when closer than 10m to the marked point
            if self.location_status != "HOME":
                self.location_status = "HOME"
                self.client.telemetry_publish('status', 10)
                self.client.alarm_publish('status', 0, 'Device is home :)', republish=True)
                sms.send(recipient=self.app_config["recipient"], message=' is home')
                return True
        elif dist > 30: # away when longer than 100m from the marked point
            if self.location_status != "AWAY":
                self.location_status = "AWAY"
                self.client.telemetry_publish('status', 0)
                self.client.alarm_publish('status', 1, 'Device is away :(', republish=True)
                sms.send(recipient=self.app_config["recipient"], message=' is away')
                return True
        else:
            if self.location_status != "MEASURING":
                self.location_status = "MEASURING"
                self.client.telemetry_publish('status', 5)
                self.client.alarm_publish('status', 2, 'Measuring Device status :|', republish=True)
        if self.location_status == "UNKNOWN":
            self.location_status = "MEASURING"
            self.client.telemetry_publish('status', 5)
            self.client.alarm_publish('status', 2, 'Measuring Device status :|', republish=True)
        # notify distance remaining if moved more than 5m
        if abs(self.lastDist - dist) > 5:
            self.lastDist = dist
            self.client.telemetry_publish('distance', round(dist, 2))
        return False

    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}{}'.format(stype, status)

    def on_pause(self):
        gps.stop()
        return True

    def on_resume(self):
        gps.start(2000, 5)
        pass


if __name__ == '__main__':
    Gps().run()
