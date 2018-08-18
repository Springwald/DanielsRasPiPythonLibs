#!/usr/bin/env python

#     ##############################
#     # LX-16A servo communication #
#     ##############################
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

from __future__ import division
import time, sys, os

import atexit

clear = lambda: os.system('cls' if os.name=='nt' else 'clear')

my_file = os.path.abspath(__file__)
my_path ='/'.join(my_file.split('/')[0:-1])

sys.path.insert(0,my_path + "/../multitasking/" )

from MultiProcessing import *
from array import array
from SharedInts import SharedInts
from SharedFloats import SharedFloats
from LX16AServos import LX16AServos

class SmartServoManager(MultiProcessing):
	
	_lastUpdateTime	= time.time()
	_actualSpeedDelay = .001
	_readServosWhileRunning = True

	_maxServos			= 0
	servoCount 			= 0
	_servos 			= None
	
	_servoIds					= []
	_masterIds					= []
	_reverseToMaster			= []
	_centeredValues				= []
	_isReadOnly					= []
	_servoMaxStepsPerUpdate		= []
	_servoRamp					= []
	
	__targets					= None
	__values					= None 
	
	__shared_ints__		= None
		
	_nextServoToReadPos = 0;
	_started 	= False
	__startTime 	= None
	__fpsCount	= 0
	__fpsShow	= 0
	
	_released = False;
	
	__lastReadNo = 0
	

	def __init__(self, lX16AServos, maxServos=255, ramp=0, maxSpeed=1, readServosWhileRunning = False):
		
		super().__init__(prio=-20)
		
		self._ramp = ramp
		self._maxStepsPerSpeedDelay = maxSpeed
		self._readServosWhileRunning = readServosWhileRunning
		
		# fill other arrays
		self._masterIds					= []
		self._centeredValues			= []
		self._reverseToMaster			= []
		self._servoMaxStepsPerUpdate 	= SharedInts(max_length=maxServos)
		self._servoRamp 				= SharedInts(max_length=maxServos)
		self._servos 					= lX16AServos
		self.__targets					= SharedInts(max_length=maxServos)
		self.__values					= SharedInts(max_length=maxServos)
		
		self.__shared_ints__			= SharedInts(max_length=3)
		self.__targets_reached_int__	= self.__shared_ints__.get_next_key()
		
		self._processName = "SmartServoManager";
		
		

	@property
	def allTargetsReached(self):
		return self.__shared_ints__.get_value(self.__targets_reached_int__)== 1
	@allTargetsReached.setter
	def allTargetsReached(self, value):
		if (value == True):
			self.__shared_ints__.set_value(self.__targets_reached_int__,1)
		else:
			self.__shared_ints__.set_value(self.__targets_reached_int__,0)
			
	def Start(self):
		# initial read of servo positions
		allRead = False
		tryCount = 0
		while (allRead == False and tryCount <  10):
			allRead = True
			for pos in range(0, self.servoCount):
				id = self._servoIds[pos]
				value = self._servos.ReadPos(id, showError= tryCount > 2)
				if (value == -1):
					allRead = False
				else:
					self.__values.set_value(pos, value)
					self.__targets.set_value(pos, value)
					print ("servo " + str(id) + ": " + str(value))
			if (allRead==False):
				time.sleep(1)
				tryCount = tryCount + 1
				
		if (allRead == False):
			raise ValueError('unable to initial read all servo positions')

		if (self._started==False):
			self._started=True;
			self.__startTime = time.time()
			self.__fpsCount = 0
			super().StartUpdating()
		
	def AddMasterServo(self, servoId, centeredValue=500):
		self.___addServo(servoId, centeredValue=centeredValue)
		self._masterIds.append(servoId)

	def AddSlaveServo(self, servoId, masterServoId, reverseToMaster=1, centeredValue=500 ):
		self.___addServo(servoId, centeredValue=centeredValue)
		self._masterIds.append(masterServoId)
		self._reverseToMaster[self.servoCount-1] = reverseToMaster

	def ___addServo(self, servoId, centeredValue):
		self.servoCount = self.servoCount+1
		no = self.servoCount-1
		self._servoIds.append(servoId);
		self._servoMaxStepsPerUpdate.set_value(no,self._maxStepsPerSpeedDelay); # default value from init
		self._servoRamp.set_value(no,self._ramp);	# default value from init
		self._centeredValues.append(centeredValue);	# standard value: 500
		self._isReadOnly.append(False);				# standard: False = active Servo (True: Servo is used as input device)
		self._reverseToMaster.append(1);			# standard: 1 = not reverse (-1 would be reverse)

	#def SetMasterId(self, servoId, masterServoId, reverseToMaster):
	#	no = self.__getNumberForId(servoId);
	#	self._masterIds[no]= masterServoId;
	#	self._reverseToMaster[no]= reverseToMaster;
		
	def SetCenteredValue(self, servoId, centeredValue):
		no = self.__getNumberForId(servoId);
		self._centeredValues[no]= centeredValue;
		
	def GetCenteredValue(self, servoId):
		no = self.__getNumberForId(servoId)
		return self._centeredValues[no]
		
	def SetReadOnly(self, servoId, isReadOnly):
		no = self.__getNumberForId(servoId);
		self._isReadOnly[no]= isReadOnly;
		if (isReadOnly==True):
			self._servos.SetServoPower(servoId, False)
		else:
			self._servos.SetServoPower(servoId, True)

	def SetMaxStepsPerUpdate(self, servoId, maxSteps):
		no = self.__getNumberForId(servoId);
		self._servoMaxStepsPerUpdate.set_value(no, maxSteps);

	def Update(self):
		#print("update start " + str(time.time()))
		if (super().updating_ended == True):
			return
		
		timeDiff = time.time() - self._lastUpdateTime
		if (timeDiff < self._actualSpeedDelay):
			time.sleep(self._actualSpeedDelay - timeDiff)
		allReached = True
		
		self.__lastReadNo = self.__lastReadNo-1
		if (self.__lastReadNo == -1):
			self.__lastReadNo = self.servoCount
			
		if (False): # calc fps
			self.__fpsCount = self.__fpsCount + 1
			self.__fpsShow = self.__fpsShow + 1
			if (self.__fpsShow == 100):
				self.__fpsShow = 0
				delta = time.time() - self.__startTime
				print(self.__fpsCount / delta)

		for i in range(0, self.servoCount):
			
			if (super().updating_ended == True):
				return
				
			id = self._servoIds[i]
			
			if (self._isReadOnly[i] == True ):
				if (self.__lastReadNo == i):
					value = self._servos.ReadPos(id) # only read a single servo per update because of performance
					self.__values.set_value(i, value);
				continue # is a readOnly Servo used as input

			if (self._masterIds[i] !=  id):
				continue # is a slave servo

			if (self._readServosWhileRunning == True and self._nextServoToReadPos == i):
			#if (id == 13 or id == 12):
				getValue = self._servos.ReadPos(id)
				if (getValue != -1):
					value = getValue
					self.__values.set_value(i, value);
				#print(str(i)+ " " + str(value))
			else:
				value = self.__values.get_value(i);
				
			if (value == -1):
				# this servo has an invalid value. do nothing, to prevent damage!
				reachedThis = False
				allReached = False
			else:
				
				diff = int(self.__targets.get_value(i) - value) 
				plus = 0
				
				tolerance = 10;
				
				if (diff < tolerance and diff > -tolerance):
					reachedThis = True
					#if (diff != 0):
					#	if (super().updating_ended == False):
					#		l = 1
							#newValue = int(self.__targets.get_value(i))
							#self._servos.MoveServo(id, self._ramp, newValue)
							#self.__values.set_value(i, newValue)
				else:
					reachedThis = False;
					
				servoMaxStepsPerUpdate = self._servoMaxStepsPerUpdate.get_value(i);
					
				diff = max(diff, -servoMaxStepsPerUpdate);
				diff = min(diff, servoMaxStepsPerUpdate);
				
				if (reachedThis == False):
					allReached = False
					newValue = int(value + diff) 
					if (super().updating_ended == False):
						self._servos.MoveServo(id, self._servoRamp.get_value(i), newValue);
						self.__values.set_value(i, newValue)
						
						for no in range(0, self.servoCount):
							if (no != i):
								if (self._masterIds[no] == id):
									slaveId = self._servoIds[no]
									newValue = (newValue - self._centeredValues[i]) * self._reverseToMaster[no] + self._centeredValues[no] 
									self._servos.MoveServo(slaveId, self._servoRamp.get_value(i), newValue);
									self.__values.set_value(no, newValue)

		self._nextServoToReadPos = self._nextServoToReadPos + 1
		if (self._nextServoToReadPos >= self.servoCount):
			self._nextServoToReadPos = 0

		self.allTargetsReached = allReached
		self._lastUpdateTime = time.time()
			
			
		#for pos in range(0, self.servoCount):
		#	id = self._servoIds[pos];
		#	value = self._servos.ReadPos(id);
		#	target = self.__targets.get_value(pos);
		#	diff = target-value;
		#	zone = 3;
		#	if (True or diff < -zone or diff > zone):
		#		#print ("diff: " + str(diff))
		#		diff = max(-10, diff);
		#		diff = min(10, diff);
		#		self._servos.MoveServo(id, 0, value + diff);

		
	def MoveServo(self, id, pos):
		masterNo = self.__getNumberForId(id)
		self.__targets.set_value(masterNo, pos);
		self.allTargetsReached = False;
		
	def ReadServo(self, id):
		masterNo = self.__getNumberForId(id)
		return self.__values.get_value(masterNo);

	def __getNumberForId(self, id):
		for no in range(0, self.servoCount):
			if (id == self._servoIds[no]):
				return no;

	#def _readServoDirectly(self, id, pos):
	#	no = self.__getNumberForId(id);
	#	value = self._servos.ReadPos(id);
	#	self.__values.set_value(pos, value); # cache the value

	#def _moveServoDirectly(self, id, pos):
	#	no = self.__getNumberForId(id);
	#	self._servos.MoveServo(id,0,pos);
	
	def MoveToAndWait(self, positions):
		self.MoveToWithOutWait(positions);
		while (self.allTargetsReached == False):
			time.sleep(0.01);
			
	def MoveToWithOutWait(self, positions):
		for p in range(0,len(positions)):
			id = positions[p][0]
			value = positions[p][1]
			self.MoveServo(id, value)
			
	def PrintReadOnlyServoValues(self, onlyMasterServos=True):
		import pyperclip
		out = ""
		firstCode= True
		code = "_gesture 	= ["
		# print all readonly servos
		for a in range(0, self.servoCount):
			id = self._servoIds[a]
			if (self._isReadOnly[a]==True):
				p = self.ReadServo(id)
				if (p != -1):
					out = out  + str(id) + ": " + str(p) + "\r\n"
					if (self._masterIds[a] == id):
						if (firstCode==True or onlyMasterServos==False):
							firstCode = False
						else:
							code = code + ","
						code = code + "[" + str(id) + "," + str(p) +"]"

		# print only the master servos in in copy format
		code = code + "]"
		out = out + "\r\n" + code 
		
		## push to screen
		#clear()
		#print(out)
		
		## copy to clipboard
		pyperclip.copy(code)
		#spam = pyperclip.paste()



			

	def Release(self):
		if (self._released == False):
			print("releasing " + self._processName)
			self._released = True;
			super().EndUpdating();
			print("super().EndUpdating() " + self._processName)
			time.sleep(self._actualSpeedDelay*10); 
			self._servos.ShutDown(self._servoIds);
			self._servos.Release();

	def __del__(self):
		self.Release()

