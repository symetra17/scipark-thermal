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
    '''
    - Connect visible IP camera and get picture data(YUV).
    - Convert YUV to RGB through YUV2RGB.dll
    '''

    def __init__(self):
        
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
        
        self.netsdk.NET_DVR_Login_V30.argtypes = [c_char_p, wintypes.WORD, c_char_p, c_char_p,
                                                  POINTER(td.NET_DVR_DEVICEINFO_V30)]
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
        self.netsdk.NET_DVR_RealPlay_V30.argtypes = [c_long, POINTER(td.NET_DVR_CLIENTINFO), 
                                                     POINTER(td.FREALDATACALLBACK), c_void_p, c_bool]

        self.lRealPlayHandle = self.netsdk.NET_DVR_RealPlay_V30(self.lUserID, self.ClientInfo, None, None, 0)

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
    #    # Note: frame rate can drop to 1 frame per few seconds in night time, 
    #    # due to camera decide exposure time        
    #    try:
    #        frameInfo = pFrameInfo.contents
    #        self.callbackcnt += 1
    #        t0=time.time()            
    #        if frameInfo.lHeight < 1 or frameInfo.lWidth < 1:
    #            print('frameInfo.lHeight = %s,frameInfo.lWidth = %s' % (frameInfo.lHeight, frameInfo.lWidth))
    #
    #        if lSize < (frameInfo.lHeight * frameInfo.lWidth / 2) + (frameInfo.lHeight * frameInfo.lWidth):
    #            print('Size of YUV = %s' % lSize)
    #            
    #        pRGB = self.yuv2rgb.YUVToRGB(pBuffer, frameInfo.lHeight, frameInfo.lWidth, 0)
    #        rgb = np.ndarray(buffer=(c_ubyte * frameInfo.lHeight * frameInfo.lWidth * 3).from_address(addressof(pRGB.contents)),
    #                         dtype=np.uint8, shape=(frameInfo.lHeight, frameInfo.lWidth, 3))
    #        RGB = rgb.copy()
    #        self.yuv2rgb.FreeMem()
    #        if True or frameInfo.dwFrameNum % 2 == 0:
    #            size = RGB.shape[0] * RGB.shape[1] * RGB.shape[2]
    #            #self.map[0:(size)] = RGB.tobytes()
    #        
    #        cv2.imshow('',RGB)
    #        cv2.waitKey(10)
    #
    #    except Exception as e:
    #        print('Exception in decode callback', e.message)
        pass
        
    def realDataCallBack(self, lRealHandle, dwDataType, pBuffer, dwBufSize, dwUser):
    
        if dwDataType == td.NET_DVR_SYSHEAD or dwDataType == td.NET_DVR_STREAMDATA:
            if dwBufSize > 0:
                    buff = bytearray(ctypes.string_at(pBuffer, dwBufSize))
                    
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
                    
                    b_res = self.playCtrl.PlayM4_OpenStreamEx(self.lPort[0], pBuffer, dwBufSize, 1024 * 100000)
                    if not b_res:
                        print("3: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        return 0

                    b_res = self.playCtrl.PlayM4_SetDecCBStream(self.lPort[0], 1)  # 1 is Video Stream
                    if not b_res:
                        print("4: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                    
                    if not self.playCtrl.PlayM4_SetDecodeFrameType(self.lPort[0], td.DECODE_KEY_FRAME):  #td.DECODE_NORMAL
                        print("5: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))

                    if not self.playCtrl.PlayM4_SetDecCallBack(self.lPort[0], self.fSetDecCallBack):
                        print("7: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                    
                    if not self.playCtrl.PlayM4_Play(self.lPort[0], hWnd):
                        print("8: Error:%r" % self.playCtrl.PlayM4_GetLastError(self.lPort[0]))
                        return 0
                    
            elif dwDataType == td.NET_DVR_STREAMDATA:
                if dwBufSize > 0 & self.lPort[0] != -1:                    
                    # Put encoded video streaming package into decoder
                    b_res = self.playCtrl.PlayM4_InputData(self.lPort[0], pBuffer, dwBufSize)
                    if not b_res:
                        #print ('Error in PlayM4_InputData')
                        return 0
            return 1
        except Exception as e:
            print('Exception in real callback', e.message)

    def py_ExceptionCallBack(self, dwType, lUserID, lHandle, pUser):
        print("NET_DVR Error ERROR CODE: %r" % self.netsdk.NET_DVR_GetLastError())
        return 0

def decodeCallBack(lPort, pBuffer, lSize, pFrameInfo, lReserved1, lReserved2):
        # Note: frame rate can drop to 1 frame per few seconds in night time, 
        # due to camera decide exposure time        
        
        frameInfo = pFrameInfo.contents
        
        print 'Height = %s, Width = %s' % (frameInfo.lHeight, frameInfo.lWidth)
        #print('Size of YUV420 = %s' % lSize)
        h = frameInfo.lHeight
        w = frameInfo.lWidth
        
        npa = np.ctypeslib.as_array(pBuffer, (lSize,1))
        end = (h*w)
        y = npa[0:end].copy()
        y = y.reshape((h,w))
        
        start = end
        end = end + (h//2)*(w//2)
        
        u = npa[start:end]
        u = u.reshape((h//2),(w//2))
        u = cv2.resize(u, None, fx=2, fy=2, 
                interpolation=cv2.INTER_NEAREST)
        
        start = end
        end = end + (h//2)*(w//2)

        v = npa[start:end]
        v = v.reshape((h//2),(w//2))
        v = cv2.resize(v, None, fx=2, fy=2, 
                interpolation=cv2.INTER_NEAREST)
        
        yuv = cv2.merge((y,u,v))
        bgr = cv2.cvtColor(yuv, cv2.COLOR_YCrCb2BGR)
        
        cv2.imshow('', bgr)
        cv2.waitKey(20)

            
if __name__ == '__main__':
      
    player = windll.LoadLibrary('PlayCtrl.dll')
    
    hWnd = wintypes.HWND()
    lPort = pointer(c_long())
    if not player.PlayM4_GetPort(lPort):
        print("1: Error:%r" % player.PlayM4_GetLastError(lPort[0]))
        quit()
    
    res = player.PlayM4_SetStreamOpenMode(lPort[0], td.STREAME_REALTIME)
    if not res:
        print("2: Error:%r"%player.PlayM4_GetLastError(lPort[0]))
        quit()

    fid=open('video.mp4','rb')
    str1 = fid.read(40)
    b_str1 = bytes(str1)
    xxx = ctypes.c_char_p(b_str1)
    res = player.PlayM4_OpenStream(lPort[0], xxx, len(b_str1), 1024*1024)
    if not res:
        print("3: Error:%r"%player.PlayM4_GetLastError(lPort[0]))
        quit()
        
    fSetDecCallBack = td.FSETDECCALLBACK(decodeCallBack)
    res = player.PlayM4_SetDecCBStream(lPort[0], 1)  # 1 is Video Stream
    if not res:
        print("4: Error:%r"%player.PlayM4_GetLastError(lPort[0]))
        quit()      
    if not player.PlayM4_SetDecodeFrameType(lPort[0], td.DECODE_NORMAL):
        print("5: Error:%r" % player.PlayM4_GetLastError(lPort[0]))

    if not player.PlayM4_SetDecCallBack(lPort[0], fSetDecCallBack):
        print("7: Error:%r" % player.PlayM4_GetLastError(lPort[0]))
        quit()      
        
    if not player.PlayM4_Play(lPort[0], hWnd):
        print("8: Error:%r" % player.PlayM4_GetLastError(lPort[0]))
        quit()

    while True:
        print('feed')
        time.sleep(0.05)
        N = 4096*8
        str1 = fid.read(N)
        if len(str1)==0:
            break
        b_str1 = bytes(str1)
        xxx = ctypes.c_char_p(b_str1) 
        res = player.PlayM4_InputData(lPort[0], xxx, N)
        if not res:
            print('error in input data')
            quit()
    fid.close()
    
    