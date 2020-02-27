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
import wave
import scipy.io.wavfile
import sounddevice as sd
import tkinter as tk
# Recording extension header and tail number of frame
# when an overtemperature event occur, a few seconds of record ahead of the 
# event would be saved, after the event, a few seconds of record folowing
# the event would also be saved.
RECORD_EXTEND_T = 20   
AUDIO_FILE = 'doodoo.wav'      # sample rate 16KHz
RGB_IP = "192.168.88.249"
THERMAL_IP = "192.168.88.253"
NMAP_FILE = "sharedmem.dat"
RGB_SHAPE = (1080,1920,3)
RGB_NPIX = RGB_SHAPE[0] * RGB_SHAPE[1] * RGB_SHAPE[2]
SCR_WIDTH = 1900
SCR_HEIGHT = 900
COX_MODEL = 'CG'
COLOR_STYLE=='BW'

storage_q = mp.Queue(2*RECORD_EXTEND_T+10)
buf_q = collections.deque(maxlen=RECORD_EXTEND_T)
sound_q = mp.Queue(1)

if COX_MODEL=='CG':
    THERMAL_WIDTH = 640
    THERMAL_HEIGHT = 480
else:
    THERMAL_WIDTH = 384
    THERMAL_HEIGHT = 288

def sound_process(snd_q):
    a, audio_array = scipy.io.wavfile.read(AUDIO_FILE)
    while True:
        snd_q.get()
        sd.play(audio_array, 16000)
        sd.wait()

