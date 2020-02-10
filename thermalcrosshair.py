# -*- coding: utf-8 -*-	 
'''
Created on 2015-June

@author: Insight Robotics HK LTD
'''

import sys,os

parentPath = os.path.abspath("..")
if parentPath not in sys.path:
    sys.path.insert(0, parentPath)


import zerorpc
import gevent, gevent.event
import importlib
import numpy as np
import cv2

import str2mat
import sqlite3
from struct import *
import time
from datetime import datetime


#Database INFRARED table keys
IRCAM_ADDR              ='ircamaddr'
IRCAM_PORT              ='ircamport'
IRCAM_USERNAME          ='ircamusername'
IRCAM_PASSWORD          ='ircampassword'
IRCAM_BRAND             ='ircambrand'
IRCAM_WIDTH             ='ircamwidth'
IRCAM_HEIGHT            ='ircamheight'
IRCAM_THRESHOLD         ='ircamthreshold'
IRCAM_THRESHOLD_INFO    ='ircamthresholdinfo'
IRCAM_DISTANCE_INFO     ='ircamdistanceinfo'
IRCAM_THRESHOLD_MODE    ='ircamthresholdmode'

IRCAM_CAPTURE_NUM		='ircamcapturetime'

def resizedisplay(img,ratio):

	h = img.shape[0]/2
	w = img.shape[1]/2
	color = (0, 0, 255)
	
	for n in range(15, 120):
		img[h, w+n] = (0,0,0)
		img[h, w-n] = (0,0,0)
		img[h+n, w] = (0,0,0)
		img[h-n, w] = (0,0,0)
		
	for n in range(6, 15):
		img[h, w + n] = color
		img[h, w - n] = color
		img[h + n, w] = color				
		img[h - n, w] = color
			
	img = cv2.resize(img, None, fx = (1*ratio), fy = (1*ratio), interpolation = cv2.INTER_NEAREST)
	cv2.imshow("Thermal image", img)
	Key = cv2.waitKey(10)
		
		
