import enum
import ctypes

def StringBuffer(size: int):
	"""
	creates a char array class of given size, but automatically fetches value when used as an out param.
	"""
	return type(
		f"StringBuffer[{size}]",
		(ctypes.c_char*size,),
		{'__ctypes_from_outparam__': lambda self: self.value}
	)

class ParamFlag(enum.IntFlag):
	IN = 1
	OUT = 2

def declareCFunction(dll, res, name, args):
	ft = ctypes.CFUNCTYPE(res, *(a[0] for a in args))
	fp = ft(
		(name, dll),
		tuple(a[1:] for a in args)
	)
	errcheck = getattr(res, '_errcheck')
	if errcheck:
		fp.errcheck = errcheck
	return fp
