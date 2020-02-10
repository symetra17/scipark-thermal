#! /usr/bin/env python
# -*- coding: utf-8 -*-  
# The most useful windows datatypes
import ctypes
from ctypes import *
import enum
from ctypes import wintypes


BYTE = wintypes.BYTE
WORD = wintypes.WORD
DWORD = wintypes.DWORD

UINT = wintypes.UINT

#UCHAR = ctypes.c_uchar
CHAR = ctypes.c_char
WCHAR = ctypes.c_wchar
UINT = ctypes.c_uint
INT = ctypes.c_int

DOUBLE = ctypes.c_double
FLOAT = ctypes.c_float

BOOLEAN = BYTE
BOOL = ctypes.c_bool

class VARIANT_BOOL(ctypes._SimpleCData):
	_type_ = "v"
	def __repr__(self):
		return "%s(%r)" % (self.__class__.__name__, self.value)

ULONG = ctypes.c_ulong
LONG = ctypes.c_long

USHORT = ctypes.c_ushort
SHORT = ctypes.c_short

# in the windows header files, these are structures.
_LARGE_INTEGER = LARGE_INTEGER = ctypes.c_longlong
_ULARGE_INTEGER = ULARGE_INTEGER = ctypes.c_ulonglong

LPCOLESTR = LPOLESTR = OLESTR = ctypes.c_wchar_p
LPCWSTR = LPWSTR = ctypes.c_wchar_p
LPCSTR = LPSTR = ctypes.c_char_p
LPCVOID = LPVOID = ctypes.c_void_p

# WPARAM is defined as UINT_PTR (unsigned type)
# LPARAM is defined as LONG_PTR (signed type)
if ctypes.sizeof(ctypes.c_long) == ctypes.sizeof(ctypes.c_void_p):
	WPARAM = ctypes.c_ulong
	LPARAM = ctypes.c_long
elif ctypes.sizeof(ctypes.c_longlong) == ctypes.sizeof(ctypes.c_void_p):
	WPARAM = ctypes.c_ulonglong
	LPARAM = ctypes.c_longlong

ATOM = wintypes.WORD
LANGID = wintypes.WORD

COLORREF = wintypes.DWORD
LGRPID = wintypes.DWORD
LCTYPE = wintypes.DWORD

LCID = wintypes.DWORD

################################################################
# HANDLE types
HANDLE = ctypes.c_void_p # in the header files: void *

################################################################
# Pointer types

LPBOOL = PBOOL = ctypes.POINTER(BOOL)
PBOOLEAN = ctypes.POINTER(BOOLEAN)
LPBYTE = PBYTE = ctypes.POINTER(BYTE)
PCHAR = ctypes.POINTER(CHAR)
LPCOLORREF = ctypes.POINTER(COLORREF)
LPDWORD = PDWORD = ctypes.POINTER(wintypes.DWORD)
PFLOAT = ctypes.POINTER(FLOAT)
LPHANDLE = PHANDLE = ctypes.POINTER(HANDLE)
LPINT = PINT = ctypes.POINTER(INT)
PLARGE_INTEGER = ctypes.POINTER(LARGE_INTEGER)
PLCID = ctypes.POINTER(LCID)
LPLONG = PLONG = ctypes.POINTER(LONG)
PSHORT = ctypes.POINTER(SHORT)
LPUINT = PUINT = ctypes.POINTER(UINT)
PULARGE_INTEGER = ctypes.POINTER(ULARGE_INTEGER)
PULONG = ctypes.POINTER(ULONG)
PUSHORT = ctypes.POINTER(USHORT)
PWCHAR = ctypes.POINTER(WCHAR)
LPWORD = PWORD = ctypes.POINTER(wintypes.WORD)

################################################################
# Some important structure definitions
'''---------------------COX IR wintype defination------------------------------------------'''
class IRF_MESSAGE_TYPE_T(enum.Enum):
		_IRF_ACK = 0
		_IRF_NAK = 1
		_IRF_ALIVE = 2
		_IRF_STREAM_ON =3
		_IRF_STREAM_OFF=4
		_IRF_STREAM_DATA=5
		_IRF_BROADCAST=6
		_IRF_REQ_CAM_DATA=7		# Request all camera setting value.
		_IRF_CAM_DATA=8			# Received all camera setting value.
		_IRF_SAVE_CAM_DATA=9		# Request to do save camera setting value.
		_IRF_SET_CAM_DATA=10		# Set camera unit function setting.
		_IRF_SET_USER_PALETTE=11	# User color palette update. (pc --> cam)
		_IRF_REQ_SYS_INFO=12		# Request System Information. (pc --> cam)
		_IRF_SYS_INFO=13			# Get System Information.	(cam --> pc)

class strSPOT(Structure):
	_fields_ = [('enable',c_ubyte),
				('x',c_ushort),
				('y',c_ushort),
				('local',c_ubyte),
				('em',c_ubyte),
				('tr',c_ubyte),
				('at',c_short),
				('reserved', c_ubyte * 6)
			]

class CG_ROI(Structure):
	_fields_ = [('mode',c_ubyte),
				('temp_type',c_ubyte),
				('x',c_ushort),
				('y',c_ushort),
				('w',c_ushort),
				('h',c_ushort),
				('f_corr',c_ubyte),
				('em',c_ubyte),
				('tr',c_ubyte),
				('at',c_short),
				('reserved',c_ubyte)			
			]

class CG_ISO(Structure):
	_fields_ = [('mode_mask',c_ubyte),
				('tran_mask',c_ubyte),
				('max_temp',c_short),
				('min_temp',c_short),
				('above_color',c_uint32),
				('below_color',c_uint32),
				('between_color',c_uint32)
			]
	
class strISO(Structure):
	_fields_ = [('enable',c_ubyte),
				('seed_color',c_uint),
				('top',c_short),
				('bottom',c_short),
				('reserved', c_ubyte * 3)
			]

class roi(Structure):
	_fields_ = [('flag',c_ubyte),
				('x1',c_ushort),
				('y1',c_ushort),
				('x2',c_ushort),
				('y2', c_ushort)
			]
		
	
