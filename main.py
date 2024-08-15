# import launcher  # noqa F401

# import wifiManager
import WIFI_CONFIG
import time
import uasyncio as asyncio
import drivers.mqttData as mqttData
import badger2040
import badger_os
import _thread
import machine
import lib.buttonManager as buttonManager


display = badger2040.Badger2040()
display.led(128)
buttons = buttonManager.ButtonManager(display)
asyncio.new_event_loop()
mqtt = mqttData.MQTTData(
    ssid=WIFI_CONFIG.SSID_2,
    psk=WIFI_CONFIG.PSK_2,
    device_num=0,
    server="instruments.local",
    port=1883,
    user=WIFI_CONFIG.MQTT_USER_1,
    password=WIFI_CONFIG.MQTT_PASSWORD_1,
    event_loop=asyncio.get_event_loop(),
    control_topic=WIFI_CONFIG.MQTT_CONTROL_TOPIC,
    display=display,
    buttons=buttons,
)
mqtt.client.DEBUG = False


# asyncio.new_event_loop()
# asyncio.get_event_loop().create_task(mqtt.connect())
# asyncio.get_event_loop().create_task(buttons.asyncPollButtons())
# asyncio.get_event_loop().create_task(launcher.start())
# asyncio.get_event_loop().run_forever()

update_display = True

display.set_thickness(2)
display.set_pen(15)
display.clear()
display.set_pen(0)
display.set_update_speed(badger2040.UPDATE_NORMAL)
loadingTextScaling = 1.25
loadingText = "JPG Industries"
loadingTextWidth = int(display.measure_text(loadingText, loadingTextScaling))
center_x = int(badger2040.WIDTH / 2)
x_pos = int(center_x - (loadingTextWidth / 2))
display.text(
    text="JPG Industries",
    x1=x_pos,
    y1=int(badger2040.HEIGHT / 2),
    angle=0,
    scale=loadingTextScaling,
)

asyncio.run(mqtt.connect())
if not mqtt.client.isconnected():
    print("CONNECTION FAILED: RESETTING DEVICE IN 10 SECONDS. (press rightbutton to cancel.)")
    display.led(255)
    for i in range(1000):
        time.sleep(.01)
        buttons.pollButtons()
    if buttons.getLastButton() == None:
        print("Machine reset")
        machine.reset()
    else:
        print("reset aborted")
loopCount= 0
while True:
    if not (loopCount % 4):
        display.update()
        update_display = False

    asyncio.run(mqtt.poll_for_messages())
    asyncio.run(buttons.pollButtons())

    newButton = buttons.getLastButton()
    if newButton == buttons.pin_c:
        # asyncio.get_event_loop().stop()
        machine.reset()
        break
    elif newButton == buttons.pin_up:
        mqtt.topicIncrement(increment=True)
        update_display = True
    elif newButton == buttons.pin_up:
        mqtt.topicIncrement(increment=False)
        update_display = True

    if mqtt.getDisplayUpdate() == True:
        print("updating display")
        update_display = True

    asyncio.sleep_ms(250)
    if loopCount < 1024:
        loopCount = loopCount + 1
    else:
        loopCount = 0
