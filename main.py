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

class insight_thermal_analyzer(object):

    def correct_temp(self, ir_reading):
        strchr = self.dll.GetCorrectedTemp
        strchr.restype = c_float
        return self.dll.GetCorrectedTemp(byref(self.pfloat_lut), 
                                    self.corrPara, int(ir_reading))

    def __init__(self,width,height,ip,port):
        self.rgb_width = 1920
        self.rgb_height = 1080
        self.scr_width = 1800
        self.scr_height = 900
        self.init_cam_vari(width,height,ip,port)
        self.load_app_settings()
        self.fid = open('sharedmem.dat', "r+")
        self.map = mmap.mmap(self.fid.fileno(), 0)
        cv2.namedWindow('', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        self.disp_buff = np.empty((self.scr_height, self.scr_width, 3), dtype=np.uint8)
        cv2.imshow('', self.disp_buff)
        cv2.resizeWindow('', (self.scr_width,self.scr_height))
        self.hour_dir = ''

    def init_cam_vari(self,width,height,ip,port):
        self.width = width
        self.height = height
        self.npix = width * height
        self.ip = ip
        self.port = port
        self.windowName = 'show'
        dll_path = opjoin('dll', 'ThermalCamDll.dll')
        self.dll = windll.LoadLibrary(dll_path)
        self.mHandle = wintypes.HANDLE()
        self.keepAlive = c_uint()
        self.camData = td.IRF_IR_CAM_DATA_T()
        self.ushort_ptr = (c_ushort *(self.width * self.height ))()
        self.camData.ir_image = cast(self.ushort_ptr, POINTER(c_ushort))
        self.camData.image_buffer_size = self.width * self.height
        self.lpsize = (c_byte*8192)()
        self.camData.lpNextData = cast(self.lpsize, POINTER(c_byte))
        self.camData.dwSize = 0
        self.camData.dwPosition = 0
        self.corrPara = td.IRF_TEMP_CORRECTION_PAR_T()
        self.corrPara.atmTemp = 25.0
        self.corrPara.atmTrans = 1.0
        self.corrPara.emissivity = 1.0
        self.pfloat_lut = (c_float*65536)()

    def load_app_settings(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.thd = 19000
        if os.path.exists('thd.cfg'):
            try:
                fid=open('thd.cfg','r')
                self.thd = int(fid.read())
                fid.close()
            except:
                pass
        if os.path.exists('emissivity.cfg'):
            try:
                fid=open('emissivity.cfg','r')
                self.corrPara.emissivity = float(fid.read())
                fid.close()
            except Exception as e:
                print e.message
        fid = open(r'TempMapTable_L.bin','rb')
        x = fid.read()
        nfloat = len(x)/4
        fid.close()
        self.temp_lut = struct.unpack('f'*nfloat, x)
        for n in range(0, 65535):
            self.pfloat_lut[n] = self.temp_lut[n]

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
        print("Connecting  ", self.ip, self.port)
        self.dll.OpenConnect.restype = c_short
        err = -1
        val = self.dll.OpenConnect(byref(self.mHandle), byref(self.keepAlive), 
                            self.ip, self.port, 2, 1)
        if val != 1:
            print("Could not connect thermal camera")
            return
        self.requestCameraData()
        self.setSize()
        self.setNUC()
        while (self.mHandle != -1):
            self.processing()

    def get_raw_image(self):
        val = self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
        if val != 1:
            print("Get IR Images fail errcode=%d"%(val))
            return
        self.np_img_16 = np.ndarray(buffer=(c_uint16 * self.npix).from_address(addressof(self.ushort_ptr)), 
                        dtype=np.uint16,
                        shape=(self.height, self.width))

    def thresholding(self):
        b_img = self.np_img_16.copy()
        b_img[b_img <= self.thd] = 0
        b_img[b_img > self.thd] = 255
        b_img = b_img.astype(np.uint8)
        kern = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
        b_img = cv2.dilate(b_img, kern)
        contours,_ = cv2.findContours(b_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours
        
    def draw_contours(self, img8, img16, contours):
        for n,_ in enumerate(contours):
            mask = np.zeros(img8.shape[0:2], dtype=np.uint8)
            cv2.fillPoly(mask, pts=contours[n:n+1], color=(1))
            mmax = (img16*mask).max()
            max_t = self.correct_temp(mmax)
            pt = contours[n]
            x = []
            y = []
            for m in range(len(pt)):
                x.append(pt[m][0][0])
                y.append(pt[m][0][1])
            lb_xpos = np.array(x).max()
            lb_ypos = np.array(y).max()
            cv2.rectangle(img8, (lb_xpos, lb_ypos-12), (lb_xpos+35, lb_ypos+1), 
                                                (128,128,128), cv2.FILLED)
            cv2.putText(img8, '%.1f'%max_t, (lb_xpos,lb_ypos), self.font,
                        0.5, (255,255,255), 1, cv2.LINE_AA)

    def processing(self):
        '''GetIRImages(HANDLE handle, UINT *pTimerID, IRF_IR_CAM_DATA_T* cam_data)'''
        test = False
        if not test:
            self.get_raw_image()
        else:
            self.np_img_16 = cv2.imread('ir_test_02.jpg',0).astype(np.uint16)
            self.np_img_16 = self.np_img_16 * 200

        contours = self.thresholding()

        np_img_float = self.np_img_16.astype(np.float)
        np_img_float = np_img_float - np_img_float.min()
        np_img_float = 255 * np_img_float / np_img_float.max()
        im_8 = np_img_float.astype(np.uint8)
        
        alarm = False
        im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_JET)
        cv2.drawContours(im_8, contours, -1, (255,255,255))
        if len(contours) > 0:
            alarm = True
        self.draw_contours(im_8, self.np_img_16, contours)

        im_8 = cv2.resize(im_8, (self.scr_width/2,self.scr_height), 
                                    interpolation=cv2.INTER_NEAREST)
        cv2.rectangle(im_8, (10, 10), (440, 40), (128,128,128), cv2.FILLED)
        cv2.putText(im_8, 'THD(+/-) %.2f  Emissivity(w/s)%.2f MAX %.2f'%(
                    self.correct_temp(self.thd), 
                    self.corrPara.emissivity,
                    self.correct_temp(self.np_img_16.max())), 
                    (15, 30), self.font, 0.5, (255,255,255), 1, cv2.LINE_AA)
        npix = self.rgb_width * self.rgb_height * 3
        rgb = np.frombuffer(self.map[0:npix], dtype=np.uint8)
        rgb = rgb.reshape((self.rgb_height,self.rgb_width,3))
        rgb = cv2.resize(rgb, (self.scr_width/2, self.scr_height), 
                                    interpolation=cv2.INTER_NEAREST)

        self.disp_buff[:,0:self.scr_width/2,:]= im_8
        self.disp_buff[:,self.scr_width/2:,:] = rgb

        if True:
            hdd = psutil.disk_usage('/')
            space_megabytes = hdd.free/(1024*1024)
            print space_megabytes
            if space_megabytes < 1000:
                cv2.putText(self.disp_buff, 'Storage is full',
                    (15, 100), self.font, 1, (0,255,255), 2, cv2.LINE_AA)
            else:
                ts_str = datetime.now().strftime("%y%m%d-%H%M%S-%f")
                ts_str = ts_str[:-3]
                t0=time.time()
                if alarm:
                    dir = 'alarm'
                else:
                    dir = 'record'
                hour_dir = ts_str[0:9]
                if hour_dir != self.hour_dir:
                    self.hour_dir = hour_dir
                    try:
                        os.mkdir(opjoin(dir, hour_dir))
                    except:
                        pass
                cv2.imwrite(opjoin(dir, hour_dir, ts_str+'.jpg'), self.disp_buff)
                #print int(1000*(time.time()-t0))
        cv2.imshow('', self.disp_buff)
        key = cv2.waitKey(100)
        if key & 0xff == ord('+'):
            self.thd += 10
            self.save_thd()
        elif key & 0xff == ord('-'):
            self.thd -= 10
            self.save_thd()
        elif key & 0xff == ord('w'):
            self.corrPara.emissivity += 0.01
            self.save_emissivity()
        elif key & 0xff == ord('s'):
            self.corrPara.emissivity -= 0.01
            self.save_emissivity()
        elif key & 0xff == ord('q'):
            pass

    def save_emissivity(self):
        fid=open('emissivity.cfg','w')
        fid.write('%.2f'%self.corrPara.emissivity)
        fid.close()

    def save_thd(self):
        fid=open('thd.cfg','w')
        fid.write('%d'%self.thd)
        fid.close()

    def requestCameraData(self):
        self.dll.SendCameraMessage.restype = c_short
        self.dll.SendCameraMessage.argtypes = [wintypes.HANDLE, POINTER(c_uint), 
                                                        c_int,c_ushort,c_ushort]
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
    
    def setSize(self):
        self.dll.GetIRImages.restypes = c_short
        self.dll.GetIRImages.argtypes = [wintypes.HANDLE, POINTER(c_uint), 
                                            POINTER(td.IRF_IR_CAM_DATA_T)]
        try:
            err = self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
            if err == 1:
                if self.camData.save_data.sensor == 0:
                    if self.camData.save_data.tv == 0:
                        self.width = 320
                        self.height = 240
                    else:
                        self.width = 384
                        self.height = 288
                else:
                    if self.camData.save_data.tv == 0:
                        self.width = 640
                        self.height = 480
                    else:
                        self.width = 640
                        self.height = 480
                print("COX width = %d Cox height = %d"%(self.width, self.height))
            else:
                print("set size errcode = %d "%(err))
        except Exception as e:
            print("Exception in set size",e.message)
        
        return err

    
    def getRAW(self):
        IRData = np.ndarray(buffer=(c_uint16 * self.width * self.height).from_address(addressof(self.irimage)), dtype=np.uint16,shape=(self.height,self.width))
        return IRData
    
    def setNUC(self):
        self.dll.SendMessageToCamera.restype = c_short
        self.dll.SendMessageToCamera.argtypes = [wintypes.HANDLE, POINTER(c_uint), 
                                    c_int,c_ushort,c_ushort,c_ulong,c_ulong,c_ulong]
        try:
            err = self.dll.SendMessageToCamera(self.mHandle, byref(self.keepAlive),
                                                  td.IRF_MESSAGE_TYPE_T._IRF_SET_CAM_DATA.value,
                                                  td.CAMMAND_CODE.CMD_NUC.value, 7, 0, 0, 0)
            if err == 1:
                pass
            else:
                print("Set NUC message fail errcode=%d"%(err))
        except Exception as e:
            print("Exception in Set NUC message",e.message)        
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
    password = "12345"
    ipcam.vis_init(ipaddr, ipport, userName, password)
    ipcam.login()
    while True:
        time.sleep(10)

if __name__ == '__main__':
    fid = open("sharedmem.dat", "wb")
    buf = bytearray(1920*1080*3)
    fid.write(buf)
    fid.close()
    dirlist = ['record','alarm']
    for d in dirlist:
       try:
           os.mkdir(d)
       except:
           pass
    rgb_proc = mp.Process(target=rgb_capture_process, args=("192.168.1.119",))
    rgb_proc.start()

    cox = insight_thermal_analyzer(384, 288, "192.168.88.253", "15001")
    cox.connect()
