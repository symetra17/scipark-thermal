import os
import sys
from ctypes import wintypes
import ctypes
from ctypes import *
import hikvision_define as td
import numpy as np
import cv2
import time
from datetime import datetime
import mmap
import multiprocessing as mp
import tkinter as tk

NET_DVR_PAN_LEFT = 23
NET_DVR_PAN_RIGHT = 24
NET_DVR_TILT_UP = 21
NET_DVR_TILT_DOWN = 22
NET_DVR_START = 0
NET_DVR_STOP = 1

try:
    playCtrl = windll.LoadLibrary('PlayCtrl.dll')
except Exception as e:
    print("Exception in loading PlayCtrl dll")
    print(e)
    os._exit(0)

try:            
    netsdk = windll.LoadLibrary('HCNetSDK.dll')
    netsdk.NET_DVR_PTZControl.restype = c_bool
except Exception as e:
    print("Exception in loading HCNetSDK dll")
    print(e)
    os._exit(0)

try:
    yuv2rgb = windll.LoadLibrary('YUV2RGB.dll')
except Exception as e:
    print("Exception in loading YUV2RGB dll")
    print(e)
    os._exit(0)


class HikVision(object):
    '''
    - Connect visible IP camera and get picture data(YUV).
    - Convert YUV to RGB through YUV2RGB.dll
    '''

    def __init__(self):
        self.nmap_fid = open("sharedmem.dat", "r+")
        self.map = mmap.mmap(self.nmap_fid.fileno(), 0)

        self.lUserID = 0L
        self.lPort = pointer(c_long())
        
        # Set Argument Types
        yuv2rgb.YUVToRGB.argtypes = [POINTER(c_ubyte), c_int, c_int, c_int]
        yuv2rgb.YUVToRGB.restype = POINTER(c_ubyte)

        #playCtrl.PlayM4_GetLastError.argtypes = [c_long]
        #playCtrl.PlayM4_GetPort.argtypes = [POINTER(c_long)]        
        #playCtrl.PlayM4_SetStreamOpenMode.argtypes = [c_long, wintypes.DWORD]        
        #playCtrl.PlayM4_OpenStreamEx.argtypes = [c_long, POINTER(wintypes.BYTE), wintypes.DWORD, wintypes.DWORD]        
        #playCtrl.PlayM4_Play.argtypes = [c_long, wintypes.HWND]               
        #playCtrl.PlayM4_GetSpecialData.argtypes = [c_long]
        #playCtrl.PlayM4_SetDecCBStream.argtypes = [c_long, wintypes.DWORD]        
        #playCtrl.PlayM4_SetDecodeFrameType.argtypes = [c_long, wintypes.DWORD]
        #playCtrl.PlayM4_SetDecCallBack.argtypes = [c_long, td.FSETDECCALLBACK]
        #playCtrl.PlayM4_InputData.argtypes = [c_long, POINTER(wintypes.BYTE), wintypes.DWORD]
        # Set Return Types
        playCtrl.PlayM4_GetLastError.restype = wintypes.DWORD
        playCtrl.PlayM4_GetPort.restype = c_bool
        playCtrl.PlayM4_SetStreamOpenMode.restype = c_bool
        playCtrl.PlayM4_OpenStreamEx.restype = c_bool
        playCtrl.PlayM4_Play.restype = c_bool
        playCtrl.PlayM4_InputData.restype = c_bool
        playCtrl.PlayM4_GetSpecialData.restype = wintypes.DWORD
        
        self.callbackcnt = 0
        self.flag_request_img = False
        self.lRealPlayHandle = 0

    def vis_init(self, ip, port, username, password, smokeDetect=False, streamChnl='main'):
        self.ipaddr = ip
        self.port = int(port)
        self.username = username
        self.password = password

        #For Visable camera variable
        self.fSetDecCallBack = td.FSETDECCALLBACK(self.decodeCallBack)
        netsdk.NET_DVR_Init.restype = c_bool   
        netsdk.NET_DVR_SetConnectTime.argtypes = [wintypes.DWORD, wintypes.DWORD]
        netsdk.NET_DVR_SetConnectTime.restype = c_bool 
        netsdk.NET_DVR_SetReconnect.argtypes = [wintypes.DWORD, c_bool]
        netsdk.NET_DVR_SetReconnect.restype = c_bool      
        if not netsdk.NET_DVR_Init():
            print("NET_DVR_Init Error")
            sys.exit(0)
        if not netsdk.NET_DVR_SetConnectTime(2000, 1):
            print("NET_DVR_SetConnectTime Error")
            sys.exit(0)
        if not netsdk.NET_DVR_SetReconnect(10000, True):
            print("NET_DVR_SetReconnect Error")
            sys.exit(0)

        self.fRealDataCallBack = td.FREALDATACALLBACK(self.realDataCallBack)
        self.fExceptionCallBack = td.FEXCEPTIONCALLBACK(self.py_ExceptionCallBack)
                    
        # Start Error Message Reporting Callback
        netsdk.NET_DVR_SetExceptionCallBack_V30(0, None, self.fExceptionCallBack, None)
        
        self.RGB = None
        self.except_error = False
        self.lockDecodeCallBack = 0
        self.streamChnl = streamChnl
        self.setClientInfo()
        
    def setClientInfo(self):
        self.ClientInfo = td.NET_DVR_CLIENTINFO()
        self.ClientInfo.lChannel = 1
        self.ClientInfo.hPlayWnd = None
        if self.streamChnl == 'sub':
            # 0  # If 31st bit is 0, it means connecting main stream, 1 means sub stream. Bit 0~bit 30 are used for link mode: 0-TCP, 1-UDP, 2-multicast, 3-RTP
            self.ClientInfo.lLinkMode = 0x80000000
        else:
            # 0  # If 31st bit is 0, it means connecting main stream, 1 means sub stream. Bit 0~bit 30 are used for link mode: 0-TCP, 1-UDP, 2-multicast, 3-RTP
            self.ClientInfo.lLinkMode = 0x00000000
        self.ClientInfo.sMulticastIP = None
        
    def login(self):
        struDeviceInfo = td.NET_DVR_DEVICEINFO_V30()
        self.lUserID = 0L
        netsdk.NET_DVR_Login_V30.argtypes = [c_char_p, wintypes.WORD, c_char_p, c_char_p,
                                                  POINTER(td.NET_DVR_DEVICEINFO_V30)]
        self.lUserID = netsdk.NET_DVR_Login_V30(self.ipaddr, self.port, self.username, self.password, 
                                                    byref(struDeviceInfo))
        if self.lUserID < 0:
            print("Camera Login Failed", self.ipaddr, self.port, self.username, self.password)
            netsdk.NET_DVR_Cleanup()
            return {'status': 'ERR'}
        elif self.lUserID >= 0:
            self.ts_diff = time.time()
            print("Camera Login Successful  Camera IP: " + self.ipaddr + ":" + str(self.port))
            self.start()
        return {'status': 'OK'}
    
    def start(self):
        #int NET_DVR_RealPlay_V30(int iUserID, ref NET_DVR_CLIENTINFO lpClientInfo, 
        #                                           REALDATACALLBACK fRealDataCallBack_V30, 
        #                                           IntPtr pUser, 
        #                                           UInt32 bBlocked);
        netsdk.NET_DVR_RealPlay_V30.argtypes = [c_long, POINTER(td.NET_DVR_CLIENTINFO), 
                                                POINTER(td.FREALDATACALLBACK), 
                                                c_void_p, c_uint32]

        self.lRealPlayHandle = netsdk.NET_DVR_RealPlay_V30(self.lUserID, self.ClientInfo, 
                                                            None, None, 0)        
        if self.lRealPlayHandle < 0:
            print('error realplayhandle < 0')
            self.logout()
            quit()
        netsdk.NET_DVR_SetRealDataCallBack.argtypes = [c_long, 
                                                        td.FREALDATACALLBACK, wintypes.DWORD]
        result = netsdk.NET_DVR_SetRealDataCallBack(self.lRealPlayHandle,
                                                         self.fRealDataCallBack, 0)
        if not result:
            print("SET_DVR_SetRealDataCallBack failed")
            quit()

    def stop(self):
        print("Stop real play function")
        netsdk.NET_DVR_StopRealPlay.argtypes = [c_long]
        netsdk.NET_DVR_StopRealPlay(self.lRealPlayHandle)
        
        if not playCtrl.PlayM4_FreePort(self.lPort[0]):
            print('Free real play port not success')
        else:
            self.lPort[0] = -1
        
    def logout(self):
        print("Logout IPC camera")
        self.stop()
        netsdk.NET_DVR_Logout_V30.argtypes = [c_long]
        netsdk.NET_DVR_Logout_V30(self.lUserID)
        netsdk.NET_DVR_Cleanup()      
    
    def decodeCallBack(self, lPort, pBuffer, lSize, pFrameInfo, lReserved1, lReserved2):
        # Note: frame rate can drop to 1 frame per few seconds in night time, 
        # due to camera decide exposure time        
        try:
            frameInfo = pFrameInfo.contents
            self.callbackcnt += 1
            t0=time.time()            
            if frameInfo.lHeight < 1 or frameInfo.lWidth < 1:
                print('frameInfo.lHeight = %s,frameInfo.lWidth = %s' % (frameInfo.lHeight, frameInfo.lWidth))

            if lSize < (frameInfo.lHeight * frameInfo.lWidth / 2) + (frameInfo.lHeight * frameInfo.lWidth):
                print('Size of YUV = %s' % lSize)
                
            pRGB = yuv2rgb.YUVToRGB(pBuffer, frameInfo.lHeight, frameInfo.lWidth, 0)
            rgb = np.ndarray(buffer=(c_ubyte * frameInfo.lHeight * frameInfo.lWidth * 3).from_address(addressof(pRGB.contents)),
                             dtype=np.uint8, shape=(frameInfo.lHeight, frameInfo.lWidth, 3))
            RGB = rgb.copy()
            yuv2rgb.FreeMem()
            if True or frameInfo.dwFrameNum % 2 == 0:
                size = RGB.shape[0] * RGB.shape[1] * RGB.shape[2]
                self.map[0:(size)] = RGB.tobytes()
            
            cv2.imshow('',RGB)
            cv2.waitKey(10)

        except Exception as e:
            print('Exception in decode callback', e.message)
            
    def realDataCallBack(self, lRealHandle, dwDataType, pBuffer, dwBufSize, dwUser):
        try:
            if dwDataType == td.NET_DVR_SYSHEAD:
                
                hWnd = wintypes.HWND()
                if not playCtrl.PlayM4_GetPort(self.lPort):
                    print("1: Error:%r" % playCtrl.PlayM4_GetLastError(self.lPort[0]))
                    return 0
                print("lPort:%r" % self.lPort[0])
                
                if dwBufSize > 0:
                    res = playCtrl.PlayM4_SetStreamOpenMode(self.lPort[0], td.STREAME_REALTIME)
                    if not res:
                        print("2: Error:%r" % playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        return 0
                    
                    b_res = playCtrl.PlayM4_OpenStream(self.lPort[0], pBuffer, dwBufSize, 1024 * 100000)
                    if not b_res:
                        print("3: Error:%r" % playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()

                    b_res = playCtrl.PlayM4_SetDecCBStream(self.lPort[0], 1)  # 1 is Video Stream
                    if not b_res:
                        print("4: Error:%r" % playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()
                    
                    if not playCtrl.PlayM4_SetDecodeFrameType(self.lPort[0], td.DECODE_NORMAL):
                        print("5: Error:%r" % playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()

                    if not playCtrl.PlayM4_SetDecCallBack(self.lPort[0], self.fSetDecCallBack):
                        print("7: Error:%r" % playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()
                    if not playCtrl.PlayM4_Play(self.lPort[0], hWnd):
                        print("8: Error:%r" % playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()
                    
            elif dwDataType == td.NET_DVR_STREAMDATA:
                if dwBufSize > 0 & self.lPort[0] != -1:                    
                    # Put encoded video streaming package into decoder
                    b_res = playCtrl.PlayM4_InputData(self.lPort[0], pBuffer, dwBufSize)
                    if not b_res:
                        print ('Error in PlayM4_InputData')
                        quit()
            return 1
        except Exception as e:
            print('Exception in real callback', e.message)
            quit()

    def py_ExceptionCallBack(self, dwType, lUserID, lHandle, pUser):
        print("NET_DVR ERROR CODE: %r" % netsdk.NET_DVR_GetLastError())
        return 0

def gui_process(action_q):
    def up():
        if not action_q.full():
            action_q.put(NET_DVR_TILT_UP)
    def down():
        if not action_q.full():
            action_q.put(NET_DVR_TILT_DOWN)
    def left():
        if not action_q.full():
            action_q.put(NET_DVR_PAN_LEFT)
    def right():
        if not action_q.full():
            action_q.put(NET_DVR_PAN_RIGHT)

    root=tk.Tk()
    root.geometry("+70+960")
    root.resizable(0,0)
    btns = []
    btns.append(tk.Button(root,text=''))
    btns.append(tk.Button(root,text=u'\u2B05',command=left))  # left arrow
    btns.append(tk.Button(root,text=u"\u2B06",command=up))    # up arow
    btns.append(tk.Button(root,text='',))
    btns.append(tk.Button(root,text=''))
    btns.append(tk.Button(root,text=u'\u27A1',command=right)) #right arrow
    btns.append(tk.Button(root,text=''))
    btns.append(tk.Button(root,text=u'\u2B07',command=down))  # down arrow
    btns.append(tk.Button(root,text=''))

    for item in btns:
        item.config(width=6)
    
    btns[2].grid(row = 0, column = 1, padx=4, pady=4)
    btns[1].grid(row = 1, column = 0, padx=4, pady=4)
    btns[5].grid(row = 1, column = 2, padx=4, pady=4)
    btns[7].grid(row = 2, column = 1, padx=4, pady=4)
    
    root.mainloop()

if __name__ == '__main__':
    action_q = mp.Queue(2)
    gui_proc = mp.Process(target=gui_process, args=(action_q,))
    gui_proc.daemon = True
    gui_proc.start()

    ipcam = HikVision()
    ipaddr = "192.168.88.249"
    ipport = "8000"
    userName = "admin"
    password = "insight108!"
    ipcam.vis_init(ipaddr, ipport, userName, password)
    ipcam.login()
    while True:
        action = action_q.get()
        print 'action', action
        t0 = time.time()
        netsdk.NET_DVR_PTZControl(ipcam.lRealPlayHandle, 
                                    action, 
                                    NET_DVR_START)
        time.sleep(0.2)
        netsdk.NET_DVR_PTZControl(ipcam.lRealPlayHandle, 
                                    action, 
                                    NET_DVR_STOP)
        print 'stop', int(1000*(time.time() - t0)), 'ms'

