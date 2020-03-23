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


class HikVision(object):

    def __init__(self):
        self.nmap_fid = open("sharedmem.dat", "r+")
        self.map = mmap.mmap(self.nmap_fid.fileno(), 0)

        try:
            self.playCtrl = windll.LoadLibrary('PlayCtrl.dll')
        except Exception as e:
            print("Exception in loading PlayCtrl dll")
            print(e)
            os._exit(0)

        try:            
            self.netsdk = windll.LoadLibrary('HCNetSDK.dll')
        except Exception as e:
            print("Exception in loading HCNetSDK dll")
            print(e)
            os._exit(0)

        try:            
            self.yuv2rgb = windll.LoadLibrary('YUV2RGB.dll')
        except Exception as e:
            print("Exception in loading YUV2RGB dll")
            print(e)
            os._exit(0)

        self.lUserID = 0
        self.lPort = pointer(c_long())
        
        # Set Argument Types
        self.yuv2rgb.YUVToRGB.argtypes = [POINTER(c_ubyte), c_int, c_int, c_int]
        self.yuv2rgb.YUVToRGB.restype = POINTER(c_ubyte)

        # looks like not used
        self.playCtrl.PlayM4_GetLastError.argtypes = [c_long]
        self.playCtrl.PlayM4_GetPort.argtypes = [POINTER(c_long)]        
        self.playCtrl.PlayM4_SetStreamOpenMode.argtypes = [c_long, wintypes.DWORD]        
        self.playCtrl.PlayM4_OpenStreamEx.argtypes = [c_long, POINTER(wintypes.BYTE), wintypes.DWORD, wintypes.DWORD]        
        self.playCtrl.PlayM4_Play.argtypes = [c_long, wintypes.HWND]               
        self.playCtrl.PlayM4_GetSpecialData.argtypes = [c_long]
        self.playCtrl.PlayM4_SetDecCBStream.argtypes = [c_long, wintypes.DWORD]        
        self.playCtrl.PlayM4_SetDecodeFrameType.argtypes = [c_long, wintypes.DWORD]
        self.playCtrl.PlayM4_SetDecCallBack.argtypes = [c_long, td.FSETDECCALLBACK]
        self.playCtrl.PlayM4_InputData.argtypes = [c_long, POINTER(wintypes.BYTE), wintypes.DWORD]
        # Set Return Types
        self.playCtrl.PlayM4_GetLastError.restype = wintypes.DWORD
        self.playCtrl.PlayM4_GetPort.restype = c_bool
        self.playCtrl.PlayM4_SetStreamOpenMode.restype = c_bool
        self.playCtrl.PlayM4_OpenStreamEx.restype = c_bool
        self.playCtrl.PlayM4_Play.restype = c_bool
        self.playCtrl.PlayM4_InputData.restype = c_bool
        self.playCtrl.PlayM4_GetSpecialData.restype = wintypes.DWORD
        
        self.callbackcnt = 0
        self.flag_request_img = False


    def vis_init(self, ip, port, username, password, smokeDetect=False, streamChnl='main'):
        self.ipaddr = ip
        self.port = int(port)
        self.username = username
        self.password = password

        #For Visable camera variable
        self.fSetDecCallBack = td.FSETDECCALLBACK(self.decodeCallBack)
        self.netsdk.NET_DVR_Init.restype = c_bool   
        self.netsdk.NET_DVR_SetConnectTime.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.netsdk.NET_DVR_SetConnectTime.restype = c_bool 
        self.netsdk.NET_DVR_SetReconnect.argtypes = [wintypes.DWORD, c_bool]
        self.netsdk.NET_DVR_SetReconnect.restype = c_bool      
        if not self.netsdk.NET_DVR_Init():
            print("NET_DVR_Init Error")
            sys.exit(0)
        if not self.netsdk.NET_DVR_SetConnectTime(2000, 1):
            print("NET_DVR_SetConnectTime Error")
            sys.exit(0)
        if not self.netsdk.NET_DVR_SetReconnect(10000, True):
            print("NET_DVR_SetReconnect Error")
            sys.exit(0)

        self.fRealDataCallBack = td.FREALDATACALLBACK(self.realDataCallBack)
        self.fExceptionCallBack = td.FEXCEPTIONCALLBACK(self.py_ExceptionCallBack)
                    
        # Start Error Message Reporting Callback
        self.netsdk.NET_DVR_SetExceptionCallBack_V30(0, None, self.fExceptionCallBack, None)
        
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
        self.lUserID = 0
        #self.netsdk.NET_DVR_Login_V30.argtypes = [c_char_p, wintypes.WORD, c_char_p, c_char_p,
        #                                          POINTER(td.NET_DVR_DEVICEINFO_V30)]
        self.lUserID = self.netsdk.NET_DVR_Login_V30(self.ipaddr, self.port, self.username, self.password, 
                                                    byref(struDeviceInfo))
        if self.lUserID < 0:
            print("Camera Login Failed", self.ipaddr, self.port, self.username, self.password)
            self.netsdk.NET_DVR_Cleanup()
            return {'status': 'ERR'}
        elif self.lUserID >= 0:
            self.ts_diff = time.time()
            print("Camera Login Successful  Camera IP: " + self.ipaddr + ":" + str(self.port))
            self.start()
        return {'status': 'OK'}
    
    def start(self):
        self.lRealPlayHandle = 0
        
        #int NET_DVR_RealPlay_V30(int iUserID, ref NET_DVR_CLIENTINFO lpClientInfo, 
        #                                           REALDATACALLBACK fRealDataCallBack_V30, 
        #                                           IntPtr pUser, 
        #                                           UInt32 bBlocked);
        self.netsdk.NET_DVR_RealPlay_V30.argtypes = [c_long, POINTER(td.NET_DVR_CLIENTINFO), 
                                                     POINTER(td.FREALDATACALLBACK), c_void_p, c_uint32]

        self.lRealPlayHandle = self.netsdk.NET_DVR_RealPlay_V30(self.lUserID, self.ClientInfo, 
                                                                    None, None, 0)        
        if self.lRealPlayHandle < 0:
            print('error realplayhandle < 0')
            self.logout()
            quit()
        self.netsdk.NET_DVR_SetRealDataCallBack.argtypes = [c_long, 
                                                        td.FREALDATACALLBACK, wintypes.DWORD]
        result = self.netsdk.NET_DVR_SetRealDataCallBack(self.lRealPlayHandle,
                                                         self.fRealDataCallBack, 0)
        if not result:
            print("SET_DVR_SetRealDataCallBack failed")
            quit()

    def stop(self):
        print("Stop real play function")
        self.netsdk.NET_DVR_StopRealPlay.argtypes = [c_long]
        self.netsdk.NET_DVR_StopRealPlay(self.lRealPlayHandle)
        
        if not self.playCtrl.PlayM4_FreePort(self.lPort[0]):
            print('Free real play port not success')
        else:
            self.lPort[0] = -1
        
    def logout(self):
        print("Logout IPC camera")
        self.stop()
        self.netsdk.NET_DVR_Logout_V30.argtypes = [c_long]
        self.netsdk.NET_DVR_Logout_V30(self.lUserID)
        self.netsdk.NET_DVR_Cleanup()      
    
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
                
            pRGB = self.yuv2rgb.YUVToRGB(pBuffer, frameInfo.lHeight, frameInfo.lWidth, 0)
            rgb = np.ndarray(buffer=(c_ubyte * frameInfo.lHeight * frameInfo.lWidth * 3).from_address(addressof(pRGB.contents)),
                             dtype=np.uint8, shape=(frameInfo.lHeight, frameInfo.lWidth, 3))
            RGB = rgb.copy()
            self.yuv2rgb.FreeMem()
            if True or frameInfo.dwFrameNum % 2 == 0:
                size = RGB.shape[0] * RGB.shape[1] * RGB.shape[2]
                self.map[0:(size)] = RGB.tobytes()
            
            #cv2.imshow('',RGB)
            #cv2.waitKey(10)

        except Exception as e:
            print('Exception in decode callback', e.message)
            
    def realDataCallBack(self, lRealHandle, dwDataType, pBuffer, dwBufSize, dwUser):
        try:
            if dwDataType == td.NET_DVR_SYSHEAD:
                
                hWnd = wintypes.HWND()
                if not self.playCtrl.PlayM4_GetPort(self.lPort):
                    print("1: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                    return 0
                print("lPort:%r" % self.lPort[0])
                
                if dwBufSize > 0:
                    res = self.playCtrl.PlayM4_SetStreamOpenMode(self.lPort[0], td.STREAME_REALTIME)
                    if not res:
                        print("2: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        return 0
                    
                    b_res = self.playCtrl.PlayM4_OpenStream(self.lPort[0], pBuffer, dwBufSize, 1024 * 100000)
                    if not b_res:
                        print("3: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()

                    b_res = self.playCtrl.PlayM4_SetDecCBStream(self.lPort[0], 1)  # 1 is Video Stream
                    if not b_res:
                        print("4: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()
                    
                    if not self.playCtrl.PlayM4_SetDecodeFrameType(self.lPort[0], td.DECODE_NORMAL):
                        print("5: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()

                    if not self.playCtrl.PlayM4_SetDecCallBack(self.lPort[0], self.fSetDecCallBack):
                        print("7: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()
                    if not self.playCtrl.PlayM4_Play(self.lPort[0], hWnd):
                        print("8: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        quit()
                    
            elif dwDataType == td.NET_DVR_STREAMDATA:
                if dwBufSize > 0 & self.lPort[0] != -1:                    
                    # Put encoded video streaming package into decoder
                    b_res = self.playCtrl.PlayM4_InputData(self.lPort[0], pBuffer, dwBufSize)
                    if not b_res:
                        print('Error in PlayM4_InputData')
                        quit()
            return 1
        except Exception as e:
            print('Exception in real callback', e.message)
            quit()

    def py_ExceptionCallBack(self, dwType, lUserID, lHandle, pUser):
        print("NET_DVR ERROR CODE: %r" % self.netsdk.NET_DVR_GetLastError())
        return 0


if __name__ == '__main__':
    ipcam = HikVision()
    ipaddr = "192.168.88.249"
    ipport = "8000"
    userName = "admin"
    password = "insight108!"
    ipcam.vis_init(ipaddr, ipport, userName, password)
    ipcam.login()
    while True:
        time.sleep(10)

