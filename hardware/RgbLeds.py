#!/usr/bin/env python

#     ##########################
#     # RGB LED control module #
#     ##########################
#
#     Licensed under MIT License (MIT)
#
#     Copyright (c) 2018 Daniel Springwald | daniel@springwald.de
#
#     Permission is hereby granted, free of charge, to any person obtaining
#     a copy of this software and associated documentation files (the
#     "Software"), to deal in the Software without restriction, including
#     without limitation the rights to use, copy, modify, merge, publish,
#     distribute, sublicense, and/or sell copies of the Software, and to permit
#     persons to whom the Software is furnished to do so, subject to
#     the following conditions:
#
#     The above copyright notice and this permission notice shall be
#     included in all copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#     THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#     FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#     DEALINGS IN THE SOFTWARE.

#!/usr/bin/python

import time
from neopixel import *

class RgbLeds():

	# LED strip configuration:
	LED_PIN        		= 18		# GPIO pin connected to the pixels (must support PWM!).
	LED_FREQ_HZ    		= 800000	# LED signal frequency in hertz (usually 800khz)
	LED_DMA        		= 5			# DMA channel to use for generating signal (try 5)
	LED_INVERT     		= False		# True to invert the signal (when using NPN transistor level shift)
	
	_pixels				= None;
	_released			= False

	def __init__(self, ledCount, ledBrightness=255):
	# ledBrightness: Set to 0 for darkest and 255 for brightest
		self._ledCount = ledCount;
		self._pixels = Adafruit_NeoPixel(self._ledCount, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, ledBrightness)
		self._pixels.begin()
		
	def ClearAll(self):
		for i in range(0, self._ledCount):
			self._pixels.setPixelColor(i, 0)
		self._pixels.show()     

	def theaterChase(self, color, countLed, startLed=0, wait_ms=50, iterations=1):
		# Movie theater light style chaser animation."""
		for j in range(iterations):
			for q in range(3):
				for i in range(0, countLed, 3):
					self._pixels.setPixelColor(startLed+i+q, color)
				self._pixels.show()
				time.sleep(wait_ms/1000.0)
				for i in range(0, countLed, 3):
					self._pixels.setPixelColor(startLed+i+q, 0)
					
	def colorWipe(self, color, countLed, startLed=0, wait_ms=0.1):
		# Wipe color across display a pixel at a time.
		for i in range(countLed):
			self._pixels.setPixelColor(startLed+i , color)
			self._pixels.show()
			time.sleep(wait_ms/1000.0)
			
	def wheel(self,pos):
		# Generate rainbow colors across 0-255 positions."""
		if pos < 85:
			return Color(pos * 3, 255 - pos * 3, 0)
		elif pos < 170:
			pos -= 85
			return Color(255 - pos * 3, 0, pos * 3)
		else:
			pos -= 170
			return Color(0, pos * 3, 255 - pos * 3)
			
	def rainbowCycle(self, countLed, startLed=0, wait_ms=10, iterations=1):
		# Draw rainbow that uniformly distributes itself across all pixels."""
		strip = self._pixels
		for j in range(256*iterations):
			for i in range(countLed):
				strip.setPixelColor(startLed+i, self.wheel(((int(i * 256 / countLed) + j) & 255)))
			strip.show()
			time.sleep(wait_ms/1000.0)

	def Release(self):
		if (self._released == False):
			self._released = True
			print("RGB LEDs releasing")
			self.ClearAll();

	def __del__(self):
		self.Release()    

if __name__ == "__main__":

	leds = RgbLeds(ledCount=29, ledBrightness=100);
	leds.colorWipe(Color(255,0,255), countLed=29, wait_ms=100);
	for i in range(1,100):
		print(i);
		#leds.theaterChase(Color(255,255,0), countLed=29);
		leds.rainbowCycle(countLed=29)

	leds.Release()









