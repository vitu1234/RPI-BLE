from bluepy.btle import Scanner, Peripheral

def discover_ble_devices(target_device_name):
    scanner = Scanner()
    devices = scanner.scan(10)  # Scan for 10 seconds

    matching_devices = []
    for device in devices:
        device_name = device.getValueText(9)
        print(f"Found BLE Device: {device.addr} ({device_name})")
        if device.getValueText(9) is not None and target_device_name in device.getValueText(9):
            matching_devices.append(device)

    return matching_devices

def connect_and_read_data(device_address):
    device = Peripheral(device_address)

    # Discover services and characteristics
    for service in device.getServices():
        print(f"Service UUID: {service.uuid}")

        for char in service.getCharacteristics():
            print(f"Characteristic UUID: {char.uuid}")
            value = char.read()
            print(f"Characteristic Value: {value.decode('utf-8')}")

    device.disconnect()

if __name__ == "__main__":
    target_device_name = "BME280_ESP32"  # Replace with the actual BLE device name
    devices = discover_ble_devices(target_device_name)
    
    if devices:
        for device in devices:
            print(f"Found BLE Device: {device.addr}")
            connect_and_read_data(device.addr)
    else:
        print(f"No devices found with the name '{target_device_name}'.")
