#pragma once
// Prototype: PC G1T albedo recoloring. Never use on normal/specular maps.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <vector>
#define BCDEC_IMPLEMENTATION
#define BCDEC_STATIC
#include "third_party/bcdec.h"
namespace hairtexture {
using Bytes=std::vector<uint8_t>;
inline uint32_t u32(const Bytes& b,size_t p){if(p>b.size()||b.size()-p<4)throw std::runtime_error("Truncated G1T");uint32_t v;memcpy(&v,b.data()+p,4);return v;}
inline void put(Bytes& b,size_t p,uint32_t v){if(p>b.size()||b.size()-p<4)throw std::runtime_error("Invalid output offset");memcpy(b.data()+p,&v,4);}
inline int format(uint8_t f){switch(f){case 0:case 9:return 0;case 1:case 10:return -1;case 6:case 16:case 0x59:case 0x60:return 1;case 7:case 17:case 0x5a:case 0x61:return 2;case 8:case 18:case 0x5b:case 0x62:return 3;case 0x5f:case 0x66:return 7;default:throw std::runtime_error("Unsupported albedo encoding");}}
inline void tint(Bytes& rgba,uint32_t rgb){
    // Preserve strand shading and alpha, including fully transparent pixels.
    float c[3]={float((rgb>>16)&255)/255,float((rgb>>8)&255)/255,float(rgb&255)/255};
    for(size_t p=0;p<rgba.size();p+=4){
        float l=(0.2126f*rgba[p]+0.7152f*rgba[p+1]+0.0722f*rgba[p+2])/255;
        float shade=std::min(1.0f,std::sqrt(l)*1.55f);
        for(int k=0;k<3;k++)rgba[p+k]=uint8_t(std::clamp(std::lround(c[k]*shade*255),0l,255l));
    }
}
inline Bytes convert(const Bytes& src,uint32_t rgb,bool recolor=true){
    if(src.size()<32||u32(src,0)!=0x47315447||u32(src,8)!=src.size()||u32(src,0x14)!=10)throw std::runtime_error("Expected PC G1T with matching size");
    size_t table=u32(src,12),count=u32(src,16),unk=u32(src,24);
    if(!count||count>128||table<32||table>src.size()||count*4+unk>src.size()-table)throw std::runtime_error("Invalid G1T table");
    size_t head=table+count*4+unk;Bytes out(src.begin(),src.begin()+head);
    for(size_t i=0;i<count;i++){
        size_t begin=table+u32(src,table+i*4),end=i+1<count?table+u32(src,table+(i+1)*4):src.size();
        if(begin<head||end>src.size()||end<begin||end-begin<8)throw std::runtime_error("Invalid texture bounds");
        unsigned mips=src[begin]>>4,w=1u<<(src[begin+2]&15),h=1u<<(src[begin+2]>>4),arrays=1;
        if(!mips)mips=1;
        size_t data=begin+8;
        if(src[begin+7]){size_t n=u32(src,data);if(n<4||n>end-data)throw std::runtime_error("Invalid extra header");if(n>=12)arrays=std::max(1u,unsigned(src[data+8]>>4));if(n>=16)w=u32(src,data+12);if(n>=20)h=u32(src,data+16);data+=n;}
        if(!w||!h||w>8192||h>8192||arrays>1)throw std::runtime_error("Unsupported dimensions/array texture");
        int fmt=format(src[begin+1]);size_t expected=0;unsigned mw=w,mh=h;
        for(unsigned m=0;m<mips;m++){expected+=fmt<=0?size_t(mw)*mh*4:size_t((mw+3)/4)*((mh+3)/4)*(fmt==1?8:16);mw=std::max(1u,mw/2);mh=std::max(1u,mh/2);}
        if(end-data!=expected)throw std::runtime_error("Unexpected mip payload size; refusing to guess");
        put(out,table+i*4,uint32_t(out.size()-table));size_t dst=out.size();out.insert(out.end(),src.begin()+begin,src.begin()+data);out[dst+1]=9;
        mw=w;mh=h;
        for(unsigned m=0;m<mips;m++){
            Bytes rgba(size_t(mw)*mh*4);
            if(fmt<=0){memcpy(rgba.data(),src.data()+data,rgba.size());data+=rgba.size();if(fmt==-1)for(size_t p=0;p<rgba.size();p+=4)std::swap(rgba[p],rgba[p+2]);}
            else for(unsigned y=0;y<mh;y+=4)for(unsigned x=0;x<mw;x+=4){
                alignas(16) uint8_t block[64]{};
                if(fmt==1)bcdec_bc1(src.data()+data,block,16);else if(fmt==2)bcdec_bc2(src.data()+data,block,16);else if(fmt==3)bcdec_bc3(src.data()+data,block,16);else bcdec_bc7(src.data()+data,block,16);
                data+=fmt==1?8:16;
                for(unsigned by=0;by<4&&y+by<mh;by++)for(unsigned bx=0;bx<4&&x+bx<mw;bx++)memcpy(rgba.data()+((y+by)*mw+x+bx)*4,block+(by*4+bx)*4,4);
            }
            if(recolor)tint(rgba,rgb);out.insert(out.end(),rgba.begin(),rgba.end());mw=std::max(1u,mw/2);mh=std::max(1u,mh/2);
        }
        if(out.size()>512*1024*1024)throw std::runtime_error("Output too large");
    }
    put(out,8,uint32_t(out.size()));return out;
}
}