class IRF_SAVEDATA_T(Structure):
	_fields_ = [('crc',c_uint),
				('ver',c_ubyte),
				('sensor',c_ubyte),
				('tv',c_ubyte),
				('temp_mode',c_ubyte),
				('id',c_ubyte),
				('baudrate',c_ubyte),
				('level',c_short),
				
				('span',c_ushort),
				('agc',c_ubyte),
				('invert',c_ubyte),
				('mirror',c_ubyte),
				('flip',c_ubyte),
				('colorbar',c_ubyte),
				('showinfo',c_ubyte),
				('indicator',c_ubyte),
				('unit',c_ubyte),
				('dhcp',c_ubyte),
				('color',c_ubyte),
				('alpha',c_ubyte),
				('zoom',c_ubyte),
				('sharp',c_ubyte),
				
				('noise',c_ubyte),
				('nuc',c_ushort),
				('econt',c_ubyte),
				('ipaddr',c_uint),
				('netmask',c_uint),
				('gateway',c_uint),
				('dns',c_uint),
				('alarm1_func',c_ubyte),
				('alarm1_cond',c_ubyte),
				('alarm1_value',c_short),
				('alarm2_func',c_ubyte),
				('alarm2_cond',c_ubyte),
				('alarm2_value',c_short),
				('down_filter',c_ubyte),
				('show_center',c_ubyte),
				('show_spot',c_ubyte),
				('show_correction',c_ubyte),
				('show_isotherm',c_ubyte),
				('alarm1_duration',c_ubyte),
				('alarm2_duration',c_ubyte),
				
				('roi',roi*2),
				('reserved1',c_ubyte*48),
				
				('limit9', c_ubyte),
				('enable_high', c_ubyte),
				('correction', c_ubyte),
				('emissivity', c_ubyte),
				('transmission', c_ubyte),
				('atmosphere', c_short),
				
				('spot', strSPOT*10),
				('iso', strISO*3),
				('reserved2',c_ubyte*53),
				('reserved3',c_ubyte*128)

			]
class ALRMCFG(Structure):
	_fields_ = [('f_enable',c_ubyte),
				('output_mask',c_ubyte),
				('cond',c_ubyte),
				('reserved',c_ubyte),
				('temp',c_short),
				('delay',c_ushort),
			]
class temp_alarm(Structure):
	_fields_ = [('max_temp',ALRMCFG),
				('min_temp',ALRMCFG),
				('avg_temp',ALRMCFG),
				('ctr_temp',ALRMCFG),
				('roi_temp',ALRMCFG*10),
			]
class CG_IRF_SAVEDATA_T(Structure):
	_fields_ = [('crc',c_uint),
				('ver',c_ubyte),
				('sensor',c_ubyte),
				('tv',c_ubyte),
				('temp_mode',c_ubyte),
				('id',c_ubyte),
				('baudrate',c_ubyte),
				('level',c_short),
				
				('span',c_ushort),
				('agc',c_ubyte),
				('invert',c_ubyte),
				('mirror',c_ubyte),
				('flip',c_ubyte),
				('colorbar',c_ubyte),
				('showinfo',c_ubyte),
				('indicator',c_ubyte),
				('unit',c_ubyte),
				('dhcp',c_ubyte),
				('color',c_ubyte),
				('alpha',c_ubyte),
				('zoom',c_ubyte),
				('sharp',c_ubyte),
				
				('noise',c_ubyte),
				('nuc',c_ushort),
				('econt',c_ubyte),
				('ipaddr',c_uint),
				('netmask',c_uint),
				('gateway',c_uint),
				('dns',c_uint),
				('alarm1_func',c_ubyte),
				('alarm1_cond',c_ubyte),
				('alarm1_value',c_short),
				('alarm2_func',c_ubyte),
				('alarm2_cond',c_ubyte),
				('alarm2_value',c_short),
				('down_filter',c_ubyte),
				('show_center',c_ubyte),
				('show_spot',c_ubyte),
				('show_correction',c_ubyte),
				('show_isotherm',c_ubyte),
				('alarm1_duration',c_ubyte),
				('alarm2_duration',c_ubyte),
				
				('roi',roi*2),
				('f_disp_icon',c_ubyte),
				('brightness',c_ubyte),
				('contrast',c_ubyte),
				('f_edge_enhance',c_ubyte),
				('nuc_mode',c_ubyte),
				('nuc_time',c_ubyte),
				('nuc_thres',c_ushort),
				('agc_man_max',c_ushort),
				('agc_man_min',c_ushort),
				('srl_protocol',c_ubyte),			
				('scn0_l_margin',c_ushort),
				('scn0_r_margin',c_ushort),
				('scn0_t_margin',c_ushort),
				('scn0_b_margin',c_ushort),
				('scn1_l_margin',c_ushort),
				('scn1_r_margin',c_ushort),
				('scn1_t_margin',c_ushort),
				('scn1_b_margin',c_ushort),
				
				('hdmi_mode',c_ubyte),
				('alarm1_type',c_ubyte),
				('alarm1_mode',c_ubyte),
				('alarm1_dura',c_ubyte),
				('alarm1_remote_ctrl',c_ubyte),
				('alarm2_type',c_ubyte),
				('alarm2_mode',c_ubyte),
				('alarm2_dura',c_ubyte),
				('alarm2_remote_ctrl',c_ubyte),
				('zero_offset',c_short),
				('measure_distance',c_ushort),
				('nr1_strength',c_ubyte),
				('nr2_strength',c_ubyte),
				('ee_strength',c_ubyte),				
				
				('reserved1',c_ubyte*128),
				
				('limit9', c_ubyte),
				('enable_high', c_ubyte),
				('correction', c_ubyte),
				('emissivity', c_ubyte),
				('transmission', c_ubyte),
				('atmosphere', c_short),
				
				('spot', strSPOT*10),
				('cg_roi',CG_ROI*10),				
				('iso', strISO*3),
				('cg_iso',CG_ISO*2),
				('hdmi_list',c_ubyte*8),
					
				('reserved2',c_ubyte*256),
				('temp_alarm',temp_alarm),
				('reserved3',c_ubyte*128)
			]
