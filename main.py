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
#from PIL import Image,ImageTk
import tkinter as tk
import queue

# Recording extension header and tail number of frame
# when an overtemperature event occur, a few seconds of record ahead of the 
# event would be saved, after the event, a few seconds of record folowing
# the event would also be saved.
RECORD_EXTEND_T = 20   
RGB_IP = "192.168.88.249"
THERMAL_IP = "192.168.88.253"
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
IR_full_scr=False

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
        if self.USE_BBODY:
            val = self.ref_pair.interp_temp(ir_reading)
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

    def __init__(self, ip, port, sn_q, sto_q, action_q, sen_q, sock):
        self.weekdaydict={0:"MON",1:"TUE",2:"WED",3:"THU",4:"FRI",5:"SAT",6:"SUN"}
        print("aa")
        print('Loading Thermal camera library')
        dll_path = opjoin('dll', 'CG_ThermalCamDll_2018.dll')
        try:
            self.dll = windll.LoadLibrary(dll_path)
        except:
            print('Could not load Thermal camera DLL.')
            quit()
        print('Completed')
        self.dll.GetCorrectedTemp.restype = c_float
        self.load_temp_map() #there is problme with the map
        self.init_cam_vari(ip,port)
        self.load_app_settings()
        self.fid = open(NMAP_FILE, "r+")
        self.map = mmap.mmap(self.fid.fileno(), 0)
        self.COLOR_STYLE=COLOR_STYLE
        self.width=1080
        self.height=810
        self.crop_width=1320
        self.crop_height=990
        self.load_offset_of_camera()
        self.load_face_offset()
        print(self.detection_offset_x,self.detection_offset_y)
        buf = np.empty((480, 640, 3), dtype=uint8)
        self.hour_dir = ''
        self.record_counter = 0
        self.sound_q = sn_q
        self.storage_q = sto_q
        self.logo = cv2.imread('IR-logo-h57.png')
        self.setting_logo  = cv2.imread('Setting-icon.png')
        self.scr_buff = np.empty((SCR_HEIGHT, SCR_WIDTH, 3), dtype=uint8)   # preallocate this array to speed up
        self.action_q = action_q
        self.sen_q = sen_q
        self.src_rgb = np.zeros((SCR_HEIGHT,SCR_WIDTH//2,3),dtype=uint8)
        self.ref_pair = rp.reference_pair()
        self.load_bbody_mode()
        self.ir_full=IR_full_scr
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
        self.show_mask = False
        self.cursor = (50,50)
        self.cursor_textpos = (50,50)
        self.cursor_reading = 0
        self.free_space_cnt=0
        self.sock = sock
        self.fps_counter=0
        self.fps=0
        self.disp_q = queue.Queue(3)
        self.imshow_thread = threading.Thread(target=self.imshow_loop, args=(self.disp_q, ))
        self.imshow_thread.start()
        self.disp_q_rgb = queue.Queue(3)
        self.imshow_thread_rgb = threading.Thread(target=self.imshow_loop_rgb, args=(self.disp_q_rgb, ))
        self.imshow_thread_rgb.start()

    def imshow_loop(self, disp_q):
        title = 'Insightrobotics Fever Monitoring System'
        cv2.namedWindow(title, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow(title,SCR_WIDTH,SCR_HEIGHT)
        cv2.setMouseCallback(title, self.mouse_callback)
        while True:
            if not disp_q.empty():
                if self.fps_counter==0:
                    starttime=time.time()
                img = disp_q.get()
                cv2.imshow(title, img)
                if self.fps_counter>10:
                    sec=time.time()-starttime
                    self.fps=self.fps_counter/sec
                    starttime=time.time()
                    self.fps_counter=0
                self.fps_counter+=1
            else:
                cv2.waitKey(10)

    def imshow_loop_rgb(self, disp_q_rgb):
        title = 'Visible Video Window'
        cv2.namedWindow(title, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow(title,800,600)        
        while True:
            if not disp_q_rgb.empty():
                img = disp_q_rgb.get()
                cv2.imshow(title, img)
            else:
                cv2.waitKey(10)

    #there are some value missing from the dictinary !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def load_temp_map(self):
        fname=open("table_for_temp_to_thd.txt")
        dict_of_temp=fname.read()
        self.temp_dict=eval(dict_of_temp)
        fname.close()

    def load_bbody_mode(self):
        try:
            fid = open('black_body.cfg','r')
            s = fid.read()
            self.USE_BBODY = eval(s)
            fid.close()
        except:
            self.USE_BBODY = False
            self.save_bbody_mode()

    def save_bbody_mode(self):
        fid = open('black_body.cfg','w')
        fid.write(str(self.USE_BBODY))
        fid.close()

    def load_offset_of_camera(self):
        fname_x='camera_offset_x.cfg'
        fname_y='camera_offset_y.cfg'
        if os.path.exists(fname_x):
            try:
                fid=open(fname_x,'r')
                self.offset_x=int(fid.read())
                fid.close()
            except:
                pass
        else:
            self.offset_x=0
            print("cannot acces ",fname_x)   

        if os.path.exists(fname_y):
            try:
                fid=open(fname_y,'r')
                self.offset_y=int(fid.read())
                fid.close()
            except:
                pass
        else:
            self.offset_y=0
            print("cannot acces ",fname_y)
    
    def load_face_offset(self):
        fname_x='detection_offset_x.cfg'
        fname_y='detection_offset_y.cfg'
        if os.path.exists(fname_x):
            try:
                fid=open(fname_x,'r')
                self.detection_offset_x=int(fid.read())
                fid.close()
            except:
                pass
        else:
            self.offset_x=0
            print("cannot acces ",fname_x)   

        if os.path.exists(fname_y):
            try:
                fid=open(fname_y,'r')
                self.detection_offset_y=int(fid.read())
                fid.close()
            except:
                pass
        else:
            self.offset_y=0
            print("cannot acces ",fname_y)

    def save_detection_offset(self):
        fname_x='detection_offset_x.cfg'
        fname_y='detection_offset_y.cfg'
        if os.path.exists(fname_x):
            try:
                fid=open(fname_x,'w')
                fid.write('%d'%self.detection_offset_x)
                fid.close()
            except:
                pass
        if os.path.exists(fname_y):
            try:
                fid=open(fname_y,'w')
                fid.write('%d'%self.detection_offset_y)
                fid.close()
            except:
                pass

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
    def load_thd(self):
        self.thd = 19000
        if COX_MODEL == 'CG':
            fname = 'thd_cg.cfg'
            self.thd = 6000
        else:
            fname = 'thd.cfg'
        if os.path.exists(fname):
            try:
                fid=open(fname,'r')
                self.thd = int(fid.read())
                fid.close()
            except:
                pass

        fname = 'thd_cels.cfg'
        for _ in range(2):
            if os.path.exists(fname):
                fid=open(fname,'r')
                self.thd_cels = float(fid.read())
                fid.close()
                break
            else:
                fid=open(fname,'w')
                fid.write('36.0')
                fid.close()


    def load_app_settings(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.load_thd()
        if os.path.exists('emissivity.cfg'):
            try:
                fid=open('emissivity.cfg','r')
                self.corrPara.emissivity = float(fid.read())
                fid.close()
            except Exception as e:
                print(e.message)
        fid = open(r'TempMapTable_L.bin','rb')
        x = fid.read()
        nfloat = len(x)//4
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
        self.setNUC()
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
        if len(boxes)>29:
            boxes=boxes[:29]
        return boxes

    def thresholding(self,box):
        b_img = self.np_img_16.copy()
        b_img[b_img <= self.thd] = 0
        b_img[b_img > self.thd] = 255        
        #negative sign for detection offset is to compansate the small distortion in the thermal cam
        width_ratio=b_img.shape[1]/self.crop_width
        height_ratio=b_img.shape[0]/self.crop_height
        left = int(box[0]*width_ratio)+self.detection_offset_x
        top = int(box[1]*height_ratio)+self.detection_offset_y
        width = int(box[2]*width_ratio)
        height = int(box[3]*height_ratio)
        right=(left+width)
        bottom=(top+height)
        box_for_IR=[left,top,width,height]
        b_img[:,0:left]=0
        b_img[0:top,:]=0
        b_img[:,right:b_img.shape[1]]=0
        b_img[bottom:b_img.shape[0],:]=0
        b_img = b_img.astype(uint8)
        mask = cv2.resize(self.mask_bw, (b_img.shape[1],b_img.shape[0]), 
                    interpolation=0)//255
        b_img = b_img * mask
        kern = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
        b_img = cv2.dilate(b_img, kern)
        contours,_ = cv2.findContours(b_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        img16 = self.np_img_16.copy()
        max_t_list = []
        for n,_ in enumerate(contours):
            mask = np.zeros(img16.shape[0:2], dtype=uint8)
            cv2.fillPoly(mask, pts=contours[n:n+1], color=(1))
            mmax = (img16*mask).max()
            max_t = self.correct_temp(mmax)
            max_t_list.append(max_t)
        return contours, max_t_list,box_for_IR

    def draw_contours(self, img8, img16, contours):
        for n,_ in enumerate(contours):
            mask = np.zeros(img8.shape[0:2], dtype=uint8)
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
                lb_xpos = np.array(x).max() - 35
            lb_ypos = np.array(y).max()
            cv2.rectangle(img8, (lb_xpos, lb_ypos-12), (lb_xpos+35, lb_ypos+1), 
                                                (128,128,128), cv2.FILLED)
            if max_t < 42.1:
                color = (255,255,255)
            else:
                color = (255,0,255)
            cv2.putText(img8, '%.1f'%max_t, (lb_xpos,lb_ypos), self.font,
                        0.5, color, 1, cv2.LINE_AA)
    
    def change_yolo_to_left_top(self,box_from_yolo):
        x_ratio=self.crop_width/608
        y_ratio=self.crop_height/608
        center_x=box_from_yolo[0]
        center_y=box_from_yolo[1]
        width = box_from_yolo[2]
        height = box_from_yolo[3]
        left = (center_x-width/2)
        top = (center_y-height/2)
        box_after_adjust=[0,0,0,0]
        box_after_adjust[0]=left*x_ratio
        box_after_adjust[1]=top*y_ratio
        box_after_adjust[2]=width*x_ratio
        box_after_adjust[3]=height*y_ratio
        return box_after_adjust

    def croppping(self,img):
        target_width=self.crop_width #original:1920
        target_height=self.crop_height #original:1080
        originalwidth=img.shape[1]
        originalheight=img.shape[0]
        offset_x=self.offset_x
        offset_y=self.offset_y
        img_copy=img.copy()
        img=img_copy[(originalheight-target_height)//2+offset_y:originalheight-(originalheight-target_height)//2+offset_y,
                            (originalwidth-target_width)//2+offset_x:originalwidth-(originalwidth-target_width)//2+offset_x,0:3]
        return img

    def processing(self):
        if not self.action_q.empty():
            action = self.action_q.get()
            if action[0] == 'thd':
                self.thd_cels = round(action[1],1)
                self.save_thd()
            elif action[0] == 'emv':
                self.corrPara.emissivity=action[1]
                self.save_emissivity
            elif action[0] == 'bbody':
                self.USE_BBODY=action[1]
                self.save_bbody_mode()

            elif action=='thd+':
                self.ir_full=True
            #    self.thd+=30
            #    self.save_thd()
            elif action=='thd-':
                self.ir_full=False
            #    self.thd-=30
            #    self.save_thd()
            elif action=='offset+':
               self.detection_offset_x += 1
               self.save_detection_offset()
            #    self.save_emissivity()
            elif action=='offset-':
               self.detection_offset_x -= 1
               self.save_detection_offset()
            #    self.save_emissivity()
            elif action=='refl':
                if self.USE_BBODY:
                    self.ref_pair.pick_l = True
                    self.ir_full=True
            elif action=='refh':
                if self.USE_BBODY:
                    self.ref_pair.pick_h = True
                    self.ir_full=True
            elif action=='ref head':
               self.ref_pair.pick_head()
            elif action=='ref head tape':
               self.ref_pair.pick_head_tape()
            elif action=='BW':
                self.COLOR_STYLE=action
            elif action=='JET':
                self.COLOR_STYLE=action
            elif action=='HSV':
                self.COLOR_STYLE=action
            elif action=='RED':
                self.COLOR_STYLE=action
                                
        if not self.sen_q.empty():
            temp_c = self.sen_q.get()
            self.ref_pair.sensor_feed(temp_c)

        if not NO_HARDWARE_TEST:
            self.get_raw_image()
        else:
            self.np_img_16 = cv2.imread('ir_test_02.jpg',0).astype(uint16)
            self.np_img_16 = self.np_img_16 * 200
            self.np_img_16[160,120] = random.randint(16000, 18000)
            time.sleep(0.03)  
        rgb = np.frombuffer(self.map[0:RGB_NPIX], dtype=uint8)
        rgb = rgb.reshape(RGB_SHAPE)
        rgb_full=rgb.copy()
        rgb_full=self.croppping(rgb_full)
        cv2.resize(rgb, (SCR_WIDTH//2, SCR_HEIGHT), self.src_rgb, 
                                            interpolation=0)

        # resize image to 608 before yolo speeding up detection process significantly
        img_608 = cv2.resize(rgb_full, (608,608), interpolation=cv2.INTER_LINEAR)
        boxes_from_yolo=self.client_to_yolo(img_608)
        numofhead=len(boxes_from_yolo)
        contours_list=[]
        max_t_list=[]
        IR_boxes=[]
        for i in range(numofhead):
            box_after_adjust=self.change_yolo_to_left_top(boxes_from_yolo[i][2])
            contours, max_t , box_for_IR = self.thresholding(box_after_adjust)
            contours_list.extend(contours)
            max_t_list.extend(max_t)
            IR_boxes.append(box_for_IR)
        self.ref_pair.update(self.np_img_16)
        if self.USE_BBODY:
            self.thd = self.ref_pair.temp2raw(self.thd_cels)
        f_img = self.np_img_16.astype(np.float)
        fmin = np.percentile(f_img, 0.1)
        fmax = np.percentile(f_img, 99.9)+50
        f_img = np.interp(f_img, [fmin,fmax],[0.0,255.0])
        im_8 = f_img.astype(uint8)
        tmax = self.correct_temp(self.np_img_16.max())
        if self.COLOR_STYLE=='BW':
            im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_BONE)
        elif self.COLOR_STYLE=='JET':
            im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_JET)
        elif self.COLOR_STYLE=='HSV':
            im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_HSV)
        elif self.COLOR_STYLE=='RED':
            im_8 = cv2.applyColorMap(im_8, cv2.COLORMAP_HOT)
        cv2.drawContours(im_8, contours_list, -1, (255,255,255), thickness=2)
        t0=time.time()
        for i in range(numofhead):
            IR_box=IR_boxes[i]
            IR_left=IR_box[0]
            IR_top=IR_box[1]
            IR_width=IR_box[2]
            IR_height=IR_box[3]
            IR_right=int(IR_left+IR_width)
            IR_bottom=int(IR_top+IR_height)
            box_one_head=self.change_yolo_to_left_top(boxes_from_yolo[i][2])
            left=int(box_one_head[0])
            top=int(box_one_head[1])
            width=int(box_one_head[2])
            height=int(box_one_head[3])
            right=int(box_one_head[0]+box_one_head[2])
            bottom=int(box_one_head[1]+box_one_head[3])
            try:
                if max_t_list[i]>self.correct_temp(self.thd):
                    cv2.rectangle(im_8,(IR_left,IR_top),(IR_right,IR_bottom),(0,0,255),2)
                    cv2.rectangle(rgb_full, (left, top), (right, bottom), (0, 0, 255), 2)
            except:
                cv2.rectangle(im_8,(IR_left,IR_top),(IR_right,IR_bottom),(0,255,0),2)
                face_to_blur=rgb_full[top:top+int(height),left:left+int(width),0:3]
                blur=cv2.GaussianBlur(face_to_blur,(51,51),0)
                rgb_full[top:top+int(height),left:left+int(width),0:3]=blur   
            
            alart_flag = False
            for item in max_t_list:
                if item < 42.1:
                    alart_flag = True

            if alart_flag:
                self.record_counter = RECORD_EXTEND_T
                if not self.sound_q.full():
                    self.sound_q.put(0)

            self.draw_contours(im_8, self.np_img_16, contours_list)
        print('proc time ',int(1000*(time.time()-t0)))
        im_8 = cv2.resize(im_8, (SCR_WIDTH//2,SCR_HEIGHT), interpolation=0)
        reading = self.correct_temp(self.np_img_16[self.cursor])
        x1 = self.cursor_textpos[0]-3
        y1 = self.cursor_textpos[1]-15
        x2 = self.cursor_textpos[0]+46
        y2 = self.cursor_textpos[1]+5
        cv2.rectangle(im_8, (x1,y1), (x2, y2), (50,50,50), cv2.FILLED)
        cv2.putText(im_8, '%.2f'%reading, self.cursor_textpos, 
                self.font, 0.5, (255,255,255), 1, cv2.LINE_AA)

        if self.USE_BBODY:
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

        self.scr_buff[:,0:SCR_WIDTH//2,:]= im_8
        self.scr_buff[:,SCR_WIDTH//2:,:] = self.src_rgb
        
        ts_str = datetime.now().strftime("%y%m%d-%H%M%S-%f")[:-3]
        fn = opjoin('record', ts_str + '.jpg')

        if self.record_counter == 0:
            fn = opjoin('record', ts_str + '.jpg')
            buf_q.append([fn, self.scr_buff.copy()])
        else:
            if self.record_counter == RECORD_EXTEND_T:
                for k in range(len(buf_q)):
                    if not self.storage_q.full():
                        self.storage_q.put(buf_q.pop())

            if not self.storage_q.full():
                self.storage_q.put([fn, self.scr_buff.copy()])

            self.record_counter -= 1
            self.free_space_cnt += 1
            if self.free_space_cnt > 10:
                self.free_space_cnt = 0
                hdd = psutil.disk_usage('/')
                space_mb = hdd.free//(1024*1024)
                if space_mb < 1000:
                    cv2.putText(self.scr_buff, 'Storage is full',
                        (15, 100), self.font, 1, (0,255,255), 2, cv2.LINE_AA)

        if self.ir_full:
            im_8_full=cv2.resize(im_8,(SCR_WIDTH,SCR_HEIGHT))
            print(im_8_full.shape)
            self.scr_buff=im_8_full
        else:
            rgb_buf=cv2.resize(rgb_full,(SCR_WIDTH//2,SCR_HEIGHT))
            self.scr_buff[:,SCR_WIDTH//2:,:]=rgb_buf

        cv2.rectangle(self.scr_buff, (self.logo.shape[1], 0), (SCR_WIDTH-self.setting_logo.shape[1], 56), (84,68,52), cv2.FILLED)
        cv2.putText(self.scr_buff,"AI-ASSISTED BODY TEMPERATURE SCREENING SYSTEM",(15+self.logo.shape[1],57//2+5),self.font,0.64,(60, 199, 165),1,cv2.LINE_AA)
        date=datetime.now().strftime("%Y-%m-%d ")+self.weekdaydict[datetime.today().weekday()]
        cv2.putText(self.scr_buff,date,(SCR_WIDTH//2+50,57//2+5),self.font,0.5,(255,255,255), 1, cv2.LINE_AA)
        now_time=datetime.now().strftime(" %H:%M:%S")
        cv2.putText(self.scr_buff,now_time,(SCR_WIDTH//2+300,57//2+5),self.font,0.85,(228,193,110), 1, cv2.LINE_AA)
        cv2.putText(self.scr_buff, 'THD %.1f (%d) EMISIV(w/s)%.2f MAX %.2f'%(
                    self.thd_cels, 
                    self.thd, 
                    self.corrPara.emissivity,
                    tmax), 
                    (SCR_WIDTH-self.setting_logo.shape[1]-400, 57//2+5), self.font, 0.5, (255,255,255), 1, cv2.LINE_AA)
        cv2.putText(self.scr_buff,'FPS: %.1f'%self.fps,(0,self.logo.shape[0]+15),self.font,0.5,(255,255,255),1,cv2.LINE_AA)
        self.scr_buff[0:self.logo.shape[0], 0:self.logo.shape[1], :] = self.logo
        #self.scr_buff[0:self.logo.shape[0], 0:self.logo.shape[1], :] += self.logo

        if not(self.show_mask):
            px = SCR_WIDTH-self.setting_logo.shape[1]
            py = 0
            self.scr_buff[py:py+self.setting_logo.shape[0], px:px+self.setting_logo.shape[1], :] = self.setting_logo

        # decouple main loop and display loop so to avoid main loop freeze duriong mouse drag
        if not self.disp_q.full():
            self.disp_q.put(self.scr_buff)
        if not self.disp_q_rgb.full():
            self.disp_q_rgb.put(rgb_full)

        #key = cv2.waitKey(30)
        #if key & 0xff == ord('+'):
        #    if COX_MODEL == 'CG':
        #        self.thd += 6
        #    else:
        #        self.thd += 10
        #    self.save_thd()
        #elif key & 0xff == ord('-'):
        #    if COX_MODEL == 'CG':
        #        self.thd -= 6
        #    else:
        #        self.thd -= 10
        #    self.save_thd()
        #elif key & 0xff == ord('w'):
        #    self.corrPara.emissivity += 0.01
        #    self.save_emissivity()
        #elif key & 0xff == ord('s'):
        #    self.corrPara.emissivity -= 0.01
        #    self.save_emissivity()
        #elif key & 0xff == ord('b'):
        #    if self.USE_BBODY:
        #        self.USE_BBODY = False
        #        self.save_bbody_mode()
        #    else:
        #        self.USE_BBODY = True
        #        self.save_bbody_mode()
        #elif key&0xff==ord(' '):
        #    if self.show_mask:
        #        self.show_mask = False
        #    else:
        #        self.show_mask = True
        #elif key & 0xff == ord('q'):
        #    return -1
        return 0

    def save_emissivity(self):
        fid=open('emissivity.cfg','w')
        fid.write('%.2f'%self.corrPara.emissivity)
        fid.close()

    def save_thd(self):
        if COX_MODEL == 'CG':
            fname = 'thd_cg.cfg'
        else:
            fname = 'thd.cfg'
        fid=open(fname,'w')
        self.change_thd(self.thd_cels)
        fid.write('%d'%self.thd)
        fid.close()

        fid = open('thd_cels.cfg','w')
        fid.write('%.1f'%self.thd_cels)
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

    def mouse_callback(self, event, x, y, flags, param):
        h = self.scr_buff.shape[0]
        w = SCR_WIDTH
        xratio = float(x)/w
        yratio = float(y)/h
        top_of_setting=0
        left_of_setting=SCR_WIDTH-self.setting_logo.shape[1]
        bottom_of_setting=self.setting_logo.shape[0]
        right_of_setting=SCR_WIDTH

        if ( x>left_of_setting and x<right_of_setting ) and (y>top_of_setting and y<bottom_of_setting):
            if event == 1 and not(self.show_mask):
                import setting
                setting_proc=mp.Process(target=setting.func1,args=(self.action_q,))
                setting_proc.daemon=True
                setting_proc.start()

        if event == 0:
          if not self.show_mask:
            xcoo = int(xratio*self.np_img_16.shape[1])
            ycoo = int(yratio*self.np_img_16.shape[0])
            self.cursor = (ycoo,xcoo)
            xcoo = int(xratio*SCR_WIDTH)
            ycoo = int(yratio*SCR_HEIGHT)
            self.cursor_textpos = (xcoo+10, ycoo-5)

        if event == 1:
            self.ref_pair.click({'x ratio':xratio, 'y ratio':yratio})
            if self.show_mask:
                xcoor = int(self.mask_bw.shape[1] * xratio)
                ycoor = int(self.mask_bw.shape[0] * yratio)
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
        corr_temp=self.temp_dict[temperture]
        self.thd=corr_temp

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

def thermal_process(sn_q, sto_q, acn_q, sns_q, sock):
    cox = insight_thermal_analyzer(THERMAL_IP, "15001", sn_q, sto_q, acn_q, sns_q, sock)
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

    if True:
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
        guip = mp.Process(target=gproc.gui_process, args=(action_q,))
        guip.daemon = True
        guip.start()

    sensor_que = mp.Queue(2)
    sensor_p = mp.Process(target=senproc.sensor_proc, args=(sensor_que,))
    sensor_p.daemon = True

    while True:
        tp = mp.Process(target=thermal_process, args=(sound_q,storage_q,action_q,sensor_que,sock,))
        #tp.daemon = True
        tp.start()
        tp.join()
        time.sleep(5)