class insight_thermal_analyzer(object):

    def correct_temp(self, ir_reading):
        if COX_MODEL=='CG':
            strchr = self.dll.ConvertRawToTempCG
            strchr.restype = c_float
            res = self.dll.ConvertRawToTempCG(byref(self.camData.ir_image), self.corrPara, int(ir_reading))
            return res
        else:
            #return 0.321
            # this function requires different number of input arguments in 2018 and 2015 dll
            # GetCorrectedTemp
            strchr = self.dll_2015.GetCorrectedTemp
            strchr.restype = c_float
            return self.dll_2015.GetCorrectedTemp(byref(self.pfloat_lut), 
                                        self.corrPara, int(ir_reading))


    def __init__(self, ip, port, sn_q, sto_q, action_q):

        self.init_cam_vari(ip,port)
        self.load_app_settings()
        self.fid = open(NMAP_FILE, "r+")
        self.map = mmap.mmap(self.fid.fileno(), 0)
        self.title = 'Hong KONG Science and Technology Park Visitors Fever Monitoring System'
        cv2.namedWindow(self.title, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        buf = np.empty((SCR_HEIGHT, SCR_WIDTH, 3), dtype=np.uint8)
        cv2.imshow(self.title, buf)
        cv2.resizeWindow('', (SCR_WIDTH,SCR_HEIGHT))
        self.hour_dir = ''
        self.alarm = 0
        self.sound_q = sn_q
        self.storage_q = sto_q
        self.logo = cv2.imread('logo.png')
        self.scr_buff = np.empty((SCR_HEIGHT, SCR_WIDTH, 3), dtype=np.uint8)   # preallocate this array to speed up
        self.action_q = action_q

    def init_cam_vari(self,ip,port):
        self.npix = THERMAL_WIDTH * THERMAL_HEIGHT
        self.ip = ip
        self.port = port
        dll_path = opjoin('dll', 'CG_ThermalCamDll_2018.dll')    
        self.dll = windll.LoadLibrary(dll_path)
        self.dll_2015 = windll.LoadLibrary(opjoin('dll', 'ThermalCamDll_2015.dll'))
        self.mHandle = wintypes.HANDLE()
        self.keepAlive = c_uint()
        self.camData = td.IRF_IR_CAM_DATA_T()
        self.ushort_ptr = (c_ushort *(THERMAL_WIDTH * THERMAL_HEIGHT ))()
        self.camData.ir_image = cast(self.ushort_ptr, POINTER(c_ushort))
        self.camData.image_buffer_size = 4 * THERMAL_WIDTH * THERMAL_HEIGHT
        self.lpsize = (c_byte*8192)()
        self.camData.lpNextData = cast(self.lpsize, POINTER(c_byte))
        self.camData.dwSize = 0
        self.camData.dwPosition = 0
        if COX_MODEL=='CG':
            self.corrPara = td.IRF_TEMP_CORRECTION_PAR_T_CG()
        else:
            self.corrPara = td.IRF_TEMP_CORRECTION_PAR_T()
        self.corrPara.atmTemp = 25.0
        self.corrPara.atmTrans = 1.0
        self.corrPara.emissivity = 1.0
        self.pfloat_lut = (c_float*65536)()
        self.dll.SendCameraMessage.restype = c_short
        self.dll.SendCameraMessage.argtypes = [wintypes.HANDLE, 
                                                POINTER(c_uint), 
                                                c_int,
                                                c_ushort,
                                                c_ushort]

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
        print "Connecting  ", self.ip, self.port
        self.dll.OpenConnect.restype = c_short
        self.dll.CloseConnect.restype = c_short
        err = -1
        val = self.dll.OpenConnect(byref(self.mHandle), byref(self.keepAlive), 
                            self.ip, self.port, 2, 1)
        if val != 1:
            print("Could not connect thermal camera")
            return
        self.requestCameraData()
        self.setNUC()
        # Function GetIRImages got to be called twice before it would not return error code
        self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
        self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
        while (self.mHandle != -1):
            try:
                self.processing()
            except Exception as e:
                print e
                print "Thermal ccamera comm reset required", str(datetime.now())
                break

    def get_raw_image(self):
        NAVG = 2
        acm32 = np.zeros((THERMAL_HEIGHT,THERMAL_WIDTH), dtype=np.uint32)
        for p in range(NAVG):
            val = self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
            if val == -100:
                return -1
            elif val != 1:
                raise Exception("Get IR Images fail errcode=%d"%(val))
            im16 = np.ndarray(buffer=(c_uint16 * self.npix).from_address(addressof(self.ushort_ptr)), 
                        dtype=np.uint16,
                        shape=(THERMAL_HEIGHT, THERMAL_WIDTH))
            acm32 += im16
        acm32 = acm32/NAVG
        self.np_img_16 = acm32.astype(np.uint16)

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
            if lb_xpos > 350:
                lb_xpos = np.array(x).max() - 30
            lb_ypos = np.array(y).max()
            cv2.rectangle(img8, (lb_xpos, lb_ypos-12), (lb_xpos+35, lb_ypos+1), 
                                                (128,128,128), cv2.FILLED)
            cv2.putText(img8, '%.1f'%max_t, (lb_xpos,lb_ypos), self.font,
                        0.5, (255,255,255), 1, cv2.LINE_AA)

    def processing(self):
        if not self.action_q.empty():
            action = self.action_q.get()
            if action=='thd+':
                self.thd+=3
                self.save_thd()
            elif action=='thd-':
                self.thd-=3
                self.save_thd()
            elif action=='offset+':
                self.corrPara.emissivity += 0.01
                self.save_emissivity()
            elif action=='offset-':
                self.corrPara.emissivity -= 0.01
                self.save_emissivity()

        test = False
        if not test:
            self.get_raw_image()
        else:
            self.np_img_16 = cv2.imread('ir_test_02.jpg',0).astype(np.uint16)
            self.np_img_16 = self.np_img_16 * 200
        contours = self.thresholding()
        f_img = self.np_img_16.astype(np.float)
        t0 = time.time()
        fmin = np.percentile(f_img, 0.1)
        fmax = np.percentile(f_img, 99.9)+50
        f_img = np.interp(f_img, [fmin,fmax],[0.0,255.0])
        print int(1000*(time.time()-t0)),'ms'
        im_8 = f_img.astype(np.uint8)
        tmax = self.correct_temp(self.np_img_16.max())
        if COLOR_STYLE=='BW':
            im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_BONE)
            cv2.drawContours(im_8, contours, -1, (0,0,255), thickness=2)
        else:
            im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_JET)
            cv2.drawContours(im_8, contours, -1, (255,255,255), thickness=2)

        if len(contours) > 0:
            self.alarm = RECORD_EXTEND_T
            if tmax < 42.1:
                if not self.sound_q.full():
                    self.sound_q.put(0)

        self.draw_contours(im_8, self.np_img_16, contours)

        im_8 = cv2.resize(im_8, (SCR_WIDTH/2,SCR_HEIGHT), 
                                            interpolation=cv2.INTER_NEAREST)
        cv2.rectangle(im_8, (10, 10), (440, 40), (128,128,128), cv2.FILLED)
        cv2.putText(im_8, 'THD(+/-) %.2f  Emissivity(w/s)%.2f MAX %.2f'%(
                    self.correct_temp(self.thd), 
                    self.corrPara.emissivity,
                    tmax), 
                    (15, 30), self.font, 0.5, (255,255,255), 1, cv2.LINE_AA)

        rgb = np.frombuffer(self.map[0:RGB_NPIX], dtype=np.uint8)
        rgb = rgb.reshape(RGB_SHAPE)
        rgb = cv2.resize(rgb, (SCR_WIDTH/2, SCR_HEIGHT), 
                                            interpolation=cv2.INTER_NEAREST)

        self.scr_buff[:,0:SCR_WIDTH/2,:]= im_8
        self.scr_buff[:,SCR_WIDTH/2:,:] = rgb

        ts_str = datetime.now().strftime("%y%m%d-%H%M%S-%f")[:-3]
        fn = opjoin('record', ts_str + '.jpg')

        if self.alarm == 0:
            fn = opjoin('record', ts_str + '.jpg')
            buf_q.append([fn, self.scr_buff.copy()])
        else:
            if self.alarm == RECORD_EXTEND_T:
                for k in range(len(buf_q)):
                    if not self.storage_q.full():
                        self.storage_q.put(buf_q.pop())

            if not self.storage_q.full():
                self.storage_q.put([fn, self.scr_buff.copy()])

            self.alarm -= 1
            hdd = psutil.disk_usage('/')
            space_mb = hdd.free/(1024*1024)
            if space_mb < 1000:
                cv2.putText(self.scr_buff, 'Storage is full',
                    (15, 100), self.font, 1, (0,255,255), 2, cv2.LINE_AA)
        self.scr_buff[800:800+self.logo.shape[0], 1600:1600+self.logo.shape[1], :] /= 2
        self.scr_buff[800:800+self.logo.shape[0], 1600:1600+self.logo.shape[1], :] += self.logo/2
        cv2.imshow(self.title, self.scr_buff)
        key = cv2.waitKey(10)
        if key & 0xff == ord('+'):
            self.thd += 3
            self.save_thd()
        elif key & 0xff == ord('-'):
            self.thd -= 3
            self.save_thd()
        elif key & 0xff == ord('w'):
            self.corrPara.emissivity += 0.01
            self.save_emissivity()
        elif key & 0xff == ord('s'):
            self.corrPara.emissivity -= 0.01
            self.save_emissivity()
        elif key & 0xff == ord('q'):
            return -1

        return 0

    def save_emissivity(self):
        fid=open('emissivity.cfg','w')
        fid.write('%.2f'%self.corrPara.emissivity)
        fid.close()

    def save_thd(self):
        fid=open('thd.cfg','w')
        fid.write('%d'%self.thd)
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
    
    def getRAW(self):
        IRData = np.ndarray(buffer=(c_uint16 * THERMAL_WIDTH * THERMAL_HEIGHT).from_address(addressof(self.irimage)), dtype=np.uint16,shape=(THERMAL_HEIGHT,THERMAL_WIDTH))
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