class IRF_IR_CAM_DATA_T(Structure):
	_fields_ = [('ir_image',POINTER(c_ushort)),
				('image_buffer_size',c_ulong),
				('lpNextData',LPBYTE),
				('dwSize',c_ulong),
				('dwPosition',c_ulong),
				('msg_type',c_int),
				('save_data',IRF_SAVEDATA_T),
				('fw_ver',c_uint),
				('PMSGTYPE',c_ushort),
				('RCODE',c_ushort)
			]

class CG_IRF_MESSAGE_TYPE_T(enum.Enum):
	CG_IRF_NONE				= -1			#	No Received Packet
	CG_IRF_ACK				= 0			#	Receive Acknowledgement as a result of request
	CG_IRF_NAK				= 1			#	Receive Negative Acknowledgement as a result of request
	CG_IRF_ALIVE			= 2			#	Send Alive Message
	CG_IRF_STREAM_ON		= 3			#	Request to start raw data transfer.
	CG_IRF_STREAM_OFF		= 4			#	Request to stop raw data transfer.
	CG_IRF_STREAM_DATA		= 5			#	Receive raw data
	CG_IRF_REQ_CAM_DATA		= 7			#	Request a camera configuration data.
	CG_IRF_CAM_DATA			= 8			#	Receive a camera configuration data as a result of request.
	CG_IRF_SET_CAM_DATA		= 10			#	Request camera to save one of various setting CMD_xxxx.
	CG_IRF_SET_USER_PALETTE	= 11			#	User color palette update. (pc --> cam)
	CG_IRF_REQ_SYS_INFO		= 12			#	Request System Information. (pc --> cam)
	CG_IRF_SYS_INFO			= 13			#	Receive System Information as a result of request.	(cam --> pc)
	CG_IRF_SPOT_STREAM_ON	= 14			#	Request to start spot streaming transfer.
	CG_IRF_SPOT_STREAM_OFF	= 15			#	Request to stop spot streaming transfer.
	CG_IRF_SPOT_STREAM_DATA	= 16			#	Receive spot streaming data.
	CG_IRF_REQ_TEMP_TABLE	= 19			#	Request temperature and offset table. (pc --> cam)




class CG_IRF_IR_CAM_DATA_T(Structure):
	_fields_ = [('ir_image',POINTER(c_ushort)),
				('image_buffer_size',c_ulong),
				('lpNextData',LPBYTE),
				('dwSize',c_ulong),
				('dwPosition',c_ulong),
				('msg_type',c_int),
				('save_data',CG_IRF_SAVEDATA_T),
				('fw_ver',c_uint),
				('PMSGTYPE',c_ushort),
				('RCODE',c_ushort)
			]


class IRF_AUTOMATIC_TYPE_T(enum.Enum):
	_IRF_AUTO = 0
	_IRF_MANUAL = 1
	
class IRF_AUTO_RANGE_INPUT_METHOD_T(enum.Enum):
	_IRF_MIN_MAX = 0
	_IRF_BRIGHTNESS_RATE = 1
	_IRF_SD_RATE = 2
	_IRF_AUTO_BRIGHT= 3
	
class IRF_AUTO_RANGE_OUTPUT_METHOD_T(enum.Enum):
	_IRF_LINEAR= 0				# Linear method. (contrast + brightness)
	_IRF_NON_LINEAR = 1			# Non-Linear method. (Gamma function)
	_IRF_TPE = 2				# Tail-less Plateau Equalization.
	_IRF_APE =3					# Adaptive Plateau Equalization.
	_IRF_SAPE = 4				# Self-adaptive plateau equalization.
	

class IRF_AUTO_RANGE_METHOD_T(Structure):
	_fields_ = [('autoScale',c_int),
				('inputMethod',c_int),
				('outputMethod',c_int),
				('B_Rate',c_float),
				('SD_Rate',c_float),
				('intercept',BYTE),
				('gamma',c_float),
				('plateau',UINT),
				('epsilon',c_float),
				('psi',c_float),
				('prevPalteau',c_float)
				
			]
class IRF_TEMP_CORRECTION_PAR_T(Structure):
	_fields_ = [('emissivity',c_float),
				('atmTemp',c_float),
				('atmTrans',c_float)
			]

class IRF_IMAGE_INFO_T(Structure):
	_fields_ = [('xSize',c_ushort),
				('ySize',c_ushort)
			]
	
class IRF_DYNAMIC_RANGE_T(enum.Enum):
	_IRF_LOW_RANGE = 0		# -20 ~ 120;
	_IRF_MIDDLE_RANGE = 1	# -20 ~ 650;
	_IRF_HIGH_RANGE = 2		# 
	


