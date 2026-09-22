#!/usr/bin/env python3

import hashlib
import logging
import io
import os
import struct
import sys
from time import time
import zlib

from collections import namedtuple

logger = logging.getLogger('doa5')
#logger.setLevel(logging.DEBUG)

debug=logger.debug
info=logger.info
warn=logger.warn
error=logger.error

from doa5exe import DOA5Exe,get_zstr,align,SlDef


def char_name(idx): return CHARACTER_TBL[idx]
def char_idx(name): return CHARACTER_TBL.index(name)
def asset_desc(typ): return ASSET_TYPES[typ] if typ in ASSET_TYPES else ""



def read_mod_config_file(path):
        info("loading mod.config ...")
        try:
                with io.open(path, 'r', encoding='utf8') as fs:
                        return fs.read().splitlines()
        except UnicodeDecodeError as e:
                info("utf8 decoding error while reading mod.config")
                info(str(e))
                info("")

        # previously (<4.8) we just used pythons standard encoding
        # try to use that to open the file - in case utf8 parsing failed
        info("try with pythons standard encoding ...")
        try:
                with open(path, 'r') as fs:
                        return fs.read().splitlines()
        except UnicodeDecodeError as e:
                info("nope - didn't work")
                info(str(e))
                info("")

        # running out of ideas ...
        raise DOAError("failed to parse mod.config.(charset encoding error)")


ModCompatInfo = { '1.02' : 0,
                  '1.02A': 1,
                  '1.04' : 1,
                  '1.04p1':1,
                  '1.04p2':1,
                  '1.04p3':1,
                  '1.04p4':1,
                  '1.04p5':1,
                  '1.05'  :2, #new char + new files inserted into the middle of the asset table
                  '1.06'  :3, #added size/crc entry for dlc files -> crc idx changed
                  '1.06p1':3,
                  '1.06p2':3,
                  '1.07' : 3,
                  '1.07p1':3,
                  '1.08'  :4,
                  '1.08Ap1':4,
                  '1.09' : 4,
                  '1.09p1' : 4,
                  '1.09A' : 4,
                  '1.09Ap1' : 4,
                  '1.09B' : 4,
                  '1.09Bp1' : 4,
                  '1.10' : 4,
                  '1.10p1' : 4,
                  '1.10A' : 4,
                  '1.10B' : 4,
                  '1.10C' : 4,
                  '1.10Cp1' : 4,
                }

class ModConfig:
        MOD_FMT_VER=2
        def __init__(self, doa, path):
                self.fmt_ver=0
                self.ver=""
                self.char=None
                self.has_data=False
                self.compat = ModCompatInfo[ doa.exe.ver ]
                self.doa = doa
                self.idx_map = []
                self.need_update = False

                self.path=os.path.join(path, 'mod.config')
                if not os.path.exists(self.path): return

                lines = read_mod_config_file( self.path )

                self.has_data=True
                for i,line in enumerate(lines):
                        try:
                                p=line.split(':')
                                self.parse_line(doa, p)
                        except ValueError:
                                warn("mod.config:%i invalid line"%(i+1))
                                warn("  '%s'"%line)
        def is_old_fmt(self): return self.fmt_ver<self.MOD_FMT_VER
        def make_backup(self):
                for i in range(100):
                        path=self.path+".backup%02d"%i
                        if os.path.exists(path): continue
                        with io.open(self.path, 'r', encoding='utf8') as fsin:
                                buf = fsin.read()
                                with io.open(path, 'w', encoding='utf8') as fsout:
                                        fsout.write(buf)
                                        fname=os.path.basename(path)
                                        info("mod.config: saved backup as "+fname)
                                        return fname
                raise DOAError("failed to make backup of mod.config")


        def map_idx(self, idx): # idx = string '0x####' or 'N0x#####'
                if idx[0]=='N': return self.doa.num_assets + int( idx[1:], 0) # added to the end, mapping doesn't matter
                idx = int(idx, 0)
                for end, diff in self.idx_map:
                        if idx >= end: continue
                        if diff!=None: return idx+diff
                        raise DOAError("mod.config update cannot succeed: revert swap of file idx:%x and try again"%idx)
                        return 0xffff
                return idx
        def map_idxs(self, idxs, start=0): # idxs: list of strings [ '0x####', ]
                return [ self.map_idx(j) for j in idxs[start:] ]

        def resolve_idx(self, doa, args, start=0):
                for i, p in enumerate( doa._resolve_list(self.map_idxs(args, start), "") ):
                        yield i, p

        def get_cos(self, cs_idx):
                x = 0
                for cs in self.char.costumes:
                        if cs.is_xtend: continue
                        if x == cs_idx: return cs
                        x+=1
                return None
        def get_xt_cos(self, xt_idx):
                i = 0
                for cs in self.char.costumes:
                        if not cs.is_xtend: continue
                        if i == xt_idx: return cs
                        i+=1
                return None
        def parse_cs_mod(self, doa, args):
                for i, p in self.resolve_idx( doa, args):
                        self.cs[i]=p
        def parse_asset_list(self, doa, desc, field, args):
                f_i =int(args[1])
                modlist = getattr(desc, field)
                if f_i >= len(modlist):
                        warn("fixup data inconsistency")
                        modlist.set_size(f_i+1)
                for i,new in self.resolve_idx(doa, args, 2):
                        desc.mod_list(field,f_i,i,new)
        def parse_set_list(self, doa, objects, args):
                idx = int(args[1])
                if len(objects) <= idx: objects.set_size(idx)
                obj = objects[ idx ]
                for i,new in self.resolve_idx(doa, args, 2):
                        obj[i]=new

        def parse_face(self,doa, idx, idxs):
                # handle case when number of face in exe change during update or
                # a nfaces: statement got missing somehow
                if len(self.cs.faces) <= idx: self.cs.faces.set_size(idx+1)
                f = self.cs.faces[idx]
                idxs = self.map_idxs( idxs )
                f.hair = HairMdl._make(doa, idxs[:2], "")
                f.face = FaceMdl._make(doa, idxs[2:4], "")
                f.body = BodyMdl._make(doa, idxs[4:], "")

        def parse_line(self, doa, p):
                if p[0]=='.fmt':
                        self.fmt_ver=int(p[1])
                        return
                elif self.fmt_ver==0:
                        if len(p)!=4: raise ValueError("invalid line")
                        doa.assets[int(p[0],0)].swap(name=p[3], flags=int(p[1],0),
                                                        size=int(p[2],0))
                        return
                elif self.fmt_ver>2: raise DOAError("unknown version %d"%self.fmt_ver)

                if p[0][0]!='.': return # silently ignore
                if p[0]=='.ver':
                        self.ver=p[1]
                        comp = ModCompatInfo.get(self.ver, -1)
                        debug("mod.config: for version: %s compat:%d / exe:%s compat:%d"%(self.ver, comp,doa.exe.ver,self.compat))
                        if comp==-1:
                                warn("unknown version / mod.config might not be compatible")
                        elif comp != self.compat:
                                if ModCompatInfo[self.ver]==1 and self.compat ==2:
                                        info("updating file indices 1.04* -> 1.05")
                                        self.idx_map = ( (0x20fe, 0), (0x48f1, 0xc50), (0x48f2, None), (0x51a8, 0xc50-1)  )
                                        self.need_update=True
                                elif ModCompatInfo[self.ver]==1 and self.compat ==3: # should work as well (not tested)
                                        info("updating file indices 1.04* -> 1.06")
                                        self.idx_map = ( (0x20fe, 0), (0x48f1, 0xc50), (0x48f2, None), (0x51a8, 0xc50-1)  )
                                        self.need_update=True
                                elif ModCompatInfo[self.ver]==2 and self.compat==3:
                                        info("updating crc indices 1.05 -> 1.06/1.07")
                                        # just rewrite with new flags(crc idx!)
                                        self.need_update=True
                                elif ModCompatInfo[self.ver]==2 and self.compat==4:
                                        info("updating file indices 1.05 -> 1.08")
                                        self.idx_map = ( (0x5e66, 0), (0x5e67, None), (0x5f2a,-1)  )
                                        self.need_update=True
                                elif ModCompatInfo[self.ver]==3 and self.compat==4:
                                        info("updating file indices 1.06/1.07 -> 1.08")
                                        self.idx_map = ( (0x5e67, 0), (0x5e68, None), (0x5f2b,-1)  )
                                        self.need_update=True
                                else:
                                        raise DOAError("mod.config not usable for selected game version.\nmod.config: %s\n"
                                                       "game.exe: %s"%(self.ver,doa.exe.ver))
                elif p[0]=='.xtend': doa.xtend=int(p[1],0) # just keep the value around
                elif p[0]=='.debug': doa.debug=int(p[1],0) # ditto
                elif p[0]=='.new': doa.make_new_assets( int(p[1],0) )
                elif p[0]=='.swap':
                        doa.assets[self.map_idx(p[1])].swap(name=p[5], flags=int(p[3],0),
                                        size=int(p[4],0), typ=int(p[2],0) )
                elif p[0]=='.char': self.char=doa.get_char(p[1])
                elif p[0]=='.cos': self.cs= self.get_cos( int(p[1]) )
                elif p[0]=='.nfaces': self.cs.faces.set_size(int(p[1]))
                elif p[0]=='.cs_def': self.parse_cs_mod(doa,p[1:])
                elif p[0]=='.glasses': self.cs.glasses=(int(p[1])==1)
                elif p[0]=='.face': self.parse_face(doa,int(p[1]),p[2:])
                elif p[0]=='.nalt': self.cs.alt.set_size(int(p[1]))
                elif p[0]=='.alt': self.parse_asset_list(doa, self.cs, 'alt', p)

                elif p[0]=='.xcos': self.cs= self.get_xt_cos( int(p[1]) )
                elif p[0]=='.xnfaces': self.cs.faces.set_size(int(p[1]))
                elif p[0]=='.xcs_def': self.parse_cs_mod(doa,p[1:])
                elif p[0]=='.xglasses': self.cs.glasses=(int(p[1])==1)
                elif p[0]=='.xface': self.parse_face(doa,int(p[1]),p[2:])
                elif p[0]=='.xnalt': self.cs.alt.set_size(int(p[1]))
                elif p[0]=='.xalt': self.parse_asset_list(doa, self.cs, 'alt', p)

                elif p[0]=='.ndlc_hair': self.char.dlc_hair.set_size(int(p[2]))
                elif p[0]=='.ndlc_face': self.char.dlc_face.set_size(int(p[2]))
                elif p[0]=='.dlc_hair': self.parse_set_list(doa, self.char.dlc_hair,p)
                elif p[0]=='.dlc_face': self.parse_set_list(doa, self.char.dlc_face, p)
                elif p[0]=='.xenable': self.cs.enable=( int(p[1])==1 )
                elif p[0]=='.enable': self.cs.enable=( int(p[1])==1 )

                else: warn("mod.config: invalid command: '%s'"%p[0])

