# Import module
from python2wb.mqtt import WbMqtt

# Creating an object and passing connection parameters
wb = WbMqtt("wirenboard-a25ndemj.local", 1883)  # server, port, username, password

# Create a virtual device
wb.create_virtual_device(
    "my-device", # device identifier
    {"ru": "Моё устройство", "en": "My Device"}, # device title
    [
        {
            "name": "temp", # control identifier in mqtt. Required.     
            "title": {"ru": "Температура", "en": "Temperature"}, # control title. Required.
            "type": "value", # control type. Required.
            "default": 50, # default value
            "order": 1, # order number for sorting
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
            "name": "text-demo",
            "title": {"ru": "Текстовый контрол", "en": "Text Control"},
            "type": "text",
            "default": "string",
            "readonly": False,
            "order": 5,
        },      
    ],
)

# Function for publishing logs to the wb-rules console
def log(device_id, control_id, new_value):
    log_value = "[python2wb] Changed control %s, value: %s" % (control_id, new_value)
    
    # We publish the log directly to the MQTT topic
    wb.publish_raw("/wbrules/log/info", log_value, retain=True)

# Temperature setting function in control
def set_temp(device_id, control_id, new_value):
    wb.set("my-device/temp", new_value)

# Subscribe to control
wb.subscribe("my-device/set_temp", set_temp)

# Subscription to all device controls my-device
wb.subscribe("my-device/+", log)

# Subscription to a list of controls
wb.subscribe(["wb-gpio/A1_OUT", "wb-gpio/A2_OUT"], log)

try:
    # Looping a script so it doesn't terminate
    wb.loop_forever()
finally:
    # Cleaning virtual devices and subscriptions before exiting
    wb.clear()
