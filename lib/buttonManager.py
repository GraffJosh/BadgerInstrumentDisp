import badger2040
import badger_os
import uasyncio as asyncio


class ButtonManager:
    def __init__(self, display):
        self.display = display
        self.pin_a = badger2040.BUTTON_A
        self.pin_b = badger2040.BUTTON_B
        self.pin_c = badger2040.BUTTON_C
        self.pin_up = badger2040.BUTTON_UP
        self.pin_down = badger2040.BUTTON_DOWN
        self.pin_list = [self.pin_a, self.pin_b, self.pin_c, self.pin_up, self.pin_down]
        self.last_button = None

    def getLastButton(self):
        last_pressed = None
        last_pressed = self.last_button
        self.last_button = None
        return last_pressed

    async def wait_for_user_to_release_buttons(self):
        while self.display.pressed_any():
            asyncio.sleep(0.01)

    async def pollButtons(self):
        for pin in self.pin_list:
            if self.display.pressed(pin):
                # print("buttonPressed: ", pin)
                self.last_button = pin
                await self.wait_for_user_to_release_buttons()

    async def asyncPollButtons(self):
        while True:
            await self.pollButtons()
            # if self.last_button == self.pin_c:
            #     return
            asyncio.sleep(0.25)
            self.display.led(255)
            asyncio.sleep(0.25)
            self.display.led(0)