class DOA5:
        def __init__(self, dat_dir=None):

                # duh
                global DOA
                DOA=self

                if not dat_dir: dat_dir = os.path.join( os.path.dirname(sys.argv[0]), 'dat' )

                self.assets=[]
                self.chars=[]
                self.bodys={}
                self.hairs={}
                self.faces={}
                self.lnks={}

                self.xtend=1
                self.debug=0
                self.exe_path=None
                self.game_path=None

                load_names_db(dat_dir)

                self.hairs["ffffffff"]=HairMdl(name="------")
                self.faces["ffffffff"]=FaceMdl(name="------")
                self.bodys["ffffffff"]=BodyMdl(name="------")

        def load(self, exe_path):
                self.exe_path=exe_path
                self.game_path=os.path.dirname(exe_path)
                debug("doa5: game path: %s"%self.game_path)

                # load data from exe
                try:
                        self.exe = DOA5Exe(exe_path)
                except DOA5Exe.Invalid as e:
                        raise DOAError("error: "+str(e)+"\nfile: "+os.path.basename(exe_path))


                st=time()
                # load nfo from lnk files
                self.lnks={}
                self.dlc_files={}
                for entry in os.listdir(path=self.game_path):
                        if not entry.endswith('.bin'): continue
                        try:
                                lnk = LNKFile(self.game_path, entry[:-4])
                                self.lnks[lnk.name]=lnk
                        except DOAError as e:
                                print(e)
                # load dlc
                self.dlc_files={}
                dlc_path=os.path.join(self.game_path, 'DLC')
                try:
                        for entry in os.listdir(path=dlc_path):
                                path=os.path.join(dlc_path,entry,'data')
                                if not os.path.exists( path ): continue
                                for bcm in os.listdir(path=os.path.join(dlc_path,entry)):
                                        if not bcm.endswith('.bcm'): continue
                                        try:
                                                lnk=LNKFile(path, bcm[:-4])
                                                for k in lnk.asset_map.keys():
                                                        self.dlc_files[k]=lnk.name
                                                self.lnks[lnk.name]=lnk
                                        except DOAError as e:
                                                print(e)
                except FileNotFoundError:
                        pass # no DLC directory???
                debug("doa5: loaded nfo from lnk files (%.3f)"%(time()-st))

                # process data from exe
                a_tbl = self.exe.table['ASSET']
                crc_tbl = self.exe.table['CRC']
                fl_tbl = self.exe.table['FLAG']
                self.assets=[ self._make_asset(i, crc_tbl, p, fl) for i,(p,fl) in enumerate(zip(a_tbl, fl_tbl))]
                self.num_assets = len(self.assets)
                self.num_crc = len(crc_tbl)
                debug("initial len: %x assets %x crc"%(self.num_assets, self.num_crc))

                for k, lnk in self.lnks.items(): # update info for dlc packages
                        if lnk.blp: self._update_from_blp(lnk)

                for p in self.assets: p.update_status()

                # process costume data from exe
                tbl_ch=self.exe.table['CHAR']
                tbl_sl=self.exe.table['SLOT']
                tbl_cs=self.exe.table['CSOPT']
                tbl_h=self.exe.table['HAIR']
                tbl_f=self.exe.table['FACE']
                self.chars=[]
                for i,(ch,sl,cfg,h,f) in enumerate(zip(tbl_ch,tbl_sl,tbl_cs,tbl_h,tbl_f)):
                        if ch.cos==0: cos=None
                        else: cos = [ self._make_cos(i, j, cs,cfg, (j<cfg.num_base)) for j, cs in enumerate(ch.cos) ]
                        ref = str(char_name(i))+"_DLC"
                        dlc_hair= [HairMdl._make(self, a, ref) for a in h ] if h!=0 else []
                        dlc_face= [FaceMdl._make(self, a, ref) for a in f ] if f!=0 else []
                        slots=sl.slots if sl.slots else []
                        self.chars.append( CharDesc(i, CHARACTER_TBL[i], slots, cos,dlc_hair,dlc_face) )

                # process stage data
                tbl_st=self.exe.table['STAGE']
                self.stages= [ self._resolve_list(st[:-2],"stage%02d"%i) +
                        [st[-2],] + self._resolve_list(st[-1],"stage%02d"%i) for i,st in enumerate(tbl_st) ]

                # add extension slots
                for char in self.chars:
                        if not char.slots: continue
                        ENABLE = self.exe.table['CS_STATUS'][char.idx]
                        num_base = tbl_cs[char.idx].num_base
                        num_base_slots = tbl_sl[char.idx].num_base
                        # note: num_dlc is the number of pre-LastRound DLC's, those are now (mostly) included
                        # enabling a costume as a non-dlc is controlled by: COS_ENABLE(which has 42 entries per char)
                        # this controls the first 42 costumes (which include COS_*, DLC_* and also DLCU_* )
                        num_dlc = self.exe.table['NDLC'][char.idx]

                        # look for last used idx in ENABLE array
                        for last_used in range(41,num_base-2,-1):
                                if ENABLE[last_used]!=0: break
                        num_extend = 41 - last_used
                        pos = num_base + num_dlc

                        debug("char(%d)%s: num_base: %d num_dlc: %d last_used: %d => xtend: %d @%d"%(
                                char.idx, char.name, num_base, num_dlc, last_used, num_extend, pos))

                        new_cs = [ CosDesc( [None,None,None,None,None], False, False, [], [], base=False, xtend=True ) for i in range(num_extend)]
                        char.costumes = char.costumes[:pos] + new_cs + char.costumes[pos:]

                        # adjust slots
                        pos_slot = num_base_slots + num_dlc
                        debug("adj slot: [:%d] [%d:%d] [%d:%d"%(pos_slot,pos_slot,pos_slot+num_extend,pos_slot+num_extend,len(char.slots)+num_extend))
                        new_slots = [ SlDef(j, 2) for j in range(pos,pos+num_extend) ]
                        shift_slots = [ SlDef( sl.cs_idx+num_extend,2) for sl in char.slots[pos_slot:] ]

                        char.slots = char.slots[:pos_slot] + new_slots + shift_slots


        def load_mod(self):
                self.mod = ModConfig(self, self.game_path)

        def revert_swap(self, asset):
                info("doa5: reverting swap: "+asset.alias)
                path = os.path.join( self.game_path, asset.name.replace('/',os.sep))
                info(" .deleting "+path)
                try:
                        os.remove(path)
                except FileNotFoundError as e:
                        print(e)
                asset.revert()
                asset.update_status()
                info("doa5: .restored "+asset.alias)


        def delete_asset(self, asset):
                info("doa5: deleting: "+asset.alias)
                if not asset.is_new: raise DOA5Error("trying to delete builtin asset")
                del self.assets[asset.idx]
                for i in range(asset.idx, len(self.assets)):
                        #print(">adj %x->%x"%(self.assets[i].idx, i))
                        self.assets[i].idx = i
                path = os.path.join( self.game_path, asset.name.replace('/',os.sep))
                info(" .deleting "+path)
                try:
                        os.remove(path)
                except FileNotFoundError as e:
                        print(e)

        def make_new_assets(self, num):
                i = len(self.assets)
                assets = [ DoaAsset(i, "(NONE)","(NONE)", 0, "NO_LINK",0, 0, 0) for i in range(i,i+num) ]
                for p in assets: debug("new asset(%x):"%p.idx+str(p))
                for p in assets: p.is_new = True

                self.assets+= assets
                return assets

        def swap(self, asset, mod_dir, src, typ, compression, dst=None):
                if not asset: return
                if not os.path.exists(src): return

                with open(src, 'rb') as fs:
                        data_in = fs.read()

                if len(data_in)<0x51200: # < 50kb
                        print("disable compression in small files")
                        compression=False

                # flag
                flags = asset.flags & ~0x20000000 # don't do crc
                flags = flags & ~0x80000000 # don't waste time with encryption

                if not compression: # probably should just write flags=0
                        flags = flags & ~0x0000ffff # clear crc tbl idx
                        flags = flags & ~0x40000000 # clear zip flag

                # path
                if not dst: dst=os.path.join(mod_dir, os.path.basename(src))
                if flags & 0x40000000: dst+='.__'

                out_path = os.path.join( self.game_path, dst )
                if os.path.exists( out_path ):
                        # allow updating the same file
                        if not asset.has_mod() or asset.name != dst:
                                raise DOAError("target file already exists in mod/ folder: %s"%dst)

                # create dir if necessary
                dst_dir=os.path.join(self.game_path, os.path.dirname(dst))
                if not os.path.isdir(dst_dir): os.makedirs(dst_dir)

                info("doa5: swap %s -> %s typ:%#02x"%(asset.alias, dst, typ))

                # compress
                if flags & 0x40000000:
                        out=struct.pack('<L', len(data_in))
                        packed = pack_buffer(data_in)
                        out+=packed
                else: out = data_in

                with open(out_path, 'wb') as fs:
                        fs.write(out)
                        info("doa5: .written %s"%dst)

                #NOTE the game uses unix path seperators('/') internally
                dst = dst.replace('\\','/')
                asset.swap(name=dst, flags=flags, size=len(data_in), typ=typ)

        def extract_asset(self, asset, dst_dir):
                if not asset or not asset.has_data: return
                if not dst_dir: dst_dir='.'
                elif not os.path.isdir(dst_dir):
                        os.makedirs(dst_dir)
                st=time()
                info("doa5: extract: %s -> %s"%(asset.alias, dst_dir))
                if asset.lnk == 'NO_LINK':
                        # read directly
                        lnk=None
                        path=os.path.join(self.game_path,asset.name.replace('/',os.sep))
                        info(" .from: "+path)
                        with open(path, 'rb') as fs: buf=fs.read()
                        if asset.flags & 0x40000000:
                                buf=buf[4:] # discard
                                buf=unpack_buffer(buf)
                elif asset.is_dlc:lnk=self.lnks[ self.dlc_files[asset.name] ]
                elif asset.lnk in self.lnks: lnk = self.lnks[asset.lnk]
                else: raise DOAError("invalid lnk: %s"%asset.lnk)

                if lnk: buf = lnk.extract(asset.name, asset.flags)

                i = asset.alias.rfind('/')
                if i!=-1: out_name=asset.alias[i+1:]
                else: out_name=asset.alias
                with open( os.path.join(dst_dir, out_name),'wb') as fs:
                        fs.write(buf)
                info("extract done (%.3f)"%(time()-st))

        def write_mod_config(self):
                path=os.path.join(self.game_path, 'mod.config')

                info("updating mod.config ...")

                buf =".fmt:%d\n"%ModConfig.MOD_FMT_VER
                buf+=".ver:%s\n"%self.exe.ver
                buf+=".xtend:%d\n"%self.xtend
                buf+=".debug:%d\n"%self.debug
                new = len(self.assets)-self.num_assets
                if new:
                        buf+=".new:%#04x:0\n"%new # don't use new crc yet
                # swap
                for p in self.assets:
                        if p.has_mod(): buf+=p.mod_cmd(self)+"\n"
                # face options
                for ch in self.chars:
                        cs_mod = mod=ch.mod_save(self)
                        xt_idx=0
                        for cs_i, cs in enumerate(ch.costumes):
                                mod=cs.mod_cmd(self)
                                if cs.is_xtend:
                                        if mod: cs_mod+=".xcos:%d\n%s"%(xt_idx,mod)
                                        xt_idx+=1
                                else:
                                        if mod: cs_mod+=".cos:%d\n%s"%(cs_i-xt_idx,mod)
                        if cs_mod:
                                buf+=".char:%s\n"%ch.name
                                buf+=cs_mod
                with io.open(path, 'w', encoding='utf8') as fs:
                        fs.write(buf)

        def get_char(self, name):
                for ch in self.chars:
                        if ch.name==name: return ch
                raise ValueError

        def _update_from_blp(self, lnk):
                for idx, entry in lnk.blp.items():
                        if idx>len(self.assets):
                                error("invalid idx:%#x in blp:%s"%(idx, lnk.name))
                                continue
                        p = self.assets[idx]
                        if entry.flags & 0x40000000: size=entry.size_unc
                        else: size=entry.size

                        if p.flags != entry.flags and p.size!=entry.size:
                                #debug(".update %x %s with info from blp:%s"%(idx,p.alias,lnk.name))

                                p.flags,p.size=entry.flags,entry.size
                        p.commit_change()

        def _resolve(self, idx, ref, invalid=(0xffff,)):
                if idx in invalid: return None
                if idx < len(self.assets):
                        a = self.assets[idx]
                        a.refs.append(ref)
                        return a
                warn("unresolved asset idx: %x"%idx)
                return None

        def _resolve_list(self, input_list, ref, invalid=(0xffff,)):
                return [ self._resolve(p, ref, invalid) for p in input_list ]


        def _make_hairstyle(self, idxs, ref):
                hair = HairMdl._make(self, idxs[:2], ref)
                face = FaceMdl._make(self, idxs[2:4], ref)
                body = BodyMdl._make(self, idxs[4:], ref)
                return Head( hair, face, body)

        def _make_cos(self, ch_idx, cs_idx, cos, cfg, is_base):
                ref="%s:COS_%02d"%(CHARACTER_TBL[ch_idx],cs_idx+1)
                cs_def=[ self._resolve(p, ref) for p in cos[:5] ]
                faces = [ self._make_hairstyle(f, ref) for f in cos.faces ] if cos.faces!=0 else []
                alt=[ self._resolve_list(a,ref) for a in cos.alt ] if cos.alt!=0 else []
                enable = self.exe.table['CS_STATUS'][ch_idx]
                if cs_idx <42: enable= enable[cs_idx]
                else: enable=0

                return CosDesc(cs_def, cfg.glasses[cs_idx]==2, enable, faces, alt, base=is_base)

        def _make_asset(self, idx, crc, p, fl):
                if fl.flag&0xffff >= len(crc):
                        raise DOAError("%s %08x %04x"%(p.name, fl.flag, fl.flag&0xffff))
                return DoaAsset( idx, lookup_name(p.name), p.name, p.typ, p.lnk, p.replace, fl.flag,
                                crc[fl.flag&0xffff].size if fl.flag & 0x40000000 else fl.size)

