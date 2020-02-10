import sys
import os

parentPath = os.path.abspath("..")
if parentPath not in sys.path:
    sys.path.insert(0, parentPath)

import cv2
import numpy as np
import traceback
from postype import *
import str2mat
import irdetr
import irconfig

class IRConnectorDummy:

    def __init__(self, cfg_path, geoinfo_path):
        self.cfg = irconfig.Irconfig()
        self.cfg.read_db(cfg_path)
        self.IRCamera = None
        self.passby = False
        self.fakeFire = False
        self.accm_size = (self.cfg.camheight, self.cfg.camwidth)
        self._create_folder(self.cfg.dataPath + 'IRImage')
        self._create_folder(self.cfg.dataPath + 'IREvent')
        self.savesettings = [cv2.IMWRITE_JPEG_QUALITY, 93]
        
        # distance and threshold info string to list
        threshold_info = self.str2list(self.cfg.thresholdinfo, int)
        distance_info = self.str2list(self.cfg.distanceinfo, float)
        
        self.flirScalingObj = str2mat.cvtStr2Img(-32768, -32768, self.cfg.cambrand,
                                                 self.cfg.camwidth, self.cfg.camheight,
                                                 self.cfg.camsegment)
                                                 
        framesize = size2i(self.cfg.camwidth, self.cfg.camheight)
        seg = size2i(self.cfg.camsegment, self.cfg.camsegment)
        fov = angle2f(self.cfg.fovh, self.cfg.fovv)
        self.detector = irdetr.Irdetector(framesize, seg, np.array(threshold_info),
                                          np.array(distance_info), fov, cfg_path, geoinfo_path)
        
        self.Hindex = 0
        self.Vindex = 0

        if not os.path.exists(self.cfg.dataPath + 'emulator'):
            os.makedirs(self.cfg.dataPath + 'emulator')

        if not os.path.exists(self.cfg.dataPath + 'emulator\\iremulator'):
            os.makedirs(self.cfg.dataPath + 'emulator\\iremulator')

    @staticmethod
    def _create_folder(name):
        if not os.path.exists(name):
            os.makedirs(name)

    def captureDetect(self, ha, va, fname, auto_mode, hind, vind, detection_en=True):
        return True
        
    def getframe(self):
        #get image from file and return
        #IRData = pickle.load( open( "emulator/iremulator.txt", "rb" ) )
        #return IRData
        pass
        
    def init_detector(self, fovh, fovv):
        pass
        
    @staticmethod
    def str2list(in_str, listtype):
        valuelist = in_str.split(',')
        list_info = []
        for cur in valuelist:
            list_info.append(listtype(cur))
        return list_info
        
    def importModule(self, module, class_name):
        return True
        
    def connectIR_Module(self, is_imported):
        pass
        
    def setNUC(self):
        pass
        
    def override(self, x, y, value):
        pass
        
    def maskCmdFromUI(self, cmd):
        return self.detector.modifyMask(cmd)
            
    def modifyDistance(self, cmd):
        """
        :type cmd:dict
        :rtype:dict
        """
        print 'irconn', cmd
        
        if cmd['maskaction'].upper() == 'GET':
            try:
                ha = float(cmd['hangle'])/1000.0
                va = float(cmd['vangle'])/1000.0
                center = angle2f(ha, va)
                seg = size2i(self.cfg.camsegment, self.cfg.camsegment)
                dist_map = self.detector.getDistanceByAngle(center, seg)
                dist_map = dist_map.ravel()           # 2d array to 1d array then change to list
                dist_map = ','.join(map(str, dist_map))
                cmd.update({'status': 'OK', 'distance': dist_map})
                cmd.update({'statuus': 'OK'})
                return cmd
            except Exception as e:
                #print traceback.print_exc()
                cmd.update({'status': 'ERR', 'msg': e.message})
                return cmd
                
        elif cmd['maskaction'].upper() == 'ADD':
            try:
                new_dist_map = np.array(cmd['distance'].split(','), np.float)
                new_dist_map = np.reshape(new_dist_map, (self.cfg.camsegment, self.cfg.camsegment))
                ha = float(cmd['hangle']) / 1000.0
                va = float(cmd['vangle']) / 1000.0
                center = angle2f(ha, va)
                self.detector.setDistanceByAngle(center, new_dist_map)
                cmd.pop('distance')
                cmd.update({'status': 'OK'})
                return cmd
            except Exception as e:
                cmd.update({'status': 'ERR', 'msg': e.message})
                return cmd
    
    def getOriginDist(self, cmd):
        """
        :type cmd: dict
        :rtype: dict
        """
        if cmd['maskaction'].upper() == 'GET':
            try:
                ha = float(cmd['hangle'])/1000.0
                va = float(cmd['vangle'])/1000.0
                center = angle2f(ha, va)
                seg = size2i(self.cfg.camsegment, self.cfg.camsegment)
                dist_map = self.detector.getOriginDistByAgl(center, seg)
                dist_map = (dist_map.ravel())            # 2d array to 1d array then change to list
                dist_map = ','.join(map(str, dist_map))
                cmd.update({'status': 'OK', 'distance': dist_map})
                return cmd
            except Exception as e:
                cmd.update({'status': 'ERR', 'msg': e.message})
                return cmd
                
    @staticmethod
    def watchdog():
        return {'status': 'OK'}
        
    def addEvent(self, event):
        pass
        
    def getSize(self):
        width = self.IRCamera.getWidth()
        height = self.IRCamera.getHeight()
        return width, height

    def getResult(self):
        """        
            :rtype: (bool, list)
            """
        return []
        
    def getImageStr(self):
       """
            :rtype: str
            """
       self.img = cv2.imread("emulator//iremulator.jpg")

       img_str = cv2.imencode('.jpg', self.img, self.savesettings)[1].tostring()
       return img_str
    

    def flush(self):
        pass

    def get_dist_lat_lon_alt(self, hangle, vangle):    # for an single beam
        """
        :type hangle: float
        :type vangle: float
        :rtype: (float, float, float, int)
        """
        center = angle2f(hangle, vangle)
        return self.detector.get_dist_lat_lon_alt(center)

    def set_sensitivity(self, sens):
        # sens should be close to 1.0
        """
        :type sens: float
        :rtype: dict
        """
        self.detector.set_sensitivity(sens)
        return {"status": "OK"}