class CAMMAND_CODE(enum.Enum):
	CMD_AGC=				0x0101		#	AGC On/OFF								( CX, CG )
										#	CX RCODE  => 0 : OFF, 1 : HISTOGRAM, 2 : BRIGHTNESS
										#	CG RCODE  => 0 : MANUAL, 1 : AUTO

	CMD_LEVEL=				0x0102		#	LEVEL									( CX )
										#	RCODE  => -20 ~ 120

	CMD_CG_BRIGHT=			0x0102		#	BRIGHTNESS								( CG )
										#	RCODE  => -40 ~ 40

	CMD_SPAN=				0x0103		#	SPAN									( CX )
										#	RCODE  => 10 ~ 100

	CMD_CG_CONTRAST=		0x0103		#	CONTRAST								( CG )
										#	RCODE  => -10 ~ 10

	CMD_PALETTE=			0x0105		#	PALETTE									( CX, CG )
										#	RCODE  => IRF_CAM_PALETTE_TYPE_T

	CMD_INVERT=				0x0106		#	INVERT									( CX, CG )
										#	CX RCODE  => 0 : OFF, 1 : ON
										#	CG RCODE  => 0 : OFF, 1 : LUMA, 2 : CHROMA, 3 : L + C

	CMD_MIRROR=				0x0107		#	MIRROR									( CX, CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_FLIP=				0x0108		#	FLIP									( CX, CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_ZOOM=				0x0109		#	ZOOM									( CX, CG )
										#	RCODE  => 0 : OFF, 1 : x2, 2 : x4

	CMD_NOISE_FILTER=		0x010A		#	NOISE FILTER							( CX, CG )
										#	CX RCODE  => 0 : OFF, 1 : SLIGHT, 2 : STRONG, 3 : MEDIAN, 4 : GAUSSIAN
										#	CG RCODE  => 0 : OFF, 1 : NR1, 2 : NR2, 3 : NR1 + NR2

	CMD_EDGE_FILTER=		0x010B		#	EDGE FILTER								( CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_NR1_LEVEL=			0x010C		# CG MODEL ONLY							( CG )
										#	RCODE	: NR1 LEVEL	(0 : LOWEST, 1 : LOW, 2 : MIDDLE, 3 : HIGH, 4 : HIGHEST)

	CMD_NR2_LEVEL=			0x010D		# CG MODEL ONLY							( CG )
										#	RCODE	: NR2 LEVEL	(0 : LOWEST, 1 : LOW, 2 : MIDDLE, 3 : HIGH, 4 : HIGHEST)

	CMD_EE_LEVEL=			0x010E		# CG MODEL ONLY							( CG )
										#	RCODE	: EE LEVEL	(0 : LOWEST, 1 : LOW, 2 : MIDDLE, 3 : HIGH, 4 : HIGHEST)

	CMD_COLORBAR=			0x0201		#	DISPLAY COLOR-BAR						( CX, CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_TEMP_VIEW=			0x0202		#	DISPLAY TEMPERATURE INFORAMTION			( CX, CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_TEMP_INDICATOR=		0x0203		#	DISPLAY HOT/COLD INDICATOR				( CX, CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_TEMP_TYPE=			0x0204		#	TEMPERATURE UNIT						( CX, CG )
										#	RCODE  => 0 : CELSIUS, 1 : FAHRENHEIT

	CMD_TRANSPARENCY=		0x0205		#	OSD MENU ALPHA BLENDING					( CX, CG )
										#	RCODE  => 0 : OFF, 1 : 20%, 2 : 40%, 3 : 60%, 4 : 80%

	CMD_CENTER_CROSS=		0x0206		#	DISPLAY CENTER-CROSS					( CX, CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_SPOT_INFO=			0x0207		#	DISPLAY SPOT INFORMATION				( CX )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_CG_ROI_INFO=		0x0207		#	DISPLAY ROI INFORMATION					( CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_SHOW_CORR=			0x0208		#	DISPLAY CORRECTION INFORMATION			( CX, CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_SHOW_ICON=			0x0209		#	DISPLAY ICON							( CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_ETHERNET=			0x0301		#	NETWORK CONFIG							( CX, CG )
										#	RCODE  => 0 : DHCP OFF, 1 : DHCP ON
										#	RCODE2 => IP Address
										#	RCODE3 => Subnet Mask
										#	RCODE4 => Gateway

	CMD_PROTOCOL=			0x0305		#	SERIAL PROTOCOL							( CG )
										#	RCODE  => 0 : Pelco-D, 1 : COX

	CMD_CAM_ID=				0x0306		#	RS485 CAMERA ID							( CX, CG )
										#	RCODE  => 1 ~ 255

	CMD_BAUDRATE=			0x0307		#	SERIAL BAUDRATES						( CX, CG )
										#	CX RCODE  => 0 : 2400, 1 : 4800, 2 : 9600, 3 : 19200, 4 : 38400
										#	CG RCODE  => 0 : 2400, 1 : 4800, 2 : 9600, 3 : 19200, 4 : 38400, 5 : 57600, 6 : 115200

	CMD_ALARM1_RMC=			0x0401		#	ALARM01 REMOTE CONTROL					( CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_ALARM1_FUNC=		0x0401		#	ALARM01 FUNCTION						( CX )
										#	RCODE  => 0 : OFF, 1 : CENTER, 2 : MEAN, 3 : MAX, 4 : MIN, 5 : ON

	CMD_ALARM1_COND=		0x0402		#	ALARM01 CONDITION						( CX )
										#	RCODE  => 0 : ABOVE, 1 : BELOW

	CMD_ALARM1_VAL=			0x0403		#	ALARM01 VALUE							( CX )
										#	RCODE  => -20 ~ 120

	CMD_ALARM2_RMC=			0x0404		#	ALARM02 REMOTE CONTROL					( CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_ALARM2_FUNC=		0x0404		#	ALARM02 FUNCTION						( CX )
										#	RCODE  => 0 : OFF, 1 : CENTER, 2 : MEAN, 3 : MAX, 4 : MIN, 5 : ON

	CMD_ALARM2_COND=		0x0405		#	ALARM02 CONDITION						( CX )
										#	RCODE  => 0 : ABOVE, 1 : BELOW

	CMD_ALARM2_VAL=			0x0406		#	ALARM02 VALUE							( CX )
										#	RCODE  => -20 ~ 120

	CMD_ALARM1_DUR=			0x0407		#	ALARM01 DURATION						( CX )
										#	RCODE  => 0 ~ 99

	CMD_ALARM2_DUR=			0x0408		#	ALARM02 DURATION						( CX )
										#	RCODE  => 0 ~ 99

	CMD_ALARM1_ROI=			0x0409		#	ALARM01 ROI								( CX )
	CMD_ALARM2_ROI=			0x040A		#	ALARM02 ROI								( CX )
										#	RCODE  => [31:2] : Not used
										#			     [1] : 0 Include ROI, 1 Exclude ROI
										#			     [0] : 0 Full Screen, 1 ROI
										#	CX320 RCODE2 => [31:24] : y2 point (half of the real coordinate)
										#					[23:16] : x2 point (half of the real coordinate)
										#					[15: 8] : y1 point (half of the real coordinate)
										#					[ 7: 0] : x1 point (half of the real coordinate)
										#	CX640 RCODE2 => [31:16] : y1 point (the real coordinate)
										#					[15: 0] : x1 point (the real coordinate)
										#	CX640 RCODE3 => [31:16] : y2 point (the real coordinate)
										#					[15: 0] : x2 point (the real coordinate)

	CMD_ALARM_CONFIG=		0x0411		#	ALARM OUTPUT CONFIG						( CG )
										#	RCODE  => 0 : ALARM01, 1 : ALARM02
										#	RCODE2 => [31:24] ALARM TYPE ( NO = 0,  NC = 1 )
										#	RCODE2 => [23:16] ALARM MODE ( OFF = 0, STABILIZE = 1, ALIVE PWM = 2, TEMPERATURE = 3, TEST ALARM ON = 4, TEST ALARM OFF = 5 )
										#	RCODE2 => [15:8]  ALARM DURATION ( 0~ 99 )
										#	RCODE2 => [7:0]	  ALARM REMOTE CONTROL ( 0 : OFF, 1 : ON )

	CMD_ALARM01_TYPE=		0x0412		#	ALARM01 TYPE							( CG )
										#	RCODE  => 0 : NO, 1 : NC

	CMD_ALARM01_MODE=		0x0413		#	ALARM01 MODE							( CG )
										#	RCODE  => 0 : OFF, 1 : STABILIZE, 2 : ALIVE PWM, 3 : TEMPERATURE, 4 : TEST ALARM ON, 5 : TEST ALARM OFF

	CMD_ALARM01_DURA=		0x0414		#	ALARM01 DURATION						( CG )
										#	RCODE  => 0 ~ 99

	CMD_ALARM01_RMCT=		0x0415		#	ALARM01 REMOTE CONTROL					( CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_ALARM02_TYPE=		0x0416		#	ALARM02 TYPE							( CG )
										#	RCODE  => 0 : NO, 1 : NC

	CMD_ALARM02_MODE=		0x0417		#	ALARM02 MODE							( CG )
										#	RCODE  => 0 : OFF, 1 : STABILIZE, 2 : ALIVE PWM, 3 : TEMPERATURE, 4 : TEST ALARM ON, 5 : TEST ALARM OFF

	CMD_ALARM02_DURA=		0x0418		#	ALARM02 DURATION						( CG )
										#	RCODE  => 0 ~ 99

	CMD_ALARM02_RMCT=		0x0419		#	ALARM02 REMOTE CONTROL					( CG )
										#	RCODE  => 0 : OFF, 1 : ON

	CMD_ALARM_TEMPCFG=		0x0421		#	ALARM TEMPERATURE CONFIG				( CG )
										#	RCODE  => MAX : 0, MIN : 1, AVG : 2, CTR : 3, ROI_01 : 11 ~ ROI_10 : 20
										#	RCODE2 => [31:24] ALARM Enable 0 or 1
										#	RCODE2 => [23:16] ALARM-Output Mask ( ALARM01 : 0x01, ALARM02 : 0x02 )
										#	RCODE2 => [15:8]  ALARM Condition ( 0 : Above, 1 : Below )
										#	RCODE3 => [31:16] ALARM-IN DURATION ( 0 ~ 1800 )
										#	RCODE3 => [15:0]  ALARM Temperature

	CMD_ROI_COORCFG=		0x0422		#	ROI COORDINATE CONFIG					( CG )
										#	RCODE  => [15:8]  ROI_01 : 11 ~ ROI_10 : 20
										#	RCODE  => [7:0]   ROI Mode ( 0 : OFF, 1 : SPOT, 2 : RECT )
										#	RCODE2 => [31:16] ROI X Position ( QVGA : 0 ~ 383, VGA : 0 ~ 639 )
										#	RCODE2 => [16:0]  ROI Y Position ( QVGA : 0 ~ 287, VGA : 0 ~ 479 )
										#	RCODE3 => [31:16] ROI WIDTH ( QVGA : 16 ~ 384, VGA : 16 ~ 640 )
										#	RCODE3 => [16:0]  ROI HEIGHT ( QVGA : 16 ~ 288, VGA : 16 ~ 480 )

	CMD_ROI_TEMPCFG=		0x0423		#	ROI TEMPERATURE CONFIG					( CG )
										#	RCODE  => [15:8]  ROI_01 : 11 ~ ROI_10 : 20
										#	RCODE  => [7:0]   ROI Correction Enable 0 or 1
										#	RCODE2 => [31:24] Emissivity ( 100 ~ 1 )
										#	RCODE2 => [23:16] Transmission ( 100 ~ 1 )
										#	RCODE2 => [15:0]  Atmosphere ( -500 ~ 1000 )
										#	RCODE3 => Temperature Type ( 0 : AVG, 1 : MAX, 2 : MIN )

	CMD_NUC_CFG=			0x0431		#	NUC CONFIG								( CG )
										#	RCODE  => NUC MODE ( 0 : OFF, 1 : TIME, 2 : AUTO, 3 : TIME + AUTO, 4 : SHUTTER OPEN, 5 : SHUTTER CLOSE )
										#	RCODE2 => [31:16]	NUC TIME CONFIG ( 0 : 1 MIN, 1 : 5 MIN, 2 : 10 MIN, 3 : 30 MIN, 4 : 60 MIN )
										#	RCODE2 => [15:0]	NUC AUTO THRESHOLD ( 0 : LOWEST, 1 : LOW, 2 : MIDDLE, 3 : HIGH, 4 : HIGHEST )

	CMD_NUC_ONETIME=		0x0432		#	NUC ONE TIME							( CG )

	CMD_CVBS_VDO_SIZE=		0x0441		#	CVBS VIDEO SIZE							( CG )
										#	RCODE  => NONE
										#	RCODE2 => [31:16]	Left Margin ( 0 ~ 70 )
										#	RCODE2 => [15:0]	Right Margin ( 0 ~ 70 )
										#	RCODE3 => [31:16]	Top Margin ( 0 ~ 70 )
										#	RCODE3 => [15:0]	Bottom Margin ( 0 ~ 70 )

	CMD_HDMI_VDO_SIZE=		0x0442		#	HDMI VIDEO SIZE							( CG )
										#	RCODE  => NONE
										#	RCODE2 => [31:16]	Left Margin ( 0 ~ 150 )
										#	RCODE2 => [15:0]	Right Margin ( 0 ~ 150 )
										#	RCODE3 => [31:16]	Top Margin ( 0 ~ 150 )
										#	RCODE3 => [15:0]	Bottom Margin ( 0 ~ 150 )

	CMD_VDO_ROT=			0x0451		#	VIDEO RATATION							( CG )
										#	RCODE  => 0 : OFF, 1 : MIRROR, 2 : FLIP, 3 : MIRROR + FLIP

	CMD_AGC_MANMAX=			0x0461		#	VIDEO AGC MANUAL MAXIMUM				( CG )
										#	RCODE  => 0 : INC, 1 : DEC

	CMD_AGC_MANMIN=			0x0462		#	VIDEO AGC MANUAL MINIMUM				( CG )
										#	RCODE  => 0 : INC, 1 : DEC

	CMD_HDMI_MODE=			0x0471		#	HDMI MODE								( CG )
										#	RCODE  => HDMI MODE ( 2 : 480P, 3 : 576P, 4 : 720P 50, 5 : 720P 60, 6 : 1080I 50, 7 : 1080I 60, 9 : 1080P 50, 10 : 1080P 60 )

	CMD_CGISO_CFG=			0x0481		#	CG Isotherm Configuration				( CG )
										#	RCODE  => must be 0
										#	RCODE2 => [15:8] Transparent Mask ( 0x01 : above transparent, 0x02 : below transparent, 0x04 : between transparent )
										#	RCODE2 => [7:0]  ISO Mode Mask ( 0x01 : min above mode, 0x02 : max below mode, 0x04 : min/max between mode ) 
										#	RCODE3 => [31:16]	Max Temperature ( -20 ~ 650 )
										#	RCODE3 => [15:0]	Min Temperature ( -20 ~ 650 )

	CMD_CGISO_CLR=			0x0482		#	CG Isotherm Color Configuration			( CG )
										#	RCODE  => must be 0
										#	RCODE2 => Above RGB Color ( [31:24] : NOT USED, [23:16] : BLUE, [15:8] : GREEN, [7:0] : RED )
										#	RCODE3 => Below RGB Color ( [31:24] : NOT USED, [23:16] : BLUE, [15:8] : GREEN, [7:0] : RED )
										#	RCODE4 => Between RGB Color ( [31:24] : NOT USED, [23:16] : BLUE, [15:8] : GREEN, [7:0] : RED )

	CMD_MOTORIZED=			0x0491		#	CG Motorized Controller					( CG )
										#	RCODE  => FOCUS OR ZOOM ( 0 : FOCUS, 1 : ZOOM )
										#	RCODE2 => OFF, INC or DEC ( 0 : OFF, 1 : INC, 2 : DEC )

	CMD_TV_MODE=			0x0501		#	TV MODE									( CG )
										#	RCODE  => 0 : NTSC, 1 : PAL

	CMD_NUC=				0x0502		#	NUC										( CX )
										#	RCODE  => 0 : 1 MIN, 1 : 5 MIN, 2 : 10 MIN, 3 : 30 MIN, 4 : 60 MIN, 5 : OFF, 7 : MANUAL

	CMD_TEMP_MODE=			0x0503		#	TEMPERATURE MODE						( CX, CG )
										#	RCODE  => 0 : NORMAL, 1 : HIGH

	CMD_NETWORK_FPS=		0x0A01		#	RAW DATA CAPTURE FPS					( CX, CG )
										#	RCODE  => SKIP FRAME NUMBER ( 0 : NO SKIP, 1 : 1/2 fps, 2 : 1/3 fps ... )
										#			  0 ~ 255

	CMD_DISPLAY_FPS=		0x0A02		#	DISPLAY DATA CAPTURE FPS				( CG )
										#	RCODE  => SKIP FRAME NUMBER ( 0 : NO SKIP, 1 : 1/2 fps, 2 : 1/3 fps ... )
										#			  0 ~ 255

	CMD_TEMP_CORRECT=		0x0B01		#	Entire emissivity correction			( CX, CG )
										#	RCODE  => USED CORRECTION ( 0 : OFF, 1 : ON )
										#	RCODE2 => [31:24] Emissivity ( 100 ~ 1 )
										#	RCODE2 => [23:16] Transmission ( 100 ~ 1 )
										#	RCODE2 => [15:0]  Atmosphere ( -500 ~ 1000 )
										#	RCODE3 => [15:0]  ZERO OFFSET ( -200 ~ 200 )  CG ONLY

	CMD_SPOT_CONF=			0x0B02		# Spot configuration						( CX )

	CMD_ISOTHERM_CONF=		0x0B03		# Isotherm configuration					( CX )

	CMD_FACTORYDEF=			0x0F01		# Factory Default							( CG )
	
