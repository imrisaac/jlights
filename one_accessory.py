"""Starts a fake fan, lightbulb, garage door and a TemperatureSensor
"""
import logging
import signal
import random

import time
import board
import neopixel

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import (CATEGORY_FAN,
                         CATEGORY_LIGHTBULB,
                         CATEGORY_GARAGE_DOOR_OPENER,
                         CATEGORY_SENSOR)


logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")


class TemperatureSensor(Accessory):
    """Fake Temperature sensor, measuring every 3 seconds."""

    category = CATEGORY_SENSOR

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        serv_temp = self.add_preload_service('TemperatureSensor')
        self.char_temp = serv_temp.configure_char('CurrentTemperature')

    @Accessory.run_at_interval(3)
    async def run(self):
        self.char_temp.set_value(random.randint(18, 26))


class FakeFan(Accessory):
    """Fake Fan, only logs whatever the client set."""

    category = CATEGORY_FAN

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add the fan service. Also add optional characteristics to it.
        serv_fan = self.add_preload_service(
            'Fan', chars=['RotationSpeed', 'RotationDirection'])

        self.char_rotation_speed = serv_fan.configure_char(
            'RotationSpeed', setter_callback=self.set_rotation_speed)
        self.char_rotation_direction = serv_fan.configure_char(
            'RotationDirection', setter_callback=self.set_rotation_direction)

    def set_rotation_speed(self, value):
        logging.debug("Rotation speed changed: %s", value)

    def set_rotation_direction(self, value):
        logging.debug("Rotation direction changed: %s", value)

class LightBulb(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_LIGHTBULB

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        serv_light = self.add_preload_service('Lightbulb')
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.set_bulb)

    def set_bulb(self, value):
        logging.info("Bulb value: %s", value)

class GarageDoor(Accessory):
    """Fake garage door."""

    category = CATEGORY_GARAGE_DOOR_OPENER

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_preload_service('GarageDoorOpener')\
            .configure_char(
                'TargetDoorState', setter_callback=self.change_state)

    def change_state(self, value):
        logging.info("Bulb value: %s", value)
        self.get_service('GarageDoorOpener')\
            .get_characteristic('CurrentDoorState')\
            .set_value(value)

class NeoPixelLightStrip(Accessory):

    category = CATEGORY_LIGHTBULB

    def __init__(self, LED_count, is_GRB, LED_pin,
                 LED_freq_hz, LED_DMA, LED_brightness,
                 LED_invert, *args, **kwargs):

        """
        LED_Count - the number of LEDs in the array
        is_GRB - most neopixels are GRB format - Normal:True
        LED_pin - must be PWM pin 18 - Normal:18
        LED_freq_hz - frequency of the neopixel leds - Normal:800000
        LED_DMA - Normal:10
        LED_Brightness - overall brightness - Normal:255
        LED_invert - Normal:False
        For more information regarding these settings
            please review rpi_ws281x source code
        """

        super().__init__(*args, **kwargs)

        # Set our neopixel API services up using Lightbulb base
        serv_light = self.add_preload_service(
            'Lightbulb', chars=['On', 'Hue', 'Saturation', 'Brightness'])

        # Configure our callbacks
        self.char_hue = serv_light.configure_char(
            'Hue', setter_callback=self.set_hue)
        self.char_saturation = serv_light.configure_char(
            'Saturation', setter_callback=self.set_saturation)
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.set_state)
        self.char_on = serv_light.configure_char(
            'Brightness', setter_callback=self.set_brightness)

        # Set our instance variables
        self.accessory_state = 0  # State of the neo light On/Off
        self.hue = 0  # Hue Value 0 - 360 Homekit API
        self.saturation = 100  # Saturation Values 0 - 100 Homekit API
        self.brightness = 100  # Brightness value 0 - 100 Homekit API

        self.is_GRB = is_GRB  # Most neopixels are Green Red Blue
        self.LED_count = LED_count

        self.neo_strip = neopixel.NeoPixel(board.D18, 2, brightness=0.2, auto_write=False, pixel_order=neopixel.GRBW)

    def set_state(self, value):
        self.accessory_state = value
        if value == 1:  # On
            self.set_hue(self.hue)
        else:
            self.update_neopixel_with_color(0, 0, 0)  # Off

    def set_hue(self, value):
        # Lets only write the new RGB values if the power is on
        # otherwise update the hue value only
        if self.accessory_state == 1:
            self.hue = value
            rgb_tuple = self.hsv_to_rgb(
                self.hue, self.saturation, self.brightness)
            if len(rgb_tuple) == 3:
                self.update_neopixel_with_color(
                    rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
        else:
            self.hue = value

    def set_brightness(self, value):
        self.brightness = value
        self.set_hue(self.hue)

    def set_saturation(self, value):
        self.saturation = value
        self.set_hue(self.hue)

    def update_neopixel_with_color(self, red, green, blue):
        self.neo_strip.fill((green, red, blue, 0))
        self.neo_strip.show()

    def hsv_to_rgb(self, h, s, v):
        """
        This function takes
         h - 0 - 360 Deg
         s - 0 - 100 %
         v - 0 - 100 %
        """

        hPri = h / 60
        s = s / 100
        v = v / 100

        if s <= 0.0:
            return int(0), int(0), int(0)

        C = v * s  # Chroma
        X = C * (1 - abs(hPri % 2 - 1))

        RGB_Pri = [0.0, 0.0, 0.0]

        if 0 <= hPri <= 1:
            RGB_Pri = [C, X, 0]
        elif 1 <= hPri <= 2:
            RGB_Pri = [X, C, 0]
        elif 2 <= hPri <= 3:
            RGB_Pri = [0, C, X]
        elif 3 <= hPri <= 4:
            RGB_Pri = [0, X, C]
        elif 4 <= hPri <= 5:
            RGB_Pri = [X, 0, C]
        elif 5 <= hPri <= 6:
            RGB_Pri = [C, 0, X]
        else:
            RGB_Pri = [0, 0, 0]

        m = v - C

        return int((RGB_Pri[0] + m) * 255), int((RGB_Pri[1] + m) * 255), int((RGB_Pri[2] + m) * 255)

def get_accessory(driver):
    """Call this method to get a standalone Accessory."""
    return NeoPixelLightStrip(2, True, 18, 800000, 10, 255, False, driver, 'NeoPixel')

def get_bridge(driver):
    bridge = Bridge(driver, 'Bridge')

    bridge.add_accessory(LightBulb(driver, 'Lightbulb'))
    bridge.add_accessory(FakeFan(driver, 'Big Fan'))
    bridge.add_accessory(GarageDoor(driver, 'Garage'))
    bridge.add_accessory(TemperatureSensor(driver, 'Sensor'))
    bridge.add_accessory(get_accessory(driver))

    return bridge

driver = AccessoryDriver(port=51826, persist_file='one_accessory.state')
driver.add_accessory(get_accessory(driver))

signal.signal(signal.SIGTERM, driver.signal_handler)
driver.start()