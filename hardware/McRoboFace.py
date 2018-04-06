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

import time, random
from neopixel import *
from RgbLeds import RgbLeds

class McRoboFace():

	_rgbLeds			= None;

	LED_COUNT_FACE		= 17

	_pixels				= None;
	_released			= False

	# Define various facial expressions
	smileData		= [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]
	frownData		= [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1]
	grimaceData		= [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]
	oooohData		= [0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1]
	
	neutral			= [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1]
	blink			= [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0]
	
	speak1			= [0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]
	speak2			= [0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]
	speak3			= [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]
	speak4			= [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1]
	speak5			= [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1]
	speaking		= [speak1, speak3, speak4, speak5]
	_actualSpeak	= 0;
	
	def __init__(self, rgbLeds, startLed=0):
	# startLed: LEDs before the McRoboFace
		self._rgbLeds = rgbLeds;
		self._startLed = startLed;

	def clearFace(self):
		for i in range(0, self._startLed + self.LED_COUNT_FACE):
			self._rgbLeds._pixels.setPixelColor(i, 0)
			self._rgbLeds._pixels.show()   

	def Speak(self, red=255, green=255, blue=255):
		last = self._actualSpeak
		while (last==self._actualSpeak):
			self._actualSpeak = random.randrange(len(self.speaking));
		self.showFace(self.speaking[self._actualSpeak], red, green, blue);
		
	def NeutralAndBlink(self, red=255, green=255, blue=255):
		rnd = random.randrange(50);
		if (rnd ==1):
			self.showFace(self.blink, red, green, blue);
		else:
			self.showFace(self.neutral, red, green, blue);
		
	def showFace (self, data, red=255, green=255, blue=255):
		for i in range(0, len(data)):
			value = data[i]
			if (value > 0):
				self._rgbLeds._pixels.setPixelColor(self._startLed + i, Color(int(green*value), int(red*value), int(blue*value)))
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
	face.showFace(face.speak2);
	#time.sleep(2);
	#face.Demo();
	for i in range(1,100):
		face.Speak();
		time.sleep(0.2);
	face.Release()