def exit_handler():
	tester.Release()
	
def TestReadSpeed():
	servos = LX16AServos()
	tester = SmartServoManager(lX16AServos=servos)
	tester.AddMasterServo(servoId=1)
	tester.SetReadOnly(servoId=1,isReadOnly=True)
	tester.AddMasterServo(servoId=2)
	tester.SetReadOnly(servoId=2,isReadOnly=True)
	tester.AddMasterServo(servoId=3)
	tester.SetReadOnly(servoId=3,isReadOnly=True)
	tester.Start()
	while(True):
		value = tester.ReadServo(1)

	
def bigTest():
	ended = False;
	servos = LX16AServos();
	tester = SmartServoManager(lX16AServos=servos, servoIds= [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],ramp=0, maxSpeed=1);
	tester.SetMaxStepsPerUpdate(5,2);
	tester.SetMaxStepsPerUpdate(6,3);


	armHanging 		= [[1,151],[2,168],[3,455],[4,613],[5,471],[6,550]];
	wink1 			= [[1,374],[2,451],[3,693],[4,816],[5,565]];
	wink2 			= [[1,192],[2,678],[3,888],[4,872],[5,509]];
	strechSide		= [[1,299],[2,249],[3,663],[4,660],[5,848]];
	lookHand		= [[1,592],[2, 90],[3,361],[4,787],[5,795]];
	ghettoFist1		= [[1,105],[2,140],[3,525],[4,910],[5,116],[6,420]];
	ghettoFist2		= [[1,339],[2,138],[3,525],[4,753],[5,116],[6,420]];
	
	closeHand		= [[6,420]];
	openHand		= [[6,550]];
	
	lookRightHand	= [[13,500-150],[14,500+150],[15,500-250]];
	lookFront		= [[13,500],[14,500],[15,500]];
	
	#tester.MoveServo(4,613);
	
	
	#while(True):
	if (True):
	
		tester.MoveToAndWait(lookFront + armHanging);
		time.sleep(1);
	
		tester.MoveToAndWait(openHand);
		tester.MoveToAndWait(closeHand);
		

		tester.MoveToAndWait(strechSide + lookRightHand);
		tester.MoveToAndWait(openHand);
		time.sleep(2);
		
	
		for wink in range(0,1):
			tester.MoveToAndWait(wink1);
			tester.MoveToAndWait(wink2);

		tester.MoveToAndWait(armHanging);
		time.sleep(1);
			
		tester.MoveToAndWait(strechSide);
		time.sleep(2);
		
		tester.MoveToAndWait(armHanging);
		time.sleep(1);

	tester.MoveToAndWait(ghettoFist1);
	tester.MoveToAndWait(ghettoFist2);
	tester.MoveToAndWait(ghettoFist1);

	tester.MoveToAndWait(armHanging);
	time.sleep(2);
	
	tester.Release();
	print("done");
	
def TestSlave():
	servos = LX16AServos();
	tester = SmartServoManager(lX16AServos=servos,ramp=0, maxSpeed=1);
	tester.AddMasterServo(servoId=5);
	tester.AddSlaveServo(servoId=6, masterServoId=5, reverseToMaster=-1);
	tester.Start();

	plus = 100;

	while(True):
		plus = - plus;
		tester.MoveServo(5,500+plus);
		while (tester.allTargetsReached == False):
			time.sleep(0.1);

def TestReadOnly():
	servos = LX16AServos();
	tester = SmartServoManager(lX16AServos=servos);
	tester.AddMasterServo(servoId=5);
	tester.SetReadOnly(servoId=5,isReadOnly=True)
	tester.Start();
	while(True):
		value = tester.ReadServo(5);
		print(value)
		time.sleep(1)

if __name__ == "__main__":
	#TestSlave()
	TestReadOnly()
	#TestReadSpeed();
	#bigTest();