class ErrorCode(enum.Enum):
	IRF_NO_ERROR =					   1;			#* OK, No error */
	IRF_HANDLE_ERROR =				   -1;			#* No handle */
	IRF_FILE_OPEN_ERROR =				-2;			#* File open error. */
	IRF_FILE_CLOSE_ERROR =			   -3;			#* File close error. */
	IRF_IR_IMAGE_READ_ERROR =			-4;			#* IR image read error. */
	IRF_FILE_BUFFER_ALLOCATION_ERROR =	 -5;			#* File Stream Buffer allocation error. */
	IRF_END_OF_FILE =					-6;			#* End of IR image */
	IRF_BEGIN_OF_FILE =				  -7;			#* Start of IR image */
	IRF_IR_IMAGE_WRITE_ERROR =		   -8;			#* IR image write error. */
	IRF_NOT_FOUND_WINSOCK_DLL =		  -9;			#* Incorrect version of WS2_32.dll found */
	IRF_CAMERA_CONNECTION_ERROR =		-10;		#* Connection error from a camera */
	IRF_CAMERA_DISCONNECTION =		   -11;		#* Disconnected from a camera */
	IRF_PACKET_ID_ERROR =				-12;		#* Unknown packet ID */
	IRF_MESSAGE_SEND_ERROR =			 -13;		#* Message sending error */
	IRF_FIRST_FRAME_POS_ERROR =		  -14;		#* First frame position error */
	IRF_FILTER_SIZE_ERROR =			  -15;		#* Image filter size error. */
	IRF_FILE_WRITE_COUNT_OVER =		  -16;		#* Image frame count over */
	IRF_PALETTE_FILE_OPEN_ERROR =		-17;		#* Palette File open error. */
	IRF_NAK =							-100;		#* Received NAK message from a camera. */
	IRF_BUFFER_ALLOCATION_ERROR =		-1000;		#* Buffer allocation error. */
