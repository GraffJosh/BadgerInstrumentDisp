import lib.mqtt_as as uMQTTClient
import badger2040
import uasyncio as asyncio
import json


# {
#   "topics": {
#     "vessels/self/environment/depth/belowTransducer": {
#       "name": "Depth",
#       "digits":"1",
#       "units": "m"
#     },
#     "vessels/self/environment/wind/speedApparent": {
#       "name": "Wind Speed",
#       "digits":"1",
#       "units": ""
#     }
#   }
# }

class MQTTData:
    def __init__(
        self,
        ssid,
        psk,
        device_num,
        server,
        port,
        user,
        password,
        event_loop,
        control_topic=[{"name": "", "topic": ""}],
        display: Badger2040 = None,
        buttons: ButtonManager = None,
    ):
        # mqttClient = MQTTClient("badger_display_" + str(device_num), server, port, user, password)
        #  config['server'] = 'test.mosquitto.org'

        config = uMQTTClient.config
        config["client_id"] = "badger_display_" + str(device_num)  # Change to suit
        self.TOPIC = config["client_id"]
        config["ssid"] = ssid
        config["wifi_pw"] = psk
        config["user"] = user  # Change to suit
        config["password"] = password  # Change to suit
        config["server"] = server  # Change to suit
        config["port"] = port  # Change to suit
        config["will"] = (self.TOPIC, "Goodbye cruel world!", False, 0)
        config["keepalive"] = 120
        config["queue_len"] = 1  # Use event interface with default queue
        # config["subs_cb"] = self.callback
        self.client = uMQTTClient.MQTTClient(config)
        self.outages = 0
        self.message_count = 0
        self.control_topic = control_topic
        self.event_loop = event_loop
        self.data = {}
        self.current_topic_index = 0
        self.display = display
        self.display.set_font("sans")
        self.buttons = buttons
        self.requestUpdateDisplay = False
        self.displayType = 0
        self.updateLock = asyncio.Lock()

    async def connect(self):
        global outages
        try:
            print("connecting: ")
            await self.client.connect(quick=True)
            for coroutine in (self.up, self.down, self.messages):
                print("create tasks: ", coroutine)
                self.event_loop.create_task(coroutine())
            n = 0
        except OSError as e:
            print("Connection failed." + str(e))
            return

    async def setTopics(self, topics={}):
        for topic in topics.keys():
            if topics[topic]["name"] not in self.getTopics():
                print("Adding topic: ", topic)
                self.data[topic] = topics[topic]
                await self.client.subscribe(topic, 1)

    async def getDisplayUpdate(self):
        async with self.updateLock:
            return self.requestUpdateDisplay

    def getTopics(self):
        return list(self.data.keys())

    def getTopicName(self, topic):
        return self.data[topic]["name"]

    def getTopicValue(self, topic):
        if "digits" in self.data[topic].keys():
            data = float(self.data[topic]["current"])
            data = round(data,int(self.data[topic]["digits"]))
        else:
            data =self.data[topic]["current"]    
        return data


    def getTopicUnits(self, topic):
        return self.data[topic]["units"]

    def getTopicByIndex(self, index):
        return list(self.data.keys())[index]

    def setTopicValue(self, topic, value):
        self.data[topic]["current"] = value

    def setDisplayType(self, displayType):
        self.displayType = displayType

    def setTopicIndex(self, topic_index):
        if topic_index > len(self.getTopics()) - 1:
            topic_index = 0
        elif topic_index < 0:
            topic_index = len(self.getTopics()) - 1
        self.current_topic_index = topic_index
        print("Update Selected Topic: ", self.current_topic_index)

    def topicIncrement(self, increment=True):
        if increment:
            self.setTopicIndex(self.current_topic_index + 1)
        else:
            self.setTopicIndex(self.current_topic_index - 1)

    async def messages(self):
        async for topic, msg, retained in self.client.queue:
            self.display.led(128)
            topic_str = str(topic.decode())
            data_str = str(msg.decode())
            if self.client.DEBUG:
                print(f'Topic: "{topic.decode()}" Message: "{msg.decode()}" Retained: {retained}')
            if topic_str == self.control_topic:
                payload = json.loads(msg)
                print("control topic receieved: ", payload)
                await self.setTopics(payload["topics"])
            else:
                print("topic_str")
                # self.data[topic_str] = data_str
                self.setTopicValue(topic_str, data_str)
            if topic_str == self.getTopics()[self.current_topic_index]:
                await self.update_display()
            self.display.led(0)

    async def down(self):
        while True:
            await self.client.down.wait()  # Pause until connectivity changes
            self.client.down.clear()
            self.outages += 1
            print("WiFi or broker is down.")

    async def up(self):
        while True:
            await self.client.up.wait()
            self.client.up.clear()
            print("We are connected to broker.")
            await self.client.subscribe(self.control_topic)

    async def poll_for_messages(self):
        # await asyncio.sleep(5)
        # print("publish", self.message_count)
        # If WiFi is down the following will pause for the duration.
        await self.client.publish(self.TOPIC, "Control Topic:{} {}".format(self.control_topic,self.message_count), qos=1)
        self.message_count += 1

    async def update_display(self):
        topic_name = self.getTopicName(self.getTopicByIndex(self.current_topic_index))
        topic_value = "{}{}".format(
            self.getTopicValue(self.getTopicByIndex(self.current_topic_index)),
            self.getTopicUnits(self.getTopicByIndex(self.current_topic_index)),
        )
        print(
            "Current topic: index: ",
            self.current_topic_index,
            " Topic: ",
            topic_name,
            " value: ",
            topic_value,
        )
        center_x = int(badger2040.WIDTH / 2)
        center_y = int(badger2040.HEIGHT / 2)
        text_height = 15
        name_text_scaling = 1
        name_text_width = int(self.display.measure_text(topic_name, name_text_scaling))
        while (name_text_width > badger2040.WIDTH) and name_text_scaling > 0.5:
            name_text_scaling = name_text_scaling - 0.1
            name_text_width = int(self.display.measure_text(topic_name, name_text_scaling))

        name_text_x_pos = int(center_x - (name_text_width / 2))
        name_text_y_pos = int(text_height)
        name_text_height = int(text_height * name_text_scaling)

        data_text_scaling = 3
        data_text_width = int(self.display.measure_text(topic_value, data_text_scaling))
        # scale the text down until it fits, to a limit.
        while (data_text_width > badger2040.WIDTH) and data_text_scaling > 1.5:
            data_text_scaling = data_text_scaling - 0.1
            data_text_width = int(self.display.measure_text(topic_name, data_text_scaling))
        data_text_height = int(text_height * data_text_scaling + 5)
        data_text_x_pos = int(center_x - (data_text_width / 2))
        data_text_y_pos = int(name_text_y_pos + data_text_height)

        self.display.set_pen(15)
        self.display.clear()
        self.display.set_pen(0)

        self.display.set_thickness(2)
        self.display.text(
            text=topic_name,
            x1=name_text_x_pos,
            y1=name_text_y_pos,
            angle=0,
            scale=name_text_scaling,
            wordwrap=int(badger2040.WIDTH),
        )

        self.display.set_thickness(5)
        self.display.text(
            text=topic_value,
            x1=data_text_x_pos,
            y1=data_text_y_pos,
            angle=0,
            scale=data_text_scaling,
            wordwrap=int(badger2040.WIDTH),
        )
        self.display.set_update_speed(badger2040.UPDATE_TURBO)
        async with self.updateLock:
            self.requestUpdateDisplay = True
        # self.display.update()
        # self.display.partial_update(data_text_offset, 40, data_text_width, 56)
