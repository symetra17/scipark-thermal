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
import gui_process as gproc
import sensor_process as senproc
from numpy import uint8,uint16
import glob
import cleanup
import socket
import pickle
import tkinter as tk
import queue
from cv2 import cv2
import get_img_process as get_img_proc
import cfg
import face_processing
import logging
from logging.handlers import RotatingFileHandler

# Recording extension header and tail number of frame
# when an overtemperature event occur, a few seconds of record ahead of the 
# event would be saved, after the event, a few seconds of record folowing
# the event would also be saved.
RECORD_EXTEND_T = 20   
#RGB_IP = "192.168.88.249"
#THERMAL_IP = "192.168.88.253"
NMAP_FILE = "sharedmem.dat"
RGB_SHAPE = (1080,1920,3)
RGB_NPIX = RGB_SHAPE[0] * RGB_SHAPE[1] * RGB_SHAPE[2]
SCR_WIDTH = 1900
SCR_HEIGHT = 900
COX_MODEL = 'CG'
COLOR_STYLE ='BW'
NO_HARDWARE_TEST = False
yolo_host = '127.0.0.1'
yolo_port = 50000

storage_q = mp.Queue(2*RECORD_EXTEND_T+10)
buf_q = collections.deque(maxlen=RECORD_EXTEND_T)
sound_q = mp.Queue(1)

if COX_MODEL=='CG':
    THERMAL_WIDTH = 640
    THERMAL_HEIGHT = 480
else:
    THERMAL_WIDTH = 384
    THERMAL_HEIGHT = 288


