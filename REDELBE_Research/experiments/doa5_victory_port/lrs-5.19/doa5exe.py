#!/usr/bin/env python3


import io
import hashlib
import logging
import os
import struct
from sys import argv,stdout

from time import time
from collections import namedtuple

SlDef=namedtuple('SlDef',['cs_idx','typ'])
SlEn=namedtuple('SlEn',['num','num_base','slots'])


logger = logging.getLogger('doa5exe')
logger.setLevel(logging.DEBUG)
debug=logger.debug
info=logger.info
warn=logger.warn
error=logger.error

##################
# helper
def readfmt(buf, fmt, ofs=0, cls=None):
        res = struct.unpack_from(fmt, buf, ofs)
        if len(res)==1: res=res[0]
        if cls: res=cls(*res)
        return res

def align(num, boundary):
        x = boundary-1
        return  (num + x) & ~x

def get_zstr(buf, ofs):
        idx = buf.find(b'\x00', ofs)
        return buf[ofs:idx].decode('ASCII')

class DOA5Exe:
        AssetEnt= namedtuple('AssetEnt',['name','typ','lnk','replace'])
        CrcEnt  = namedtuple('CrcEnt', ['size','crc'])
        FlEnt   = namedtuple('FlEnt',  ['size', 'flag'])
        CsOptEnt= namedtuple('CsEnt',  ['num','num_base','dlc', 'nfaces','nalt', 'glasses'])
        CosEnt  = namedtuple('CosEnt', ['tmc','tmcl','c','p','phyd','faces','alt'])
        AltEnt  = namedtuple('AltEnt', ['h','hl'])
        CharEnt = namedtuple('CharEnt',['unks','cos','fx_tmc','fx_tmcl','ai_tmc','ai_tmcl','cam',
                                        'phyd','unk'])

        Info=None
        class Invalid(Exception):
                pass
        def __init__(self, path):
                st=time()
                if not DOA5Exe.Info:
                        DOA5Exe.Info = load_exe_conf( os.path.join(os.path.dirname(argv[0]),'doa5exe.dat') )

                info("doa5exe: loading "+path)
                try:
                        pe = PEFile(path, keep_secs=('.rdata', '.data') )
                except PEFile.Invalid as e:
                        raise self.Invalid( str(e) )
                debug("doa5exe: chksum: "+pe.chksum)
                exe_info = DOA5Exe.Info.get( pe.chksum )
                if not exe_info: raise DOA5Exe.Invalid("unknown exe")
                self.ver = exe_info['ver']
                self.num_char = exe_info['num_char']
                info("doa5exe: found version: %s"%self.ver)

                self.table={}
                self._load_assets(pe, exe_info['table'], exe_info['num_char'])
                self._load_dlc_tbl(pe, exe_info['table'], exe_info['num_char'])
                info("doa5exe: loading done (%.3f)"%(time()-st))



        def _load_assets(self, pe, ofs, num_char):
                # since asset/crc/flag table are directly next to each other
                # we can compute the number of entries for asset&crc
                # flag table len matches asset table
                num_assets = (ofs['CRC'] - ofs['ASSET'])//16
                num_crc = (ofs['FLAG'] - ofs['CRC'])//8
                debug("doa5exe: assets:%x crc:%x"%(num_assets,num_crc))

                self.table['ASSET'] = [ self.AssetEnt( pe.zstr(name), typ, pe.zstr(lnk),
                                        repl) for name,typ,lnk,repl in pe.getTableI32(ofs['ASSET'], num_assets, 4) ]

                self.table['CRC'] = pe.getTableI32(ofs['CRC'], num_crc, 2, Cls=self.CrcEnt)
                self.table['FLAG'] = pe.getTableI32(ofs['FLAG'], num_assets, 2, Cls=self.FlEnt)

                info("doa5exe: loading costume data (%d chars)..."%num_char)

                # SLOTS
                def _make_slot(pe, num, numb, list_ofs):
                        return SlEn(num, numb, pe.getTableI32(list_ofs, num, 2, Cls=SlDef))
                self.table['SLOT'] = [ _make_slot(pe,*row)  for row in pe.getTableI32(ofs['SLOT'], num_char, 3) ]


                # CSOPTS
                def _make_csopt(pe, num, nb, ofs_dlc, ofs_nface, ofs_nalt, ofs_glass):
                        return self.CsOptEnt(num, nb, pe.getTableI8(ofs_dlc, num, 1),
                                                        pe.getTableI8(ofs_nface, num, 1),
                                                        pe.getTableI8(ofs_nalt, num, 1),
                                                        pe.getTableI8(ofs_glass, num, 1) )
                self.table['CSOPT'] = [ _make_csopt(pe,n&0xff,(n>>8)&0xff,*row) for n,*row in pe.getTableI32(ofs['CSOPT'],num_char,5) ]

                # CHAR+COS
                def _make_cos(pe, cfg, idx, tmc,tmcl,c, p, phyd, ofs_faces, ofs_alt):
                        return self.CosEnt(tmc, tmcl, c, p, phyd,
                              pe.getTableI32(ofs_faces, cfg.nfaces[idx], 6),
                              pe.getTableI32(ofs_alt, cfg.nalt[idx], 2, Cls=self.AltEnt) )

                def _make_char(pe, csopt, ofs_unk, ofs_cos, *dat):
                        tmp = pe.getTableI32(ofs_cos, csopt.num, 7)
                        cos_list = [ _make_cos(pe, csopt, i, *row) for i,row in enumerate(tmp) ]
                        return self.CharEnt(ofs_unk, cos_list, *dat)

                ch = pe.getTableI32(ofs['CHAR'], num_char, 9)
                self.table['CHAR'] = [ _make_char(pe, csopt, *row) for csopt,row in zip(self.table['CSOPT'],ch)]

                # STAGES
                def _make_stage(pe, row):
                        row[14] = pe.getTableI32(row[14], row[13], 1)
                        return row
                self.table['STAGE']= [ _make_stage(pe, s) for s in pe.getTableI32(ofs['STAGE'], 74, 15) ]


                # NUM_DLC
                ofs_dlcu = align( ofs['NUM_DLC']+num_char*4, 8)
                ofs_dlcx = align( ofs_dlcu+num_char*4, 8)

                self.table['NDLC'] = pe.getTableI32(ofs['NUM_DLC'], num_char, 1)
                self.table['NDLCU'] = pe.getTableI32( ofs_dlcu, num_char, 1)
                self.table['NDLCX'] = pe.getTableI32( ofs_dlcx, num_char, 1)

                # CS_STATUS
                self.table['CS_STATUS'] = pe.getTableI8(ofs['CS_STATUS'], num_char, 42)


        def _calc(self, ofs_list, end, num):
                n=[0]*num
                for i in reversed(range(num)):
                        if ofs_list[i]==0:continue # avoid empty
                        n[i]=(end-ofs_list[i])//8 # 2dwords per hair
                        end = ofs_list[i]
                return n

        def _load_dlc_tbl(self, pe, ofs, num_char):
                info("doa5exe: loading dlc hair/face table...")
                hair=pe.getTableI32(ofs['HAIR'], num_char, 1)
                face_ofs=align(ofs['HAIR']+num_char*4, 0x08)
                face=pe.getTableI32(face_ofs, num_char, 1)

                # doesn't seem to store how many faces/hair are there for each char
                # just the offset into the long list

                # calc number of hairs per char
                n=self._calc(hair, face[0], num_char)
                self.table['HAIR']=[ pe.getTableI32(ofs, num, 2) for ofs,num in zip(hair,n) ]

                # same for faces except that we need to hard code the last entry
                n=self._calc(face, face[-1]+2*8, num_char) # naotora has 2 entries
                self.table['FACE']=[ pe.getTableI32(ofs, num, 2) for ofs,num in zip(face, n) ]