##
#
class Filter:
        def __init__(self, func, val, success=True):
                self.func = func
                self.val=val
                self.success=success
class FilterList:
        def_filter={ 'mod' : ( lambda p,v: p.has_mod(), None),
                     'alias': ( lambda p,v: p.name!=p.alias, None),
                     'dlc' : ( lambda p, v: 'chara_dlccos' in p.lnk, None),
                     'typ' : ( lambda p, v: p.typ==v, 'i'),
                     'lnk' : ( lambda p, v: v in p.lnk, 's'),
                     'file': ( lambda p, v: p.name in DOA.dlc_files and v in DOA.dlc_files[p.name], 's'),
                     'zip' : ( lambda p, v: p.flags&0x40000000!=0, None ),
                     'idx' : ( lambda p, v: p.idx==v, 'i'),
                     'crc' : ( lambda p, v: p.flags&0xffff==v, 'i'),
                     'data': ( lambda p, v: p.has_data, None),
                     'patch':( lambda p, v: p.replace!=None, None),
                     'obsolete': ( lambda p, v: not p.has_mod() and p.replace and p.replace.updates[-1]!=p,None),
                     'update': ( lambda p, v:  len(p.updates)!=0, None),
                     'new' : ( lambda p, v: p.is_new, None), }
        def __init__(self):
                self.reset()
        def reset(self):
                self.filters={}
                self.txt_filter=[]
                self.update()
        def set_filter(self, name, fi):
                if fi==None:
                        if name in self.filters: del self.filters[name]
                else: self.filters[name]=fi
        def update(self):
                assets=list(DOA.assets) # copy
                for f in self.filters.values():
                        assets[:]=[ p for p in assets if f.func(p, f.val)==f.success ]
                self.result=sorted(assets, key=lambda p: p.alias)
        def __getitem__(self, idx): return self.result[idx]
        def __iter__(self): return self.result.__iter__()
        def __next__(self): return self.result.__next__()
        def __len__(self): return len(self.result)
        def total(self): return len(DOA.assets)
        def create_filter(self, word):
                success,i=True,0
                if word[0]=='-': success,i=False,1
                if word[i]!='.':
                        return Filter(lambda p,val: val in p.name or val in p.alias,
                                        word[i:], success)
                key, arg = word[i+1:],None

                if key.find(':')!=-1: key,arg=key.split(':',maxsplit=1)
                if key not in FilterList.def_filter: raise ValueError

                func, has_arg = FilterList.def_filter[key]
                if not has_arg: return Filter(func, None,success)
                # need arg
                if not arg: raise Error
                if has_arg=='s': return Filter(func, arg, success)
                elif has_arg=='i':
                        if arg[-1]=='x': raise Error  # catch '0x'
                        else: return Filter(func, int(arg, 0), success)
                # huh, shouldn't end up here
                raise ValueError
        def set_filter_string(self,filter_string):
                idx=0
                res=0
                new_filter = filter_string.split()
                for idx in range(max(len(self.txt_filter), len(new_filter))):
                        if len(new_filter)==0 or idx >= len(new_filter):
                                self.set_filter("custom%d"%idx, None)
                                res=1
                                continue
                        f = new_filter[idx]
                        if len(f)<3: continue
                        if idx < len(self.txt_filter) and self.txt_filter[idx]==f:
                                continue
                        try:
                                f = self.create_filter(f)
                                self.set_filter("custom%d"%idx,f)
                                res=1
                                idx+=1
                        except Error: # not enough input
                                pass
                self.txt_filter = new_filter
                return res

