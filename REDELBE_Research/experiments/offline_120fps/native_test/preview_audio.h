#pragma once
#include <deque>
#include <memory>
struct PreviewAudio {
 struct Block {WAVEHDR header{};std::vector<BYTE> data;};
 ComPtr<IMFSourceReader> reader;HWAVEOUT output=nullptr;
 std::deque<std::unique_ptr<Block>> blocks;
 bool ended=false,started=false;
 void close() {
  if(output){waveOutReset(output);for(auto& b:blocks)waveOutUnprepareHeader(output,&b->header,sizeof(WAVEHDR));waveOutClose(output);}
  blocks.clear();output=nullptr;reader.Reset();ended=started=false;
 }
 ~PreviewAudio(){close();}
 bool open(const std::wstring& path,unsigned volume) {
  close();ComPtr<IMFMediaType> format,actual;
  if(FAILED(MFCreateSourceReaderFromURL(path.c_str(),nullptr,&reader)))return false;
  reader->SetStreamSelection(MF_SOURCE_READER_ALL_STREAMS,FALSE);
  if(FAILED(reader->SetStreamSelection(MF_SOURCE_READER_FIRST_AUDIO_STREAM,TRUE))){close();return false;}
  MFCreateMediaType(&format);format->SetGUID(MF_MT_MAJOR_TYPE,MFMediaType_Audio);format->SetGUID(MF_MT_SUBTYPE,MFAudioFormat_PCM);
  format->SetUINT32(MF_MT_AUDIO_BITS_PER_SAMPLE,16);format->SetUINT32(MF_MT_AUDIO_NUM_CHANNELS,2);format->SetUINT32(MF_MT_AUDIO_SAMPLES_PER_SECOND,48000);
  if(FAILED(reader->SetCurrentMediaType(MF_SOURCE_READER_FIRST_AUDIO_STREAM,nullptr,format.Get()))||FAILED(reader->GetCurrentMediaType(MF_SOURCE_READER_FIRST_AUDIO_STREAM,&actual))){close();return false;}
  WAVEFORMATEX* wave=nullptr;UINT32 size=0;
  if(FAILED(MFCreateWaveFormatExFromMFMediaType(actual.Get(),&wave,&size))){close();return false;}
  auto result=waveOutOpen(&output,WAVE_MAPPER,wave,0,0,CALLBACK_NULL);CoTaskMemFree(wave);
  if(result!=MMSYSERR_NOERROR){close();return false;}
  DWORD gain=std::min(volume,100u)*65535/100;waveOutSetVolume(output,gain|(gain<<16));return true;
 }
 void rewind() {
  if(!output||!reader)return;
  waveOutReset(output);for(auto& b:blocks)waveOutUnprepareHeader(output,&b->header,sizeof(WAVEHDR));blocks.clear();
  PROPVARIANT position{};position.vt=VT_I8;position.hVal.QuadPart=0;
  ended=FAILED(reader->SetCurrentPosition(GUID_NULL,position));started=false;
 }
 bool pump() {
  if(!output||!reader)return false;
  while(!blocks.empty()&&(blocks.front()->header.dwFlags&WHDR_DONE)) {
   waveOutUnprepareHeader(output,&blocks.front()->header,sizeof(WAVEHDR));blocks.pop_front();
  }
  for(unsigned attempt=0;!ended&&blocks.size()<3&&attempt<6;++attempt) {
   DWORD flags=0;LONGLONG timestamp=0;ComPtr<IMFSample> sample;
   if(FAILED(reader->ReadSample(MF_SOURCE_READER_FIRST_AUDIO_STREAM,0,nullptr,&flags,&timestamp,&sample))){ended=true;break;}
   if(flags&MF_SOURCE_READERF_ENDOFSTREAM){ended=true;break;}
   if(!sample)continue;
   ComPtr<IMFMediaBuffer> buffer;if(FAILED(sample->ConvertToContiguousBuffer(&buffer))){ended=true;break;}
   BYTE* bytes=nullptr;DWORD size=0;if(FAILED(buffer->Lock(&bytes,nullptr,&size))){ended=true;break;}
   auto block=std::make_unique<Block>();block->data.assign(bytes,bytes+size);buffer->Unlock();
   block->header.lpData=reinterpret_cast<LPSTR>(block->data.data());block->header.dwBufferLength=size;
   if(waveOutPrepareHeader(output,&block->header,sizeof(WAVEHDR))!=MMSYSERR_NOERROR){ended=true;break;}
   if(waveOutWrite(output,&block->header,sizeof(WAVEHDR))!=MMSYSERR_NOERROR){waveOutUnprepareHeader(output,&block->header,sizeof(WAVEHDR));ended=true;break;}
   started=true;blocks.push_back(std::move(block));
  }
  return started&&!blocks.empty();
 }
};
