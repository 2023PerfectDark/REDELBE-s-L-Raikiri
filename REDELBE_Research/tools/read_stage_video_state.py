import ctypes as c,sys
class Frame(c.Structure):
 _fields_=[('version',c.c_uint32),('active',c.c_uint32),('tick',c.c_uint64),('slot',c.c_char*24),('x',c.c_float),('y',c.c_float),('width',c.c_float),('height',c.c_float),('nameAlpha',c.c_uint32)]
class Shared(c.Structure):
 _fields_=[('sequence',c.c_int32),('frame',Frame)]
k=c.WinDLL('kernel32',use_last_error=True)
k.OpenFileMappingW.argtypes=[c.c_uint32,c.c_bool,c.c_wchar_p];k.OpenFileMappingW.restype=c.c_void_p
k.MapViewOfFile.argtypes=[c.c_void_p,c.c_uint32,c.c_uint32,c.c_uint32,c.c_size_t];k.MapViewOfFile.restype=c.c_void_p
k.UnmapViewOfFile.argtypes=[c.c_void_p];k.CloseHandle.argtypes=[c.c_void_p]
h=k.OpenFileMappingW(4,False,'Local\\REDELBE_LR_StageVideo_'+sys.argv[1]);assert h,c.get_last_error()
p=k.MapViewOfFile(h,4,0,0,c.sizeof(Shared));assert p,c.get_last_error()
s=Shared.from_buffer_copy(c.string_at(p,c.sizeof(Shared)))
print({name:getattr(s.frame,name) for name,_ in Frame._fields_})
k.UnmapViewOfFile(p);k.CloseHandle(h)
