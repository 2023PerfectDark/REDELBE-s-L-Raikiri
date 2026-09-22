from pathlib import Path
p=Path('prototype/layer2_runtime.h');s=p.read_text();s=s.replace('    if(isVersionText(text,length)) {','    static unsigned titleTrace=0;\n    if(text&&length&&length<160&&titleTrace++<200)log("TITLE TRACE pane="+hex(pane)+" len="+std::to_string(length)+" text="+utf8(std::wstring(text,length)));\n    if(isVersionText(text,length)) {');p.write_text(s)
