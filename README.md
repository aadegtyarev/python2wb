# python2wb
## Description
A wrapper for paho-mqtt with which you can work with MQTT [Wiren Board](https://wirenboard.com) from Python.

In the Wiren Board controller, information is exchanged through an MQTT broker, where devices are created according to the convention. Wiren Board has a standard tool for creating automation scripts [wb-rules](https://wirenboard.com/wiki/Wb-rules), but it has disadvantages: there are no community modules for different tasks, you cannot run and debug scripts on computer. Using Python allows you to write scripts the way you are used to and debug them in a familiar IDE: run the scripts locally on your computer and connect to the controller via MQTT.

Files in the repository:
- Module source code in the `src` folder
- Examples in the `examples` folder

It was done “for oneself”, without guarantees and technical support, only for those who understand what they are doing.

## Install
Install the module and dependencies using pip: `pip install paho-mqtt python2wb`.

## Starting work
Connect the module to your script, create an object and specify the parameters for connecting to the MQTT broker. Minimal script example:

```python
# Import module
from python2wb.mqtt import WbMqtt

# Creating an object and passing connection parameters
wb = WbMqtt("wirenboard-a25ndemj.local", 1883)  # server, port, username, password

# Declaring a function to handle subscriptions
def log(device_id, control_id, new_value):
    print("log: %s %s %s" % (device_id, control_id, new_value))

# Subscription to all system device topics
wb.subscribe('system/+', log)
# Subscribe to LVA15 value of device metrics
wb.subscribe('metrics/load_average_15min', log)

try:
    # Looping a script so it doesn't terminate
    wb.loop_forever()
finally:
    # Cleaning virtual devices and subscriptions before exiting
    wb.clear()
```

## Deploying the project to the controller
After writing and debugging the project on the computer, you need to move it to the controller. Let's say the script will be in the folder `/mnt/data/bin/python2wb/`:
1. Copy our files to the controller, for example, like this: `scp -r ./* root@wirenboard-a25ndemj.local:/mnt/data/bin/python2wb`
2. Go to the controller console again and make the script file executable `chmod +x /mnt/data/bin/python2wb/script.py`
3. Next, create a description of the service `nano /etc/systemd/system/python2wb.service`, for example with the following content:

```
[Unit]
Description=python2wb
After=network.target

[Service]
ExecStart=python3 /mnt/data/bin/python2wb/script.py
WorkingDirectory=/mnt/data/bin/python2wb/
StandardOutput=inherit
StandardError=inherit
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```
5. Start the service and place it in autostart `systemctl start python2wb ; systemctl enable python2wb`

## Working with device controls
The wrapper hides long topic names from the user, providing a simple interface for interacting with device controls, allowing you to read and write data using a short path notation `device_id/control_id`:
```python
# Write value to device control
wb.set("wb-mr6c_226/K1", new_value)

# Read value from control
print(wb.get("wb-mr6c_226/K1"))
```

## Subscription to controls
In addition, you can subscribe to one or more controls, including using the `+` wildcard character. Event processing occurs in the callback function that needs to be specified. The function returns:
- `device_id` — device identifier;
- `control_id` — control identifier `wb-gpio/A1_OUT` or list of controls `["wb-gpio/A1_OUT", "wb-gpio/A2_OUT"]`;
- `new_value` — new value of the control, converted to one of the types (`float`, `int`, `str`).

You can bind multiple subscriptions to one function:
```python
# Callback function
def log(device_id, control_id, new_value):
print("log: %s %s %s" % (device_id, control_id, new_value))

# Subscribe using wildcards
wb.subscribe('wb-gpio/+', log)

# Subscribe to one control
wb.subscribe("wb-mr6c_226/K1", log)

# Subscribe to several controls
wb.subscribe(["wb-gpio/A1_OUT", "wb-gpio/A2_OUT"], log)
```

You can also unsubscribe from the control if necessary:
```python
# Unsubscribe from one control
wb.unsubscribe("wb-mr6c_226/K1")

# Unsubscribe from several controls
wb.unsubscribe(["wb-gpio/A1_OUT", "wb-gpio/A2_OUT"])
```

## Subscribe to errors
When working with devices through the wb-mqtt-serial driver, you can receive exchange errors that are published by the driver in MQTT:
- r — error reading from device;
- w — error writing to the device;
- p — the driver could not maintain the specified polling period.

There can be several errors in one message, for example `rwp` or `rp`.

Subscribe to errors of a specific control:
```python

# Callback function
def log_errors(device_id, control_id, error_value):
print("log_errors: %s %s %s" % (device_id, control_id, error_value))

# Subscribe to control errors wb-mr6c_226/K1
wb.subscribe_errors("wb-mr6c_226/K1", log_errors)

```
You can use the `+` wildcard, for example:
```python
# Subscribe to all errors of the wb-mr6c_226 module
wb.subscribe_errors("wb-mr6c_226/+", log_errors)
```

You can also subscribe to errors from several controls through the list:
```python
# Subscribe to errors of several controls
wb.subscribe_errors(["wb-gpio/A1_OUT", "wb-gpio/A2_OUT"], log_errors)
```

Unsubscribe from one or more controls:
```python
# Note from control errors wb-mr6c_226/K1
wb.unsubscribe_errors("wb-mr6c_226/K1")

# Note about control errors with wildcard character
wb.unsubscribe_errors("wb-mr6c_226/+")

# Unsubscribe from errors of several controls
wb.unsubscribe_errors(["wb-gpio/A1_OUT", "wb-gpio/A2_OUT"])
```

## Subscribe to team topic /on
If you use a module in a converter, it will be useful to subscribe to a command topic in order to process actions in the web interface or third-party software. You can use the `+` wildcard character.

```python

# Callback function
def log_on(device_id, control_id, error_value):
print("log_on: %s %s %s" % (device_id, control_id, error_value))

# Subscribe to the command control topic wb-mr6c_226/K1
wb.subscribe_on("wb-mr6c_226/K1", log_on)

```

## Subscription to arbitrary MQTT topics
Sometimes you need to work with topics from third-party devices that do not know anything about the Wiren Board convention. For this purpose, there are functions for subscribing, unsubscribing and publishing with the full name of the topic. Event processing occurs in the callback function that needs to be specified. The function returns two parameters:
- `mqtt_topic` — full path to the topic;
- `new_value` — new value of type str.

When subscribing, you can use wildcard characters `+` - subscribe to one level and `#` - subscribe to all levels below.

Example:
```python
# Callback function
def log_raw(mqtt_topic, new_value):
print("log_raw: %s %s" % (mqtt_topic, new_value))

# Subscribe to topic
wb.subscribe_raw('/wbrules/#', log_raw)

# Publish a new value to a topic
wb.publish_raw('/wbrules/log/info', 'New Log Value')

# Unsubscribe from topic
wb.unsubscribe_raw('/wbrules/#')
```

## Virtual devices

You can also create virtual devices with an arbitrary number of controls and use them to interact with the user or store data:

```python
# Description of the virtual device
wb.create_virtual_device(
    "my-device", # device id
    {"ru": "Моё устройство", "en": "My Device"}, # device title
    [
        {
            "name": "temp", # control identifier in mqtt. Required.     
            "title": {"ru": "Температура", "en": "Temperature"}, # control title. Required.
            "type": "value", # control type. Required.
            "default": 50, # default value
            "order": 1, # number fo sorting
            "units": "°C" # unit         
        },
        {
            "name": "set_temp",
            "title": {"ru": "Уставка", "en": "Set Temperature"},
            "type": "value",
            "readonly": False, # prohibits editing the control. Default True.
            "default": 12.5,
            "order": 2,
            "units": "°C",
            "min": 0,
            "max": 100        
        },        
        {
            "name": "slider",
            "title": {"ru": "Ползунок", "en": "Slider"},
            "type": "range",
            "default": 13,
            "order": 3,
            "units": "%",
            "min": 10,
            "max": 35
        },          
        {
            "name": "switch",
            "title": {"ru": "Переключатель", "en": "Switch"},
            "type": "switch",
            "default": 1,
            "order": 4,
        },
        {
            "name": "log",
            "title": "Text Control", # you can have one line for all languages
            "type": "text",
            "default": "",
            "order": 5,
        },      
    ],
)
```
The title of the device and controls can be specified using the line `"My Device Title"` or a dictionary indicating the languages ​​`{"ru": "Switch", "en": "Switch 1"}`.

Controls are passed by an array of dictionaries. The description of the controls corresponds to the current [Wiren Board convention](https://github.com/wirenboard/conventions), with the exception of `default` for `switch`, the values ​​`0` and `1` should be used in the module.

List of types and available options for each type:
| type       | Possible values                  | default | order | units | min/max | readonly |
|------------|----------------------------------|---------|-------|-------|---------|----------|
| value      | any numbers: int, float          | +       |+      |+      |+        |+         |
| range      | any numbers: int, float          | +       |+      |+      |+        |+         |
| rgb        | format "R;G;B", each 0...255     | +       |+      |+      |         |+         |
| text       | text                             | +       |+      |+      |         |+         |
| alarm      | text                             | +       |+      |       |         |          |
| switch     | 0 or 1                           | +       |+      |       |         |+         |
| pushbutton | 1                                | +       |+      |       |         |          |

List of available `units`:
| Value     | Description, EN                                   |
|---        |---                                                |
| mm/h      | mm per hour, precipitation rate (rainfall rate)   |
| m/s       | meter per second, speed                           |
| W         | watt, power                                       |
| kWh       | kilowatt hour, power consumption                  |
| V         | voltage                                           |
| mV        | voltage (millivolts)                              |
| m^3/h     | cubic meters per hour, flow                       |
| m^3       | cubic meters, volume                              |
| Gcal/h    | giga calories per hour, heat power                |
| cal       | calories, energy                                  |
| Gcal      | giga calories, energy                             |
| Ohm       | resistance                                        |
| mOhm      | resistance (milliohms)                            |
| bar       | pressure                                          |
| mbar      | pressure (100Pa)                                  |
| s         | second                                            |
| min       | minute                                            |
| h         | hour                                              |
| m         | meter                                             |
| g         | gram                                              |
| kg        | kilo gram                                         |
| mol       | mole, amount of substance                         |
| cd        | candela, luminous intensity                       |
| %, RH     | relative humidity                                 |
| deg C     | temperature                                       |
| %         | percent                                           |
| ppm       | parts per million                                 |
| ppb       | parts per billion                                 |
| A         | ampere, current                                   |
| mA        | milliampere, current                              |
| deg       | degree, angle                                     |
| rad       | radian, angle                                     |

## Known issues
Created virtual devices are not always deleted. It is possible that the script ends before the deletion procedures are completed.

During installation, you need to create a description of the system for autorun, so you must update the controller software strictly via apt. When updating from a flash drive or in the web interface, the service description will be deleted. As a crutch, you can write a script on wb-rules that will run the script in Python :D