def saving_image_process(st_q):
    while True:
        a,b = st_q.get()
        # free space check
        hdd = psutil.disk_usage('/')
        space_mb = hdd.free/(1024*1024)
        if space_mb > 1000:
            cv2.imwrite(a,b)
        time.sleep(0.05)

def thermal_process(sn_q, sto_q, acn_q):
    cox = insight_thermal_analyzer(THERMAL_IP, "15001", sn_q, sto_q, acn_q)
    cox.connect()

def gui_process(action_q):
    def thd_up():
        if not action_q.full():
            action_q.put('thd+')
    def thd_down():
        if not action_q.full():
            action_q.put('thd-')

    def thd2_up():
        if not action_q.full():
            action_q.put('thd2+')
    def thd2_down():
        if not action_q.full():
            action_q.put('thd2-')

    def offset_up():
        if not action_q.full():
            action_q.put('offset+')
    def offset_down():
        if not action_q.full():
            action_q.put('offset-')

    root=tk.Tk()
    root.wm_attributes("-topmost", 1)
    root.geometry("+970+950")
    root.overrideredirect(True) # removes title bar
    btns = []
    btns.append(tk.Button(root,text='THD+',command=thd_up))
    btns.append(tk.Button(root,text='THD-',command=thd_down))
    btns.append(tk.Button(root,text='THD2+',command=thd2_up))
    btns.append(tk.Button(root,text='THD2-',command=thd2_down))
    btns.append(tk.Button(root,text='OFFSET+',command=offset_up))
    btns.append(tk.Button(root,text='OFFSET-',command=offset_down))
    for item in btns:
        item.config(width=10)
    btns[0].grid(row = 0, column = 0, padx=10, pady=4)
    btns[1].grid(row = 1, column = 0, padx=10, pady=4)
    #btns[2].grid(row = 0, column = 1, padx=10, pady=4)
    #btns[3].grid(row = 1, column = 1, padx=10, pady=4)
    btns[4].grid(row = 0, column = 2, padx=10, pady=4)
    btns[5].grid(row = 1, column = 2, padx=10, pady=4)
    root.mainloop()

if __name__ == '__main__':
    fid = open(NMAP_FILE, "wb")
    buf = bytearray(RGB_NPIX)
    fid.write(buf)
    fid.close()
    try:
        os.mkdir('record')
    except:
        pass
    sav_proc = mp.Process(target=saving_image_process, args=(storage_q,))
    sav_proc.daemon = True
    sav_proc.start()

    rgb_proc = mp.Process(target=rgb_capture_process, args=(RGB_IP,))
    rgb_proc.daemon = True
    rgb_proc.start()

    sq = mp.Process(target=sound_process, args=(sound_q,))
    sq.daemon = True
    sq.start()

    action_q = mp.Queue(2)
    guip = mp.Process(target=gui_process, args=(action_q,))
    guip.daemon = True
    guip.start()

    while True:
        tp = mp.Process(target=thermal_process, args=(sound_q,storage_q,action_q,))
        tp.daemon = True
        tp.start()
        tp.join()
        time.sleep(5)
