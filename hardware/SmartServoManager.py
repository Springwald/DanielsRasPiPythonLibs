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
	_actualSpeedDelay = .006

	servoCount 			= 0;
	_servos 			= None;
	
	_servoIds					= [];
	_masterIds					= [];
	_reverseToMaster			= [];
	_centeredValues				= [];
	_isReadOnly					= [];
	_servoMaxStepsPerUpdate		= [];
	_servoRamp					= [];
	
	__targets					= None; 
	__values					= None; 
	
	__shared_ints__		= None
	
	_nextServoToReadPos = 0;
	
	_released = False;

	def __init__(self, lX16AServos, servoIds, ramp=0, maxSpeed=1):
		
		super().__init__(prio=-20)
		
		self.servoCount 				= len(servoIds);
		self._servoIds 					= servoIds;
		
		# fill other arrays
		self._masterIds					= [];
		self._centeredValues			= [];
		self._reverseToMaster			= [];
		for i in range(self.servoCount):
			self._masterIds.append(servoIds[i]);
			self._centeredValues.append(500);		# standard value: 500
			self._isReadOnly.append(False);			# standard: False = active Servo (True: Servo is used as input device)
			self._reverseToMaster.append(1);		# standard: 1 = not reverse (-1 would be reverse)
			
		self._servoMaxStepsPerUpdate 	= SharedInts(max_length=self.servoCount);
		self._servoRamp 				= SharedInts(max_length=self.servoCount);
		self._servos 					= lX16AServos;
		self.__targets					= SharedInts(max_length=self.servoCount);
		self.__values					= SharedInts(max_length=self.servoCount);
		
		self._ramp = ramp;
		self._maxStepsPerSpeedDelay = maxSpeed;

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
		for pos in range(0, self.servoCount):
			id = self._servoIds[pos];
			self._servoMaxStepsPerUpdate.set_value(pos,self._maxStepsPerSpeedDelay);
			self._servoRamp.set_value(pos,self._ramp);
			value = self._servos.ReadPos(id);
			self.__values.set_value(pos, value);
			self.__targets.set_value(pos, value);
			#print(self.__values.get_value(pos));
		super().StartUpdating()
		
	def SetMasterId(self, servoId, masterServoId, reverseToMaster):
		no = self.__getNumberForId(servoId);
		self._masterIds[no]= masterServoId;
		self._reverseToMaster[no]= reverseToMaster;
		
	def SetCenteredValue(self, servoId, centeredValue):
		no = self.__getNumberForId(servoId);
		self._centeredValues[no]= centeredValue;
		
	def SetReadOnly(self, servoId, isReadOnly):
		no = self.__getNumberForId(servoId);
		self._isReadOnly[no]= isReadOnly;

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

		for i in range(0, self.servoCount):
			
			if (super().updating_ended == True):
				return
				
			id = self._servoIds[i]
			
			if (self._masterIds[i] !=  id):
				continue # is a slave servo
				
			if (self._isReadOnly[i] == True):
				value = self._servos.ReadPos(id)
				self.__values.set_value(i, value);
				continue # is a readOnly Servo used as input

			if (False and self._nextServoToReadPos == i):
			#if (id == 13 or id == 12):
				value = self._servos.ReadPos(id)
				self.__values.set_value(i, value);
				#print(str(i)+ " " + str(value))
			else:
				value = self.__values.get_value(i);

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
	ended = False;
	servos = LX16AServos();
	tester = SmartServoManager(lX16AServos=servos, servoIds= [5,6],ramp=0, maxSpeed=1);
	
	tester.SetMasterId(servoId=5, masterServoId=6, reverseToMaster=-1);
	
	tester.Start();

	plus = 100;

	while(True):
		plus = - plus;
		tester.MoveServo(6,500+plus);
		# tester.MoveServo(6,500-plus);
		while (tester.allTargetsReached == False):
			time.sleep(0.1);

def TestReadOnly():
	ended = False;
	servos = LX16AServos();
	tester = SmartServoManager(lX16AServos=servos, servoIds= [5,6],ramp=0, maxSpeed=10);
	
	tester.SetReadOnly(servoId=5,isReadOnly=True)
	tester.Start();

	while(True):
		value = tester.ReadServo(5);
		tester.MoveServo(6,value);
		while (tester.allTargetsReached == False):
			time.sleep(0.001);


if __name__ == "__main__":
	#TestSlave()
	TestReadOnly()
	#bigTest();