class IRCam(object):

	def __init__(self):
				
		self.currenttime = time.time()
		self.greenLight = gevent.event.Event()    # a mutex signal to prevent NUC and image capture won't happened in same time
		self.greenLight.set()

		try:
			conn = sqlite3.connect(os.path.join(parentPath, 'config.db'))
			c = conn.cursor()
			self.cfg = {}
		except Exception as e:
			print "Exception config database %s"%(e.message)
			
		try:
			c.execute('''SELECT value FROM MAIN WHERE NAME = "datapath"''')
			dataPath = c.fetchone()
			self.dataPath = dataPath[0].strip(' \n\t\r').encode('utf-8')
		except Exception as e:
			print "get data path %s "%(e.message)
			
		try:
			c.execute(''' SELECT name, value FROM INFRARED''')			
			for row in c:
				self.cfg.update({row[0]:row[1].strip(' \n\t\r')})
				
			self.cfg.update({IRCAM_WIDTH : int(self.cfg[IRCAM_WIDTH])} )
			self.cfg.update({IRCAM_HEIGHT : int(self.cfg[IRCAM_HEIGHT])} )
			self.cfg.update({IRCAM_THRESHOLD : int(self.cfg[IRCAM_THRESHOLD])} )
			self.cfg.update({IRCAM_CAPTURE_NUM : int(self.cfg[IRCAM_CAPTURE_NUM])} )	
			self.cfg[IRCAM_ADDR] = str(self.cfg[IRCAM_ADDR])	
			self.cfg[IRCAM_PORT] = str(self.cfg[IRCAM_PORT])
			conn.close()
		except Exception as e:
			print "Error: IR config from database %s"%(e.message)
		self.IRCamera = None

		try:
			IsImported = self.importModule(self.cfg[IRCAM_BRAND], self.cfg[IRCAM_BRAND])
			if IsImported:
				self.IRCamera.disconnect()
				self.connectIR_Module(IsImported)
			else:
				self.connectIR_Module(IsImported)
						
			self.initIRCam(34, 50, 7.2, 5.294)
			gevent.spawn(self._nucTask, 300)
		except Exception as e:
			print 'Error:', e.message
			quit()

		
	def _nucTask(self, period):
		lastNUCTime = time.time()
		while True:
			if (time.time() - lastNUCTime) >= period:
				lastNUCTime = time.time()
				self.greenLight.wait()
				self.greenLight.clear()
				try:
					self.IRCamera.setNUC()
					gevent.sleep(self.cfg[IRCAM_NUC_DELAY])
				except:
					pass
				self.greenLight.set()
			else:
				cv2.waitKey(1)
				gevent.sleep(1)

	def initIRCam(self,vTotal,hTotal,FOVH, FOVV ):
		
		thresholdInfo = self.str2list(self.cfg[IRCAM_THRESHOLD_INFO], int)
		distanceInfo = self.str2list(self.cfg[IRCAM_DISTANCE_INFO], float)	
		self.flirScalingObj = str2mat.cvtStr2Img(-32768, -32768, self.cfg[IRCAM_BRAND], self.cfg[IRCAM_WIDTH], self.cfg[IRCAM_HEIGHT], 32)

		
	def str2list(self,inStr, listtype):
		valuelist=inStr.split(',')
		listInfo=[]
		for cur in valuelist:
			listInfo.append(listtype(cur))
		return listInfo
			
	def importModule(self, module, className):
		try:
			if self.IRCamera is None:
				module = importlib.import_module(module)
				self.IRCamera = getattr(module,className)
			else:
				return True
		except AttributeError:
			module = importlib.import_module(module)
			self.IRCamera = getattr(module,className)
		return False
	
	
	def connectIR_Module(self, isImported):
		
		#width,height,ip,port,userName,password
		if isImported == False:
			self.IRCamera = self.IRCamera(self.cfg[IRCAM_WIDTH], self.cfg[IRCAM_HEIGHT],
										self.cfg[IRCAM_ADDR], self.cfg[IRCAM_PORT],
										self.cfg[IRCAM_USERNAME], self.cfg[IRCAM_PASSWORD])
		self.IRCamera.IR_init()
		status = self.IRCamera.connect()
		while status['status'] == 'ERR':
			gevent.sleep(0.5)
			self.IRCamera.IR_init()
			status = self.IRCamera.connect()

	def setNUC(self):
		self.greenLight.wait()
		self.greenLight.clear()
		self.IRCamera.setNUC()
		gevent.sleep(4)
		self.greenLight.set()
			
	def startDetect(self):
	
		accumulator = np.zeros((self.cfg[IRCAM_HEIGHT], self.cfg[IRCAM_WIDTH]), dtype=np.uint32)
		self.greenLight.wait()
		self.greenLight.clear()
		try:
			N = self.cfg[IRCAM_CAPTURE_NUM]
			for i in range(N):
				inputRAW = self.IRCamera.getRAW()	#inputRAW is ndarray, inputRAW dtype must be uint16, [LSB MSB]
				accumulator += inputRAW
				gevent.sleep(0.03)
			inputRAW = accumulator/N
		except Exception as e:
			self.greenLight.set()
			raise ValueError('get RAW  %s'%(e.message))
		self.greenLight.set()
		
		if inputRAW is None or len(inputRAW)==0:
			raise ValueError('IR data size error')
		
		(flirimg, raw14bit, minVal, maxVal ,mean) = self.flirScalingObj.flir_img(inputRAW)
		flirimg = cv2.cvtColor(flirimg, cv2.COLOR_GRAY2BGR)		
		cv2.putText(flirimg, "max %d   min %d"%(maxVal,minVal),(0,15), cv2.FONT_HERSHEY_PLAIN, 1.2, [0,0,1], 1)
		if self.cfg[IRCAM_BRAND] == 'COX_CG':
			resizedisplay(flirimg,1)
		else:
			resizedisplay(flirimg,2)
		return 
		
if __name__ == '__main__':

	from time import gmtime, strftime
	ircam = IRCam()
	ircam.initIRCam(34, 50, 7.2, 5.294)
	startTime = time.time()
	while True:
		if time.time() - startTime >= 0.4:
			startTime = time.time()
			ircam.startDetect()
		else:
			gevent.sleep(0.1)


