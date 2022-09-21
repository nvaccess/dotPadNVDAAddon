from enum import Enum
import os
import ctypes

_dllPath = os.path.join(os.path.dirname(__file__), 'DotPadSDK.dll')
_dll = ctypes.cdll.LoadLibrary(_dllPath)

class DotPadErrorCode(Enum):
	NONE = 0x00
	HV_UNSUPPORTED_FEATURE = 0X1
	DOT_PAD_COULD_NOT_INIT = 0X2
	DOT_PAD_ALREADY_INIT = 0X3
	TTB_DLL_LOAD_FAIL = 0X4
	TTB_DLL_GET_FUNC_FAIL = 0X5
	TTB_DLL_COULD_NOT_LOAD = 0X6
	TTB_COULD_NOT_SET_LANGUAGE = 0X7
	DISPLAY_FILE_INVALID = 0X8
	COM_PORT_ERROR = 0x10
	COM_HANDLE_INIT_ERROR = 0X11
	COM_PORT_ALREADY_OPENED = 0X12
	COM_PORT_DISCONNECTED = 0X13
	COM_WRITE_ERROR = 0x20
	COM_INVALID_DATA = 0X21
	COM_NOT_RESPONSE = 0X22
	COM_RESPONSE_TIMEOUT = 0X23
	BRAILLE_NOT_TRANSLATE = 0x40
	KEY_OUT_OF_RANGE = 0X41
	DISPLAY_THREAD_NOT_READY = 0X42
	ACCESS_INVALID_MEM = 0x80
	DISPLAY_IN_PROGRESS = 0X81
	CERTIFY_NG = 0x80000000
	RESPONSE_TIMEOUT = 0X80000001
	DISPLAY_DATA_INVALIDE_FILE = 0X800000002
	DISPLAY_DATA_INVALIDE_LENGTH = 0X80000003
	DISPLAY_DATA_SYNC_DATA_FAIL = 0X80000004
	INVALID_DEVICE = 0X80000005
	MAX = 0X80000006

def init(portNum: int) -> DotPadErrorCode:
	oldCwd = os.getcwd()
	os.chdir(os.path.dirname(__file__))
	try:
		res = _dll.DOT_PAD_INIT(portNum)
	finally:
		os.chdir(oldCwd)
	return DotPadErrorCode(res)

def display_data(data: ctypes.c_buffer, dataLen: int) -> DotPadErrorCode:
	res = _dll.DOT_PAD_DISPLAY_DATA(data, dataLen)
	return DotPadErrorCode(res)

def deinit() -> None:
	_dll.DOT_PAD_DEINIT()
