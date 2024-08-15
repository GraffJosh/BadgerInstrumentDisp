import uasyncio as asyncio

class MQTTDriver:
    def __init__(self, display, mqtt, buttons):
        self.display = display
        self.mqtt = mqtt
        self.buttons = buttons
        self.topics = None
        self.data = {}
        self.current_topic_index = 0
        
        self.display.set_font("gothic")

    async def setMQTTCallback(self):
        self.topics = self.mqtt.getTopics()
        callbackDict = {}
        for topic in self.topics:
            callbackDict[topic] = self.updateValues
        await self.mqtt.setCallback(topics_callbacks=callbackDict, referenceObject=self)
        
    async def updateValues(self,topic, value):
        self.data[topic] = value
         
    async def displayTopic(self, topic):
        return self.mqtt.