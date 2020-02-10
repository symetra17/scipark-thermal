# -*- coding: utf-8 -*-  
import os
import sys

parentPath = os.path.abspath("..")
if parentPath not in sys.path:
    sys.path.insert(0, parentPath)

import zerorpc
import gevent
import gevent.event
import logging
import logging.handlers
from logging.handlers import RotatingFileHandler
from logging import Formatter
import importlib
import time
from datetime import datetime
import numpy as np
import cv2
import str2mat
import irdetr
from struct import *
import traceback
from postype import *
import irconfig
import custom_print
import pickle
import override


class IRConnector(object):
    
    def __init__(self):
        
        self.new_img_indicator = custom_print.CustomPrint(4049)

        self._init_logger()
        self.log = logging.getLogger('IRCAM.log')

        # a mutex signal to prevent NUC and image capture won't happened in same time
        self.greenLight = gevent.event.Event()
        self.greenLight.set()
        self.cfg = irconfig.Irconfig()
        cfg_path = os.path.join(parentPath, 'config.db')
        self.cfg.read_db(cfg_path)
        self.IRCamera = None
        self.override_ctrl = override.Override()

        self.accm_size = (self.cfg.camheight, self.cfg.camwidth)

        imported = self.importModule(self.cfg.cambrand, self.cfg.cambrand)
        if imported:
            self.IRCamera.disconnect()
            self.connectIR_Module(imported)
        else:
            self.connectIR_Module(imported)
            
        self.create_folder(os.path.join(self.cfg.dataPath, 'IRImage'))
        self.create_folder(os.path.join(self.cfg.dataPath, 'IREvent'))

        self.quality = [cv2.IMWRITE_JPEG_QUALITY, 93]

        # distance and threshold info string to list
        threshold_info = self.str2list(self.cfg.thresholdinfo, int)
        distance_info = self.str2list(self.cfg.distanceinfo, float)

        self.flirScalingObj = str2mat.cvtStr2Img(-32768, -32768, self.cfg.cambrand,
                                                 self.cfg.camwidth, self.cfg.camheight,
                                                 self.cfg.camsegment)

        framesize = size2i(self.cfg.camwidth, self.cfg.camheight)
        seg = size2i(self.cfg.camsegment, self.cfg.camsegment)
        fov = angle2f(self.cfg.fovh, self.cfg.fovv)
        geoinfo_path = os.path.join(parentPath, 'geoinfomap')
        self.detector = irdetr.Irdetector(framesize, seg, np.array(threshold_info), 
                                          np.array(distance_info), fov, cfg_path, geoinfo_path)

        gevent.spawn(self._nuc_task, self.cfg.nucperiod)
        
    @staticmethod
    def create_folder(name):
        if not os.path.exists(name):
            os.makedirs(name)

    def _nuc_task(self, period):
        last_nuc_time = time.time()
        while True:
            if (time.time() - last_nuc_time) >= period:
                last_nuc_time = time.time()
                self.greenLight.wait()
                self.greenLight.clear()
                try:
                    self.log.debug('NUC start')
                    self.IRCamera.setNUC()
                    gevent.sleep(4)
                    self.log.debug('NUC finished')
                except:
                    pass
                self.greenLight.set()
            else:
                cv2.waitKey(1)
                gevent.sleep(0.5)

    @staticmethod
    def _init_logger(file_name='irconn.log'):
        folder = 'log'
        try:
            os.makedirs(folder)
        except:
            pass   # pass if log folder exists

        logg = logging.getLogger('')
        logg.setLevel(logging.DEBUG)
        path = os.path.join(folder, file_name)
        handler = RotatingFileHandler(path, backupCount=2, maxBytes=1024*500)
        handler.setFormatter(Formatter('%(asctime)s [line:%(lineno)d] [%(levelname)s] %(message)s'))
        logg.addHandler(handler)

    @staticmethod
    def str2list(in_str, listtype):
        valuelist = in_str.split(',')
        list_info = []
        for cur in valuelist:
            list_info.append(listtype(cur))
        return list_info
            
    def importModule(self, module1, class_name):
        try:
            if self.IRCamera is None:
                module1 = importlib.import_module(module1)
                self.IRCamera = getattr(module1, class_name)
            else:
                    self.log.debug("IR module already import")
                    return True
        except AttributeError:
            self.log.info("Import obj  %s" % str(sys.exc_info()[1]))
            module1 = importlib.import_module(module1)
            self.IRCamera = getattr(module1, class_name)
        return False

    def connectIR_Module(self, is_imported):
        
        #  width, height, ip, port, userName, password
        if not is_imported:
            self.IRCamera = self.IRCamera(self.cfg.camwidth, self.cfg.camheight,
                                          self.cfg.ipaddr, self.cfg.port,
                                          self.cfg.username, self.cfg.password)
            self.log.debug("Import IR Class = %s" % str(self.IRCamera))
        
        self.IRCamera.IR_init()
        status = self.IRCamera.connect()
        while status['status'] == 'ERR':
            self.log.error("reconnect IR camera at startup %s" % datetime.now())
            gevent.sleep(0.5)
            self.IRCamera.IR_init()
            status = self.IRCamera.connect()
        self.log.info("connect IR finish at startup")

    def setNUC(self):
        self.greenLight.wait()
        self.greenLight.clear()
        self.log.debug("UI set NUC at %s" % datetime.now())
        try:
            self.IRCamera.setNUC()
            gevent.sleep(4)
        except:
            pass
        self.greenLight.set()

    def override(self, x, y, value):
        self.override_ctrl.set(x, y, value)

    def captureDetect(self, ha, va, fname, auto_mode, hind, vind, detection_en=True):
        """
        :type ha: float
        :type va: float
        :type fname: str
        :type auto_mode: bool
        :type hind: int
        :type vind: int
        :type detection_en: bool
        :rtype: bool
        """
        print "captureDetect"
        center = angle2f(ha, va)
        try:
            self._capturedetect(center, fname, auto_mode, hind, vind, detection_en)
            return True
        except:
            print sys.exc_info()
            return False

    def getframe(self):
        """
        :rtype:str
        """
        # get simple one image frame for quick display update, no detection
        accum32 = np.zeros(self.accm_size, dtype=np.uint32)
        self.greenLight.wait()
        self.greenLight.clear()
        try:
            nimg = 2
            for i in range(nimg):
                inputraw16 = self.IRCamera.getRAW()   # inputraw is ndarray, dtype must be uint16
                accum32 += inputraw16
                gevent.sleep(0.1)
            inputraw16 = accum32/nimg
        except:
            return
        self.greenLight.set()            
        floatimg, raw14bit, min_val, max_val, mean = self.flirScalingObj.flir_img(inputraw16)
        img = (255*floatimg).astype(np.uint8)
        img_str = cv2.imencode('.jpg', img, self.quality)[1].tostring()
        return img_str

    def _capturedetect(self, center, ir_filename, auto_mode, hidx, vidx, detection_en):
        """
        :type center: angle2f
        :type ir_filename: str
        :type auto_mode: bool
        :type hidx: int
        :type vidx: int
        :rtype: None
        """
        print 'start detect'
        
        date = ir_filename.split('_')[0]
        self.create_folder(os.path.join(self.cfg.dataPath, 'IRImage', date))
        self.create_folder(os.path.join(self.cfg.dataPath, 'IREvent', date))
        
        try:            
            accum32 = np.zeros(self.accm_size, dtype=np.uint32)                        
            self.greenLight.wait()
            self.greenLight.clear()
            try:
                nimg = 2
                for i in range(nimg):
                    inputraw = self.IRCamera.getRAW()   # inputraw is ndarray, dtype must be uint16
                    accum32 += inputraw
                    gevent.sleep(0.1)
                inputraw = accum32/nimg
            except Exception as e:
                self.greenLight.set()
                self.log.error("Exception in get RAW  %s" % e.message)
                raise ValueError('get RAW  %s' % e.message)
            self.greenLight.set()

            """
            :type inputraw: numpy.ndarray
            """

            if np.count_nonzero(inputraw) == 0:       # all elements are zero, reconnect IR camera
                self.log.error("ir raw data all elements are zero")
                self.log.error("terminating module.")
                os._exit(0)
                
            if inputraw is None or len(inputraw) == 0:
                self.log.error("IR data size is 0")
                raise ValueError('IR data size is 0')
            
            # for setting fake alarm
            if self.override_ctrl.is_enable():
                for item in self.override_ctrl.mlist:
                    inputraw[item.y, item.x] = item.val
                self.override_ctrl.clear()

            floatimg, raw14bit, min_val, max_val, mean = self.flirScalingObj.flir_img(inputraw)
            self.img = (255*floatimg).astype(np.uint8)
            self.min_val = min_val
            self.max_val = max_val

            try:
                self.detresult, min_thd, max_thd = self.detector.detect(
                                                        center, 
                                                        pos2i(hidx, vidx), 
                                                        inputraw,
                                                        detection_en)
                pd = pickle.dumps({'newimg': {'max'    : max_val,
                                              'min'    : min_val,
                                              'min_thd': min_thd,
                                              'max_thd': max_thd}})
                self.new_img_indicator.write(pd)
            except:
                self.detresult = []
                print "Error in detector ", 
                print traceback.format_exc()
            print 'done'

            self.save_jpg(ir_filename, date, floatimg)
            self.save_indexed_jpg(floatimg, hidx, vidx)
            self.save_npy(ir_filename, date, inputraw)

        except:
            print "Error in _capturedetect ", sys.exc_info()

    @staticmethod
    def filloutline(xcellid, ycellid, img):
        img[ycellid, xcellid] = [0, 0, 255]
        return img

    @staticmethod
    def _display(img):
        """
        :type img: numpy.ndarray
        """
        small_img = cv2.resize(img, (320, 240))
        cv2.imshow("IR Image", small_img)
        cv2.waitKey(1)
        
    def save_jpg(self, filename, date, irfile):
        """
        :type filename:str
        :type date: str
        :type irfile: numpy.ndarray
        """    
        try:
            path = os.path.join(
                self.cfg.dataPath, 'IRImage', date, 'cap_%s.jpg' % filename)
            img = np.ceil(irfile*255)
            cv2.imwrite(path, img, self.quality)
        except Exception as e:
            self.log.error("Error saving IR image %s" % e.message)

    def save_npy(self, filename, date, npa):
        try:
            if npa is not None:
                path = os.path.join(
                    self.cfg.dataPath, 'IRImage', date, 'cap_%s.npy' % filename)
                np.save(path, npa)
        except Exception as e:
            self.log.error(e.message)

    def save_indexed_jpg(self, img, hidx, vidx):
        """
        :type img: numpy.ndarray
        :type hidx: int
        :type vidx: int
        """
        fullpath = os.path.join(parentPath, 'indexed thermal image', 
                                'IM%03d%03d.jpg' % (hidx, vidx))   # IM005003
        try:
            img = np.ceil(img*255)
            cv2.imwrite(fullpath, img, self.quality)
        except Exception as e:
            print "Error in save indexed thermal image", e.message


    #def _saveEventData(self, filename, img):
    #    fullpath = os.path.join(self.cfg.dataPath, 'IREvent', self.ir_folder,
    #                            'cap_%s_%s.jpg' % (filename, 'Fire'))
    #    try:
    #        img8 = np.ceil(img*255)
    #        cv2.imwrite(fullpath, img8, self.quality)
    #    except Exception as e:
    #        self.log.error("Error saving Event image %s" % e.message)
    #
    #def _saveEventRAW(self, filename, raw_data):
    #    """
    #    :type filename: str
    #    :type raw_data: numpy.array
    #    """
    #    try:
    #        full_path = os.path.join(self.cfg.dataPath, 'IREvent', self.ir_folder, 
    #                                 'cap_%s.txt' % filename)
    #        f = open(full_path, 'wb')
    #        data = raw_data.reshape(raw_data.shape[0]*raw_data.shape[1])
    #        bin1 = [int(b) for b in data]
    #        pkg = pack('<%sH' % len(bin1), *bin1)
    #        f.write(pkg)
    #        f.close()
    #    except Exception as e:
    #        self.log.error("Error saving Event binary %s" % e.message)
        
    def maskCmdFromUI(self, cmd):
        return self.detector.modifyMask(cmd)

    def modifyDistance(self, cmd):
        """
        :type cmd:dict
        :rtype:dict
        """
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
                return cmd
            except Exception as e:
                self.log.error("Exception %s" % e.message)
                print traceback.print_exc()
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
                self.log.error("set distance %s" % e.message)
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
                self.log.error("Exception in get origin distance %s" % e.message)
                cmd.update({'status': 'ERR', 'msg': e.message})
                return cmd

    @staticmethod
    def watchdog():
        return {'status': 'OK'}
    
    def addEvent(self, event):
        pass  # self.detector.addEventPoints(event)
        
    def getSize(self):
        width = self.IRCamera.getWidth()
        height = self.IRCamera.getHeight()
        return width, height

    def getResult(self):
        """        
        :rtype: list
        """
        return self.detresult

    def getImageStr(self):
        """        
        :rtype: str
        """
        try:
            img_str = cv2.imencode('.jpg', self.img, self.quality)[1].tostring()
            return img_str
        except:
            print 'Error in getImageStr ', sys.exc_info()
            
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


if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == 'console-redirect':
                cp = custom_print.CustomPrint(4048)
                sys.stdout = cp
        IRwipper = zerorpc.Server(IRConnector(), heartbeat=10)
        IRwipper.bind("tcp://0.0.0.0:4030")
        IRwipper.run()
    except KeyboardInterrupt:
        print 'Service terminated'
    except:
        print traceback.format()
