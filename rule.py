from module.py_wb_mqtt import WbMqtt

wb = WbMqtt("wirenboard-a25ndemj.local", 1883)  # server, port

wb.create_virtual_device(
    "my-device",
    "My Device",
    [
        {
            "name": "control1",
            "title": "Temperature",
            "type": "value",
            "default": 50,
            "order": 1,
            "units": "°C",
        },
        {
            "name": "control2",
            "title": {"ru": "Переключатель", "ru": "Switch 1"},
            "type": "switch",
            "default": 1,
            "order": 2,
        },
        {
            "name": "control3",
            "title": "Текстовый контрол",
            "type": "text",
            "default": "",
            "order": 3,
        },
    ],
)


def log(device_id, control_id, new_value):
    print("log: %s %s %s %s" % (device_id, control_id, new_value, type(new_value)))
    path = "%s/%s" % (device_id, control_id)
    print("%s: %s" % (control_id, wb.get(path)))


def log_raw(mqtt_topic, new_value):
    print("log_raw: %s %s" % (mqtt_topic, new_value))


def change_a2(device_id, control_id, new_value):
    wb.set("wb-mr6c_226/K1", new_value)
    wb.set("wb-gpio/A3_OUT", new_value)


wb.subscribe("wb-gpio/A2_OUT", change_a2)
wb.subscribe('wb-gpio/+', log)
wb.subscribe_raw('/wbrules/log/#', log_raw)

wb.subscribe("my-device/control1", log)
wb.subscribe("my-device/control2", log)
wb.subscribe("my-device/control3", log)

wb.set("my-device/control1", 13.2)
wb.set("my-device/control2", 1)
wb.set("my-device/control3", "Строка")


try:
    wb.loop_forever()
finally:
    wb.clear()
