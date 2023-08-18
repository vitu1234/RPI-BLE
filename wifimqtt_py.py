import asyncio
from datetime import datetime
import json
import os
import threading
import time
import bleak
import paho.mqtt.client as mqtt
import logging

logger = logging.getLogger(__name__)


# MQTT Settings
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = "flotta"  # Replace with your MQTT username
MQTT_PASSWORD = "flotta"  # Replace with your MQTT password

FLOTTA_SQLITE_DB = os.getenv("FLOTTA_SQLITE_DB", "../flotta-device-worker/flotta.db")
PERIODIC_DELAY = os.getenv("PERIODIC_DELAY", 60)


# Global MQTT client
mqtt_client = None

def on_message(client, userdata, message):
    
    print("RECEIVING DATA...........")
    payload = message.payload.decode("utf-8")
        
    try:
        payload_json = json.loads(payload)
                
        current_time = datetime.now()
        time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        characteristics_info = []
        connected_device = {
                "wireless_device_name": payload_json.get("name"),
                "wireless_device_manufacturer": payload_json.get("manufacturer"),
                "wireless_device_model": payload_json.get("model"),
                "wireless_device_sw_version": None,
                "wireless_device_identifier": payload_json.get("identifier"),
                "wireless_device_protocol":"MQTT",
                "wireless_device_connection": "Wi-Fi",
                "wireless_device_battery": None,
                "wireless_device_availability": None,
                "wireless_device_description": None,
                "wireless_device_last_seen": time_string,
                "device_properties": characteristics_info
            }
        
        device_properties = payload_json.get("properties")
       
        if device_properties is not None and isinstance(device_properties, list):
            for property_info in device_properties:               
                char_info = {
                "property_identifier": property_info.get("id"),
                "property_service_uuid": None,
                "property_name": property_info.get("name"),
                "property_access_mode": property_info.get("mode"),
                
                "property_unit": None,
                "property_description": None,
                "property_last_seen": time_string,
                "descriptors": []
                }
                
                 # Check if exists in the property_info
                if "state" in property_info:
                    char_info["property_state"] = property_info["state"]
                if "reading" in property_info:
                    char_info["property_reading"] = property_info["reading"]
                characteristics_info.append(char_info)
                
        else:
            print("Invalid device_properties field.")
        
        
        connected_device["device_properties"] = characteristics_info
        
        
        publishData(connected_device)
        

    except json.JSONDecodeError:
        print("Invalid JSON payload.")

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker.")
    client.subscribe("device/edge/upstream/wifi")
    client.subscribe("cloud/plugin/downstream/wifi")
def periodic_task():
    while True:
        time.sleep(PERIODIC_DELAY)  # Wait for 10 seconds
        # Call your desired function here
        print("Running the periodic wifi task...")
        # You can call the function you want to execute every 10 seconds
        # For example, you might call connect_or_scan() or any other relevant function

def publishData(payload):
    mqtt_client.publish("plugin/edge/upstream", json.dumps(payload))

def main():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)  # Set MQTT username and password



    mqtt_client.on_log = lambda client, userdata, level, buf: print(buf)
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    
    periodic_thread = threading.Thread(target=periodic_task)
    periodic_thread.daemon = True  # Allow the thread to exit when the main program exits
    periodic_thread.start()

    mqtt_client.loop_forever()
    
if __name__ == "__main__":
    main()
