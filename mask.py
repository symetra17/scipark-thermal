#! /usr/bin/env python
# -*- coding: utf-8 -*-  
import os, sys
import numpy as np
import logging
import logging.handlers
from logging.handlers import RotatingFileHandler
from logging import StreamHandler, Formatter
import sqlite3
import cv2
from base64conv import *
from postype import *
import traceback
import zlib
import base64


class ImageMask(object):

    def __init__(self, segment, maskType, FOVV, FOVH, width, height, cfg_path):

        if maskType == 'irmask':
            self.maskLog = logging.getLogger('IRCAM.log')
            
        elif maskType == 'vismask':
            self.maskLog = logging.getLogger('VISCamera.log')

        self.segment = segment
        self.VStep = FOVV      # ir camera optical fov
        self.HStep = FOVH      # ir camera optical fov
        self.width = width
        self.height = height
        self.maskType = maskType

        try:
            conn = sqlite3.connect(cfg_path)
            c = conn.cursor()
            self.ptzcfg = {}
            for row in c.execute('SELECT NAME,VALUE FROM PTZ'):
                self.ptzcfg.update({row[0]: row[1].strip(' \n\t\r')})
            conn.close()
        except Exception as e:
            self.maskLog.error("Exception config database %s" % e.message)
            print 'Error in reading config database for mask'
            quit()

        self.ptzcfg['hstep'] = float(self.ptzcfg['hstep'])
        self.ptzcfg['vstep'] = float(self.ptzcfg['vstep'])
        self.htotalstep = int(self.ptzcfg['htotalstep'])
        self.vtotalstep = int(self.ptzcfg['vtotalstep'])   # number of vertical viewerable layers
        self.vtotal_180 = int(round(180.0/self.ptzcfg['vstep']))        # included non-viewerable layers


        # These H/V step must match the H/V angle of distance files
        # example:
        #  segment 80, vtotal_180 34, htotalstep 50
        #  size = (2720, 4000)
        size = (self.vtotal_180 * self.segment, self.htotalstep * self.segment)
        self.maskMap = np.zeros(size, dtype=np.uint8)
        
        if maskType == 'irmask':    
            if not os.path.isdir("IRMaskFile"):
                os.makedirs("IRMaskFile")
            path = os.path.join('IRMaskFile', 'maskMap.npy')            
            try:
                loadFile = np.load(path)
                if loadFile.shape == self.maskMap.shape:
                    self.maskMap = loadFile
                else:
                    raise ValueError("IR mask file size mismatch")
            except Exception as e:
                    np.save(path, self.maskMap)
                    
        elif maskType == 'vismask':   
            if not os.path.isdir("VISMaskFile"):
                os.makedirs("VISMaskFile")
            path = os.path.join('VISMaskFile', 'visMaskMap.npy')            
            try:
                loadFile = np.load(path)
                if loadFile.shape == self.maskMap.shape:
                    self.maskMap = loadFile
                else:
                    print 'mask shape not match'
                    raise ValueError("mask file difference file=%s,%s, Actual=%s,%s"%(loadFile.shape[0],loadFile.shape[1],
                                     self.maskMap.shape[0],self.maskMap.shape[1]))
            except Exception as e:                
                    np.save(path, self.maskMap)


    def UIMaskEvent(self, cmd):
        """
        cmd = {maskaction : ADD/DEL/GET, 
               type       : vismask/irmask
               vangle     : float or string, 
               hangle     : float or string, 
               maskstring : base64, will be convert to numpy arrtay according 
                            to self.segment
              }
        """
        compress = 'compress' in cmd
        if compress:
            cmd['compress'] = 'zlib'

        v = float(cmd['vangle'])/1000
        h = float(cmd['hangle'])/1000

        if v >=-90.0 and v<=90.0:
            if cmd['maskaction'].upper() == 'GET':
                if cmd['type'].upper() == 'IRMASK':
                    try:
                        ang2 = angle2f(h, v)
                        maskImg = self.getMaskMapByAngle(ang2)      # GET mask point vAngle,hAngle
                    except:
                        cmd.update({'status': 'ERR', 'msg': traceback.format_exc()})
                        return cmd
                elif cmd['type'].upper() == 'ALLIRMASK':
                    try:
                        maskImg, vAglOffset, hAglOffset = self.getAllMask(cmd['type'])
                        cmd.update({'voffset': vAglOffset, 'hoffset': hAglOffset})
                    except:
                        cmd.update({'status': 'ERR', 'msg': traceback.format_exc()})
                        return cmd
                        
                if compress:
                    str64 = self.numpy2base64(maskImg)
                else:
                    maskImg = maskImg.astype(bool)     # change uint8 to bool
                    maskImg = list(maskImg.ravel())    # 2d array to 1d array then change to list
                    str64 = bool2base64(maskImg)
                cmd.update({'status': 'OK', 'mask': str64})
                return cmd

            if cmd['maskaction'].upper() == 'ADD' or cmd['maskaction'].upper() == 'DEL':
                maskString = cmd.pop("maskstring")

                if compress:
                    zstr = maskString.decode('base64')
                    str_10010 = zlib.decompress(zstr)
                    npa_1d = np.fromstring(str_10010, dtype=np.uint8)
                    maskArr = npa_1d.reshape((self.segment, self.segment))
                else:
                    maskArr = base642bool(maskString)
                    maskArr = np.asarray(maskArr, dtype=np.uint8)
                    maskArr = np.reshape(maskArr, [self.segment, self.segment])
                
                if cmd['maskaction'].upper() == 'ADD':
                    maskImg = self.addMaskPoint(v, h, maskArr)   #add IR mask point vAngle,hAngle,firePoints
                    
                elif cmd['maskaction'].upper() == 'DEL':
                    maskImg = self.delMaskPoint(v, h, maskArr)       #Delete IR mask point vAngle,hAngle,firePoints
                
                if maskImg['status'].upper() == 'OK':
                    cmd.update({'status':'OK','mask': maskImg['maskArray']})
                else:
                    cmd.update({'status':'ERR','msg': maskImg['msg']})
                return cmd
        else:
            msg = "mask Angle(v=%d  h=%d) Invalid" %(v, h)
            self.maskLog.error(msg)
            cmd.update({'status': 'ERR'})
            cmd.update({'msg': 'Vertical angle out of range'})
            return cmd

    def addMaskPoint(self, va, ha, maskPoints):
        self.maskLog.debug("add Mask points %s " % (str(np.argwhere(maskPoints>0))))
        return self.updateMaskMapByAngle('ADD', ha, va, maskPoints)
            
    def delMaskPoint(self, va, ha, unmaskArray):
        self.maskLog.debug("del Mask points %s "%(str(np.argwhere(unmaskArray>0))))
        return self.updateMaskMapByAngle('DEL', ha, va,unmaskArray)
        
    def updateMaskMapByAngle(self, updateAction, HAngle, VAngle, updateMaskArr):
        # Accepting VAngle input from sky: 90 degree 
        # horizon: 0 degree, all downward: -90 degree
        # HAngle and VAngle are defined as the center of the frame
        # bigMap is scale up to self.width*self.height
        # smallMap is self.segment*self.segment map array
        h, v = self.convAngle2Index(VAngle, HAngle, self.VStep, self.HStep, self.segment)

        ro = np.roll(self.maskMap, (self.segment/2)-h, axis=1)

        smallMap = ro[v:v+self.segment, 0:self.segment]
        maskDict = {}
        
        if updateAction == 'ADD':
            maskResult = np.bitwise_or(smallMap,updateMaskArr)

        elif updateAction == 'DEL':
            allOnes = np.ones((self.segment,self.segment), dtype=np.uint8)
            updateMaskArr = np.bitwise_xor(updateMaskArr, allOnes)     # xor equal=0, not equal=1
            maskResult = np.bitwise_and(smallMap,updateMaskArr)

        ro[v:v+self.segment, 0:self.segment] = maskResult.copy()
        self.maskMap = np.roll(ro,-((self.segment/2)-h),axis=1)

        try:
            if self.maskType == 'irmask':
                path = os.path.join('IRMaskFile', 'maskMap.npy')
                np.save(path, self.maskMap)
            elif self.maskType == 'vismask':
                path = os.path.join('VISMaskFile', 'visMaskMap.npy')
                np.save(path, self.maskMap)
            maskResult = maskResult.astype(bool)              # change uint8 to bool
            maskResult = list(maskResult.ravel())             # 2d array to 1d array then change to list            
            maskResult = bool2base64(maskResult)
            maskDict.update({'status': 'OK', 'maskArray': maskResult})
            return maskDict
        except Exception as e:
            self.maskLog.error("save %s mask error, msg=%s"%(self.maskType,e.message))
            maskDict.update({'status': 'ERR', 'msg': e.message})
            return maskDict

    def getMaskMapByAngle(self, ang2):
        """
        :type ang2:angle2f
        :rtype: numpy.ndarray
        """
        # Accepting VAngle input from sky: 90 degree 
        # horizon: 0 degree, all downward: -90 degree
        # HAngle and VAngle are defined as the center of the frame
        # bigMap is scale up to self.width*self.height
        # smallMap is self.segment*self.segment map array
        h,v = self.convAngle2Index(ang2.va, ang2.ha, self.VStep, self.HStep, self.segment)
        ro = np.roll(self.maskMap, (self.segment/2)-h, axis=1)
        smallMap = ro[v:v+self.segment, 0:self.segment]
        return smallMap

    def getAllMask(self, maskType):
        """
        :type maskType:str
        """
        try:
            if maskType.upper() == 'ALLIRMASK':
                path = os.path.join('IRMaskFile', 'maskMap.npy')
                maskFile = np.load(path)
            elif maskType.upper() == 'ALLVISMASK':
                path = os.path.join('VISMaskFile', 'visMaskMap.npy')
                maskFile = np.load(path)
        except Exception as e:
            self.maskLog.error("load %s %s"%(maskType,e.message))
            raise ValueError('%s'%e.message)

        try:
            ptzUpVAng = -((self.vtotalstep/2) * (self.ptzcfg['vstep']))  # -37.058
            startVAng = (ptzUpVAng + 90.0) - (0.5 * self.ptzcfg['vstep'])   # 50.295
            startVAng = np.clip(startVAng, 0.0, 170.0)
            startVIdx = int(round(self.segment*startVAng/float(self.VStep)))   # 760
            ptzDnVAng = self.vtotalstep * self.ptzcfg['vstep']  # +37.058
            endVAng = ptzDnVAng + startVAng
            endVAng = np.clip(endVAng, 0.0, 170.0)
            endVIdx = int(round(self.segment*endVAng/float(self.VStep)))

            endHIdx = self.segment * self.htotalstep

            rollHSeg = int(round(((self.ptzcfg['hstep']/float(self.HStep))/2)*self.segment))
            ro = np.roll(maskFile, rollHSeg, axis=1)
            smallMap = ro[startVIdx: endVIdx, 0:endHIdx]
            
            startVIdxFloat = self.segment*startVAng/float(self.VStep)
            startVIdxFloat = str(startVIdxFloat-int(startVIdxFloat))
            
            startHIdxFloat = ((self.ptzcfg['hstep']/float(self.HStep))/2)*self.segment
            startHIdxFloat = str(startHIdxFloat-int(startHIdxFloat))

            print 'smallMap.shape', smallMap.shape

            return smallMap, startVIdxFloat, startHIdxFloat
        except Exception as e:
            self.maskLog.error('read %s mask numpy file error %s'%(maskType.upper(),e.message))
            raise ValueError('%s'%e.message)
            
    @staticmethod
    def convAngle2Index(vAngle, hAngle, FOVV, FOVH, seg):
        VAngle = -vAngle
        VAngle += 90
        VAngle -= 0.5*FOVV
        HAngle = hAngle%360
        h = int(round(seg*HAngle/FOVH))
        v = int(round(seg*VAngle/FOVV))
        return h, v
    
    @staticmethod
    def numpy2base64(npa):
        str_10010 = str(npa.ravel().tobytes())
        zstr64 = zlib.compress(str_10010, 2).encode('base64')
        return zstr64


