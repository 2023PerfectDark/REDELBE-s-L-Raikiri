"""Mono Microsoft ADPCM encoder with the destination bank's exact block size."""
import array,struct
from srsa_lr import COEFF,chunk
ADAPT=(230,230,230,230,307,409,512,614,768,614,512,409,307,230,230,230)

def encode_block(samples):
    best=None
    for predictor,(c1,c2) in enumerate(COEFF):
        s2,s1=samples[:2];delta=max(16,min(32767,abs(s1-s2)))
        header=struct.pack('<BHhh',predictor,delta,s1,s2);nibbles=[];error=0
        for target in samples[2:]:
            prediction=(s1*c1+s2*c2)//256
            difference=target-prediction
            q=(abs(difference)+delta//2)//delta
            if difference<0:q=-q
            q=max(-8,min(7,q));decoded=max(-32768,min(32767,prediction+q*delta))
            error+=(target-decoded)**2
            code=q&15;nibbles.append(code)
            delta=max(16,ADAPT[code]*delta//256);s2,s1=s1,decoded
        if best is None or error<best[0]:
            payload=bytes((nibbles[i]<<4)|nibbles[i+1] for i in range(0,len(nibbles),2))
            best=(error,header+payload)
    return best[1]

def encode(pcm,rate,block):
    if len(pcm)%2 or not pcm:raise ValueError('Expected nonempty mono 16-bit PCM')
    if not 7<block<=8192 or not 1000<=rate<=384000:raise ValueError('Unsupported ADPCM target')
    samples=array.array('h');samples.frombytes(pcm)
    count=len(samples);spb=(block-7)*2+2;parts=[]
    for p in range(0,count,spb):
        values=list(samples[p:p+spb]);values.extend([values[-1]]*(spb-len(values)))
        parts.append(encode_block(values))
    fmt=struct.pack('<HHIIHHHHH',2,1,rate,rate*block//spb,block,4,32,spb,7)+b''.join(struct.pack('<hh',*v) for v in COEFF)
    body=b'WAVE'+chunk(b'fmt ',fmt)+chunk(b'fact',struct.pack('<I',count))+chunk(b'data',b''.join(parts))
    return b'RIFF'+struct.pack('<I',len(body))+body
