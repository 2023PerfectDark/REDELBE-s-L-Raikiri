#pragma once
namespace haircache {
static bool enabled=false;
static std::wstring root;
static std::map<std::wstring,uint32_t> ids;
static thread_local bool generating=false;
static std::wstring get(const std::wstring& source,int color){
 auto found=ids.find(source);if(!enabled||found==ids.end()||color<0||color>15||generating)return L"";
 wchar_t filename[40];swprintf_s(filename,L"%08x_%02d.file",found->second,color);
 auto target=root+L"Cache\\"+filename;
 if(GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES){
  auto h=realW(target.c_str(),FILE_WRITE_ATTRIBUTES,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,0,nullptr);
  if(h!=INVALID_HANDLE_VALUE){FILETIME now;GetSystemTimeAsFileTime(&now);SetFileTime(h,nullptr,nullptr,&now);CloseHandle(h);}return target;
 }
 generating=true;
 struct Clear {~Clear(){generating=false;}} clear;
 auto exe=root+L"HairCacheWorker.exe";
 std::wstring cmd=L"\""+exe+L"\" --no-pause --game \""+gameRoot+L".\" --cache-request "+wide(hex(found->second))+L" --color "+std::to_wstring(color);
 STARTUPINFOW si{};si.cb=sizeof(si);PROCESS_INFORMATION pi{};
 if(!CreateProcessW(exe.c_str(),cmd.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW,nullptr,gameRoot.c_str(),&si,&pi)){log("HAIR CACHE helper start failed");return L"";}
 CloseHandle(pi.hThread);
 DWORD wait=WaitForSingleObject(pi.hProcess,120000),code=1;
 if(wait==WAIT_OBJECT_0)GetExitCodeProcess(pi.hProcess,&code);
 CloseHandle(pi.hProcess);
 if(code||GetFileAttributesW(target.c_str())==INVALID_FILE_ATTRIBUTES){log("HAIR CACHE generation failed for "+hex(found->second));return L"";}
 return target;
}
}
