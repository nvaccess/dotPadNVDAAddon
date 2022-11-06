from enum import Enum
import os
import ctypes
from .ctypesUtils import StringBuffer, ParamFlag, declareCFunction


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
	DISPLAY_DATA_UNCHANGED = 0X80000005
	DISPLAY_DATA_RANGE_INVALID = 0X80000006
	INVALID_DEVICE = 0X80000007
	MAX = 0X80000008


KeyCallbackType = ctypes.WINFUNCTYPE(ctypes.c_voidp, ctypes.c_int)
DisplayCallbackType = ctypes.WINFUNCTYPE(ctypes.c_voidp)


DEVICE_NAME_LEN = 10
FW_VERSION_LEN = 8
HW_VERSION_LEN = 1


class DOT_PAD_ERROR(ctypes.c_ulong):

	@classmethod
	def _errcheck(cls, res, func, args):
		res = DotPadErrorCode(res.value)
		if res != DotPadErrorCode.NONE:
			raise DotPadError(res)
		return args


class DotPadError(Exception):

	def __init__(self, code):
		self.code = code

	def __repr__(self):
		return f"DotPadException({self.code.name})"


init = declareCFunction(
	_dll, DOT_PAD_ERROR, 'DOT_PAD_INIT', (
		(ctypes.c_int, ParamFlag.IN, 'portNum'),
	)
)


getDeviceName = declareCFunction(
	_dll, DOT_PAD_ERROR, 'DOT_PAD_GET_DEVICE_NAME', (
		(StringBuffer(DEVICE_NAME_LEN), ParamFlag.OUT, 'deviceName'),
	)
)


getHwVersion = declareCFunction(
	_dll, DOT_PAD_ERROR, 'DOT_PAD_GET_HW_VERSION', (
		(ctypes.POINTER(ctypes.c_ubyte), ParamFlag.OUT, 'hwVersion'),
	)
)


getFwVersion = declareCFunction(
	_dll, DOT_PAD_ERROR, 'DOT_PAD_GET_FW_VERSION', (
		(StringBuffer(FW_VERSION_LEN), ParamFlag.OUT, 'fwVersion'),
	)
)


displayData = declareCFunction(
	_dll, DOT_PAD_ERROR, 'DOT_PAD_DISPLAY_DATA', (
		(ctypes.POINTER(ctypes.c_char), ParamFlag.IN, 'data'),
		(ctypes.c_int, ParamFlag.IN, 'length'),
	)
)


registerDisplayCallback = declareCFunction(
	_dll, DOT_PAD_ERROR, 'DOT_PAD_REGISTER_DISPLAY_CALLBACK', (
		(DisplayCallbackType, ParamFlag.IN, 'callback'),
	)
)


registerKeyCallback = declareCFunction(
	_dll, DOT_PAD_ERROR, 'DOT_PAD_REGISTER_KEY_CALLBACK', (
		(KeyCallbackType, ParamFlag.IN, 'callback'),
	)
)


deinit = declareCFunction(
	_dll, DOT_PAD_ERROR, 'DOT_PAD_DEINIT', ()
)
