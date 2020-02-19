#! /usr/bin/env python
# -*- coding: utf-8 -*-  
'''
Created on 2015-June

@author:  Insight Robotics HK LTD
'''
import types_define
import ctypes
from ctypes import *
from ctypes import wintypes
import numpy as np
import sys
import time
import pdb
import cv2
import os
import traceback

import skimage.util as skimage
from datetime import datetime

import gevent

from struct import *


class COX_CG(object):
    def __init__(self, width, height, ip, port, userName, password):
        self.width = width
        self.height = height
        self.ip =ip
        self.port = port
        self.userName = userName
        self.password = password
        self.IRConnected = False
        self.lowBound = -1
        self.highBound = -1
        self.windowName = 'show'
        try:
            dll = os.path.join('dll', 'CG_ThermalCamDll.dll')
            self.coxDLL = windll.LoadLibrary(dll)
        except Exception as e:
            print "Unable to load Cox DLL ", e.message
        
    def disconnect(self):
        print"Disconnect mhandle ",self.mHandle, self.keepAlive
        
        if self.mHandle.value != None:
            self.coxDLL.CloseConnect.restype = c_short
            self.coxDLL.CloseConnect.argtypes = [POINTER(wintypes.HANDLE), c_uint]
            try:
                err = self.coxDLL.CloseConnect(byref(self.mHandle), self.keepAlive)
                if err == 1:
                    return err
            except Exception as e:
                print "!!! Exception in close connection ",e.message
        return None
    
    def IR_init (self):
        ''' 
        Cox Init procedure, assign width *height memory
        ''' 
        self.mHandle = wintypes.HANDLE()
        self.keepAlive = c_uint32()
        self.camData = types_define.CG_IRF_IR_CAM_DATA_T()
        
        #self.irimage = (c_ushort *(self.width * self.height ))()
        self.irimage = (c_ushort *(1024 * 1024 ))() #(c_ushort *(self.width * self.height ))()
        
        self.camData.ir_image = cast(self.irimage, POINTER(c_ushort))
        
        self.camData.image_buffer_size = (1024 * 1024 )# self.width * self.height
        
        self.lpsize = (c_byte*8192)()
        self.camData.lpNextData = cast(self.lpsize, POINTER(c_byte))
        
        self.camData.dwSize = 0
        self.camData.dwPosition = 0
        self.agc_ctrl = types_define.IRF_AUTO_RANGE_METHOD_T()
        self.agc_ctrl.autoScale = types_define.IRF_AUTOMATIC_TYPE_T._IRF_AUTO.value
        self.agc_ctrl.inputMethod = types_define.IRF_AUTO_RANGE_INPUT_METHOD_T._IRF_SD_RATE.value
        self.agc_ctrl.SD_Rate = 5.0
        self.agc_ctrl.B_Rate = 0.01
        self.agc_ctrl.outputMethod = types_define.IRF_AUTO_RANGE_OUTPUT_METHOD_T._IRF_LINEAR.value
        self.agc_ctrl.intercept = 0
        self.agc_ctrl.gamma = 1.0
        self.agc_ctrl.plateau = 100
        self.agc_ctrl.epsilon = 0.5
        self.agc_ctrl.psi = 0.3
        self.agc_ctrl.prevPalteau = 0
        self.coxDLL.GetIRImages.restypes = c_short
        self.coxDLL.GetIRImages.argtypes = [wintypes.HANDLE, POINTER(c_uint), POINTER(types_define.CG_IRF_IR_CAM_DATA_T)]
        
    def connect(self):
        '''
        Connect Cox camera
        '''
        #Connect to Cox Camera
        #address = c_wchar()
        #devicePort = c_wchar()
        
        print "Cox connect  ", self.ip, self.port
        self.coxDLL.OpenConnect.restype = c_short
        #self.coxDLL.OpenConnect.argtypes = [POINTER(wintypes.HANDLE), POINTER(c_uint), c_wchar_p, c_wchar_p,c_int,c_int]
        err = -1
        try:
            err = self.coxDLL.OpenConnect(byref(self.mHandle), byref(self.keepAlive), self.ip, self.port, 2, 1)
            if err == 1:
                print "Cox Connect OK!"
                err = self.requestCameraData()
                if err == 1:
                    err = self.setSize()
                    if err == 1:
                        err = self.setNUC() #cg series call this function will crash GetIRImage function
                        if err ==1:
                            try:
                                gevent.spawn(self.threadProc)
                            except Exception as e:
                                print "Execption in set thread",e.message
            else:
                print "Cox Connect Fail errcode=%d self.keepAlive =%d self.mHandle=%d"%(err, self.keepAlive.value, self.mHandle.value)
        except Exception as e:
            print "Exception in open connection ",e.message
        
        if err < 0:
            return {'status':'ERR'}
        return {'status':'OK'}

    def requestCameraData(self):
        '''
        request all camera setting value _IRF_REQ_CAM_DATA
        '''
        
        self.coxDLL.SendCameraMessage.restype = c_short
        self.coxDLL.SendCameraMessage.argtypes = [wintypes.HANDLE, 
                                                    POINTER(c_uint), 
                                                    c_int,
                                                    c_ushort,
                                                    c_ushort]
        
        try:
            err = self.coxDLL.SendCameraMessage(
                    self.mHandle, byref(self.keepAlive),
                    types_define.IRF_MESSAGE_TYPE_T._IRF_REQ_CAM_DATA.value, 0, 0)
            if err == 1:
                print "request all cam data message OK!"
            else:
                print "send request all cam data message fail errcode =%d "%(err)
        except Exception as e:
            print"Exception in request all cam data message",e.message
        
        #request stream on_IRF_STREAM_ON
        try:
            err = self.coxDLL.SendCameraMessage(
                    self.mHandle, byref(self.keepAlive),
                    types_define.IRF_MESSAGE_TYPE_T._IRF_STREAM_ON.value, 0, 0)
            if err == 1:
                print "request stream on message OK!"
            else:
                print "send stream on message fail errcode=%d"%(err)
        except Exception as e:
            print"Exception in stream on message",e.message
        
        return err
    
    def setSize(self):
        '''
        Get IR image width and height from camera
        '''        
        try:
            err = self.coxDLL.GetIRImages(
                self.mHandle, byref(self.keepAlive), byref(self.camData))
            if err == 1:
                if self.camData.save_data.sensor == 0x20:
                    self.width = 384
                    self.height = 288
                elif self.camData.save_data.sensor == 0x21:
                    self.width = 640
                    self.height = 480
                print "COX width=%d height=%d Sensor=%d"%(self.width, self.height,self.camData.save_data.sensor)
            else:
                print "set size errcode = %d "%(err)
        except Exception as e:
            print"Exception in set size",e.message
        
        return err
    

    def threadProc(self):
        '''
        start a thread to get raw data from COX camera
        '''
        
        while (1):
            try:
                err = self.coxDLL.GetIRImages(
                    self.mHandle, byref(self.keepAlive), byref(self.camData))

                if err != 1:
                    print "Get IR Images fail errcode=%d"%(err)
                    break
                #print "Get IR Images OK"
            except Exception as e:
                print "exception in get ir image",e.message
                break
            gevent.sleep(0.02)
        self.disconnect()
        self.IR_init()
        status = self.connect()
        while status['status'] == 'ERR':
            print 'reconnect when network suddently lost'
            gevent.sleep(0.5)
            self.disconnect()
            self.IR_init()
            status = self.connect()         
    
    def getRAW(self):
        IRData = np.ndarray(buffer=(c_uint16 * self.width * self.height).from_address(addressof(self.irimage)),
                            dtype=np.uint16, shape=(self.height,self.width))
        return IRData

    
    def setNUC(self):
        '''
        Perform NUC (non uniformity correction) 
        '''
        self.coxDLL.SendMessageToCamera.restype = c_short
        self.coxDLL.SendMessageToCamera.argtypes = [wintypes.HANDLE, POINTER(c_uint), c_int,c_ushort,c_ushort,c_ulong,c_ulong,c_ulong]
        
        try:
            err = self.coxDLL.SendMessageToCamera(
                self.mHandle, byref(self.keepAlive),
                types_define.IRF_MESSAGE_TYPE_T._IRF_SET_CAM_DATA.value,
                types_define.CAMMAND_CODE.CMD_NUC_ONETIME.value, 0, 0, 0, 0)
            if err == 1:
                print "Set NUC message OK!"
            else:
                print "Set NUC message fail errcode=%d"%(err)
        except Exception as e:
            print"Exception in Set NUC message",e.message
        
        return err
    
    def showIR(self):
        
        #self.uint16Img = np.ndarray(buffer=(c_ushort * self.height * self.width * 1).from_address(addressof(self.camData.ir_image.contents)), dtype=np.uint8, shape=(self.height, self.width, 1))
        
        self.uint16Img = np.ndarray(buffer=self.irimage, dtype=np.uint16,shape=(self.height , self.width))
        #self.uint16Img = np.ndarray(buffer=self.byteData, dtype=np.uint16,shape=(288 , 384))
        #print "LowBound = %s, HighBound = %s minVal = %s, MaxVal = %s "%(lowBound,highBound,np.min(self.uint16Img),np.max(self.uint16Img))
        offsetIRData = skimage.dtype.convert(self.uint16Img, np.float32)
        
        maxVal= np.max(np.max(offsetIRData))
        minVal = np.min(np.min(offsetIRData))
        
        img=np.array(offsetIRData,np.float32)
        img=img[0:self.height,:]
        
        if minVal<0 or maxVal<0:
            pass
        elif self.lowBound ==-1 or self.highBound ==-1:
            self.lowBound = minVal
            self.highBound = maxVal          
        elif minVal<self.lowBound or maxVal>self.highBound:
            if minVal<self.lowBound and maxVal>self.lowBound:
                self.lowBound = minVal
            if maxVal>self.highBound and minVal<self.highBound:
                maxVal-= minVal #np.max(np.max(img - minVal)) * ratio + (self.highBound - self.lowBound) * (float(1.0)-ratio)
                self.highBound = maxVal + minVal
                maxVal+=minVal
        img = np.clip(img, minVal, maxVal)
        maxVal -= minVal
        img=(img - minVal )
        if maxVal>0:
            img = img/maxVal    #255
        
        cv2.imshow(self.windowName, img)
        Key = cv2.waitKey(1)
        #self.saveIRimage(img)
    
    def saveIRimage(self,Img):

        img=np.array(Img,np.float32)
            
        #print "IR RAW data size ",img.shape
        minVal = np.min(img)
        maxVal= np.max(img)
        img = np.clip(img, minVal, maxVal)
        maxVal -= minVal
        #print "maxVal:%d"%(maxVal),img.dtype.type
        img=img-minVal
        #print "max=%f"%(max(img))
        #print "float max=%f,min=%f,maxVal=%d"%(np.max(img),np.min(img),maxVal)
        if maxVal>0:
            img = img/maxVal    #255
        img=np.clip(img,0.0,1.0)
        meanVal = np.mean(img)

        flirimg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
        try:
            currenttime = datetime.now().strftime("%Y_%m_%d_%H.%M.%S.%f")
            fullpath = '%s/cap_%s.jpg' % ('IRImage', currenttime)
            flirimg = np.ceil(flirimg*255)
            cv2.imwrite(fullpath, flirimg, [cv2.IMWRITE_JPEG_QUALITY, 90])
        except Exception as e:
            print "Exception in save IR",e.message
    
    def getWidth(self):
        return self.width

    def getHeight(self):
        return self.height

    def _saveIRTextData(self, rawData):
        '''
        save IR raw data to txt binary file
        '''
        currenttime = datetime.now().strftime("%Y_%m_%d_%H.%M.%S.%f")
        try:
            if rawData is not None:
                f=open('IRImage/cap_%s.txt' % currenttime, 'wb')
                data=rawData.reshape(rawData.shape[0]*rawData.shape[1])
                bin=[int(b) for b in data]
                pkg=pack('<%sH' % len(bin), *bin)
                f.write(pkg)
                f.close()
            print 'IRImage/cap_%s.txt saved' % currenttime
        except Exception as e:
            print "Error when saving text data: %s %s"%('cap_%s.txt' % currenttime, e.message)

    def _setFocus(self, direction):
        '''
        Control Focus motor
        direction = 1 or 2
        RCODE  => FOCUS OR ZOOM ( 0 : FOCUS, 1 : ZOOM )
        RCODE2 => OFF, INC or DEC ( 0 : OFF, 1 : INC, 2 : DEC )
        '''
    
        try:
            err = self.coxDLL.SendMessageToCamera(
                self.mHandle, byref(self.keepAlive),
                types_define.IRF_MESSAGE_TYPE_T._IRF_SET_CAM_DATA.value,
                types_define.CAMMAND_CODE.CMD_MOTORIZED, 0, direction, 0, 0)
            if err == 1:
                print "Set focus message OK!"
            else:
                print "Set focus message fail errcode=%d"%(err)
        except Exception as e:
            print"Exception in Set focus message",e.message

        gevent.sleep(0.05)
        try:
            err = self.coxDLL.SendMessageToCamera(
                self.mHandle, byref(self.keepAlive),
                types_define.IRF_MESSAGE_TYPE_T._IRF_SET_CAM_DATA.value,
                types_define.CAMMAND_CODE.CMD_MOTORIZED, 0, 0, 0, 0)
            if err == 1:
                print "Set stop focus message OK!"
            else:
                print "Set stop focus message fail errcode=%d"%(err)
        except Exception as e:
            print"Exception in Set stop focus message",e.message
        
        return err
        
if __name__ == '__main__':
    cox = COX_CG(640,480,"192.168.88.253","15001","admin","12345")
    cox.IR_init()
    cox.connect()
    #cnt = 0
    while True:
        cox.showIR()
        #cnt += 1
        #if cnt >= 2:
            #cox._setFocus(1)
            #cnt =0
        #rawdata = cox.getRAW()
        #cox.saveIRimage(rawdata)
        #cox._saveIRTextData(rawdata)
        gevent.sleep(0.5)