############################
# name<->alias db

NAME_DB={}
NAME_CHANGES={}
def lookup_name(name): return NAME_DB[name] if name in NAME_DB else name

def load_names_db(path):
        if NAME_DB: return # only load once
        for entry in os.listdir(path=path):
                if not entry.endswith('.dat'): continue
                with open(os.path.join(path, entry), 'r') as fs:
                        lines = fs.read().splitlines()
                for i,line in enumerate(lines):
                        if not line or line[0]=='#': continue
                        try:
                                p=line.split()
                                if len(p)!=2: raise ValueError
                        except ValueError:
                                error("invalid data in %s:%d:'%s'"%(entry,i,line))
                                continue
                        if p[1] in NAME_DB: error("multiple alias for: %s"%p[1])
                        NAME_DB[p[1]]=p[0]

        for entry in os.listdir(path=path):
                if not entry.endswith('.changed'): continue
                with open(os.path.join(path, entry), 'r') as fs:
                        lines = fs.read().splitlines()
                for i,line in enumerate(lines):
                        if not line or line[0]=='#': continue
                        try:
                                p=line.split()
                                # format
                                # alias<TAB>old<TAB>new
                                if len(p)!=3: raise ValueError
                        except ValueError:
                                error("invalid data in %s:%d:'%s'"%(entry,i,line))
                                continue
                        if p[1] in NAME_DB: error("multiple alias for: %s"%p[1])
                        NAME_DB[p[1]]=p[0] # keep names for old stuff
                        NAME_CHANGES[p[1]]=p[2]

        debug("name db loaded: %d entries"%len(NAME_DB))


