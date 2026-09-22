"""Native file drops and copy-only audio exports to Explorer."""
from pathlib import Path
import re, uuid
from tkinter import filedialog, messagebox
from tkinterdnd2 import COPY, DND_FILES, REFUSE_DROP
from srs_audio_core import Document
from srs_pairs import resolve,choose_inputs

def resolve_banks(paths):
    banks=[]
    for value in paths:
        path=Path(value).resolve()
        if path.suffix.lower() not in ('.srsa','.srst') or not path.is_file():
            raise ValueError('Drop SRSA banks, optionally with their matching SRST files.')
        path,_=resolve(path)
        if path not in banks:banks.append(path)
    return banks

def install(studio):
    def drop(event):
        if studio.busy:return REFUSE_DROP
        try:
            banks=[]
            def choose(title,suffix):return filedialog.askopenfilename(parent=studio.root,title=title,filetypes=[('Matching bank','*'+suffix)])
            for value in studio.root.tk.splitlist(event.data):
                pair=choose_inputs(value,choose)
                if pair not in banks:banks.append(pair)
        except Exception as exc:
            messagebox.showerror('Cannot extract bank',str(exc),parent=studio.root);return REFUSE_DROP
        if not banks:return REFUSE_DROP
        parent=filedialog.askdirectory(parent=studio.root,title='Extract dropped banks into new folders here')
        if not parent:return REFUSE_DROP
        def task():
            results=[]
            for bank,pair in banks:
                target=Path(parent)/(bank.stem+'_extracted_'+uuid.uuid4().hex[:8])
                Document(bank,pair).export(target);results.append(str(target))
            return results
        studio.run('Extracting dropped banks…',task,lambda paths:studio.status.set('Extracted: '+'; '.join(paths)))
        return COPY
    studio.root.drop_target_register(DND_FILES)
    studio.root.dnd_bind('<<Drop>>',drop)
    attach_tree(studio,studio.tree)

def attach_tree(studio,tree,library=None):
    tree.drag_source_register(1,DND_FILES)
    def start(event):
        if studio.busy:return (REFUSE_DROP,)
        x=tree.winfo_pointerx()-tree.winfo_rootx();y=tree.winfo_pointery()-tree.winfo_rooty()
        if tree.identify_region(x,y)!='cell':return (REFUSE_DROP,)
        selected=tree.selection()
        if not selected:return (REFUSE_DROP,)
        folder=Path(studio.temp.name)/('drag_'+uuid.uuid4().hex);folder.mkdir()
        files=[];used=set()
        try:
            for iid in selected:
                if library:
                    row=library.visible[int(iid)];ext,data=library.library.audio(row)
                else:
                    fid=int(iid,16);row=studio.doc.rows[fid];ext,data=studio.doc.audio(fid)
                label=re.sub(r'[^A-Za-z0-9_.-]','_',row.get('name','')).rstrip('. ')[:120] or 'unnamed_track'
                if label.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:label='_'+label
                name=label+ext;n=2
                while name.lower() in used:name=f'{label}_{n}{ext}';n+=1
                used.add(name.lower());path=folder/name;path.write_bytes(data);files.append(str(path))
            studio.status.set('Drag audio into a folder to copy it. Temporary exports stay available until SRS closes.')
            return (COPY,DND_FILES,tuple(files))
        except Exception as exc:
            studio.status.set('Could not extract dragged audio: '+str(exc));return (REFUSE_DROP,)
    tree.dnd_bind('<<DragInitCmd>>',start)