'''---------------------COX IR wintype defination End ----------------------------------------'''

'''---------------------DALI IR wintype defination -------------------------------------------'''

'''---------------------DALI IR wintype defination End ----------------------------------------'''
'''---------------------HikVision vis wintype defination --------------------------------------'''
class FRAME_INFO(Structure):
	_fields_ =[
			   ('lWidth', c_long),
			   ('lHeight', c_long),
			   ('lStamp', c_long),
			   ('lType', c_long),
			   ('lFrameRate', c_long),
			   ('dwFrameNum', wintypes.DWORD)
			   ]


class NET_DVR_CLIENTINFO(Structure):
	_fields_ =[
			   ('lChannel', c_long),		#channel no.
			   ('lLinkMode', c_long),		#If 31st bit is 0,	it means connect main stream,  is 1 means sub stream. Bit 0~bit 30 are used for link mode:	0:	TCP mode,  1:  UDP mode,  2:  Multi- play mode,	 3:	 RTP mode,4-RTP/RTSP,5-RSTP/HTTP
			   ('hPlayWnd', wintypes.HWND), #the play window's handle;	set NULL to disable preview
			   ('sMultiCastIP', c_char_p)	#Multicast IP address 
			   ]
	
class NET_DVR_DEVICEINFO_V30(Structure):
	_fields_ =[
			   ('sSerialNumber', c_ubyte*48),	#SN
			   ('byAlarmInPortNum', c_ubyte),	#Number of Alarm input
			   ('byAlarmOutPortNum', c_ubyte),	#Number of Alarm Output
			   ('byDiskNum', c_ubyte),			#Number of Hard Disk
			   ('byDVRType', c_ubyte),			#DVR Type,	1: DVR 2: ATM DVR 3: DVS ......
			   ('byChanNum', c_ubyte),			#Number of Analog Channel
			   ('byStartChan', c_ubyte),		#The first Channel No. E.g. DVS- 1, DVR- 1
			   ('byAudioChanNum', c_ubyte),		#Maximum number of IP Channel
			   ('byIPChanNum', c_ubyte),		#Number of Analog Channel
			   ('byZeroChanNum', c_ubyte),		#Zero channel encoding number//2010- 01- 16
			   ('byMainProto', c_ubyte),		#Main stream transmission protocol 0- private,	1- rtsp
			   ('bySubProto', c_ubyte),			#Sub stream transmission protocol 0- private,  1- rtsp
			   ('bySupport', c_ubyte),			#Ability, the 'AND' result by bit: 0- not support;	1- support
			   ('bySupport1', c_ubyte),			#Ability expand, the 'AND' result by bit: 0- not support;  1- support
			   ('byRes1', c_ubyte),				#bySupport1&0x1, support snmp v30
			   ('wDevType', c_uint64),			#bySupport1&0x2support distinguish download and playback
			   ('byAlarmInPortNum', c_ubyte),
			   ('byAlarmInPortNum', c_ubyte),
			   ('byRes2', c_ubyte*16)			#//device type
			   ]			

