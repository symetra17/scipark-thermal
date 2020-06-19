import types_define as td
import mmap
from ctypes import *
import os
from os.path import join as opjoin
import numpy as np
import os
import sys
import time
import pdb
import cv2
from datetime import datetime
import pickle
import threading
import struct
import hikvision
import multiprocessing as mp
import psutil
import collections
import random
import reference_pair as rp
import sound_process
import gui_process_for_adjustment as gproc
import sensor_process as senproc
from numpy import uint8,uint16
import glob
import cleanup

# Recording extension header and tail number of frame
# when an overtemperature event occur, a few seconds of record ahead of the 
# event would be saved, after the event, a few seconds of record folowing
# the event would also be saved.
RECORD_EXTEND_T = 20   
RGB_IP = "192.168.88.249" # "127.0.0.1" 
THERMAL_IP = "192.168.88.253"
NMAP_FILE = "sharedmem.dat"
RGB_SHAPE = (1080,1920,3)
RGB_NPIX = RGB_SHAPE[0] * RGB_SHAPE[1] * RGB_SHAPE[2]
SCR_WIDTH = 1900
SCR_HEIGHT = 900
COX_MODEL = 'CG'
COLOR_STYLE ='BW'
NO_HARDWARE_TEST = False


buf_q = collections.deque(maxlen=RECORD_EXTEND_T)

if COX_MODEL=='CG':
    THERMAL_WIDTH = 640
    THERMAL_HEIGHT = 480
else:
    THERMAL_WIDTH = 384
    THERMAL_HEIGHT = 288