class insight_thermal_analyzer(object):

    def correct_temp(self, ir_reading):
        if self.cfg_data.USE_BBODY:
            val=self.ref_pair.calibrate(ir_reading)
            return val
        else:
          if COX_MODEL=='CG':
            strchr = self.dll.ConvertRawToTempCG
            strchr.restype = c_float
            res = self.dll.ConvertRawToTempCG(byref(self.camData.ir_image), self.corrPara, int(ir_reading))
            return res
          else:
            #return 0.321
            # this function requires different number of input arguments in 2018 and 2015 dll
            # GetCorrectedTemp
            t_c = self.dll.GetCorrectedTemp(byref(self.pfloat_lut), 
                                        self.corrPara, int(ir_reading))
            
            return t_c

    def __init__(self, ip, port, sn_q, sto_q, action_q, sen_q, img_q,sock):
        print('Loading Thermal camera library')
        dll_path = opjoin('dll', 'CG_ThermalCamDll_2018.dll')
        try:
            self.dll = windll.LoadLibrary(dll_path)
        except:
            print('Could not load Thermal camera DLL.')
            quit()
        print('Completed')
        self.img_q=img_q
        self.dll.GetCorrectedTemp.restype = c_float
        self.init_cam_vari(ip,port)
        self.fid = open(NMAP_FILE, "r+")
        self.map = mmap.mmap(self.fid.fileno(), 0)
        self.width=1080
        self.height=810
        self.crop_width=1320
        self.crop_height=990
        self.load_app_settings()
        self.cfg_data=cfg.get_config()
        # buf = np.empty((480, 640, 3), dtype=uint8)
        self.hour_dir = ''
        self.record_counter = 0
        self.sound_q = sn_q
        self.storage_q = sto_q
        # self.logo = cv2.imread('logo.png')
        self.setting_logo  = cv2.imread('Setting-icon.png')
        self.split_logo =cv2.imread('quit-logo.png')
        self.scr_buff = np.empty((SCR_HEIGHT, SCR_WIDTH, 3), dtype=uint8)   # preallocate this array to speed up
        self.action_q = action_q
        self.sen_q = sen_q
        # self.src_rgb = np.zeros((SCR_HEIGHT,SCR_WIDTH//2,3),dtype=uint8)
        self.ref_pair = rp.reference_pair()
        self.ir_full=False
        try:
            self.mask_bw = np.load('mask.npy')
            # print(self.mask_bw)
        except:
            self.mask_bw = 255 * np.ones((32,40), dtype=uint8)
            np.save('mask', self.mask_bw)
        self.mask_color = np.ones((self.mask_bw.shape[0],self.mask_bw.shape[1],3),
                            dtype=uint8)
        self.mask_color[:,:,0] = (np.invert(self.mask_bw)/255)*0
        self.mask_color[:,:,1] = (np.invert(self.mask_bw)/255)*69
        self.mask_color[:,:,2] = (np.invert(self.mask_bw)/255)*255
        self.show_mask = False
        self.cursor = (50,50)
        self.cursor_textpos = (50,50)
        self.cursor_reading = 0
        self.sock = sock
        self.exit_all=False
        self.rgb_pop_up=False
        self.disp_q = queue.Queue(3)
        self.imshow_thread = threading.Thread(target=self.imshow_loop, args=(self.disp_q,self.storage_q,self.scr_buff ))
        self.imshow_thread.daemon=True
        self.imshow_thread.start()
        self.alert_timer=time.time()
        self.alert_counter=0
        self.no_mask_counter=0
        self.reconnected=True
        self.on_setting=False
        # import setting
        # self.setting_proc=mp.Process(target=setting.func1,args=(self.action_q,))
        # self.setting_proc.daemon=True
        FORMAT = '%(asctime)s %(levelname)s: %(message)s'
        path=opjoin('log','main.log')
        logging.basicConfig(level=logging.DEBUG,format=FORMAT,datefmt='%Y-%m-%d %H:%M',handlers=[RotatingFileHandler(path, maxBytes=2*1024*1024,backupCount=9)])


    def imshow_loop(self, disp_q, sto_q,scr_buff):
        title = 'Insightrobotics Fever Monitoring System'
        cv2.namedWindow(title, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow(title,SCR_WIDTH,SCR_HEIGHT)
        cv2.setMouseCallback(title, self.mouse_callback)
        logo = cv2.imread('logo.png')
        setting_logo  = cv2.imread('Setting-icon.png')
        split_logo =cv2.imread('Split-icon.png')
        fps_counter=0
        fps=0
        free_space_cnt=0
        weekdaydict={0:"MON",1:"TUE",2:"WED",3:"THU",4:"FRI",5:"SAT",6:"SUN"}
        font=self.font
        while True:
            if self.exit_all:
                    cv2.destroyAllWindows()
                    break
            else:
                if not disp_q.empty():
                    window_close_flag=cv2.getWindowProperty(title,0)
                    if window_close_flag==-1:
                        self.exit_all=True
                    if fps_counter==0:
                        starttime=time.time()
                    dis_list = disp_q.get()
                    img=dis_list[0]
                    im_8=dis_list[1]
                    ir_full=dis_list[2]
                    thd_cels=dis_list[3]
                    thd=dis_list[4]
                    emissivity=dis_list[5]
                    mouse_info=dis_list[6]
                    im_8 = cv2.resize(im_8, (SCR_WIDTH//2,SCR_HEIGHT), interpolation=0)
                    if self.cfg_data.USE_BBODY:
                        self.ref_pair.draw(im_8)

                    if self.show_mask:
                        try:
                            h = im_8.shape[0]
                            w = im_8.shape[1]
                            mask = cv2.resize(self.mask_color, (w,h), interpolation=0)
                            im_8 = im_8//2 + mask//2
                            cv2.putText(im_8, 'MASK EDITING', 
                                (15, 150), self.font, 0.5, (255,255,255), 1, cv2.LINE_AA)
                        except Exception as e:
                            print(e)
                    scr_buff[:,0:SCR_WIDTH//2,:]= im_8
                    reading=mouse_info['reading']
                    cursor_textpos=mouse_info['textpos']
                    x1 = cursor_textpos[0]-3
                    y1 = cursor_textpos[1]-15
                    x2 = cursor_textpos[0]+46
                    y2 = cursor_textpos[1]+5
                    if ir_full:
                        im_8_full=cv2.resize(im_8,(SCR_WIDTH,SCR_HEIGHT),interpolation=0)
                        scr_buff=im_8_full
                        cv2.rectangle(scr_buff, (x1,y1), (x2, y2), (50,50,50), cv2.FILLED)
                        cv2.putText(scr_buff, '%.2f'%reading, cursor_textpos,font, 0.5, (255,255,255), 1, cv2.LINE_AA)
                    else:
                        rgb_buf=cv2.resize(img,(SCR_WIDTH//2,SCR_HEIGHT),interpolation=0)
                        scr_buff[:,SCR_WIDTH//2:,:]=rgb_buf
                        if ((x2)<SCR_WIDTH//2):
                            cv2.rectangle(scr_buff, (x1,y1), (x2, y2), (50,50,50), cv2.FILLED)
                            cv2.putText(scr_buff, '%.2f'%reading, cursor_textpos,font, 0.5, (255,255,255), 1, cv2.LINE_AA)
                    
                    cv2.rectangle(scr_buff, (logo.shape[1], 0), (SCR_WIDTH-setting_logo.shape[1], 56), (84,68,52), cv2.FILLED)
                    cv2.putText(scr_buff,"AI-ASSISTED BODY TEMPERATURE SCREENING SYSTEM",(50+logo.shape[1],57//2+4),font,0.64,(60, 199, 165),1,cv2.LINE_AA)
                    date=datetime.now().strftime("%Y-%m-%d ")+weekdaydict[datetime.today().weekday()]
                    cv2.putText(scr_buff,date,(SCR_WIDTH//2+50,57//2+5),font,0.5,(255,255,255), 1, cv2.LINE_AA)
                    now_time=datetime.now().strftime(" %H:%M:%S")
                    cv2.putText(scr_buff,now_time,(SCR_WIDTH//2+190,57//2+6),font,0.85,(228,193,110), 1, cv2.LINE_AA)
                    cv2.putText(scr_buff, 'THD %.1f (%d) EMISIV(w/s)%.2f'%(
                                thd_cels, 
                                thd, 
                                emissivity), 
                                (SCR_WIDTH-setting_logo.shape[1]-500, 57//2+5), font, 0.5, (255,255,255), 1, cv2.LINE_AA)
                    cv2.putText(scr_buff,'FPS: %.1f '%fps,(0,logo.shape[0]+15),font,0.5,(255,255,255),1,cv2.LINE_AA)
                    scr_buff[0:logo.shape[0], 0:logo.shape[1], :] = logo
                    px = SCR_WIDTH-split_logo.shape[1]
                    py = 0
                    scr_buff[py:py+split_logo.shape[0], px:px+split_logo.shape[1], :] = split_logo
                    scr_buff[py:py+setting_logo.shape[0], px-setting_logo.shape[1]:px, :] = setting_logo
                    cv2.imshow(title, scr_buff)
                    if fps_counter>10:
                        sec=time.time()-starttime
                        fps=fps_counter/sec
                        starttime=time.time()
                        fps_counter=0
                    fps_counter+=1
                    ts_str = datetime.now().strftime("%y%m%d-%H%M%S-%f")[:-3]
                    loc=opjoin('record','Photo')
                    if not os.path.exists(loc):
                        os.mkdir(loc)
                    fn = opjoin(loc,ts_str + '.jpg')
                    if ir_full:
                            save_buf=scr_buff
                            save_buf[57:SCR_HEIGHT,0:SCR_WIDTH//2,:]= im_8[57:,:,:]
                            rgb_buf=cv2.resize(img,(SCR_WIDTH//2,SCR_HEIGHT),interpolation=0)
                            save_buf[57:SCR_HEIGHT,SCR_WIDTH//2:,:]=rgb_buf[57:,:,:]
                            scr_buff=save_buf
                    if self.record_counter == 0:
                        fn = opjoin(loc, ts_str + '.jpg')
                        buf_q.append([fn, scr_buff.copy()])
                    else:
                        if self.record_counter == RECORD_EXTEND_T:
                            for k in range(len(buf_q)):
                                if not sto_q.full():
                                    sto_q.put(buf_q.pop())

                        if not sto_q.full():
                            sto_q.put([fn, scr_buff.copy()])

                        self.record_counter  -= 1
                        free_space_cnt += 1
                        if free_space_cnt > 10:
                            free_space_cnt = 0
                            hdd = psutil.disk_usage('/')
                            space_mb = hdd.free//(1024*1024)
                            if space_mb < 1000:
                                cv2.putText(scr_buff, 'Storage is full',
                                    (15, 100), font, 1, (0,255,255), 2, cv2.LINE_AA)
                else:
                    cv2.waitKey(10)
        return

    def imshow_loop_rgb(self, disp_q_rgb):
        title = 'Visible Video Window'
        cv2.namedWindow(title, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow(title,800,600)        
        while True:
            if not disp_q_rgb.empty():
                rgb_window_close_flag=cv2.getWindowProperty(title,0)
                if rgb_window_close_flag==-1:
                    self.ir_full=False
                    self.rgb_pop_up=False
                    break
                img = disp_q_rgb.get()
                cv2.imshow(title, img)
            else:
                cv2.waitKey(10)
    
    def save_bbody_emv_h(self):
        path=opjoin('cfg','bbody_emv_h.cfg')
        fid=open(path,'w')
        fid.write(str(self.cfg_data.bbody_emv[0]))
        fid.close()

    def save_bbody_emv_l(self):
        path=opjoin('cfg','bbody_emv_l.cfg')
        fid=open(path,'w')
        fid.write(str(self.cfg_data.bbody_emv[1]))
        fid.close()

    def save_color_style(self):
        path=opjoin('cfg','tone.cfg')
        fid=open(path,'w')
        fid.write(self.cfg_data.COLOR_STYLE)
        fid.close()

    def save_blur(self):
        path=opjoin('cfg','blur.cfg')
        fid=open(path,'w')
        fid.write(str(self.cfg_data.blur_flag))
        fid.close()

    def save_bbody_mode(self):
        bbody_path=opjoin('cfg','black_body.cfg')
        fid = open(bbody_path,'w')
        fid.write(str(self.cfg_data.USE_BBODY))
        fid.close()

    def save_detection_offset(self):
        fname_x=opjoin('cfg','detection_offset_x.cfg')
        fname_y=opjoin('cfg','detection_offset_y.cfg')
        if os.path.exists(fname_x):
            try:
                fid=open(fname_x,'w')
                fid.write('%d'%self.cfg_data.detection_offset_x)
                fid.close()
            except:
                pass
        if os.path.exists(fname_y):
            try:
                fid=open(fname_y,'w')
                fid.write('%d'%self.cfg_data.detection_offset_y)
                fid.close()
            except:
                pass
        self.cfg_data.detection_offset={'x':self.cfg_data.detection_offset_x,'y':self.cfg_data.detection_offset_y}
    
    def save_emissivity(self):
        path=opjoin('cfg','emissivity.cfg')
        fid=open(path,'w')
        fid.write('%.2f'%self.corrPara.emissivity)
        fid.close()

    def save_thd(self):
        if COX_MODEL == 'CG':
            fname = opjoin('cfg','thd_cg.cfg')
        else:
            fname = opjoin('cfg','thd.cfg')
        fid=open(fname,'w')
        self.change_thd(self.cfg_data.thd_cels)
        fid.write('%d'%self.cfg_data.thd)
        fid.close()
        path=opjoin('cfg','thd_cels.cfg')
        fid = open(path,'w')
        fid.write('%.1f'%self.cfg_data.thd_cels)
        fid.close()
    
    def save_on_mask(self):
        path=opjoin('cfg','on_mask.cfg')
        fid=open(path,'w')
        fid.write(str(self.cfg_data.turn_on_mask))
        fid.close()

    def save_temp_offset(self):
        path=opjoin('cfg','temp_offset.cfg')
        fid=open(path,'w')
        fid.write(str(round(float(self.cfg_data.temp_offset),1)))
        fid.close()

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

        self.corrPara = td.IRF_TEMP_CORRECTION_PAR_T_CG()
        self.corrPara.offset = 0

        #if COX_MODEL=='CG':
        #    self.corrPara = td.IRF_TEMP_CORRECTION_PAR_T_CG()
        #    self.corrPara.offset = 0
        #else:
        #    self.corrPara = td.IRF_TEMP_CORRECTION_PAR_T()
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
        fname = opjoin('cfg','emissivity.cfg')
        if os.path.exists(fname):
            fid=open(fname, 'r')
            self.corrPara.emissivity = float(fid.read())
            fid.close()
        fid = open(r'TempMapTable_L.bin','rb')
        x = fid.read()
        nfloat = len(x)//4
        fid.close()
        self.temp_lut = struct.unpack('f'*nfloat, x)
        for n in range(0, 65535):
            self.pfloat_lut[n] = self.temp_lut[n]

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
            logging.error("canot connect to the camera")
            return
        self.requestCameraData()
        self.setNUC()
        # Function GetIRImages got to be called twice before it would not return error code
        self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
        #self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
        self.processing_started=False
        while (self.mHandle != -1):
            try:
                self.processing()
                if self.exit_all:
                    self.disconnect()
                    break
            except Exception as e:
                print(e)
                print("Thermal camera comm reset required", str(datetime.now()))
                logging.info("Thermal rest required")
                self.exit_all=True
                break
    
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
    
    def get_raw_image(self):
        NAVG = 1
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

    def client_to_yolo(self, img):
        pack_img = pickle.dumps(img)
        self.sock.sendall(pack_img)
        data = self.sock.recv(4096)
        boxes = pickle.loads(data)
        if len(boxes)>39:
            boxes=boxes[:39]
        return boxes

    def thresholding(self, boxes):
        # thresholding and find hot object contours
        max_t_list = []
        img16 = self.np_img_16.copy()
        mask = cv2.resize(self.mask_bw, (img16.shape[1],img16.shape[0]), 
                interpolation=0)//255
        img16 = img16 * mask
        for i in range(len(boxes)):
            box   = boxes[i]
            left  = box[0]
            top   = box[1]
            width = box[2]
            height= box[3]
            mmax=img16[top:top+height,left:left+width].max()
            # print(mmax)
            max_t = self.correct_temp(mmax)
            max_t +=self.cfg_data.temp_offset
            max_t_list.append(max_t)
        return max_t_list
    
    def label_temperature(self,img8,boxes,max_t_list):
        for n in range(len(max_t_list)):
            max_t=max_t_list[n]
            box   = boxes[n]
            left  = box[0]   
            top   = box[1]
            height= box[3]
            if left<0:
                left=0
            if top<0:
                top=0
            if max_t < 42.1:
                color = (255,255,255)
            else:
                color = (255,0,255)
            # if max_t>self.cfg_data.thd_cels:
            #     if  (top+height+20)>=img8.shape[0]:
            #         cv2.rectangle(img8,(left,top-14),(left+35,top-2),(128,128,128),cv2.FILLED)
            #         cv2.putText(img8, '%.1f'%max_t, (left,top),self.font,0.5, color, 1, cv2.LINE_AA)
            #     else:
            #         cv2.rectangle(img8,(left,top+height+8),(left+35,top+height+20),(128,128,128),cv2.FILLED)
            #         cv2.putText(img8, '%.1f'%max_t, (left,top+height+20),self.font,0.5, color, 1, cv2.LINE_AA)
            if  (top+height+20)>=img8.shape[0]:
                cv2.rectangle(img8,(left,top-14),(left+35,top-2),(128,128,128),cv2.FILLED)
                cv2.putText(img8, '%.1f'%max_t, (left,top),self.font,0.5, color, 1, cv2.LINE_AA)
            else:
                cv2.rectangle(img8,(left,top+height+8),(left+35,top+height+20),(128,128,128),cv2.FILLED)
                cv2.putText(img8, '%.1f'%max_t, (left,top+height+20),self.font,0.5, color, 1, cv2.LINE_AA)

    def processing(self):
        if not self.img_q.empty():
            if not self.reconnected:
                logging.info("reconnected")
                self.reconnected=True
            if int(time.time()-self.alert_timer)>300:
                logging.info("number of alerts: %d"%self.alert_counter)
                logging.info("number of no mask alerts: %d"%self.no_mask_counter)
                self.alert_timer=time.time()
                self.alert_counter=0
                self.no_mask_counter=0
            # print(self.ref_pair.raw_l,self.ref_pair.temp_l,self.ref_pair.raw_h,self.ref_pair.temp_h)
            self.ref_pair.get_calibrate(self.cfg_data.bbody_emv)
            t0=time.time()
            self.processing_started=True
            self.count_down_time_flag=True
            reply=self.img_q.get()
            self.np_img_16 = reply[0]
            if not self.np_img_16[0,0]==0:
                im_8=reply[1]
                if not self.action_q.empty():
                    action = self.action_q.get()
                    if action[0]=='password':
                        logging.info('login: %s'%action[1])
                    else:
                        logging.info("changed %s"%action)
                    if action[0] == 'thd':
                        self.cfg_data.thd_cels = round(action[1],1)
                        self.save_thd()
                    elif action[0] == 'emv':
                        self.corrPara.emissivity=round(action[1],2)
                        self.save_emissivity()
                    elif action[0] == 'bbody':
                        self.cfg_data.USE_BBODY=action[1]
                        self.save_bbody_mode()
                    elif action[0] == 'low':
                        if self.cfg_data.USE_BBODY:
                            self.ref_pair.pick_l = True
                            self.ir_full=True
                            self.ref_pair.save_temp_l(float(action[1]))
                            self.ref_pair.get_calibrate(self.cfg_data.bbody_emv)
                    elif action[0] == 'high':
                        if self.cfg_data.USE_BBODY:
                            self.ref_pair.pick_h = True
                            self.ir_full=True
                            self.ref_pair.save_temp_h(float(action[1]))
                            self.ref_pair.get_calibrate(self.cfg_data.bbody_emv)
                    elif action[0] == 'mask':
                        self.show_mask=(action[1])
                        if self.show_mask:
                            self.ir_full=True
                        else:
                            self.ir_full=False
                    elif action[0] == 'offset_x':
                        self.cfg_data.detection_offset_x=int(action[1])
                        self.save_detection_offset()
                    elif action[0] == 'offset_y':
                        self.cfg_data.detection_offset_y=int(action[1])
                        self.save_detection_offset()
                    elif action[0] == 'done':
                        self.ref_pair.pick_h=False
                        self.ref_pair.pick_l=False
                        if not self.rgb_pop_up:
                            self.ir_full=False
                        self.ref_pair.get_calibrate(self.cfg_data.bbody_emv)
                    elif action[0]=='BW':
                        self.cfg_data.COLOR_STYLE=action[0]
                        self.save_color_style()
                    elif action[0]=='JET':
                        self.cfg_data.COLOR_STYLE=action[0]
                        self.save_color_style()
                    elif action[0]=='blur':
                        self.cfg_data.blur_flag=action[1] 
                        self.save_blur()
                    elif action[0]=='bbody_emv_h':
                        self.cfg_data.bbody_emv[0]=action[1]
                        self.save_bbody_emv_h()
                    elif action[0]=='bbody_emv_l':
                        self.cfg_data.bbody_emv[1]=action[1]
                        self.save_bbody_emv_l()
                    elif action[0]=='off_mask':
                        self.cfg_data.turn_on_mask=action[1]
                        self.save_on_mask()
                    elif action[0]=='temp':
                        self.cfg_data.temp_offset=action[1]
                        self.save_temp_offset()
                
                if not self.sen_q.empty():
                    temp_c = self.sen_q.get()
                    self.ref_pair.sensor_feed(temp_c)
                
                self.np_img_16 += self.cfg_data.emv_table[round(self.corrPara.emissivity,2)]
                rgb = np.frombuffer(self.map[0:RGB_NPIX], dtype=uint8)
                rgb_full = rgb.reshape(RGB_SHAPE)

                rgb_full=face_processing.croppping(rgb_full,self.crop_height,self.crop_width,self.cfg_data.camera_offset)
                # resize image to 608 before yolo speeding up detection process significantly
                # h=int(650/1.2)
                # w=int(866/1.2)
                # rgb_full=face_processing.croppping(rgb_full,h,w,{'x':90,'y':10})
                img_for_yolo = cv2.resize(rgb_full, (768,576), interpolation=0)
                t1=time.time()
                boxes_from_yolo=self.client_to_yolo(img_for_yolo)
                t2=time.time()-t1
                numofhead=len(boxes_from_yolo)
            
                # get the corresponding location of the faces in threaml camera
                
                IR_boxes=face_processing.store_faces_location(boxes_from_yolo,self.np_img_16.shape,rgb_full.shape,(768,576),self.cfg_data.detection_offset)
                
                max_t_list = self.thresholding(IR_boxes)
                
                self.ref_pair.update(self.np_img_16)
                if self.cfg_data.USE_BBODY:
                    self.cfg_data.thd = self.ref_pair.temp2raw(self.cfg_data.thd_cels)
                
                if self.cfg_data.COLOR_STYLE=='BW':
                    im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_BONE)
                elif self.cfg_data.COLOR_STYLE=='JET':
                    im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_JET)
                
                alart_flag = False
                no_mask_alert=False
                for i in range(numofhead):
                    IR_box=IR_boxes[i]
                    box_one_head=face_processing.change_yolo_to_left_top(boxes_from_yolo[i][2],rgb_full.shape,(768,576))
                    box_one_head_mask=boxes_from_yolo[i][0]
                    if max_t_list[i]>=self.cfg_data.thd_cels:
                        alart_flag = True
                        self.alert_counter+=1
                        face_processing.draw_rectangle(im_8,IR_box,(0,0,255),2)
                        face_processing.draw_rectangle(rgb_full,box_one_head,(0, 0, 255),2)
                    else:
                        face_processing.draw_rectangle(im_8,IR_box,(0,255,0),2)
                        if box_one_head_mask=='with_mask' or self.cfg_data.turn_on_mask:
                            if self.cfg_data.blur_flag:
                                face_processing.blur_face(rgb_full,box_one_head)
                        else:
                            face_processing.draw_rectangle(rgb_full,box_one_head,(0,255,255),2)
                            no_mask_alert=True
                            # print("there is no mask")

                if alart_flag:
                    self.record_counter = RECORD_EXTEND_T
                    if not self.sound_q.full():
                        self.sound_q.put(0)

                if no_mask_alert:
                    self.no_mask_counter+=1
                    if not self.sound_q.full():
                        self.sound_q.put(1)
                
                self.label_temperature(im_8,IR_boxes,max_t_list)
                reading=0
                counter=0
                for i in range(-1,2):
                    for j in range(-1,2):
                        try:
                            ir_value=self.np_img_16[self.cursor[0]+i, self.cursor[1]+j]
                            reading += self.correct_temp(ir_value)
                        except:
                            counter+=1
                try:
                    reading/=(9-counter)
                except:
                    pass
                # reading=self.np_img_16[self.cursor[0], self.cursor[1]]
                mouse_info={'reading':reading,'textpos':self.cursor_textpos}
                display_list=[rgb_full,im_8,self.ir_full,self.cfg_data.thd_cels,self.cfg_data.thd,self.corrPara.emissivity,mouse_info]
                # decouple main loop and display loop so to avoid main loop freeze duriong mouse drag
                if not self.disp_q.full():
                    self.disp_q.put(display_list)
                if self.rgb_pop_up:
                    if not self.disp_q_rgb.full():
                        self.disp_q_rgb.put(rgb_full)
                # logging.info(int(1000*(time.time()-t0-t2)))
            else:
                logging.info("Thermal not working properly!")
                self.exit_all=True
        else:
            if self.processing_started:
                if self.count_down_time_flag:
                    self.t0=time.time()
                    self.count_down_time_flag=False
                t1=time.time()
                waittime=int(t1-self.t0)
                if (waittime)>3:
                    self.exit_all=True
                    global connection_error_flag
                    connection_error_flag=True
                    logging.error("lost conenction when running")
                    self.reconnected=False
                    print("Need recconect")
                    pass
            else:
                pass
        return 0

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
    
    def mouse_callback(self, event, x, y, flags, param):
        h = self.scr_buff.shape[0]
        w = SCR_WIDTH
        xratio = float(x)/w
        yratio = float(y)/h
        top_of_split=0
        left_of_split=SCR_WIDTH-self.split_logo.shape[1]
        bottom_of_split=self.split_logo.shape[0]
        right_of_split=SCR_WIDTH
        top_of_setting=0
        left_of_setting=SCR_WIDTH-self.setting_logo.shape[1]-self.split_logo.shape[1]
        bottom_of_setting=self.split_logo.shape[0]
        right_of_setting=SCR_WIDTH-self.split_logo.shape[1]

        if ( x>left_of_split and x<right_of_split ) and (y>top_of_split and y<bottom_of_split):
            if event == 1:
                    self.rgb_pop_up=True
                    self.ir_full=True
                    self.disp_q_rgb = queue.Queue(3)
                    self.imshow_thread_rgb = threading.Thread(target=self.imshow_loop_rgb, args=(self.disp_q_rgb, ))
                    self.imshow_thread_rgb.daemon=True
                    self.imshow_thread_rgb.start() 

        if ( x>left_of_setting and x<right_of_setting ) and (y>top_of_setting and y<bottom_of_setting):
            if event == 1:
                try:
                    if not self.setting_proc.is_alive():
                        self.on_setting=False
                except:
                    pass
                if not self.on_setting:
                    import setting
                    self.setting_proc=mp.Process(target=setting.func1,args=(self.action_q,))
                    self.setting_proc.daemon=True
                    self.setting_proc.start()
                    self.on_setting=True

        if event == 0:
          if not self.show_mask:
            try:
                if not self.ir_full:
                    xcoo = 2*int(xratio*self.np_img_16.shape[1])
                    if xcoo >= self.np_img_16.shape[1]:
                        xcoo = self.np_img_16.shape[1]-1
                else:
                    xcoo = int(xratio*self.np_img_16.shape[1])
                ycoo = int(yratio*self.np_img_16.shape[0])
                self.cursor = (ycoo, xcoo)
                if xcoo < 300:
                    self.cursor_textpos = (x+5, y-10)
                else:
                    self.cursor_textpos = (x-50, y-10)
            except:
                pass
        if event == 1:
            self.ref_pair.click({'x ratio':xratio, 'y ratio':yratio})
            if self.show_mask:
                xcoor = int(self.mask_bw.shape[1] * xratio)
                ycoor = int(self.mask_bw.shape[0] * yratio)
                if self.mask_bw[ycoor,xcoor]==0:
                    self.mask_color[ycoor, xcoor] = (0,0,0)
                    self.mask_bw[ycoor, xcoor] = 255
                    np.save('mask', self.mask_bw)
                else:
                    self.mask_color[ycoor, xcoor] = (60, 199, 165)  # rgb 
                    self.mask_bw[ycoor, xcoor] = 0
                    np.save('mask', self.mask_bw)
                

        elif event == 2:
            self.ref_pair.pick_l = False
            self.ref_pair.pick_h = False
            self.ref_pair.pick_head = False

            if self.show_mask:
                xcoor = int(self.mask_bw.shape[1] * xratio)
                ycoor = int(self.mask_bw.shape[0] * yratio)
                self.mask_color[ycoor, xcoor] = (0,0,0)
                self.mask_bw[ycoor, xcoor] = 255
                np.save('mask', self.mask_bw)
    
    def change_thd(self,temperture):
        corr_temp=self.cfg_data.temp_dict[temperture]
        self.cfg_data.thd=corr_temp

def rgb_capture_process(ipaddr):
    ipcam = hikvision.HikVision()
    ipcam.vis_init(ipaddr, "8000", "admin", "insight108!")
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

def thermal_process(ip, sn_q, sto_q, acn_q, sns_q,img_q, sock):
    cox = insight_thermal_analyzer(ip, "15001", sn_q, sto_q, acn_q, sns_q,img_q, sock)
    if NO_HARDWARE_TEST:
        while True:
            try:
                cox.processing()
            except Exception as e:
                print(e)
                print("Thermal camera comm reset required", str(datetime.now()))
                pass
    else:
        cox.connect()
        return 

if __name__ == '__main__': 
    connection_error_flag=False
    counter=0
    thermal_ip_fname=opjoin('cfg','thermal_ip.cfg')
    rgb_ip_fname=opjoin('cfg','rgb_ip.cfg')
    if os.path.exists(thermal_ip_fname):
        fid_t=open(thermal_ip_fname,'r')
        IR_IP=str(fid_t.read())
        fid_t.close()
    else:
        print("IP address of the thermal camera has not been configured")
        sys.exit()
    if os.path.exists(rgb_ip_fname):
        fid_r=open(rgb_ip_fname,'r')
        RGB_IP=fid_r.read()
        fid_r.close()
    else:
        print("IP address of the RGB camera has not been configured")
        sys.exit()
    fid = open(NMAP_FILE, "wb")
    buf = bytearray(RGB_NPIX)
    fid.write(buf)
    fid.close()
    try:
        os.mkdir('record')
    except:
        pass

    sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for n in range(5):
        try:
            print("connecting")
            sock.connect((yolo_host,yolo_port))
            break
        except:
            time.sleep(2)
    else:
        raise Exception('Could not connect to predictor server')

    clean_proc = mp.Process(target=cleanup.cleanup, args=(0,))
    clean_proc.daemon = True
    clean_proc.start()
    sav_proc = mp.Process(target=saving_image_process, args=(storage_q,))
    sav_proc.daemon = True
    sav_proc.start()
    
    rgb_proc = mp.Process(target=rgb_capture_process, args=(RGB_IP,))
    rgb_proc.daemon = True
    rgb_proc.start()
    
    sq = mp.Process(target=sound_process.sound_process, args=(sound_q,))
    sq.daemon = True
    sq.start()
    action_q = mp.Queue(2)

    raw_img_q = mp.Queue(2)
    
    sensor_que = mp.Queue(2)
    # sensor_p = mp.Process(target=senproc.sensor_proc, args=(sensor_que,))
    # sensor_p.daemon = True
    while True:
        raw_img_proc = mp.Process(target=get_img_proc.get_img, args=(raw_img_q,IR_IP,))
        raw_img_proc.daemon = True
        raw_img_proc.start()
        thermal_process(IR_IP,sound_q,storage_q,action_q,sensor_que,raw_img_q, sock)
        if connection_error_flag:
            raw_img_proc.terminate()
            connection_error_flag=False
            print("please reconnect the camera with the computer")
            time.sleep(10)
        else:
            break
    sock.close()
    clean_proc.terminate()
    sav_proc.terminate()
    rgb_proc.terminate()
    sq.terminate()
    # guip.terminate()
    raw_img_proc.terminate()