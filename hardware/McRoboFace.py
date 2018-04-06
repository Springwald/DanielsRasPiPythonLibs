#!/usr/bin/env python

#     #########################################
#     # RGB LED control module for McRoboFace #
#     #########################################
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
# mcroboface.py

from __future__ import division
import time, sys, os

import time
from neopixel import *
from RgbLeds import RgbLeds

class McRoboFace():

	_rgbLeds			= None;

	LED_COUNT_FACE		= 17

	_pixels				= None;
	_released			= False

	# Define various facial expressions
	smileData   = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]
	frownData   = [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1]
	grimaceData = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]
	oooohData   = [0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1]
	
	def __init__(self, rgbLeds, startLed=0):
	# startLed: LEDs before the McRoboFace
		self._rgbLeds = rgbLeds;
		self._startLed = startLed;

	def clearFace(self):
		for i in range(0, self._startLed + self.LED_COUNT_FACE):
			self._rgbLeds._pixels.setPixelColor(i, 0)
			self._rgbLeds._pixels.show()   

	def showFace (self, data, Red, Green, Blue):
		for i in range(0, len(data)):
			if (data[i] > 0):
				self._rgbLeds._pixels.setPixelColor(self._startLed + i, Color(Green, Red, Blue))
			else:
				self._rgbLeds._pixels.setPixelColor(self._startLed + i, 0)
		self._rgbLeds._pixels.show()           

	def Demo(self):
		try:
			self.clearFace()
			self.showFace (self.smileData, 255, 0 , 0)
			time.sleep(2)
			self.showFace (self.frownData, 0, 0, 255)
			time.sleep(2)
			self.showFace (self.grimaceData, 255, 0, 255)
			time.sleep(2)
			self.showFace (self.oooohData, 0, 255, 0)
			time.sleep(2)
		except KeyboardInterrupt:
			print
		finally:
			self.clearFace()

	def Release(self):
		if (self._released == False):
			self._released = True
			print("McRoboFace releasing")
			self.clearFace();

	def __del__(self):
		self.Release()    

if __name__ == "__main__":
	leds = RgbLeds(ledCount=29, ledBrightness=100);
	face = McRoboFace(leds);
	face.Demo();
	face.Release()









