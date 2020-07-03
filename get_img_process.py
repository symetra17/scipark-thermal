import types_define as td
import numpy as np
from ctypes import *
from os.path import join as opjoin
import reference_pair as rp
import cv2
import time
import queue
import threading

THERMAL_IP = "192.168.88.253"
COX_MODEL = 'CG'
if COX_MODEL=='CG':
    THERMAL_WIDTH = 640
    THERMAL_HEIGHT = 480
else:
    THERMAL_WIDTH = 384
    THERMAL_HEIGHT = 288

class get_image_class(object):

    def __init__(self,ip,port):
        self.ip=ip
        self.port=port
        dll_path = opjoin('dll', 'CG_ThermalCamDll_2018.dll')
        try:
            self.dll = windll.LoadLibrary(dll_path)
        except:
            print('Could not load Thermal camera DLL.')
            quit()
        self.mHandle = wintypes.HANDLE()
        self.keepAlive = c_uint()
        self.camData = td.IRF_IR_CAM_DATA_T()
        self.m16 = np.zeros((THERMAL_HEIGHT,THERMAL_WIDTH), dtype=np.uint16)
        self.acm32 = np.zeros((THERMAL_HEIGHT,THERMAL_WIDTH), dtype=np.uint32)
        self.camData.ir_image = self.m16.ctypes.data_as(POINTER(c_ushort))
        self.camData.image_buffer_size = 4 * THERMAL_WIDTH * THERMAL_HEIGHT
        self.lpsize = (c_byte*8192)()
        self.camData.lpNextData = cast(self.lpsize, POINTER(c_byte))
        self.camData.dwSize = 0
        self.camData.dwPosition = 0
        self.dll.SendCameraMessage.restype = c_short
        self.dll.SendCameraMessage.argtypes = [wintypes.HANDLE, 
                                                POINTER(c_uint), 
                                                c_int,
                                                c_ushort,
                                                c_ushort]
        self.ref_pair = rp.reference_pair()

    
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
    
    def connect(self):
        print("Connecting",COX_MODEL, self.ip, self.port)
        self.dll.OpenConnect.restype = c_short
        self.dll.CloseConnect.restype = c_short
        err = -1
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
        # while (self.mHandle != -1):
        #     try:
        #         self.processing()
        #     except Exception as e:
        #         print(e)
        #         print("Thermal ccamera comm reset required", str(datetime.now()))
        #         break
        
    def get_raw_image(self):
        self.acm32.fill(0)
        val = self.dll.GetIRImages(self.mHandle, byref(self.keepAlive), byref(self.camData))
        if val == -100:
            return -1
        elif val != 1:
            raise Exception("Get IR Images fail errcode=%d"%(val))
        self.np_img_16 = self.m16.astype(np.uint16)
        return self.m16,self.np_img_16

def get_img(q):
    cox=get_image_class(THERMAL_IP,"15001")
    cox.connect()
    while True:
        img=cox.get_raw_image()
        if not q.full():
            q.put(img)
    
if __name__ == '__main__':
    disp_q=queue.Queue(3)
    proc=threading.Thread(target=get_img,args=(disp_q, ))
    proc.start()
    cv2.namedWindow("title",cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    while True:
        if not disp_q.empty():
            img=disp_q.get()
            cv2.imshow("title",img)
            k=cv2.waitKey(10)