FREALDATACALLBACK = WINFUNCTYPE(c_int, c_long, wintypes.DWORD, POINTER(wintypes.BYTE), wintypes.DWORD, wintypes.DWORD) #Create a Function Prototype for callback function
FSETDECCALLBACK = WINFUNCTYPE(c_bool, c_long, POINTER(ctypes.c_ubyte), c_long, POINTER(FRAME_INFO), c_long, c_long)
FEXCEPTIONCALLBACK = WINFUNCTYPE(c_int, wintypes.DWORD, c_long, c_long, c_void_p)
FSTANDARDDATACALLBACK = WINFUNCTYPE(c_int, c_long, wintypes.DWORD, POINTER(wintypes.BYTE), wintypes.DWORD, wintypes.DWORD)#POINTER(wintypes.BYTE) is Byte Pointer
STREAME_REALTIME = 0
NET_DVR_SYSHEAD = 1
NET_DVR_STREAMDATA = 2
DECODE_NORMAL = 0
'''---------------------HikVision vis wintype defination End ----------------------------------'''
'''---------------------Uniview wintype defination -------------------------------------------'''
class UNIVIEW_NETDEV_DEVICE_INFO_S(Structure):
	_fields_ = [
				('dwDevType',c_int),
				('wAlarmInPortNum',c_short),
				('wAlarmOutPortNum',c_short),
				('dwChannelNum',c_int),
				('szReserve',c_byte*48)
				]
class UNIVIEW_NETDEV_PREVIEWINFO_S(Structure):
	_fields_ = [
				('dwChannelID',c_int),
				('dwStreamType',c_int),
				('dwLinkMode',c_int),
				('hPlayWnd',c_void_p),
				('szReserve', c_byte*264)
				]
class UNIVIEW_NETDEV_VIDEO_STREAM_INFO_S(Structure):
	_fields_ = [ 
				('enStreamType',c_int),
				('bEnableFlag',c_int),
				('dwHeight',c_int),
				('dwWidth',c_int),
				('dwFrameRate',c_int),
				('dwBitRate',c_int),
				('enCodeType',c_int),
				('enQuality',c_int),
				('dwGop',c_int),
				('szReserve',c_byte*32)
				]