##################################
# data handling
class LNKFile:
        def __init__(self, path, name):
                self.path=path
                self.name=name
                self.asset_map={}
                self.blp={}

                if not os.path.exists( os.path.join(path, name+".lnk")):
                        raise DOAError("LNKFile: failed to open %s.lnk"%name)

                with open( os.path.join(path, name+".bin"), 'rb') as fs:
                        st=time()
                        self._parse_bin(fs)
                        #debug("loaded bin: %s %.3f"%(name,(time()-st)))
                        blp_path= os.path.join(path,name+".blp")
                        if os.path.exists(blp_path):
                                with open(blp_path, 'rb') as fs:
                                        self._parse_blp(fs)
                                        #debug(".read "+name+".blp");

        def _parse_bin(self, fs):
                lnk_id_map={}
                lnk_name_map={}

                buf = fs.read()
                magic, nlnk, nfiles, lnk_ofs, fi_ofs, lnk_names_ofs, fi_names_ofs = struct.unpack_from("<4s6L", buf)
                if magic!=b'LFMO': raise DOAError("invalid .bin file:%s"%self.bin)

                #FIXME: .bin file could point to multiple lnk files,
                # but there is no file using that
                if nlnk>1: raise DOAError(".bin file %s using more than 1 lnk - not supported")

                # for each entry lnk_id, ofs of lnk_name
                idx, name = struct.unpack_from("<2L", buf, lnk_ofs)
                name = get_zstr(buf, name)

                # for each entry: lnk_id, idx in lnkfile, ofs of name str
                data=struct.unpack_from("<%dL"%(nfiles*3),buf,fi_ofs)
                for i in range(nfiles):
                        # note: skip initial '/'
                        name = get_zstr(buf, data[i*3+2])[1:]
                        lnk_id, lnk_idx, ofs = data[i*3:i*3+3]
                        # don't need ofs, parsing the header is fast enough
                        self.asset_map[name] = lnk_idx


        BLPDesc=namedtuple('BLPDesc',('flags','size','size_unc','crc'))
        def _parse_blp(self, fs):
                if fs.read(4) != b'1PIF':
                        raise DOAError("invalid blp file: %s"%blp_path)
                nfiles, hsize, fsize = struct.unpack('<3L',fs.read(12))
                tbl = memoryview(fs.read(5*4*nfiles)).cast('I',shape=[nfiles,5])
                for idx,size,flags,size_unc,crc in tbl.tolist():
                        self.blp[idx]= LNKFile.BLPDesc(flags, size, size_unc, crc)
                tbl.release()

        def has(self, name): return True if name in self.asset_map else False

        def _lnk_header_nfo(self, fs, idx):
                buf=fs.read(28)
                magic, u0, nfiles, u1, size, u2, align = struct.unpack("<4s6L",buf)
                #debug("lnk:%s magic:%s size:%x u0:%x u1:%x u2:%x align:%x"%(lnk_name,str(magic),
                #                                                size,u0,u1,u2,u3))
                if idx >= nfiles: raise DOAError("_lnk_header_nfo: idx:%d nfiles:%d"%(idx,nfiles))
                buf=fs.read(32*nfiles)
                data=struct.unpack_from('<8L',buf, 32*idx)
                return data[1],data[3] # ofs, size


        def extract(self, name, flags=0):
                if name not in self.asset_map: raise DOAError("LNKFile.extract: invalid name: %s"%name)

                idx = self.asset_map[name]
                with open( os.path.join(self.path, self.name+'.lnk'), 'rb') as fs:
                        ofs, size = self._lnk_header_nfo(fs, idx)
                        fs.seek(ofs)
                        buf = bytearray(size)
                        fs.readinto(buf)
                        debug("extract from lnk:%s/%d ofs:%x bytes:%x"%(self.name, idx, ofs, size))
                if flags & 0x40000000: # ZIP
                        size = struct.unpack_from("<L",buf)[0]
                        buf[:4]=[] # discard

                if flags & 0x80000000:
                        key=generate_key(size)
#                        print(" ..key:0x%s"%buf_str(key))
                        xor_buffer(buf, key)

                if flags & 0x40000000:
                        #dt2=time()
                        mem=memoryview(buf)
                        buf = unpack_buffer(mem)
                        mem.release()
                        debug(" ..unpacked %#06x/exp:%#06x"%(len(buf), size))
                        if len(buf)!=size: warn("ended up with wrong size")
                else:
                        debug(" ..uncompressed")
                return buf


def pack_buffer(buf):
        buf=memoryview(buf)
        res=bytearray([])
        while(len(buf)):
                nbytes=0x4000
                if nbytes > len(buf):
                        nbytes=len(buf)
                out = bytearray([0,0,0,0,0x78, 0x9C])
                adler32 = zlib.adler32(buf[:nbytes])
                try:
                        defl = zlib.compressobj(-1, wbits=-zlib.MAX_WBITS)
                        out.extend(defl.compress(buf[:nbytes]))
                        out.extend(defl.flush())
                except Exception as ex:
                        raise DOAError("zlib exception")

                # chksum
                out.extend( struct.pack(">L", adler32) )

                size=len(out)-4
                struct.pack_into('<L',out, 0, size|0x8000)
                pad = align(len(out),0x10) - len(out)
                res.extend( out )
                res.extend( [0]*pad )
                buf=buf[nbytes:]
        buf.release()
        return res

def unpack_buffer(mem):
        out=bytearray()
        block_ofs=0
        block=mem
        while(len(block)>6):
                size = struct.unpack_from('<L', block)[0]
                if size & 0x8000:
                        size = size & ~0x8000
                        if block[4:6] != b'\x78\x9C':
                                raise DOAError("unpack @%#06x: %s"%(block_ofs,
                                        " ".join(["%x"%b for b in block[:10]])))
                        try:
                                out.extend( zlib.decompress(block[6:],
                                            -zlib.MAX_WBITS) )
                        except zlib.error as ex:
                                raise DOAError(ex)
                else:
                        out.extend( block[4:4+size] )

                next_block=align( block_ofs + size+4, 0x10)
                block = block[next_block - block_ofs:]
                block_ofs=next_block
        return out

