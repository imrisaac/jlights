"""
An Accessory for Adafruit NeoPixels attached to GPIO Pin18
 Tested using Python 3.5/3.6 Raspberry Pi
 This device uses all available services for the Homekit Lightbulb API
 Note: RPi GPIO must be PWM. Neopixels.py will warn if wrong GPIO is used
       at runtime
 Note: This Class requires the installation of rpi_ws281x lib
       Follow the installation instructions;
           git clone https://github.com/jgarff/rpi_ws281x.git
           cd rpi_ws281x
           scons

           cd python
           sudo python3.6 setup.py install
 https://learn.adafruit.com/neopixels-on-raspberry-pi/software

 USing GPIO Memory requires python to be run as root (sudo). This can be fixed by using command on rpi
 1. sudo chown -v root:root /usr/bin/python3
 2. sudo chown -v u+s /usr/bin/python3
 This will cause pip to act a bit funny when you want to install anything later on so just reverse the above changes
 from step 2 as needed. Just use the same commands but with pi instead of root and with u-s.

 Apple Homekit API Call Order
 User changes light settings on iOS device
 Changing Brightness - Brightness - State
 Changing Color      - Saturation - Hue
 Changing Temp/Sat   - Saturation - Hue
 Changing State On    - State
 First Power On at boot - Brightness - State

 Apple Homekit API Values 
 Hue: 0 -360
 Saturation: 0 - 100
 Brightness: 0 - 100
 State: 0 - 1
"""

import neopixel
from random import randrange
import time
import colorsys

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_LIGHTBULB


