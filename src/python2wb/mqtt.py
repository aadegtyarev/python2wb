import paho.mqtt.client as mqtt
import json
import atexit

WB_CONTROLS_PATH = "/devices/%s/controls/%s"


class WbMqtt:
    controls = {}
    client = None
    virtual_devices = []
    qos_pub = 0
    driver_name = ""

    def __init__(
        self,
        server_url,
        port,
        username=None,
        password=None,
        qos_pub=1,
        qos_sub=0,
        base_subscribe_topic="#",
        client_id=None,
        driver_name="python2wb",
    ):
        self.qos_pub = qos_pub
        self.driver_name = driver_name

        def on_connect(client, userdata, flags, rc):
            """Событие, которое возникает после подключения к брокеру"""

            print("Connected with result code %s." % str(rc))
            client.subscribe(base_subscribe_topic, qos=qos_sub)
            client.message_callback_add(
                WB_CONTROLS_PATH % ("+", "+"), self._watch_control
            )

        def on_disconnect(client, userdata, rc=0):
            """Событие, которое возникает после отключения от брокера"""

            print("Disconnected result code %s." % str(rc))

        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = on_connect

        if username != None and password != None:
            self.client.username_pw_set(username, password)

        self.client.connect(server_url, port, 60)

    def get(self, control_path):
        """Получение значения контрола.

        Args:
            control_path (string): Путь к контролу в формате 'device/control'

        Returns:
            float, int, str: Значение контрола, храняшее в словаре контролов self.controls.
            # Преобразуется из строки в нужный тип.
        """

        return self.parse_value(self.controls.get(control_path))

    def set(self, control_path, value):
        """Запись значения в контрол.

        Args:
            control_path (string): Путь к контролу в формате 'device/control'
            value (float, int, str): Новое значение контрола, которое будет опубликовано в MQTT
        """

        try:
            # self.controls.update({control_path: value})
            self._publish(control_path, value)
        except Exception as e:
            raise e

    # Получение списка всех контролов
    def get_all(self):
        """Получение списка всех контролов

        Returns:
            dict: Содержимое словаря self.controls
        """
        return self.controls

    def _publish(self, control_path, value):
        """Внутреннее. Команда отправки значения в MQTT.

        Args:
            control_path (string): Путь к контролу в формате 'device/control'
            value (float, int, str): Новое значение контрола, которое будет опубликовано в MQTT

        Raises:
            e: Сообщение об ошибке
        """

        items = control_path.split("/")
        device_id = items[0]
        control_id = items[1]

        try:
            if device_id in self.virtual_devices:
                topic = WB_CONTROLS_PATH % (device_id, control_id)
                self.client.publish(topic, payload=value, qos=self.qos_pub, retain=True)
            else:
                topic = WB_CONTROLS_PATH % (device_id, control_id) + "/on"
                self.client.publish(
                    topic, payload=value, qos=self.qos_pub, retain=False
                )
        except Exception as e:
            raise e

    def _subscribe(self, control_path, callback, mode="value"):
        """Подписка на контролы

        Args:
            ontrol_path (string): Путь к контролу в формате 'device/control'
            callback (function): Обработчик события, параметры device_id, control_id, new_value
            mode (string): Переключатель режимов. value — подписываемся на значения, errors — на ошибки
        """

        items = control_path.split("/")

        if mode == "errors":
            topic = WB_CONTROLS_PATH % (items[0], items[1]) + "/meta/error"
        elif mode == "on":
            topic = WB_CONTROLS_PATH % (items[0], items[1]) + "/on"
        else:
            topic = WB_CONTROLS_PATH % (items[0], items[1])

        # Декоратор, который преобразует полученные из MQTT данные в понятные
        # абстракции: device_id, control_id, new_value
        def decorator(client, userdata, msg):
            """Декоратор, который преобразует полученные из MQTT данные в понятные
                абстракции: device_id, control_id, new_value

            Args:
                client (obj): Объект mqtt-клиента
                userdata (obj): Пользовательские данные
                msg (obj): Сообщение, содержит топик и значение
            """
            topic_path_arr = msg.topic.split("/")
            device_id = topic_path_arr[2]
            control_id = topic_path_arr[4]
            control_path = "%s/%s" % (device_id, control_id)
            new_value = msg.payload.decode()
            self.write_value_in_dic(control_path, new_value)

            callback(device_id, control_id, self.parse_value(new_value))

        self.client.message_callback_add(topic, decorator)

    def subscribe(self, control_path, callback):
        """Обёртка для _subscribe, подписывается на значение"""

        if type(control_path) == list:
            for control in control_path:
                self._subscribe(control, callback, mode="value")
        else:
            self._subscribe(control_path, callback, mode="value")

    def subscribe_on(self, control_path, callback):
        """Обёртка для _subscribe, подписывается на командный топик /on"""

        if type(control_path) == list:
            for control in control_path:
                self._subscribe(control, callback, mode="on")
        else:
            self._subscribe(control_path, callback, mode="on")

    def subscribe_errors(self, control_path, callback):
        """Обёртка для _subscribe, подписывается на ошибки"""

        if type(control_path) == list:
            for control in control_path:
                self._subscribe(control, callback, mode="errors")
        else:
            self._subscribe(control_path, callback, mode="errors")

    def _unsubscribe(self, control_path, mode="value"):
        """Отписка от контролов

        Args:
            control_path (string): Путь к контролу в формате 'device/control'
            mode (string): Переключатель режимов. value — отписываемся от значений, errors — от ошибок
        """

        items = control_path.split("/")
        if mode == "errors":
            topic = WB_CONTROLS_PATH % (items[0], items[1]) + "/meta/error"
        else:
            topic = WB_CONTROLS_PATH % (items[0], items[1])

        self.client.message_callback_remove(topic)

    def unsubscribe(self, control_path):
        """Обёртка для _unsubscribe, отписывает от значений"""

        if type(control_path) == list:
            for control in control_path:
                self._unsubscribe(control, mode="value")
        else:
            self._unsubscribe(control_path, mode="value")

    def unsubscribe_errors(self, control_path):
        """Обёртка для _unsubscribe, отписывает от ошибок"""

        if type(control_path) == list:
            for control in control_path:
                self._unsubscribe(control, mode="errors")
        else:
            self._unsubscribe(control_path, mode="errors")

    def subscribe_raw(self, mqtt_topic, callback):
        """Подписка на mqtt-топик.

        Args:
            mqtt_topic (string): Полный путь к mqtt-топику
            callback (function): Обработчик события, параметры mqtt_topic, new_value
        """

        def decorator(client, userdata, msg):
            """Декоратор, который преобразует полученные из MQTT данные в понятные
                абстракции mqtt_topic, new_value

            Args:
                client (obj): Объект mqtt-клиента
                userdata (obj): Пользовательские данные
                msg (obj): Сообщение, содержит топик и значение
            """

            msg_topic = msg.topic
            new_value = msg.payload.decode()

            callback(msg_topic, self.parse_value((new_value)))

        self.client.message_callback_add(mqtt_topic, decorator)

    def unsubscribe_raw(self, mqtt_topic):
        """Отписка от топика

        Args:
            mqtt_topic (string): Полный путь к mqtt-топику
        """

        self.client.message_callback_remove(mqtt_topic)

    def publish_raw(self, mqtt_topic, value, retain=False):
        """Публикация значений в mqtt-топик

        Args:
            mqtt_topic (string): Полный путь к mqtt-топику
            value (float, int, str): Новое значение топика, которое будет опубликовано в MQTT
            retain (bool, optional): Retain-флаг. По умолчанию False.
        """

        self.client.publish(mqtt_topic, payload=value, qos=self.qos_pub, retain=retain)

    def loop_forever(self):
        """Вечный цикл"""

        self.client.loop_forever()

    def clear(self):
        """Очистка виртуальных устройств, подписок и отключение клиента от брокера"""

        self.remove_all_virtual_devices()
        self.client.disconnect()

    def _watch_control(self, client, userdata, msg):
        """Внутреннее. Слежение за контролами всех устройств, кроме создаваемых из этого модуля.
            Если пришло сообщение на нашу подрписку, то добавляем или обновляем в
            self.controls запись в формате {путь_к_контролу: заначение}

        Args:
            client (obj): Объект mqtt-клиента
            userdata (obj): Пользовательские данные
            msg (obj): Сообщение, содержит топик и значение
        """

        items = msg.topic.split("/")
        control_path = "%s/%s" % (items[2], items[4])
        new_value = msg.payload.decode()

        self.write_value_in_dic(control_path, new_value)

    def _watch_virtual_control(self, client, userdata, msg):
        """Внутреннее. Слежение за контролами виртуальных устройств, созданных этим скриптом.
        Если пришло сообщение в командный топик /on виртуального контрола,
        то публикуем его в основное.

        Args:
            client (obj): Объект mqtt-клиента
            userdata (obj): Пользовательские данные
            msg (obj): Сообщение, содержит топик и значение
        """

        items = msg.topic.split("/")
        topic = WB_CONTROLS_PATH % (items[2], items[4])
        self.client.publish(
            topic, payload=msg.payload.decode(), qos=self.qos_pub, retain=True
        )

    def write_value_in_dic(self, control_path, new_value):
        """Запись изменившегося значения в словарь контролов

        Args:
            control_path (string): Путь к контролу в формате 'device/control'
            new_value (string): Новое значение типа str
        """
        self.controls.update({control_path: new_value})

    def create_virtual_device(self, device_id, device_title, controls):
        """Создание виртуального устройства

        Args:
            device_id (string): Идентификатор устройства
            device_title (string, dict): Заголовок устройства в виде строки или словаря с ключами в виде языков.
                Строка: "My Device Title"
                Словарь: {"ru": "Моё устройство", "en": "My Device"}
            controls (array of dict): Массив контролов,

        Returns:
            string: Идентификатор устройства
        """
        if device_id not in self.virtual_devices:
            topic = "/devices/%s/meta" % (device_id)

            if type(device_title) == dict:
                title = device_title
            else:
                title = {"en": device_title}

            value = {"driver": self.driver_name, "title": title}

            self.client.publish(
                topic, payload=json.dumps(value), qos=self.qos_pub, retain=True
            )
            self.virtual_devices.append(device_id)

            for control in controls:
                self._add_control(device_id, control)

            return device_id
        else:
            print("Virtual device %s already exists." % (device_id))
            return None

    def _add_control(self, device_id, control):
        """Внутреннее. Добавление контрола

        Args:
            device_id (string): Идентификатор топика в MQTT
            control (dic): Описание контрола. {"name": "control2", "title": "Control 2 Title", "type": "switch", "default": 1, "order": 2}
                title можно задавать для разных языков "title": {"ru": "Переключатель", "en": "Switch"}

        Returns:
            string: Путь к созданному контролу в формате 'device/control'
        """

        if device_id in self.virtual_devices:
            topic = WB_CONTROLS_PATH % (device_id, control.get("name"))

            title = control.get("title")

            if type(title) != dict:
                control["title"] = {"en": title}

            self.client.publish(
                "%s/meta" % (topic),
                payload=json.dumps(control),
                qos=self.qos_pub,
                retain=True,
            )

            # Обходим багу с wb-rules, когда события не прилетают в контролы без type по старому стилю
            self.client.publish(
                "%s/meta/type" % (topic),
                payload=control.get("type"),
                qos=self.qos_pub,
                retain=True,
            )
            self.client.publish(
                topic, payload=control.get("default"), qos=self.qos_pub, retain=True
            )

            self.client.message_callback_add(
                "%s/on" % topic, self._watch_virtual_control
            )

            control_path = "%s/%s" % (device_id, control.get("name"))
            self.controls.update({control_path: control.get("default")})

            return "%s/%s" % (device_id, control.get("name"))
        else:
            print(
                "Virtual device %s does not exist. First you need to create a device, then add controls to it."
                % (device_id)
            )
            return None

    def _delete_control(self, control_path):
        """Внутреннее. Удаление контрола виртуального устройства

        Args:
            control_path (string): Путь к контролу в формате 'device/control'
        """

        items = control_path.split("/")
        topic = WB_CONTROLS_PATH % (items[0], items[1])
        self.client.publish("%s/on" % (topic), "", qos=self.qos_pub)
        self.client.publish("%s/meta/type" % (topic), "", qos=self.qos_pub)
        self.client.publish("%s/meta" % (topic), "", qos=self.qos_pub)
        self.client.publish("%s" % (topic), "", qos=self.qos_pub)
        self.controls.pop(control_path)

    def _delete_virtual_device(self, device_id):
        """Внутреннее. Удаление виртуального устройства

        Args:
            device_id (string): Идентификатор устройства в MQTT
        """

        self.client.publish("/devices/%s/meta" % (device_id), "", qos=self.qos_pub)
        self.client.publish("/devices/%s" % (device_id), "", qos=self.qos_pub)
        index = self.virtual_devices.index(device_id)
        self.virtual_devices.pop(index)

    def add_control(self, device_id, control):
        """Обёртка для _add_control"""

        self._add_control(device_id, control)

    def remove_virtual_device(self, device_id):
        """Удалить виртуальное устройство

        Args:
            device_id (string): Идентификатор устройства в MQTT
        """

        virtual_controls = []
        for item in self.virtual_devices:
            self._delete_virtual_device(item)

            for key in self.controls:
                if item in key:
                    virtual_controls.append(key)

        for item in virtual_controls:
            self._delete_control(item)

    def remove_all_virtual_devices(self):
        """Удалить все виртуальные устройства"""

        for key in self.virtual_devices:
            self.remove_virtual_device(key)

    def parse_value(self, value):
        """В MQTT все значения текстовые, но чтобы было удобно работать
         мы преобразовываем их в типовые

        Args:
            value (string): Значение типа str

        Returns:
            float, int, str: Типизированное значение
        """
        value = value.strip()
        try:
            float(value)
            try:
                int(value)
                return int(value)
            except ValueError:
                return float(value)
        except:
            return value


@atexit.register
def goodbye():
    print("The script has finished.")