def xor_buffer(buf, key):
        key = bytearray(key)
        key = (key*(len(XOR_PHRASE)//len(key)+1))[:len(XOR_PHRASE)]
        key[:]= [ (a^b) for a,b in zip(XOR_PHRASE,key) ]

        key = (key*( len(buf)//len(key)+1))[:len(buf)]
        buf[:] = [( (d^k) if (d and d!=k) else d)for d,k in zip(buf,key)]

def generate_key(num):
        A = num+0x3e7
        B = A*8 # FIXME: missing sth here to catch the possible overflow
        B -= A
        C = int(B / 0xB) + int(num % 0x11) + 0x1AC
        key=[]
        sh = 24
        while sh>=0:
                val = (C >> sh)&0xff
                if val > 0: key.append(val)
                sh-=8
        return bytes( key )

###############################
# definitions

# yeah TeamNinja, we hear you :p
XOR_PHRASE = b"Except as expressly authorized, it is strictly prohibited to reproduce, distribute, exhibit or modify this software and any of its contents, including audio and visual contents. By way of example, to capture, copy or download any of the contents in this software, including audio and visual contents, onto any hardware or other software source media for any purpose, by the Internet or any other source, is strictly prohibited. Reversed engineering, decompiling or disassembly of this software is also strictly prohibited."

CHARACTER_TBL=[ 'ZACK','TINA','JANNLEE','EIN','HAYABUSA', 'KASUMI', #0x0-0x5
                'GENFU','HELENA','LEON','BASS','KOKORO', 'HAYATE',  #0x6-0xB
                'LEIFANG','AYANE','ELIOT','LISA','ALPHA152', None,  #0xC-0x11
                None,'BRAD','CHRISTIE','HITOMI','RTM',None,          #0x12-17
                'BAYMAN',None,None,None,None,'RIG',                 #0x18-1D
                'MILA','AKIRA','SARAH','PAI',None,'AYANE_BOSS',             #0x1E-0x23
                'HAYATE_BOSS', 'KASUMI_BOSS','HAYABUSA_BOSS','MOMIJI','RACHEL','JACKY',          #0x24-0x29
                'MARIE','PHASE4','NYOTENGU','HONOKA','RAIDOU','NAOTORA', 'MAI' ]

######
# asset types
ASSET_TYPES={0x2:'shader pack',
        0x3:'mpm anim??',
        0x4:'cam',
        0x5:'bin',
        0x6:'sktm',
        0x7:'mpm char animation',
        0x8:'---c costume cfg',
        0x9:'--p costume icon',
        0xa:'tmc npc',
        0xb:'tmcl npc',
        0xc:'mpm npc anim',
        0xe:'mpm face anim',
        0x11:'tmc hair',
        0x12:'tmcl hair',
        0x13:'tmc face',
        0x14:'tmcl face',
        0x15:'tmc debug model',
        0x16:'tmcl debug model',
        0x17:'--h alt tex',
        0x18:'--hl alt tex',
        0x19:'tmc costume',
        0x1a:'tmcl costume',
        0x1b:'tmc stage',
        0x1c:'tmcl stage',
        0x1e:'mpm stage anim',
        0x1f:'scn',
        0x20:'sprites',
        0x21:'font file',
        0x22:'text',
        #0x23:'??',
        0x24:'phyd physics',
        #0x25:'stage ??',
        #0x26:'stage ??',
        0x27:'tmc effects',
        0x28:'tmcl effects',
        #0x29:'??',
        0x2b:'xws sound file',
        0x2c:'sound(extern)',
}

######################
# handle modding

class ModStruct:
        def __init__(self, init):
                self._orig = list(init)
                self._lookup=dict(zip(self._fields,range(len(self._fields))))

        def get_orig(self, key):
                if type(key)==type(0): return self._orig[ key ]
                return self._orig[ self._lookup[key] ]
        def __len__(self): return len(self._orig)
        # this will be only called when the field hasn't been written to
        def __getattr__(self, key):
                if key in self._fields: return self.get_orig(key)
                raise KeyError(key)
        # note: setting the attribute is seperate from the value in the list
        def __setattr__(self, key, val):
                self.__dict__[key] = val
                if key in self._fields and val==self.get_orig(key):
                        delattr(self,key)
        def tolist(self): return [ getattr(self,f) for f in self._fields ]

        def __setitem__(self, idx, val): setattr(self, self._fields[idx], val)
        def __getitem__(self, idx): return getattr(self, self._fields[idx])

        def iter(self):#probably don't need this
                for f in self._fields: yield getattr(self, f)
        def iterorig(self):
                for f in self._fields: yield self.get_orig(f)

        def revert(self, key=None):
                if key == None:
                        for f in self._fields: self.revert(f)
                else:
                        if type(key)==type(0): key=self._fields[key]
                        if key in self.__dict__: delattr(self,key)

        def commit_change(self):
                for f in self._fields:
                        if f in self.__dict__:
                                self._orig[self._lookup[f]] = getattr(self,f)
                                delattr(self, f)
        def has_mod(self):
                for f in self._fields:
                        if f in self.__dict__: return 1
                return 0

class ModStructList:
        def __init__(self, Cls, init):
                self._Cls=Cls
                self._orig = list(init)
                self._data={}
                self._size = len(self._orig)
        def get_orig(self, idx): return self._orig[idx]
        def __len__(self): return self._size
        def __getitem__(self, idx):
                if idx >= self._size: raise IndexError
                if idx in self._data: return self._data[idx]
                else: return self._orig[idx]
        def __setitem__(self, idx, val):
                if idx>self._size: raise IndexError
                self._data[idx]=val
                if idx < len(self._orig) and self._data[idx]==self._orig[idx]:
                        print("del")
                        del self._data[idx]
        def revert(self, idx=None):
                if idx==None:
                        self._size = len(self._orig)
                        self._data={}
                        for p in self._orig: p.revert()
                else: del self._data[idx]
        def has_mod(self):
                if self._size!=len(self._orig) or (len(self._data)!=0): return 1
                for x in self._orig:
                        if x.has_mod(): return 1
                return 0
        def itermod(self):
                for i in range(self._size):
                        if i in self._data: yield i
                        elif self._orig[i].has_mod(): yield i
        def set_size(self, num, *args):
                for i in range(num, self._size):
                        if i in self._data: del self._data[i]
                for i in range(self._size,num): # use orig if possible
                        if i >= len(self._orig): self._data[i]=self._Cls(*args)
                self._size=num
        def mod_save(self, DOA, cmd, num_cmd=None):
                res=""
                if not num_cmd: num_cmd="n"+cmd
                if len(self._orig) != self._size:
                        res+=".%s:%d\n"%(num_cmd,self._size)
                for idx in self.itermod():
                        res+=".%s:%d:"%(cmd,idx)+self[idx].mod_save(DOA)+"\n"
                return res


def ass2idx(p,DOA):
        if p.idx >= DOA.num_assets: return "N%#06x"%(p.idx - DOA.num_assets)
        else: return "%#06x"%p.idx
def assL2idx(plist, DOA, zero=0xffff):
        return ":".join([ ass2idx(p, DOA) if p else "%#06x"%zero for p in plist])

class DoaAsset(ModStruct):
        _fields=['alias','name','typ','lnk','upd_idx','flags','size']
        def __init__(self, idx, *args):
                ModStruct.__init__(self, args)
                self.idx=idx
                self.has_data=-1
                self.is_new = False
                self.is_dlc=False
                self.updates=[]
                self.replace=None # asset of upd_idx
                self.refs=[]

        def update_status(self):
                self.has_data=0
                if self.lnk=="NO_LINK":
                        self.has_data = os.path.exists(os.path.join(DOA.game_path,
                                                       self.name.replace('/',os.sep)) )
                elif self.lnk in DOA.lnks and DOA.lnks[self.lnk].has(self.name):
                        self.has_data = 1
                elif self.name in DOA.dlc_files:
                        self.has_data= 1
                        self.is_dlc=True
                elif 'chara_dlccos' in self.lnk: self.is_dlc = True


                upd_idx=self.upd_idx&0xffff
                if self.replace: # if we rerun update() make sure we don't
                                 # append to updates twice
                        idx = self.replace.updates.index(self)
                        del self.replace.updates[idx]
                if upd_idx != 0xffff:
                        orig=DOA.assets[upd_idx]
                        orig.updates.append(self)
                        orig.updates.sort(key=lambda p: p.idx)
                        self.replace=orig
                else: self.replace=None

        def swap(self, name, flags, size, typ=-1):
                if typ==-1: typ=self.typ # compat with old swap
                # build new alias
                i=name.find('/')
                if i!=-1: alias=name[i+1:]
                else: alias=name
                if alias.endswith('.__'): alias=alias[:-3]
                self.alias = alias
                self.name = name
                # make sure we don't change the crc idx (unless set to none)
                # also helps when updating to new version with changed file table (like 1.05 update)
                crc_idx = self.flags&0xffff
                new_crc_idx = flags&0xffff
                if new_crc_idx != 0xffff and new_crc_idx!=crc_idx:
                    nf = (flags&0xffff0000) | crc_idx
                    flags = nf
                self.flags = flags

                self.size = size
                if self.typ != typ: # don't use for updates anymore
                        self.upd_idx |= 0xffff
                self.typ = typ
                self.lnk = 'NO_LINK'
                self.update_status()
        def mod_cmd(self, DOA):
                return ".swap:"+ass2idx(self, DOA)+":%#04x:%#010x:%#08x:%s"%(self.typ,self.flags,
                                                                self.size,self.name)
        def __repr__(self): return "asset: %#x %s"%(self.idx,self.alias)

class AssetComp(ModStruct): # fields point to DoaAsset
        _none = 0xffff # value used for empty
        def _make(doa, comp_dict, Cls, idxs, ref, invalid=(0xffff,)): # param: (int:asset_idx)
                key = "".join( ["%04x"%(0xffff if i in invalid else i) for i in idxs ] )
                #comp = comp_dict.get(key, None)
                if 1: #not comp:
                        comp = Cls( doa._resolve_list(idxs, ref, invalid) )
                        #print("created: %s"%str(comp))
                        #comp_dict[key] = comp
                return comp

        def __init__(self, *args):
                if len(args)==0: args=[None]*len(self._fields)
                ModStruct.__init__(self, args)
                self.name = "_unnamed_"
                if args[0]:
                        self.name = args[0].alias
                        i = self.name.rfind('.')
                        if i!=-1: self.name=self.name[:i]
        def get_type(self, idx): return self._typ[idx]
        def mod_save(self, DOA):
                return ":".join( [ ass2idx(p, DOA) if p else "0xffff" for p in self ])
        def __repr__(self):
                x="name:"+self.name+"\n"
                x+="".join( ["  %s\n"%str(p) for p in self])
                return x

class HairMdl(AssetComp):
        _fields=['tmc','tmcl']
        _typ=[0x11,0x12]
        def _make(doa, idxs, ref):
                return AssetComp._make(doa, doa.hairs, HairMdl, idxs, ref)
        def __init__(self, asset_list=[], name=None):
                AssetComp.__init__(self, *asset_list)
                if name: self.name=name


class FaceMdl(AssetComp):
        _fields=['tmc','tmcl']
        _typ=[0x13,0x14]
        def _make(doa, idxs, ref):
                return AssetComp._make(doa, doa.faces, FaceMdl, idxs, ref)
        def __init__(self, asset_list=[], name=None):
                AssetComp.__init__(self, *asset_list)
                if name: self.name=name

class BodyMdl(AssetComp):
        _fields=['tmc','tmcl']
        _typ=[0x19,0x1a]
        def _make(doa, idxs, ref):
                return AssetComp._make(doa, doa.bodys, BodyMdl, idxs, ref, invalid=(0,0xffff))
        def __init__(self, asset_list=[], name=None):
                AssetComp.__init__(self, *asset_list)
                if name: self.name=name

class Costume(AssetComp):
        _fields=BodyMdl._fields+['---c','--p','phyd']
        _typ=BodyMdl._typ+[0x8,0x9,0x24]

class Head(ModStruct):
        _fields=['hair','face','body']
        _typ=HairMdl._typ + FaceMdl._typ + BodyMdl._typ
        def __init__(self, *args):
                if len(args)==0: args=(HairMdl(),FaceMdl(),BodyMdl() )
                ModStruct.__init__(self, args)
        def has_mod(self):
                for p in self:
                        if p.has_mod(): return 1
                return ModStruct.has_mod(self)
        def tolist(self): return sum([ p.tolist() for p in self ],[])
        def mod_save(self, DOA):
                return ":".join( [ p.mod_save(DOA) for p in self ] )


class AltTex(AssetComp):
        _fields=['--h','--hl'] # does this make problems as attribute?
        _typ=[0x17,0x18]


def prep_import(DOA, mod_dir, what, assets):
        action={ 'cos':Costume, 'hair' : HairMdl, 'face' : FaceMdl, 'body' : BodyMdl,
                   'detail' : AltTex }
        action2={'config': ('--c',0x8), 'icon':('--p',0x9), 'phyd':('phyd',0x24) }

        if what in action:
                fields = action[what]._fields
                typs = action[what]._typ
        elif what in action2:
                fields=(action2[what][0],)
                typs=(action2[what][1],)
        else: return
        num = len(fields)
        num_unused = -1
        if assets==None:
               data=FilterList()
               data.set_filter_string(".obsolete -.mod")
               data.update()
               if len(data)<num: # raise DOAError("not enough unused assets left")
                       assets = [None]*num
               else:
                       assets= [ data[i] for i in range(num) ]
                       debug("use unused assets")
                       for p in assets: debug(p)
               num_unused = len(data)
        else:
                fields = [ f for f,a in zip(fields, assets) if a ]
                typs = [ t for t,a in zip(typs, assets) if a ]
                assets = [ a for a in assets if a ]
#               debug("unused assets left: %d"%len(data))

        action =  ImportAction(DOA, mod_dir, what, fields, typs, assets)
        action.num_unused = num_unused
        return action


class ImportAction:
        def __init__(self, DOA, mod_dir, name, fields, typs, assets):
                self.DOA = DOA
                self.mod_dir = mod_dir
                self.name = name

                self.suffix = fields
                self.typ = typs
                self.assets = assets
                self.num = len(self.suffix)
                self.base_name = ""
                self.selected = [""]*self.num
                self.dst=[""]*self.num
                self.dst_error = [None]*self.num
                self.add_new = False
        def do(self):
                if self.add_new:
                        for i in range(self.num):
                                if self.selected[i]: self.assets[i] = DOA.make_new_assets(1)[0]
                for typ,asset,path,dst in zip(self.typ,self.assets,self.selected,self.dst):
                        if not path: continue
                        self.DOA.swap(asset,self.mod_dir,path,typ,True,dst=dst)


        def check_error(self, idx):
                src = self.selected[idx]
                dst=""
                err=""
                if src:
                        suff=src.rsplit('.',maxsplit=1)[1]
                        if not os.path.exists(src):
                               err= "src file doesn't exist"
                        else:
                                dst = os.path.join(self.mod_dir, self.base_name + '.'+suff)
                                path=os.path.join(self.DOA.game_path, dst)
                                if os.path.exists(path) or os.path.exists(path+".__"):
                                        err="target file exists already in mod folder"
                self.dst[idx]=dst
                self.dst_error[idx]=err

        def change_basename(self, name):
                self.base_name = name
                for i in range(len(self.selected)): self.check_error(i)
        def clear(self, idx):
                self.selected[idx]=""
                self.dst[idx]=""
                self.dst_error[idx]=None
                empty=0
                for s in self.selected: empty+=(s!="")
                if empty==0: self.base_name=""

        def set(self, idx, path):
                if not self.base_name: self.base_name = os.path.basename( path ).rsplit('.',maxsplit=1)[0]

                self.selected[idx]=path
                self.check_error(idx)

                if idx!=0: return
                # try to guess the next
                for i in range(1, self.num):
                        suffix=self.suffix[i]
                        base = path.rsplit('.',maxsplit=1)[0]
                        for s in (suffix.lower(),suffix.upper()):
                                fpath=base+'.'+s
                                if fpath in self.selected: continue # don't select file twice
                                if not os.path.exists(fpath): continue

                                self.selected[i]=fpath
                                self.check_error(i)

class CharDesc:
        def __init__(self, idx, name, slots, costumes, dlc_hairs, dlc_faces):
                self.idx = idx
                self.name = name
                self.slots = slots
                self.costumes = costumes
                self.num_base_cos = DOA.exe.table['CSOPT'][idx].num_base
                self.dlc_hair = ModStructList(HairMdl, dlc_hairs)
                self.dlc_face = ModStructList(FaceMdl, dlc_faces)

        def mod_save(self, DOA):
                res=""
                for lst,name in zip( (self.dlc_hair,self.dlc_face),('dlc_hair','dlc_face') ):
                        if len(lst._orig)!=lst._size:
                                res+=".n%s:%d:%d\n"%(name,len(lst._orig),lst._size)
                        for idx in lst.itermod():
                                res+=".%s:%d:"%(name,idx)+lst[idx].mod_save(DOA)+"\n"
                return res


class CosDesc(ModStruct):
        _fields=['tmc','tmcl','c','p','phyd','glasses','enable']
        _typ =  [0x19, 0x1a ,0x08, 0x09, 0x24]
        def __init__(self, cs_def,glasses, enable, faces, alt, base=False, xtend=False):
                ModStruct.__init__(self, cs_def+[glasses,(enable==1)])
                self.base = base
                self.is_xtend = xtend
                self.is_dlc = False
                self.empty_dlc = True
                if self.c and 'chara_dlccos' in self.c.lnk: self.is_dlc = True
                if self.is_dlc and self.c.has_data: self.empty_dlc=False
                alt = [ AltTex(*a) for a in alt ]
                self.alt = ModStructList(AltTex, alt)
                self.faces = ModStructList(Head, faces)

        def get_assets(self):
                for f in ('tmc','tmcl','c','p','phyd'): yield getattr(self, f)
        def mod_list(self, field, f_idx, idx, new):
                if field == 'alt': self.alt[f_idx][idx]=new
                elif field=='faces':
                        self.faces[f_idx][idx//2][idx%2]=new

        def revert(self, key=None):
                ModStruct.revert(self, key)
                if key==None:
                        self.alt.revert()
                        self.faces.revert()
        def mod_cmd(self, DOA):
                xt = "x" if self.is_xtend else ""
                if 'enable' in self.__dict__:
                        res=".%senable:%d\n"%(xt, self.enable)
                else: res=""
                if self.has_mod():
                       res+=".%scs_def:"%xt+assL2idx( (self.tmc,self.tmcl,
                                        self.c,self.p,self.phyd), DOA)+"\n"
                if 'glasses' in self.__dict__:
                        res+=".%sglasses:%d\n"%(xt,self.glasses)

                res += self.faces.mod_save(DOA, "%sface"%xt,"%snfaces"%xt)
                res += self.alt.mod_save(DOA, "%salt"%xt, "%snalt"%xt)
                return res




class DOAError(Exception):
        # blaa
        pass
class Error(Exception):
        pass

def find_sprites(opts):
        from doa5exe import PEFile
        DOA = DOA5()
        DOA.load(opts['f'])

        exe = PEFile( opts['f'] )
        #ofs = exe.find_mem_ref( bytes([0x8D,0x49,0x00,0x8D,0x46,0xe4,]), ofs=-9,rel=False)
        ofs = 0x1009f18 #110a  #0x01009238 # 109b   # 0xf94e90 ## for 1.07p1
        print("ofs:%x"%ofs)
        #ofs = exe.find_pattern(struct.pack('<L',0x2f6f))
        #if not ofs or len(ofs)>1:
        #        print("can't find ofs for sprite table: %s"%",".join(["%x"%p for p in ofs]))
        #        return
        #ofs=ofs[0]
        #print("%x"%ofs)
        xx=[]
        while 1:
                ent = exe.get(ofs, "<2L")[0]
                if ent == 0: break
                spr, ltf = ent
                if (ltf & 0xffff0000) or (spr&0xffff0000): break
                xx.append( [ DOA._resolve(p,'') for p in ent ] )
                ofs+=8

        for i, ent in enumerate(xx):
                spr, ltf = ent
                for p, suffix in zip( (spr,ltf),('SPR','LTF')):
                        alias = "sprite_unk_%03d.%s"%(i,suffix)
                        if alias != p.alias: print("%s\t%s"%(p.name, alias))
                if opts['v']: print("%#03x#: %04x %040s,  %04x %s"%(i, spr.idx, spr.alias, ltf.idx, ltf.alias))


def find_updates(opts):
        DOA = DOA5()
        DOA.load(opts['f'])
        for p in DOA.assets:
                if p.alias == p.name: continue
                if not p.updates: continue
                for i, u in enumerate(p.updates):
                        if u.alias != u.name: continue
                        try:
                                name,end=p.alias.rsplit('.',maxsplit=1)
                                if u.typ==0x20 and 'ICON' not in p.alias: continue # ignore sprite for now
                                print("%s_UPD%02d.%s\t%s"%(name,i+1,end,u.name))
                        except ValueError:
                                pass


def find_anim(opts):
        from doa5exe import PEFile
        DOA = DOA5()
        DOA.load(opts['f'])

        exe = PEFile( opts['f'] )

        pat = [0x3b35,0x3b36,0x3b37]
        #if DOA.exe.ver in ('1.05', '1.06'): pat = [x+0xc50 for x in pat]
        pat = [x+0xc50 for x in pat]

        ofs = exe.find_pattern(struct.pack("<%dL"%len(pat), *pat))
        if not ofs or len(ofs)>1:
                print("can't find ofs for sprite table: %s"%",".join(["%x"%p for p in ofs]))
                return
        ofs = ofs[0]
        idx=0
        anim_files=[]
        while True:
                ent = exe.get(ofs, "<L")[0]
                if ent==0 or ent==0xffff: break
                anim_files.append( DOA.assets[ent] )
                #print("#%03d: %04x  %s"%(idx, ent, DOA.assets[ent].alias))
                idx+=1
                ofs+=4

        pat = [0xc9,0xffff,0xff,0xffff,0,0xff,0xff,0,0,0]
        ofs = exe.find_pattern(struct.pack("<%dH"%len(pat), *pat))
        if not ofs or len(ofs)>1:
                print("can't find ofs for sprite table: %s"%",".join(["%x"%p for p in ofs]))
                return
        ofs = ofs[0]
        #print("%x"%ofs)
        idx=0
        name_root={}
        aliases={}
        seen={}
        while idx < 989:
                dat = exe.get(ofs, "<6H3L")[0]
                if dat[1]!=0xffff:
                        print("END")
                        break
                p = anim_files[dat[0]]
                what=()
                combo=()
                if dat[8] & 0x1: what+=('SINGLE',)
                if dat[8] & 0x2: what+=('TAG',)
                if dat[8] & 0x4: what+=('APPEAR',)
                if dat[8] & 0x8: what+=('WIN',)
                if dat[8] & 0x20: what+=('LOSE',)
                if dat[8] & 0x40: what+=('PB',)
                if dat[8] & 0x80: what+=('FALL',)
                if dat[7]!=0:
                        tag_of = dat[7]
                        while True:
                                x = exe.get( tag_of, "<H")[0]
                                if x==DOA.exe.num_char: break
                                what+=(char_name(x),)
                                combo+=(char_name(x),)
                                tag_of+=2
                alias = (char_name(dat[6])+'_ANIM') if dat[6]!=0xff else 'ANIM'
                if 'SINGLE' in what and 'TAG' in what:
                        pass #
                elif 'SINGLE' in what: alias+='_SOLO'
                elif 'TAG' in what: alias+='_TAG'
                for x in ('APPEAR','WIN','LOSE','FALL','PB'):
                        if x in what: alias+='_'+x
                if len(combo)==1: alias+='_'+combo[0]
                elif len(combo)>1: alias+='_MULTI'

                if p.name == p.alias and p.name not in seen:
                        if alias in name_root:
                                name_root[alias]+=1
                                if name_root[alias] == 1:
                                        aliases[alias+"_00"] = aliases[alias]
                                        del aliases[alias]
                                alias+="_%02d"%name_root[alias]
                        else: name_root[alias]=0
                        aliases[alias]=p.alias
                        seen[p.name]=1
#                print(" %02d: "%idx,alias," ".join( ["%04x"%x for x in dat]),
#                        " %s(%d)"%(char_name(dat[6]),dat[6]) if dat[6]!=0xff else "",
#                        " "+p.alias," "+",".join(what))
#                print(alias, p.alias, ",".join(what))
                ofs+=0x18
                idx+=1
        for k,v in aliases.items():
                print(k+".tdpack\t"+v)

def write_dat(opts):
        DOA = DOA5()
        DOA.load( opts['f'] )

        old_names = dict( [ (v,k) for k,v in NAME_CHANGES.items() ] )
        for p in DOA.assets:
                alias = "" if p.name==p.alias else p.alias
                print("%s\t%s\t%08X\t%X"%(p.name,alias,p.flags,p.idx))
                old = old_names.get(p.name, None)
                if old: print("%s\t%s\t%08X\t%X"%(old,alias,p.flags,p.idx))



# switch : (has_arg, descr )
OPTS={ 'f': (1, '<exe file'),
       'v': (0, 'verbose' ),
       'find-alias' : (1, '<sprites,> - find alias for unnamed'),
       'write-dat' : (0, 'write file5.dat for DLC/ArchiveTool'), }

FIND_ALIAS={'sprites' : find_sprites, 'anim' : find_anim, 'updates': find_updates }
def run():
        opts={}
        for k in OPTS.keys(): opts[k]=None
        for i in range(1, len(sys.argv)):
                arg = sys.argv[i]
                if arg[0]!='-': continue
                k = arg[1:]
                if k not in opts:
                        print("invalid commandline parameter: "+arg)
                        continue
                if OPTS[k][0]==1:
                        try:
                                i+=1
                                v = sys.argv[i]
                        except IndexError:
                                print("missing argument to: "+arg)
                                return
                else: v = True
                opts[k]=v
        if not opts['f']: return # nothing to do

        if opts['write-dat']: write_dat(opts)
        if opts['find-alias']:
                fn = FIND_ALIAS.get(opts['find-alias'])
                if fn: fn(opts)
                else: print("invalid options for -find-alias")


if __name__ == '__main__':
        run()