class UNIVIEW_NETDEV_PICTURE_DATA_S(Structure):
	_fields_ = [
				('pucData',POINTER(c_ubyte)*4),	#pucData[0]:Y 平面指针,pucData[1]:U 平面指针,pucData[2]:V 平面指针  pucData[0]: Y plane pointer, pucData[1]: U plane pointer, pucData[2]: V plane pointer
				('dwLineSize',c_int*4),	#ulLineSize[0]:Y平面每行跨距, ulLineSize[1]:U平面每行跨距, ulLineSize[2]:V平面每行跨距  ulLineSize[0]: Y line spacing, ulLineSize[1]: U line spacing, ulLineSize[2]: V line spacing
				('dwPicHeight',c_int),	#Picture height
				('dwPicWidth',c_int),	#Picture width
				('dwRenderTimeType',c_int),	#Time data type for rendering
				('tRenderTime',c_int64)	#Time data for rendering
				]

uniview_FSETDECCALLBACK = WINFUNCTYPE(None,c_void_p, POINTER(UNIVIEW_NETDEV_PICTURE_DATA_S), c_void_p)


uniview_FREALDATACALLBACK = WINFUNCTYPE(None,c_void_p, c_char_p, c_int, c_int, c_void_p)

uniview_FEXCEPTIONCALLBACK = WINFUNCTYPE(None, c_void_p, c_int,c_void_p,c_void_p )
'''---------------------Uniview wintype defination End ----------------------------------'''

'''---------------------Box camera wintype defination -----------------------------------'''
class tmConnectInfo_t(Structure):
	_fields_ = [
			('dwSize',c_uint),
			('pIp',c_char*32),
			('iPort',c_int),
			('szUser',c_char*32),
			('szPass',c_char*32),
			('iUserLevel',c_int),		
			('pUserContext',c_char*32)
			]
	
class _stuVideo(Structure):
	_fields_ = [
			('width',c_short),
			('height',c_short),
			('framerate',c_int),
			('format',c_byte),
			('temp',c_byte*3)			
			]
class BOXCAM_tmAvImageInfo_t(Structure):
	_fields_ = [ 
				('video',c_byte),
				('face',c_byte),
				('temp',c_byte*2),
				('buffer0',POINTER(c_int)),
				('buffer1',POINTER(c_int)),
				('buffer2',POINTER(c_int)),
				('buffer3',POINTER(c_int)),
				('bufsize0',c_int),
				('bufsize1',c_int),
				('bufsize2',c_int),
				('bufsize3',c_int),
				
				('width',c_short),
				('height',c_short),
				('framerate',c_int),
				('format',c_byte),
				('temp',c_byte*3),	

				('key_frame',c_int),
				('timestamp',c_uint)
				]


class BOXCAM_tmRealStreamInfo_t(Structure):
	_fields_ = [
				('dwSize',c_uint),
				('byFrameType',c_byte),
				('byNeedReset',c_byte),
				('byKeyFrame',c_byte),
				('byTemp',c_byte),
				('dwFactoryId',c_uint),		
				('dwStreamTag',c_uint),
				('dwStreamId',c_uint),
				('iSamplesPerSec',c_int),
				('iBitsPerSample',c_int),
				('iChannels',c_int),
				('nDisplayScale',c_uint),

				('dwTimeStamp',c_uint),
				('dwPlayTime',c_uint),
				('dwBitRate',c_uint),
				('pBuffer',POINTER(c_int)),
				('iBufferSize',c_int)
				
				]
class tmPlayRealStreamCfg_t(Structure):
	_fields_ = [
				('dwSize',c_uint),
				('szAddress',c_char*32),
				('szTurnAddress',c_char*32),
				('iPort',c_int),
				('szUser',c_char*32),
				('szPass',c_char*32),
				('byChannel',c_byte),
				('byStream',c_byte),
				('byTranstType',c_byte),
				('byReConnectNum',c_byte),
				('iTranstPackSize',c_int),
				('iReConnectTime',c_uint),

				('byTransProtocol',c_byte),
				('ok',c_char*128)
				]


#TMCC_Init的参数参考如下：
TMCC_INITTYPE_CONTROL	=		0		# 初始化成设备控制SDK句柄
TMCC_INITTYPE_ENUM		=		1		# 初始化成枚举SDK句柄
TMCC_INITTYPE_UPGRADE	=		2		# 初始化成升级SDK句柄
TMCC_INITTYPE_TALK		=		3		# 初始化成语音对讲SDK句柄
TMCC_INITTYPE_STREAM	=		4		# 初始化成播放数据流SDK句柄
TMCC_INITTYPE_REALSTREAM	=	5		# 初始化成播放实时数据流SDK句柄
TMCC_INITTYPE_LISTEN		=	6		# 状态接收和报警接收SDK句柄
TMCC_INITTYPE_VIDEORENDER	=	7		# 初始化为视频显示SDK句柄
TMCC_INITTYPE_VOICERENDER	=	8		# 初始化为语音对讲数据解码SDK句柄
TMCC_INITTYPE_LISTENDEVICE	=	9		# 初始化为主动监听设备上传SDK句柄
TMCC_INITTYPE_AVDECODER		=	10		# 初始化为音视频解码SDK句柄
TMCC_INITTYPE_PLAYREMOTEFILE= 	11		# 播放远程文件句柄(通过回调读取数据)
TMCC_INITTYPE_MASK			=	12		# 初始化为SDK句柄掩码

boxcam_FSETDECCALLBACK = WINFUNCTYPE(None,POINTER(c_int), POINTER(BOXCAM_tmAvImageInfo_t), POINTER(c_int))
boxcam_FSETSTREAMCALLBACK = WINFUNCTYPE(None,POINTER(c_int), POINTER(BOXCAM_tmRealStreamInfo_t), POINTER(c_int))

'''---------------------Box Camera wintype defination End -------------------------------'''




