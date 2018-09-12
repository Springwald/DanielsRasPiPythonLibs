#!/usr/bin/env python

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


import time
import os, sys
from PIL import Image

class AnimationImage():


	Frames			= []
	Delay			= 0


	def __init__(self, gifFilename):
		self.loadGif(gifFilename)
		return
		
	def loadGif(self, image_filename):
		im = Image.open(image_filename)

		try: self.Delay = im.info['duration'] / 1000
		except: pass
		
		if self.Delay < 0.08:
			self.Delay = 0.08

		self.Frames = []
		done=False
		i=0
		pal = im.getpalette()

		try:
			while 1:
				im.putpalette(pal)
				new_frame = Image.new("RGBA", im.size)
				new_frame.paste(im,(0,0), im.convert('RGBA'))
				self.Frames.append(new_frame)
				i += 1
				im.seek(im.tell() + 1)

		except EOFError:
			pass # end of sequence

if __name__ == "__main__":
	a=0