class NeoPixelColor:
    """Class is used for easy passing and converting of colors between
    Apple HomeKit API and NeoPixel Library
    Conversion from HSV to RGB use python colorsys library whos values 
    range from 0 - 1 which require conversions to 8bit rgb and HomeKit API 
    standards"""

    #  TODO: - Find all functions that are not used and remove them

    def __init__(self):
        """Do not invoke directly - Use class methods
        We are setting a default red just incase"""
        self._red = 255
        self._green = 0
        self._blue = 0
        self._hue = 0
        self._saturation = 100
        self._brightness = 100

    @classmethod
    def from_rgb(cls, red, green, blue):
        color = cls()
        color.set_color_with_rgb(red, green, blue)
        return color

    @classmethod
    def from_hsv(cls, hue, saturation, brightness):
        color = cls()
        color.set_color_with_hsv(hue, saturation, brightness)
        return color

    @classmethod
    def from_color(cls, color):
        return_color = cls()
        rgb_tuple = color.get_rgb()
        return_color.set_color_with_rgb(rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
        return return_color

    @classmethod
    def from_24Bit_RGB(cls, WRGB_24Bit):
        color = cls()
        red = WRGB_24Bit >> 16 & 0xFF
        green = WRGB_24Bit >> 8 & 0xFF
        blue = WRGB_24Bit & 0xFF
        color.set_color_with_rgb(red, green, blue)
        return color

    # Pre defined Colors
    @classmethod
    def black(cls):
        color = cls()
        color.set_color_with_rgb(0, 0, 0)
        return color

    @classmethod
    def white(cls):
        color = cls()
        color.set_color_with_rgb(255, 255, 255)
        return color

    @classmethod
    def blue(cls):
        color = cls()
        color.set_color_with_rgb(0, 0, 255)
        return color

    @classmethod
    def green(cls):
        color = cls()
        color.set_color_with_rgb(0, 255, 0)
        return color

    @classmethod
    def red(cls):
        color = cls()
        color.set_color_with_rgb(255, 0, 0)
        return color

    # End predefined colors

    @classmethod  # INFO: - Testing only remove for merge
    def generate_random_color(cls):
        color = cls()
        color.set_color_with_rgb(randrange(256),
                                 randrange(256),
                                 randrange(256))
        return color

    def _update_member_rgb_values(self, rgb_tuple):
        self._red = rgb_tuple[0] * 255
        self._green = rgb_tuple[1] * 255
        self._blue = rgb_tuple[2] * 255

    def get_rgb(self):
        return self._red, self._green, self._blue

    def set_color_with_rgb(self, red, green, blue):
        self._red = red
        self._green = green
        self._blue = blue
        hsv = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        self._hue = hsv[0] * 360
        self._saturation = hsv[1] * 100
        self._brightness = hsv[2] * 100

    def get_hsv(self):
        hue = self._hue
        sat = self._saturation
        br = self._brightness
        return hue, sat, br

    def get_hex(self):
        hexColour = int('%02x%02x%02x%02x' % (int(self._red) * 255,
                                              int(self._green) * 255,
                                              int(self._blue) * 255,
                                              1), 16)
        return hexColour

    def set_color_with_hsv(self, hue, saturation, brightness):
        self._hue = hue
        self._saturation = saturation
        self._brightness = brightness
        rgb = colorsys.hsv_to_rgb(hue / 360,
                                  saturation / 100,
                                  brightness / 100)
        self._red = rgb[0] * 255
        self._green = rgb[1] * 255
        self._blue = rgb[2] * 255

    def get_hue(self):
        return self._hue

    def set_hue(self, hue):
        self._hue = hue
        rgb = colorsys.hsv_to_rgb(self._hue / 360,
                                  self._saturation / 100,
                                  self._brightness / 100)
        self._update_member_rgb_values(rgb)

    def adj_hue(self, value):
        self._hue += value
        rgb = colorsys.hsv_to_rgb(self._hue / 360,
                                  self._saturation / 100,
                                  self._brightness / 100)
        self._update_member_rgb_values(rgb)

    def get_saturation(self):
        return self._saturation

    def set_saturation(self, saturation):
        self._saturation = saturation
        rgb = colorsys.hsv_to_rgb(self._hue / 360,
                                  self._saturation / 100,
                                  self._brightness / 100)
        self._update_member_rgb_values(rgb)

    def adj_saturation(self, value):
        self._saturation += value
        rgb = colorsys.hsv_to_rgb(self._hue / 360,
                                  self._saturation / 100,
                                  self._brightness / 100)
        self._update_member_rgb_values(rgb)

    def set_brightness(self, brightness):
        self._brightness = brightness
        rgb = colorsys.hsv_to_rgb(self._hue / 360,
                                  self._saturation / 100,
                                  self._brightness / 100)
        self._update_member_rgb_values(rgb)

    def is_equal_with(self, color):
        result = False
        if (round(self._hue, 2) == round(color.get_hue(), 2) and round(self._saturation, 2) == round(
                color.get_saturation(), 2)):
            result = True
        return result


class ColorFadeColors:
    """ This class stores the color fade colors and allows
    convenience for adding and removing
    Max Storage = 2 """

    # TODO: - Find all functions that are not used and remove them

    def __init__(self, color1, color2, color3):
        self._primaryColor = color1  # Start of the color fade
        self._secondaryColor = color2  # End of the color fade
        self._current_pixel_color = color3  # The current color between start and end

    def insert_new_color(self, color):  # TODO: - This function can probably repalced by - GetPrimary = new_color
        self._secondaryColor = self._primaryColor
        self._primaryColor = color

    def set_primary_color(self, color):
        self._primaryColor.set_color_with_rgb(color.get_rgb()[0],
                                              color.get_rgb()[1],
                                              color.get_rgb()[2])

    def get_primary_color(self):
        return self._primaryColor

    def set_secondary_color(self, color):
        self._secondaryColor.set_color_with_rgb(color.get_rgb()[0],
                                                color.get_rgb()[1],
                                                color.get_rgb()[2])

    def get_secondary_color(self):
        return self._secondaryColor

    def set_current_pixel_color(self, color):
        self._current_pixel_color.set_color_with_rgb(color.get_rgb()[0],
                                                     color.get_rgb()[1],
                                                     color.get_rgb()[2])

    def get_current_pixel_color(self):
        return self._current_pixel_color

    def print_colors(self, type):
        if type == "RGB":
            print("RGB - Pri: {}   Sec: {}   LRPC: {}".format(self._primaryColor.get_rgb(),
                                                              self._secondaryColor.get_rgb(),
                                                              self._current_pixel_color.get_rgb()))
        elif type == "HSV" or type == "HSB":
            print("HSV - Pri: {}   Sec: {}   LRPC: {}".format(self._primaryColor.get_hsv(),
                                                              self._secondaryColor.get_hsv(),
                                                              self._current_pixel_color.get_hsv()))
        else:
            print("Unknown color format - Cannot print requested colors. See ColorFadeColors.print_colors")

    def print_hex_memory_ids(self):
        print("HEX IDS: {}, {}, {}".format(hex(id(self._primaryColor)), hex(id(self._secondaryColor)),
                                           hex(id(self._current_pixel_color))))


class NeoPixelLightStrip_Fader(Accessory):
    category = CATEGORY_LIGHTBULB
    COLOR_FADE_INTERVAL = 1

    def __init__(self, startup_in_color_fade_mode: bool, LED_count, is_GRB: bool, LED_pin,
                 LED_freq_hz, LED_DMA, LED_brightness,
                 LED_invert: bool, *args, **kwargs):

        """
        startup_in_color_fade_mode - this will run color fade mode at startup
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
            'Hue', setter_callback=self.hue_changed)
        self.char_saturation = serv_light.configure_char(
            'Saturation', setter_callback=self.saturation_changed)
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.state_changed)
        self.char_on = serv_light.configure_char(
            'Brightness', setter_callback=self.brightness_changed)

        self.accessory_state = 0
        self.is_GRB = is_GRB  # Most neopixels are Green Red Blue
        self.LED_count = LED_count

        self.neo_strip = neopixel.NeoPixel(LED_count, LED_pin, LED_freq_hz,
                                           LED_DMA, LED_invert, LED_brightness)
        self.neo_strip.begin()

        # Color Fade Mode
        # Current Mode
        if startup_in_color_fade_mode:
            self.mode = 0x01  # Mode0x00: Single Color, Mode0x01: Color Fade
        else:
            self.mode = 0x00
        self.color_fade_direction = 0x00  # 0=FWD  1=REV ie start_color to end_color
        self.mode_timer = time.time()
        self.mode_counter = 0
        self.color_fade_ready_timer = time.time()
        self.color_fade_colors = ColorFadeColors(NeoPixelColor.red(), NeoPixelColor.blue(), NeoPixelColor.red())
        self.color_fade_colors.print_hex_memory_ids()
        self.old_time = time.time()
        self.wasBrightness = 0

        temp = 0
        if self.color_fade_direction == 0x01:
            temp = 1

        print("Color fade direction: {}".format(temp))
        print("NAME: {}".format(self.display_name))

    def state_changed(self, value):
        print("state_changed")
        self.accessory_state = value

        if value == 1:  # On
            if self.wasBrightness != 1:  # Apple API Hack to stop brightness changes from changing state constantly
                if 1 < time.time() - self.mode_timer < 5:
                    self.mode_counter += 1
                    # print("Counter: {}  deltaTime: {}".format(self.mode_counter, self.mode_timer))
                    if self.mode_counter == 2:
                        self.mode ^= 1
                        # print("Changing Mode To: {}".format(self.mode))
                        self.mode_counter = 0
                        if self.mode == 0x00:
                            self.flash_pixels(3, 0.5, NeoPixelColor.red())  # White indicates single color mode
                        else:
                            self.flash_pixels(3, 0.5, NeoPixelColor.green())  # Blue indicates color fade mode
                else:
                    self.mode_counter = 0
            # Turn on our lights with the primary color and update the current color to the primary color
            self.update_neopixel_with_color(self.color_fade_colors.get_primary_color())
            color = self.color_fade_colors.get_primary_color()
            rgb_tuple = color.get_rgb()
            self.color_fade_colors.get_current_pixel_color().set_color_with_rgb(rgb_tuple[0], rgb_tuple[1],
                                                                                rgb_tuple[2])

        else:
            self.update_neopixel_with_color(NeoPixelColor.black())  # Off
            self.color_fade_direction = 0x00  # Reset our color fade direction for next power on

        self.mode_timer = time.time()

        self.wasBrightness = 0  # Reset our hack to 0

    # Lets check if we should update our color
    @Accessory.run_at_interval(COLOR_FADE_INTERVAL)
    def run(self):
        if self.accessory_state == 1 and self.mode == 0x01:
            # print("----- Start Loop ----")
            start_color = self.color_fade_colors.get_primary_color()
            end_color = self.color_fade_colors.get_secondary_color()
            current_color = self.color_fade_colors.get_current_pixel_color()

            # Fade Calculation
            TRANSITION_LENGTH = 60 * 10  # seconds
            if self.color_fade_direction == 0x00:
                delta_hue = end_color.get_hue() - start_color.get_hue()
                delta_sat = end_color.get_saturation() - start_color.get_saturation()
            else:
                delta_hue = start_color.get_hue() - end_color.get_hue()
                delta_sat = start_color.get_saturation() - end_color.get_saturation()

            hue_change_value = delta_hue / TRANSITION_LENGTH * self.COLOR_FADE_INTERVAL
            sat_change_value = delta_sat / TRANSITION_LENGTH * self.COLOR_FADE_INTERVAL

            current_color.adj_hue(hue_change_value)
            current_color.adj_saturation(sat_change_value)

            # Determine Direction of fade
            if self.color_fade_direction == 0x00:
                if current_color.is_equal_with(end_color):
                    self.color_fade_direction ^= 1  # Flip the direction
            elif self.color_fade_direction == 0x01:
                if current_color.is_equal_with(start_color):
                    self.color_fade_direction ^= 1

            self.update_neopixel_with_color(current_color)

    def hue_changed(self, value):
        print("Hue_change")  # TODO: - REMOVE
        old_color = self.color_fade_colors.get_primary_color()
        new_color = NeoPixelColor.from_color(old_color)

        new_color.set_hue(value)
        self.color_fade_colors.insert_new_color(
            new_color)  # This function moves the old primary to secondary and replaces primary with new

        if self.accessory_state == 1:
            self.update_neopixel_with_color(self.color_fade_colors.get_primary_color())
            self.color_fade_colors.set_current_pixel_color(self.color_fade_colors.get_primary_color())

        # Our color has changed so we must update reset our direction
        self.color_fade_direction = 0x00

    def brightness_changed(self, value):
        print("---brightness_changed---")  # TODO: - REMOVE
        self.wasBrightness = 1  # Hack for Appkit API brightness changing state
        pri = self.color_fade_colors.get_primary_color()
        sec = self.color_fade_colors.get_secondary_color()

        pri.set_brightness(value)
        sec.set_brightness(value)

        if self.accessory_state == 1:
            self.update_neopixel_with_color(pri)
            self.color_fade_colors.set_current_pixel_color(pri)

    def saturation_changed(self, value):
        print("---saturation_changed---")  # TODO: - REMOVE
        """ Saturation is never called on its own and always followed by hue
            Because of this we will update the primary
            saturation value only and let the hue call handel the final
            insertion and application of the new colors"""
        pri = self.color_fade_colors.get_primary_color()

        pri.set_saturation(value)

    def update_neopixel_with_color(self, color):
        rgb_tuple = color.get_rgb()
        for i in range(self.LED_count):
            if self.is_GRB:
                self.neo_strip.setPixelColor(i, Color(int(rgb_tuple[1]),
                                                      int(rgb_tuple[0]),
                                                      int(rgb_tuple[2])))
            else:
                self.neo_strip.setPixelColor(i, Color(int(rgb_tuple[0]),
                                                      int(rgb_tuple[1]),
                                                      int(rgb_tuple[2])))
        self.neo_strip.show()

    def flash_pixels(self, number_of_flashes, delay_between_flashes_seconds, flash_color):
        # Note: - Flashing does not work yet because I dont know how to thread
        for x in range(number_of_flashes):
            self.update_neopixel_with_color(NeoPixelColor.black())
            time.sleep(delay_between_flashes_seconds)
            self.update_neopixel_with_color(flash_color)
            time.sleep(delay_between_flashes_seconds)