class PEFile:
        PE_SECTION = namedtuple('PE_SECTION', ['name','vsize','rva','psize', 'pofs'])

        class Invalid(Exception):
                pass
        class NotFound(Exception):
                pass
        class FoundMultiple(Exception):
                pass

        def __init__(self, path, keep_secs=None):
                self.path = path
                with open(path, 'rb') as fd:
                        self._parse_header(fd)
                        self._load_sections(fd, keep_secs)


        def _load_sections(self, fd, keep_secs):
                self.sec_data=[]
                for sec in self.sections:
                        if not keep_secs or sec.name in keep_secs:
                                fd.seek(sec.pofs)
                                data = bytearray(sec.psize)
                                fd.readinto(data)
                        else: data=None
                        self.sec_data.append(data)

        def _parse_header(self, fd):
                buf = fd.read(0x40)
                if b'MZ' != buf[:2]:
                        raise self.Invalid("invalid exe/missing MZ header")
                e_lfanew = readfmt(buf, '<L', ofs=0x3C)
                fd.seek(e_lfanew)
                buf = fd.read(24)
                if b'PE\x00\x00' != buf[:4]:
                        raise self.Invalid("invalid exe/missing PE header")
                m,nsec,stmp,p_sym,nsym,size,ch = readfmt(buf, '<HHLLLHH', ofs=4)

                opt_head = memoryview(fd.read(size)) # OPTIONAL_HEADER
                xx,szt,szrd,szd,oep,base,based,image_base = opt_head[0:8*4].cast('I').tolist()
                self.image_base = image_base
                num_data = (size-0x60)//8
                data_dir = opt_head[0x60:].cast('I',shape=(num_data,2)).tolist()
                opt_head.release()
                sec_dir = data_dir[4]

                # load SECTION info
                buf = fd.read(40*nsec)
                self.sections=[]
                for i in range(nsec):
                        name,vsize,rva,psize,pofs = readfmt(buf, '<8s4L', ofs=i*40)
                        self.sections.append( self.PE_SECTION( name.decode('ASCII').rstrip('\0'),
                                              vsize, rva+image_base, psize, pofs) )

                # calc md5
                fd.seek(sec_dir[0])
                m = hashlib.md5()
                buf = fd.read(sec_dir[1])
                m.update(buf)
                self.chksum = m.hexdigest().upper()

        def find(self, va, nbytes):
                for i, sec in enumerate(self.sections):
                        if va<sec.rva or va >= sec.rva+sec.vsize: continue
                        if va+nbytes >= sec.rva+sec.psize: raise self.Invalid("FIXME:va:%x nb:%x sec:%s"%(va,nbytes,sec.name))
                        return i, (va-sec.rva)
                raise self.NotFound("PEReader.find: address not found: %08x"%va)

        def getTableI32(self, va, num_row, len_row, Cls=None):
                return self.getTable(va, num_row, len_row, 4, 'I', Cls)
        def getTableI8(self, va, num_row, len_row, Cls=None):
                return self.getTable(va, num_row, len_row, 1, 'B', Cls)

        def getTable(self, va, num_row, len_row, el_sz,el_sym, Cls=None):
                if num_row==0 or va==0: return []
                sz = num_row*len_row*el_sz
                shape=(num_row, len_row) if len_row>1 else None
                return self.getmem(va, sz, el_sym, shape=shape, Cls=Cls)

        def getmem(self, va, sz, fmt, shape=None, Cls=None):
                if va==0 or sz==0: return []
                idx, pos = self.find(va, sz)
                m = memoryview( self.sec_data[idx] )
                x= m[pos:pos+sz]
                m.release()
                if shape: res = x.cast(fmt, shape=shape).tolist()
                else: res = x.cast(fmt).tolist()
                x.release()
                if Cls: return [ Cls(*d) for d in res ]
                else: return res
        def get(self, va, fmt, num=1, cls=None):
                if num==0: return 0
                size = struct.calcsize(fmt)
                idx, pos = self.find(va, size*num)
                if idx==-1: return 0
                data=self.sec_data[idx]
                return [readfmt(data, fmt, ofs=pos+j*size, cls=cls) for j in range(num)]
        def zstr(self, va, max_len=128):
                idx, pos = self.find(va, max_len)
                return get_zstr(self.sec_data[idx],pos)

        def find_pattern(self, buf, ofs=None, end_rva=0, just_one=True):
                res = []
                for i, data in enumerate(self.sec_data):
                        if not data: continue
                        y = data.find( buf )
                        while y !=-1:
                                x = self.sections[i].rva + y
                                if end_rva!=0 and x > end_rva: break
                                res.append( x )
                                y = data.find(buf, y+len(buf))
                if not res: raise PEFile.NotFound()
                if just_one and len(res)>1: raise self.FoundMultiple("search returned multiple results:",
                                                                 " ".join(["%#x"%o for o in res]) )
                if ofs: res = [ o+ofs for o in res ]
                return res

        def find_mem_ref(self, pattern, ofs=None, rel=False, just_one=True):
                """ ofs = offset of target value relative to byte pattern (if None, directly after)
                    rel=True => target value is relative memory address => return absolute address """
                if ofs==None: ofs = len(pattern)

                try:
                        res = self.find_pattern(pattern, ofs=ofs, just_one=just_one)
                except self.NotFound:
                        return 0xffffffff
                dst = [ self.get(o, '<l')[0] for o in res ]

                if rel: dst = [ d+r+4 for d,r in zip(dst,res) ]

                if just_one: return dst[0]
                return dst


