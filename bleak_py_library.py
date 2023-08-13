import asyncio
import argparse
import json
import bleak
import paho.mqtt.client as mqtt
import logging

logger = logging.getLogger(__name__)


# MQTT Settings
MQTT_BROKER_HOST = "192.168.12.225"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = "flotta"  # Replace with your MQTT username
MQTT_PASSWORD = "flotta"  # Replace with your MQTT password


device_history = []

# Global MQTT client
mqtt_client = None

async def connect_or_scan(device_name, device_uuid):
    logger.info("starting scan for device... ")
            
    # If not found in history, perform scanning and connecting
    scanner = bleak.BleakScanner()
    devices = await scanner.discover()
    
    for device in devices:
        try:
            print(device.name)
            if (device_name is not None and device.name == device_name) or \
               (device_uuid is not None and str(device) == device_uuid):
                await connect_and_read_characteristics(device)
                return True
        except Exception as e:
            print(f"Error while scanning/connecting to device: {e}")
    print("device %s: ",device_name," not found")
    return False

async def connect_and_read_characteristics(device):
    async with bleak.BleakClient(device) as client:
        print("HAHAHAH")
        try:
            if client.is_connected:
                await client.disconnect()
            await client.connect()
            
            # Add connected device to device history
            connected_device = {
                "name": device.name,
                "uuid": str(device)
            }
            device_history.append(connected_device)
            
            services = await client.get_services()
            
            characteristics_info = []
            for service in services:
                
                print(service.uuid)
                print("\n service \n")
                # print(service.characteristics)
                
                for char in service.characteristics:
                    char_info = {
                        "service_uuid": str(service.uuid),
                        "char_uuid": str(char.uuid),
                        "name": char.description,
                        "value": None,
                        "descriptors": []
                    }
                    
                    
                    if "notify" in char.properties:
                        print("\n READ \n")
                        
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            value_str = value.decode("utf-8")  # Decode the bytearray to a string

                            # print(value_str)
                            char_info["value"] = value_str
                        except Exception as e:
                            logger.error(
                                "  [Characteristic] %s (%s), Error: %s",
                                char,
                                ",".join(char.properties),
                                e,
                            )
                            print(e)

                    else:
                        logger.info(
                            "  [Characteristic] %s (%s)", char, ",".join(char.properties)
                        )

                    for descriptor in char.descriptors:
                        try:
                            descriptor_info = {
                                "descriptor_uuid": str(descriptor.uuid),
                                "descriptor_value": None
                            }
                            
                            # print(descriptor)
                            
                            value2 = await client.read_gatt_descriptor(descriptor.handle)
                            value_str2 = value2.decode("utf-8")
                            logger.info("    [Descriptor] %s, Value: %r", descriptor, value2)
                            print("    [Descriptor] %s, Value: %r", descriptor, value2)
                            descriptor_info["descriptor_uuid"] = descriptor.uuid
                            descriptor_info["value"] = value_str2
                            print("\n------------\n")
                            print(value_str2)
                            char_info["descriptors"].append(descriptor_info)
                        except Exception as e:
                            logger.error("    [Descriptor] %s, Error: %s", descriptor, e)
                    
                    characteristics_info.append(char_info)
            
            mqtt_client.publish("ble_scan/characteristics", json.dumps(characteristics_info))
        except Exception as e:
            print(f"Error while reading characteristics: {e}")
             
        
def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    
    try:
        payload_json = json.loads(payload)
        device_name = payload_json.get("device_name")
        device_uuid = payload_json.get("device_uuid")
        
        if device_name or device_uuid:
            asyncio.run(connect_or_scan(device_name, device_uuid))
        else:
            print("Invalid payload format.")

    except json.JSONDecodeError:
        print("Invalid JSON payload.")

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker.")
    client.subscribe("vitu/ble_scan/request")

def main(args):
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)  # Set MQTT username and password



    mqtt_client.on_log = lambda client, userdata, level, buf: print(buf)
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    
    mqtt_client.loop_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    main(args)
