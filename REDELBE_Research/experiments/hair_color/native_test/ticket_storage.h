#pragma once
#include <windows.h>
#include "ticket_wallet.h"
namespace tickets {
enum class Load { missing,loaded,failed };
inline Load loadFile(const std::wstring& path,State& state) {
    HANDLE file=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)return GetLastError()==ERROR_FILE_NOT_FOUND?Load::missing:Load::failed;
    LARGE_INTEGER size{};bool ok=GetFileSizeEx(file,&size)&&size.QuadPart>0&&size.QuadPart<=1024*1024;
    std::string data;DWORD got=0;
    if(ok){data.resize(static_cast<size_t>(size.QuadPart));ok=ReadFile(file,&data[0],static_cast<DWORD>(data.size()),&got,nullptr)&&got==data.size();}
    CloseHandle(file);
    return ok&&decode(data,state)?Load::loaded:Load::failed;
}
// One serialized wallet owner must call this function. Never overwrite the
// last committed ledger until the entire replacement has been flushed.
inline bool saveFile(const std::wstring& path,const std::string& data) {
    State check;if(!decode(data,check))return false;
    const std::wstring temporary=path+L".pending";
    HANDLE file=CreateFileW(temporary.c_str(),GENERIC_WRITE,0,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)return false;
    DWORD written=0;
    bool ok=WriteFile(file,data.data(),static_cast<DWORD>(data.size()),&written,nullptr)&&written==data.size()&&FlushFileBuffers(file);
    CloseHandle(file);
    if(ok)ok=MoveFileExW(temporary.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
    if(!ok)DeleteFileW(temporary.c_str());
    return ok;
}
}