def load_exe_conf(path):
        def parse_val( v): return v[1:-1] if v[0]=="\"" else int(v,0)
        def splitstrip(src, split=None): return map(lambda x:x.strip(), src.split(split))

        def curly_iter(buf):
                of = buf.find('{')
                while of!=-1:
                        i = buf.find('}',of+1)
                        if i!=-1: yield buf[of+1:i]
                        else: break
                        of = buf.find('{',i+1)

        def item_iter(buf):
                for el in buf.split(','):
                        k,v = splitstrip(el, ':')
                        if v[0]=='[': v= {k:parse_val(v) for k,v in [x.split('=') for x in splitstrip(v[1:-1]) if x]}
                        else: v = parse_val(v)
                        yield k,v

        with open(path, 'r') as fs:
                buf = fs.read()

        x=[ {k:v for k,v in item_iter(it)} for it in curly_iter(buf) ]
        return { ent.pop('md5'):ent for ent in x }


#####################################################
# find all those offsets in the games exe file
# <orig_path> - unmodified exe
# <decr_path> - decrypted,dumped exe

def analyze_exe(ver_descr, orig_path, decr_path, py_dat=None):
        pe = PEFile(orig_path)
        md5=pe.chksum

        pe = PEFile(decr_path)

        # get_flag_entry()
        pfn_get_flag = pe.find_mem_ref(  bytes([0x8b,0x50,0x04,
                                       0xc1,0xea,0x1e,
                                       0x83,0xc4,0x4,
                                       0xf6,0xc2,0x1,
                                       0x74,0xd]), ofs=-4,rel=True)
        # get_crc_entry()
        pfn_get_crc = pe.find_mem_ref( bytes([ 0x8b,0x40,0x04,
                                               0x25,0xff,0xff,0xff,0x1f,
                                               0x50,
                                               0xe8] ), rel=True)
        hair_tbl,face_tbl = pe.find_mem_ref( bytes([0x85,0xc9,
                                              0x74,0xf,
                                              0xf,0xb6,0xc0,
                                              0x8d,0x4,0xc1,
                                              0x85,0xc0,
                                              0x74,0x5,
                                              0x8b,0x0,
                                              0x5b]),ofs=-4,rel=False, just_one=False)
        tbl= [   # in apply_updates()
                ('ASSET',pe.find_mem_ref( bytes([0xf,0xb7,0x02,
                                              0xbe,0xff,0xff,0,0,
                                              0x66,0x3b,0xc6,
                                              0x74,0x75,
                                              0x8b,0xf8,
                                              0xc1,0xe7,0x4,
                                              0x81,0xC7,
                                             ]) ) ),
                ('CRC',  pe.get(pfn_get_crc+9,'<L')[0] ),
                ('FLAG', pe.get(pfn_get_flag+9, '<L')[0] ),
                ('SLOT', pe.find_mem_ref(bytes([0x55,0x8B,0xEC,
                                                0x80,0x7D,0xC,0x0,
                                                0xf,0xB6,0x45,0x8,
                                                0x8D,0x4,0x40,
                                                0x8d,0x4,0x85]),rel=False) ),
#                ('SLOT', pe.find_mem_ref(bytes([0x8d,0x4,0x40,
#                                             0x3,0xc0,
#                                             0x56,
#                                             0x8b,0x75,0x0c,
#                                             0x3,0xc0,
#                                             0x39,0xb0]
#                                             ), rel=False) ),
                ('CHAR', pe.find_mem_ref(bytes([0xf,0xb6,0xc3,
                                             0xf,0xb6,0xf9,
                                             0x8d,0x1c,0xc0,
                                             0x8b,0x0c,0x9d]), rel=False) ),
                ('CSOPT', pe.find_mem_ref( bytes([0x8b,0x5d,0xc,
                                               0xf,0xb6,0xc1,
                                               0x8d,0x34,0x80,
                                               0x3,0xf6,
                                               0x8a,0x84,0x36]), rel=False, just_one=False)[0] ),
                ('STAGE', pe.find_mem_ref( bytes([0xf,0xb6,0xd8,
                                               0x88,0x45,0xff,
                                               0x8b,0xc3,
                                               0xc1,0xe0,0x04,
                                               0x2b,0xc3,
                                               0x8b,0x14,0x85]), rel=False) ),

                ('HAIR', pe.find_mem_ref( bytes([0x85,0xc9,
                                              0x74,0xf,
                                              0xf,0xb6,0xc0,
                                              0x8d,0x4,0xc1,
                                              0x85,0xc0,
                                              0x74,0x5,
                                              0x8b,0x0,
                                              0x5b]),ofs=-4,rel=False, just_one=False)[0] ),# second hit is for face
                ('NUM_DLC', pe.find_mem_ref( bytes([0x8b,0x45,0x10,
                                                 0x50,
                                                 0x8b,0x45,0x08,
                                                 0xf,0xb6,0xc8,
                                                 0x8b,0x14,0x8d])) ),
                ('CS_STATUS', pe.find_mem_ref( bytes([0xf,0xb6,0x45,0x8,
                                                  0x6b,0xc0,0x2a,
                                                  0xf,0xb6,0xcb,
                                                  0x8a,0x84,0x8]) ) ),
             ]

        # func for accessing CS_STATUS changed by recent patch
        if tbl[-1][1] == 0xffffffff:
                tbl[-1] =  ('CS_STATUS', pe.find_mem_ref( bytes([0x8a,0x04,0xf0,
                                                                 0x80,0xfb,0x31,
                                                                 0x73,0xec,
                                                                 0x3C,0x2A,
                                                                 0x73,0xe8,
                                                                 0x6b,0xc9,0x2a,
                                                                 0x0f,0xb6,0xd0,
                                                                 0x8a,0x84,0x11]),rel=False ) )

        num_char = 47
        try:
                pe.find_pattern( b'N\0A\0O\0T\0O\0R\0A\0\0\0', just_one=False)
                num_char+=1
                pe.find_pattern( b'\0M\0A\0I\0\0\0', just_one=False )
                num_char+=1
        except PEFile.NotFound: pass

        # code stuff
        code=[
           ('get_num_faces', pe.find_mem_ref( bytes([0xF,0xB6,0x4C,0x30,0x11,0xF,0xB6,
                                                     0x46,0x10,0x88,0x4D,0xFC,0x8B,0x55,
                                                     0xFC,0x52,0x50,0xE8]), rel=True) ),
           ('get_num_alts',  pe.find_mem_ref( bytes([0x8B,0x55,0xF8,0x8B,0x45,0xF4,0x52,0x50,0xE8]),
                                              rel=True) ),
           ('random',       pe.find_pattern( bytes([0x55,0x8B,0xEC,0x83,0xEC,0x8,0x56,0x8B,0x75,
                                                    0x0C,0x57,0x8B,0x7D,0x8,0x3b,0xFE]))[0] ),
           ('PlayerCfgTbl', pe.find_mem_ref( bytes([0x8a,0x49,0x4,0x88,0x55,0x0a,0x88,0x4d,0x0b,0x8b,0x55,
                                         0x08,0x89,0x94,0x80]), ofs=-22, rel=False) ),
           ('get_plcfg_char', pe.find_mem_ref( bytes([0x8A,0xD3,0x2,0xD2,0x53,0x51,0x8D,0x4,0x11,
                                                      0x88,0x45,0xED,0xE8]), rel=True) ),
           ('get_plcfg_cos',  pe.find_mem_ref( bytes([0xC6,0x45,0xE4,0x1,0x8B,0x45,0xE8,
                                                      0x53,0x50,0xE8]),rel=True) ),
           ('get_something', pe.find_mem_ref( bytes([0xff,0x45,0xe8,0x83,0xc7,0x0f,0x83,0xff,
                                                     0x1e,0xf,0x8c,0xb1,0xfe,0xff,0xff]), ofs=31,rel=True) ),

           ('patch1', pe.find_pattern( bytes([0x83,0xC4,0xC,0x84,0xC0,0x74,0x03,0x8a,0x5f,0xf]),ofs=3)[0] ),
           ('patch2', pe.find_pattern( bytes([0x8d,0x55,0xe4,0x8d,0x47,0x24,0x52,0x89,
                                              0x4f,0x20,0x50]),ofs=10)[0] ),
           ('patch3', pe.find_pattern( bytes([0xff,0x45,0xe8,0x83,0xc7,0x0f,0x83,0xff,
                                              0x1e,0xf,0x8c,0xb1,0xfe,0xff,0xff]),ofs=15)[0] ),
           # disable hardcoded restricted dlc slots
          ('patch4', pe.find_pattern( bytes([0x55,0x8B,0xEC,0x0F,0xB6,0x4D,0x08,0xB8,0x01,
                                             0x00,0x00,0x00,0x83,0xF9,0x2C]))[0] ),
           # hardcoded number of alt=3
          ('patch5', pe.find_pattern( bytes([0x8b,0x55,0xc,0x83,0xc4,0x8,0x3c,0x1,0xf,0x95,
                                             0xc1,0x8a,0x5d,0xf]),ofs=8)[0] ),
          ('patch6', pe.find_pattern( bytes([0x3c,0x1,0xf,0x95,0xc0,0x8a,0x4d,0xfb,0x80,0xf9,0x3,0x77]))[0] ),
          # thumbnail patch
          #find(exe, "patch7",bytes([0xf,0xb6,0xd1,0x80,0x3c,0x2,0,0x0f,0x95,0xc0,0x84,0xc0,0x74]))
          #find(exe, "patch8",bytes([0x8a,0x4e,0x11,0x53,0x8a,0x5e,0x12,0x88,0x5d,0xf8,0x88,0x4d,
          #                           0xff,0x84,0xc9,0x74]))
          #find(exe, "CharSelect::ChangeVal",bytes([0x55,0x8B,0xEC,0x83,0xEC,0x0C,0x56,0x8b,
          #                                         0xf1,0x80,0x7e,0x11,0x00]))
          #find(exe, "CharSelect::Refresh",bytes([0x55,0x8B,0xEC,0x83,0xEC,0x0C,0x8B,0x91,
          #                                       0x88,0x17,0,0,0x53]))

          # displayval for charselect
          ('patch7', pe.find_pattern( bytes([0x55,0x8B,0xEC,0xF,0xB6,0x45,0x8,0x56,0x57,0x8b,0xf9]))[0] ),
          ('patch8', pe.find_pattern( bytes([0x83,0xc0,2,0x83,0xc1,2,0x84,0xd2,0x75,0xe4,0x33,0xc0,0xeb,0x5,
                                             0x1b,0xc0,0x83,0xd8,0xff,0x85,0xc0,0x79,0xf,
                                             0xb9,0xff,0xff,0,0]),ofs=0xe)[0] ),
          ('pfn_get_asset_file', pe.find_mem_ref( bytes([0xc7,0x46,0x04,0x33,0,0,0,0x89,0x7e,0x14,0x89,
                                                         0x56,0x1c,0x89,0x4e,0x20]), ofs=0x1f,rel=True ) ),
#          ('patch8_dlc_update_asset', pe.find_pattern( bytes([0x8b,0x4e,0x04,0x8B,0x56,0x8,0x89,0x4d,0xf8,
#                                                             0x8d,0x4d,0xf8,0x51,0x50,0x89,0x55,0xfc,0xe8]),ofs=-7)[0] ),
#          ('patch9_pfn_loadDLC', pe.find_pattern( bytes([0x6a,0,0x68,0,0,0x1,0x0,0x6a,0,0x6a,1,
#                                                        0x6a,0,0x6a,0,0xA3]), ofs=21)[0] ),
#          ('set_dlc_cos_state', pe.find_mem_ref( bytes([0x6A,0,0x6A,1,0x83,0xc3,0x9c,0x53,0x51,0xeb]),
#                                                 ofs=21, rel=True) ),
          ('DLC_CSCFG', pe.find_mem_ref( bytes([0xf,0xb6,0xc9,0x8d,0x4,0x80,0x8d,0x04,
                                         0xc1,0x8b,0x4d,0x10,0x8d,0x04,0xc0,0x8d,0x04,0x45])) ),
       ]
        # accessing DLC_CSCFG changed in patch 1.05
        if code[-1][1] == 0xffffffff:
                code[-1] = ('DLC_CSCFG', pe.find_mem_ref( bytes([0xf,0xb6,0xc0,  # movzx eax,al
                                                                 0x6b,0xc0,0x32, # imul eax, 32h
                                                                 0xf,0xb6,0xc9,  # movzx exc, cl
                                                                 0x3,0xc1,       # add eax, ecx
                                                                 0x8b,0x4d,0x10, # ecx, [ebp+10h]
                                                                 0x8d,0x4,0xc0,  # lea, eax, [eax+eax*8]
                                                                 0x8d,0x4,0x45,  # lea eax, ADDR[eax*2]
                                                                 ]) ))

        # accessing DLC_CSCFG changed in patch 1.09p1
        if code[-1][1] == 0xffffffff:
                code[-1] = ('DLC_CSCFG', pe.find_mem_ref( bytes([0x8b,0x4d,0x10,0x8d,0x04,0x90,0x8a,
                                                          0x55,0x14,0x8d,0x04,0xc0,0x8d,0x04,0x45])) )

        if py_dat: # run from script output in file
                with open(py_dat, 'w', encoding='utf8') as fs:
                        fs.write("{ ver:\""+ver_descr+"\", md5:\""+md5+"\", num_char:"+str(num_char)+",\n")
                        fs.write("  table:[\n")
                        for i in range( len(tbl)//5 ):
                                fs.write(" ".join( [ "%8s=%#010x"%(n,o) for n,o in tbl[i*5:i*5+5]]))
                                fs.write("\n")
                        fs.write("        ]\n")
                        fs.write("}\n")
                return

        # dump to stdout
        print("py dat")
        print("{ ver:\""+ver_descr+"\", md5:\""+md5+"\", num_char:",num_char,",")
        print("  table:[")
        for i in range( len(tbl)//5 ):
                print(" ".join( [ "%8s=%#010x"%(n,o) for n,o in tbl[i*5:i*5+5]]))
        print("        ]")
        print("}")

        # FIXME:
        #  make this easier to add to the code, without manual copy+pasting
        xx = { name : ofs for name,ofs in tbl }
        xx['NUM_DLCU'] = align( xx['NUM_DLC']+num_char*4, 8)
        xx['NUM_DLCX'] = align( xx['NUM_DLCU']+num_char*4, 8)

        print("doa++ data")
        print("static DWORD ofs_v%s[]={"%ver_descr,",".join( "%#09x"%(xx[name]-pe.image_base) for name in ('ASSET',
                                    'CRC','FLAG','CHAR','SLOT','CSOPT','HAIR','CS_STATUS','NUM_DLC','NUM_DLCU')),"};") #asset,crc,flag,char,slot,csopt,hair,cs_status,dlc,dlcu,)),"};")

        print("----------------")
        print("struct doa_func doa%s = {"%ver_descr)
        print("    .randomize_char_list = (void*)0")
        for name, ofs in code:
                print("    ."+name+" = (void*)%#08x,"%(ofs-pe.image_base))
        print(        ",\n};")


        # other stuff # WIP
        # 
        ofs = pe.find_mem_ref( bytes([0x8D,0x49,0x00,0x8D,0x46,0xe4,]), ofs=-9,rel=False) - 4
        print("SpriteTable: %x"%ofs)

        ofs = pe.find_mem_ref( bytes([0x55,0x8B,0xEC,0x56,0x8B,0x75,0x08,0x83,0xFE,0xff,0x74,0x58,0x8B,0xC6,0xC1,0xe8,0x10]),ofs=26, rel=True)
        print("get_sprite: %x"%ofs)

        ofs = pe.find_pattern( bytes([0x55,0x8b,0xec,0x83,0xec,0x0c,0x56,0x8b,0xf1,0x80,0x7e,0x11,0x00,0x0f,0x85]), ofs=0)[0]
        print("CharSelect: change_val %x"%ofs)

        ofs = pe.find_pattern( bytes([0x55,0x8b,0xec,0x83,0xec,0x18,0x56,0x8b,0xf1,0x80,0x7e,0x2d,0x00,0xf,0x85,0x31,0x5]),ofs=0)[0]


        print("load_ndk: %x"%ofs)
        ofs = pe.find_pattern( bytes([0x55,0x8b,0xec,0x83,0xec,0x10,0x56,0x8b,0xf1,0x80,0x7e,0x2d,0x00,0xf,0x85,0xd4,0x1]),ofs=0)[0]


        print("setup_char_select: %x"%ofs)


        ofs=pe.find_mem_ref( bytes([0x8b,0xD7,0x6a,0x0,0x2b,0xd0,0x52,0x56,0xe8]), rel=True )
        print("pfn_is_cs_enabled: %x"%ofs)
        ofs = pe.find_mem_ref( bytes([0x66,0x89,0x45,0x9,0x88,0x45,0xb,0x8b,0x4d,0x8,0x50,0x51,0x56,0x8b,0xcf,0xe8]),rel=True)
        print("pfn_is_cs_idx_available: %x"%ofs)

        ofs = pe.find_mem_ref( bytes([0xf,0xb6,0x3e,0x50,0x53,0x52,0x89,0x45,0xd4,0x83,0xc6,0x02,0xe8]), rel=True)
        print("pfn_dlc_set_num_head: %x"%ofs)

        ofs = pe.find_mem_ref( bytes([0xf,0xb6,0x3e,0x50,0x53,0x52,0x89,0x45,0xd4,0x83,0xc6,0x02,0xe8]), ofs=24, rel=True)
        print("pfn_dlc_set_num_alt: %x"%ofs)

        ofs = pe.find_mem_ref( bytes([0x8b,0x45,0xcc,0x57,0x53,0x50,0xe8]), rel=True)
        print("pfn_dlc_set_num_alt: %x"%ofs)

        ofs = pe.find_mem_ref( bytes([0x88,0x54,0x3d,0xf4,0x8b,0x55,0xcc,0x53,0x52,0x83,0xc6,0x2,0xe8]), rel=True)
        print("pfn_set_head:%x"%ofs)

        ofs = pe.find_mem_ref( bytes([0x50,0xf,0xb6,0xc9,0x51,0x57,0x88,0x54,0x3d]), ofs=19, rel=True)
        print("pfn_set_head:%x"%ofs)
#        ofs = pe.find_mem_ref( bytes([0x8b,0x55,0xcc,0x6a,0x1,0x6a,0x1,0x53,0x52,0xe8]), rel=True)
#        print("pfn_set_cos_state:%x"%ofs)

        ofs = pe.find_mem_ref( bytes([0x6A,0,0x6A,1,0x83,0xc3,0x9c,0x53,0x51,0xeb]), ofs=21, rel=True)
        print("pfn_set_cos_state:%x"%ofs)

        ofs = pe.find_pattern( bytes([0x6a,0,0x68,0,0,0x1,0x0,0x6a,0,0x6a,1,0x6a,0,0x6a,0,0xA3]), ofs=21)[0]
        print("LOAD_DLC_FILES=:%x"%ofs)

        ofs = pe.find_mem_ref( bytes([0xf,0xb6,0xc9,0x8d,0x4,0x80,0x8d,0x04,0xc1,0x8b,0x4d,0x10,0x8d,0x04,0xc0,0x8d,0x04,0x45]) )
        print("DLC_HEAD_CFG: %x"%ofs)
        #ofs = pe.find_mem_ref( bytes([0xf,0xb6,0x45,0x8,0x8d,0x14,0x80,0xf,0xb6,0xc1,0x8d,0x4,0xd0,0x8d,0xc,0xc0,0x8a,0x04,0x4d]))
        #print("DLC_HEAD_CFG: %x"%ofs)

        ofs = pe.find_mem_ref( bytes([0x8b,0x4d,0x10,0x8d,0x04,0x90,0x8a,0x55,0x14,0x8d,0x04,0xc0,0x8d,0x04,0x45]))
        print("DLCHEAD_CFG: %x"%ofs)


        end = pe.find_pattern( bytes([0x8b,0x47,0x04,0x8b,0x55,0xf0,0x8b,0x44,0x10,0x14,0x8d,0x0c,0x5b,0x8b,0x44,0xc8,0xc]))[0]
        ofs = pe.find_pattern( bytes([0x8b,0x4f,0x0c,0x33,0xc0, 0x81,0xf9,0xff,0xff,0x0,0x0,0x74,0x1e]),
                                end_rva=end)[0]
        print("get fx tmc: %x"%ofs)
        ofs = pe.find_pattern( bytes([0x8b,0x4f,0x08,0x81,0xf9,0xff,0xff,0,0,0x74,0x1d]),end_rva=end)[0]
        print("get fx tmcl: %x"%ofs)

        ofs = pe.find_pattern( bytes([0x8b,0x55,0xf0,0x52,0x8d,0x45,0xf8,0x53,0x50,0xe8]),
                               ofs=10)[0]
        print("load_mdl: func call: %x"%ofs)


        ofs = pe.find_pattern( bytes([0x33,0xC5,0x50,0x8d,0x45,0xf4,0x64,0xa3,0,0,0,0,0x8b,0x75,0x8,0x83,0xfe,0x52]),
                               ofs=-0x18) [0]
        print("display_menu:%x"%ofs)

        ofs = pe.find_pattern( bytes([0x83,0xec,0x8,0x53,0x56,0x8b,0xf1,0x8b,0x86,0x80,0,0,0,0x89,0x45,0xf8,0x48,0x57,0x83,0xf8,0x09]),
                               ofs=-3)[0]
        print("start_game: %x"%ofs)

        ofs= pe.find_pattern( bytes([0x33,0xc5,0x50,0x8d,0x45,0xf4,0x64,0xa3,0,0,0,0,0x8b,0xf1,0x8b,0x45,0x8,0x3d,0xff,0xff,0,0]), ofs=-0x1B)[0]
        print("load file: %x"%ofs)

        ofs = pe.find_pattern( bytes([0x55,0x8b,0xec,0x8b,0x45,0x8,0x8b,0x55,0x10,0x53,0x56,0x8b,0xf1,0x8b,0x4d,0x18]))[0]
        print("CAsset_load:%x"%ofs)

        ofs = pe.find_mem_ref( bytes([0x8b,0x8,0xd1,0xe9,0xf6,0xc1,0x1,0x74,0x11,0x8b,0x50,0x14,0xd1,0xea]), rel=True, ofs=-4)
        print("get_sprite_n:%x"%ofs)

        ofs = pe.find_pattern( bytes([0x8b,0x4e,0x8,0x8b,0xc3,0x8a,0x10,0x3a,0x11,0x75,0x1a,0x84,0xd2,0x74,0x12]),
                ofs=-0x60)[0]
        print("apply_updates: %x"%ofs)

        ofs = pe.find_pattern( bytes([0xf,0xb6,0x4c,0x30,0x11,0xf,0xb6,0x46,0x10,0x88,0x4d,0xfc,0x8b,0x55,0xfc,0x52,0x50,0xe8]),just_one=True)[0];
        print("get_num_face: %x"%ofs);
        #ofs = pe.find_pattern( bytes([0x4c,0,0x49,0,0x53,0,0x41]), just_one=False) #b'LISA')
        #print("LISA")
        #for o in ofs: print("%x"%o)

        #ofs = pe.find_pattern( struct.pack('<L', xx['ASSET']), just_one=False)
        #print("ASSET TBL ref")
        #for o in ofs: print("%x"%o)


def main():
        if len(argv) < 2: exit(1)
        if argv[1] == '-test':
                doa = DOA5Exe(argv[2]) # test load
        elif argv[1] == '-analyze':
                if len(argv)<5: exit(1)
                analyze_exe(argv[2],argv[3], argv[4], argv[5] if len(argv)>5 else None)
        else:
                exit(1)

if __name__ == '__main__':
        consoleHandler = logging.StreamHandler(stdout)
        logger.addHandler(consoleHandler)
        logger.setLevel(logging.DEBUG)
        main()