class insight_thermal_analyzer(object):

    def __init__(self, ip, port, action_q, sen_q):

        print('Loading Thermal camera library')
        dll_path = opjoin('dll', 'CG_ThermalCamDll_2018.dll')
        try:
            self.dll = windll.LoadLibrary(dll_path)
        except:
            print('Could not load Thermal camera DLL.')
            quit()
        print('Completed')
        self.dll.GetCorrectedTemp.restype = c_float

        self.init_cam_vari(ip,port)
        self.fid = open(NMAP_FILE, "r+")
        self.map = mmap.mmap(self.fid.fileno(), 0)
        self.title = 'Hong KONG Science and Technology Park Visitors Fever Monitoring System'
        cv2.namedWindow(self.title, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.namedWindow('RGB', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        buf = np.empty((480, 640, 3), dtype=uint8)
        cv2.imshow(self.title, buf)
        cv2.imshow('RGB', buf)
        cv2.resizeWindow(self.title, (800, 600))
        cv2.resizeWindow('RGB', (800,600))
        self.crop_width=1320
        self.crop_height=990
        self.hour_dir = ''
        self.record_counter = 0
        self.scr_buff = np.empty((SCR_HEIGHT, SCR_WIDTH, 3), dtype=uint8)   # preallocate this array to speed up
        self.action_q = action_q
        #self.sen_q = sen_q
        #self.rgb_buf = np.zeros(RGB_SHAPE, dtype=np.uint8)
        self.src_rgb = np.zeros((SCR_HEIGHT,SCR_WIDTH//2,3),dtype=uint8)
        self.ref_pair = rp.reference_pair()
        try:
            self.mask_bw = np.load('mask.npy')
        except:
            self.mask_bw = 255 * np.ones((32,40), dtype=uint8)
            np.save('mask', self.mask_bw)
        self.mask_color = np.ones((self.mask_bw.shape[0],self.mask_bw.shape[1],3),
                            dtype=uint8)
        self.mask_color[:,:,0] = (np.invert(self.mask_bw)/255)*0
        self.mask_color[:,:,1] = (np.invert(self.mask_bw)/255)*69
        self.mask_color[:,:,2] = (np.invert(self.mask_bw)/255)*255
        self.free_space_cnt=0

    def init_cam_vari(self,ip,port):
        self.npix = THERMAL_WIDTH * THERMAL_HEIGHT
        self.ip = ip
        self.port = port
        self.mHandle = wintypes.HANDLE()
        self.keepAlive = c_uint()
        self.camData = td.IRF_IR_CAM_DATA_T()
        self.m16 = np.zeros((THERMAL_HEIGHT,THERMAL_WIDTH), dtype=uint16)
        self.acm32 = np.zeros((THERMAL_HEIGHT,THERMAL_WIDTH), dtype=np.uint32)
        self.camData.ir_image = self.m16.ctypes.data_as(POINTER(c_ushort))
        self.camData.image_buffer_size = 4 * THERMAL_WIDTH * THERMAL_HEIGHT
        self.lpsize = (c_byte*8192)()
        self.camData.lpNextData = cast(self.lpsize, POINTER(c_byte))
        self.camData.dwSize = 0
        self.camData.dwPosition = 0
        self.pfloat_lut = (c_float*65536)()
        self.dll.SendCameraMessage.restype = c_short
        self.dll.SendCameraMessage.argtypes = [wintypes.HANDLE, 
                                                POINTER(c_uint), 
                                                c_int,
                                                c_ushort,
                                                c_ushort]
    
    def load_offset_of_camera(self):
        fname_x='camera_offset_x.cfg'
        fname_y='camera_offset_y.cfg'
        if os.path.exists(fname_x):
            try:
                fid=open(fname_x,'r')
                self.offset_x=int(fid.read())
                #print("cfg_x: ",self.offset_x)
                fid.close()
            except:
                pass
        if os.path.exists(fname_y):
            try:
                fid=open(fname_y,'r')
                self.offset_y=int(fid.read())
                #print("cfg_y: ",self.offset_y)
                fid.close()
            except:
                pass

    def disconnect(self):
        if self.mHandle.value != None:
            self.dll.CloseConnect.restype = c_short
            self.dll.CloseConnect.argtypes = [POINTER(wintypes.HANDLE), c_uint]
            try:
                err = self.dll.CloseConnect(byref(self.mHandle), self.keepAlive)
                if err == 1:
                    return err
            except Exception as e:
                print("Exception in close connection ", e.message)
        return None
    
        
    def connect(self):
        print("Connecting",COX_MODEL, self.ip, self.port)
        self.dll.OpenConnect.restype = c_short
        self.dll.CloseConnect.restype = c_short
        err = -1

        #self.dll.OpenConnect.argtypes = [POINTER(wintypes.HANDLE), 
        #                                POINTER(wintypes.UINT),
        #                                wintypes.LPCSTR,
        #                                wintypes.LPCSTR,
        #                                c_int, c_int]

        val = self.dll.OpenConnect(byref(self.mHandle), 
                            byref(self.keepAlive), 
                            str.encode(self.ip), 
                            str.encode(self.port),
                            2, 1)
        if val != 1:
            print("Could not connect thermal camera",val)
            return
        self.requestCameraData()
        # Function GetIRImages got to be called twice before it would not return error code
        self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
        self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
        while (self.mHandle != -1):
            try:
                self.processing()
            except Exception as e:
                print(e)
                print("Thermal ccamera comm reset required", str(datetime.now()))
                break

    def get_raw_image(self):
        NAVG = 2
        self.acm32.fill(0)
        for p in range(NAVG):
            val = self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
            if val == -100:
                return -1
            elif val != 1:
                raise Exception("Get IR Images fail errcode=%d"%(val))
            self.acm32 += self.m16
        self.acm32 = self.acm32//NAVG
        self.np_img_16 = self.acm32.astype(uint16)

    def processing(self):
        self.load_offset_of_camera()
        if not self.action_q.empty():
            action = self.action_q.get()
            if action=='offset_x_+':
                self.offset_x+=1
                print("x+")
            elif action=='offset_x_-':
                self.offset_x-=1
                print("x-")
            elif action=='offset_y_+':
                self.offset_y += 1
                print("y+")
            elif action=='offset_y_-':
                self.offset_y -= 1
                print("y-")
            elif action=='offset_x_+_10':
                self.offset_x+=10
            elif action=='offset_x_-_10':
                self.offset_x-=10
            elif action=='offset_y_+_10':
                self.offset_y+=10
            elif action=='offset_y_-_10':
                self.offset_y-=10

        if not NO_HARDWARE_TEST:
            self.get_raw_image()
        else:
            self.np_img_16 = cv2.imread('ir_test_02.jpg',0).astype(uint16)
            self.np_img_16 = self.np_img_16 * 200
            self.np_img_16[160,120] = random.randint(16000, 18000)
            time.sleep(0.03)

        self.ref_pair.update(self.np_img_16)        
        f_img = self.np_img_16.astype(np.float)
        fmin = np.percentile(f_img, 0.1)
        fmax = np.percentile(f_img, 99.9)+50
        f_img = np.interp(f_img, [fmin,fmax],[0.0,255.0])
        im_8 = f_img.astype(uint8)
        if COLOR_STYLE=='BW':
            im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_BONE)
        else:
            im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_JET)

        im_8 = cv2.resize(im_8, (SCR_WIDTH//2,SCR_HEIGHT), interpolation=0)        

        rgb = np.frombuffer(self.map[0:RGB_NPIX], dtype=uint8)
        rgb = rgb.reshape(RGB_SHAPE)
        rgb_full=rgb.copy()
        cropwidth=self.crop_width #original:1920
        cropheight=self.crop_height #original:1080
        self.originalwidth=rgb_full.shape[1]
        self.originalheight=rgb_full.shape[0]
        try: 
            if (((self.originalwidth-cropwidth)//2+self.offset_x<0) or (self.originalwidth-(self.originalwidth-cropwidth)//2+self.offset_x)>self.originalwidth):
                raise Exception
            self.save_camera_offset_x()
        except:
            print("offset x is out of bound!!")
            self.offset_x=13
            self.save_camera_offset_x()

        try:
            if (((self.originalheight-cropheight)//2+self.offset_y<0) or ((self.originalheight-(self.originalheight-cropheight)//2+self.offset_y)>self.originalheight)):
                raise Exception
            self.save_camera_offset_y()
        except:
            print("offset y is out of boud!!")
            self.offset_y=0
            self.save_camera_offset_y()
        offset_x=self.offset_x
        offset_y=self.offset_y
        rgb_copy=rgb_full.copy()
        rgb_full=rgb_copy[(self.originalheight-cropheight)//2+offset_y:self.originalheight-(self.originalheight-cropheight)//2+offset_y,(self.originalwidth-cropwidth)//2+offset_x:self.originalwidth-(self.originalwidth-cropwidth)//2+offset_x,0:3]
        cv2.line(rgb_full,(0,rgb_full.shape[0]//2),(rgb_full.shape[1],rgb_full.shape[0]//2),(0,255,255),1)
        cv2.line(rgb_full,(rgb_full.shape[1]//2,0),(rgb_full.shape[1]//2,rgb_full.shape[0]),(0,255,255),1)
        cv2.resize(rgb, (SCR_WIDTH//2, SCR_HEIGHT), self.src_rgb, 
                                            interpolation=0)
        cv2.line(im_8,(0,im_8.shape[0]//2),(im_8.shape[1],im_8.shape[0]//2),(0,255,255),1)
        cv2.line(im_8,(im_8.shape[1]//2,0),(im_8.shape[1]//2,im_8.shape[0]),(0,255,255),1)
        cv2.imshow(self.title,im_8)
        
        cv2.imshow('RGB', rgb_full)
        key = cv2.waitKey(5)
        return 0

    def save_camera_offset_x(self):
        fid=open('camera_offset_x.cfg','w')
        fid.write('%d'%self.offset_x)
        fid.close()

    def save_camera_offset_y(self):
        fid=open('camera_offset_y.cfg','w')
        fid.write('%d'%self.offset_y)
        fid.close()
    
    def requestCameraData(self):
        err = self.dll.SendCameraMessage(self.mHandle, byref(self.keepAlive),
                                td.IRF_MESSAGE_TYPE_T._IRF_REQ_CAM_DATA.value,0,0)
        if err != 1:
            print("send request all cam data message fail errcode =%d "%(err))
            return
        #request stream on_IRF_STREAM_ON
        err = self.dll.SendCameraMessage(self.mHandle, byref(self.keepAlive),
                                td.IRF_MESSAGE_TYPE_T._IRF_STREAM_ON.value,0,0)
        if err != 1:
            print("send stream on message fail errcode=%d"%(err))
        return err
    
    def saveIRimage(self,Img):
        currenttime = datetime.now().strftime("%Y_%m_%d_%H.%M.%S.%f")
        fullpath = '%s/cap_%s.jpg' % ('IRImage', currenttime)
        Img = np.ceil(Img*255)
        cv2.imwrite(fullpath, Img, [cv2.IMWRITE_JPEG_QUALITY, 90])

def rgb_capture_process(ipaddr):
    ipcam = hikvision.HikVision()
    ipport = "8000"
    userName = "admin"
    password = "insight108!"
    ipcam.vis_init(ipaddr, ipport, userName, password)
    ipcam.login()
    while True:
        time.sleep(10)

def saving_image_process(st_q):
    while True:
        a,b = st_q.get()
        # free space check
        hdd = psutil.disk_usage('/')
        space_mb = hdd.free//(1024*1024)
        if space_mb > 1000:
            cv2.imwrite(a,b)
        time.sleep(0.05)

def thermal_process(acn_q, sns_q):
    cox = insight_thermal_analyzer(THERMAL_IP, "15001",acn_q, sns_q)
    if NO_HARDWARE_TEST:
        while True:
            try:
                cox.processing()
            except Exception as e:
                print(e)
                print("Thermal camera comm reset required", str(datetime.now()))
                break
    else:
        cox.connect()

if __name__ == '__main__':
    fid = open(NMAP_FILE, "wb")
    buf = bytearray(RGB_NPIX)
    fid.write(buf)
    fid.close()
    try:
        os.mkdir('record')
    except:
        pass

    if True:
        clean_proc = mp.Process(target=cleanup.cleanup, args=(0,))
        clean_proc.daemon = True
        clean_proc.start()
        
        rgb_proc = mp.Process(target=rgb_capture_process, args=(RGB_IP,))
        rgb_proc.daemon = True
        rgb_proc.start()

        action_q = mp.Queue(2)
        guip = mp.Process(target=gproc.gui_process, args=(action_q,))
        guip.daemon = True
        guip.start()

    sensor_que = mp.Queue(2)
    sensor_p = mp.Process(target=senproc.sensor_proc, args=(sensor_que,))
    sensor_p.daemon = True
    sensor_p.start()

    while True:
        tp = mp.Process(target=thermal_process, args=(action_q,sensor_que,))
        tp.daemon = True
        tp.start()
        tp.join()
        time.sleep(5)
