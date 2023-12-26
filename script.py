# Импорт модуля
from module.python2wb import WbMqtt

# Создание объекта и передача параметров подключения
wb = WbMqtt("wirenboard-a25ndemj.local", 1883)  # server, port, username, password

# Создание виртуального устройства
wb.create_virtual_device(
    "my-device", # идентификатор устройства
    {"ru": "Моё устройство", "en": "My Device"}, # заголовой устройства (title)
    [
        {
            "name": "temp", # идентификатор контрола в mqtt. Обязательно.     
            "title": {"ru": "Температура", "en": "Temperature"}, # заголовок контрола (title). Обязательно.
            "type": "value", # тип контрола. Обязательно.
            "default": 50, # значение по умолчанию
            "order": 1, # порядковый номер для сортировки
            "units": "°C" # единица измерения          
        },
        {
            "name": "set_temp",
            "title": {"ru": "Уставка", "en": "Set Temperature"},
            "type": "value",
            "readonly": False, # запрещает редактировать контрол. По умолчанию True.
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
            "title": "Текстовый контрол",
            "type": "text",
            "default": "string",
            "readonly": False,
            "order": 5,
        },      
    ],
)

# Функция публикации логов в консоль wb-rules
def log(device_id, control_id, new_value):
    log_value = "[py-wb-mqtt] Изменён контрол %s, значение: %s" % (control_id, new_value)
    wb.publish_raw("/wbrules/log/info", log_value, retain=True)

# Функция установки температуры в контроле
def set_temp(device_id, control_id, new_value):
    wb.set("my-device/temp", new_value)

wb.subscribe("my-device/set_temp", set_temp)
wb.subscribe("my-device/+", log)

try:
    # Зацикливание скрипта, чтобы он не завершался
    wb.loop_forever()
finally:
    # Очистка винтуальных устройств и подписок перед выходом
    wb.clear()