if __name__ == '__main__':
    import gevent
    from numpy import kron
    import numpy as np
    import base64conv
    #maskObj = ImageMask(32,"D:/imgDB/", "vismask", 5.294, 7.2, 384,288)
    maskObj = ImageMask(32,"c:/imgDB/", "irmask", 5.294, 7.2, 1280, 960, r'..\config.db')
    wm = "mask32"
    while True:
        x = raw_input(">>> Input (+/-/g),v,h: ")
        s = x.split(',')
        if s[0] == '+':
            #maskcmd = {'maskaction': 'ADD', 'vangle': s[1], 'hangle': s[2], 'maskstring': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/AAAAPwAAAD8AAAA/AAAAPwAAAD8AAAA/AAAAPwAAAD8AAAA/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=', 'type': 'irmask'}
            l = np.ones((32,32),dtype=np.bool)
            #maskArr = np.asarray(l, dtype=np.uint8)
            try:
                maskImg = maskObj.updateMaskMapByAngle("ADD", 15,20,l)

            except:
                print "Error in update mask map by angle"
            
        elif s[0] == '-':
            d = np.zeros((32,32),dtype=np.bool)
            d[0:10,0:10] = True
            #maskArr = np.asarray(l, dtype=np.uint8)
            try:
                maskImg = maskObj.updateMaskMapByAngle("DEL", 15, 20, d)
            except:
                print "Error in update mask map by angle"
        elif s[0] == 'g':
                ang2 = angle2f(11.4, 22.647)
                smallmap = maskObj.getMaskMapByAngle(ang2) * 255
                cv2.namedWindow(wm, flags=cv2.cv.CV_WINDOW_NORMAL)
                cv2.resizeWindow(wm, 320,320)

                cv2.imshow(wm,smallmap)
                key = cv2.waitKey(1)        
        elif s[0] == 't':
            ang2 = angle2f(10,10)
            smallmap = maskObj.getMaskMapByAngle(ang2) * 255
            cv2.namedWindow(wm, flags=cv2.cv.CV_WINDOW_NORMAL)
            cv2.resizeWindow(wm, 320,320)
            print "small map", np.any(smallmap),list(smallmap)
            
            cv2.imshow(wm,smallmap)
            key = cv2.waitKey(1)

        gevent.sleep(0.1)