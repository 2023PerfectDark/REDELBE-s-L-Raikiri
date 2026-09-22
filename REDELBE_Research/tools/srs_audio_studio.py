"""Portable Windows editor for extracted DOA6/LR audio banks."""
from pathlib import Path
import json,os,queue,re,sys,tempfile,threading,time,tkinter as tk
from tkinter import ttk,filedialog,messagebox
import winsound
from srs_audio_core import Document,VERSION,ffmpeg,batch_files,rrpreview_game,synchronize
from srs_table import TableSort
from srs_library import CATEGORIES,CHARACTERS,category,language

class Studio:
    def __init__(self,root):
        self.root=root;self.doc=None;self.busy=False;self.events=queue.Queue();self.temp=tempfile.TemporaryDirectory(prefix='SRS-Audio-');self.buttons=[]
        root.title('SRS Audio Studio LR '+VERSION);root.geometry('1280x860');root.minsize(980,740)
        icon=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))/'assets/srs.ico'
        if icon.is_file():root.iconbitmap(default=str(icon))
        style=ttk.Style();style.theme_use('vista');style.configure('Treeview',rowheight=28);style.configure('Title.TLabel',font=('Segoe UI',21,'bold'));style.configure('Muted.TLabel',foreground='#526171')
        style.element_create('SRS.tab','from','clam','Notebook.tab')
        tab_layout=style.layout('TNotebook.Tab');tab_layout[0]=('SRS.tab',tab_layout[0][1]);style.layout('SRS.TNotebook.Tab',tab_layout)
        style.configure('SRS.TNotebook',tabmargins=(14,12,14,0))
        style.configure('SRS.TNotebook.Tab',font=('Segoe UI',14,'bold'),padding=(26,12),background='#dce6f2',foreground='#24374d')
        style.map('SRS.TNotebook.Tab',background=[('selected','#1769aa'),('active','#c4daf1')],foreground=[('selected','#ffffff'),('active','#123c64')])
        self.tabs=ttk.Notebook(root,style='SRS.TNotebook');self.tabs.pack(fill='both',expand=True)
        self.library_page=ttk.Frame(self.tabs);self.editor_page=ttk.Frame(self.tabs)
        self.tabs.add(self.library_page,text='Audio Library');self.tabs.add(self.editor_page,text='Bank Editor')
        wrap=ttk.Frame(self.editor_page,padding=22);wrap.pack(fill='both',expand=True)
        ttk.Label(wrap,text='SRS Audio Studio LR',style='Title.TLabel').pack(anchor='w')
        ttk.Label(wrap,text='Replace a voice. Keep the game’s audio settings.',style='Muted.TLabel').pack(anchor='w',pady=(3,16))
        toolbar=ttk.Frame(wrap);toolbar.pack(fill='x')
        for text,command in [('Audio library',self.library),('Open SRSA bank',self.open),('Extract all',self.extract),('Import audio folder',self.batch),('Undo all edits',self.reset),('Instructions',self.help)]:
            b=ttk.Button(toolbar,text=text,command=command);b.pack(side='left',padx=(0,8));self.buttons.append(b)
        self.bank_label=tk.StringVar(value='Open an extracted .srsa file. Streamed banks also need the matching .srst beside it.')
        ttk.Label(wrap,textvariable=self.bank_label,wraplength=1000,style='Muted.TLabel').pack(anchor='w',pady=(12,12))
        find=ttk.Frame(wrap);find.pack(fill='x',pady=(0,8));ttk.Label(find,text='Find hash / readable name / format').pack(side='left')
        self.search=tk.StringVar();entry=ttk.Entry(find,textvariable=self.search,width=35);entry.pack(side='left',padx=10);self.search.trace_add('write',lambda *args:self.populate())
        self.count=tk.StringVar(value='No bank open');ttk.Label(find,textvariable=self.count,style='Muted.TLabel').pack(side='right')
        filters=ttk.Frame(wrap);filters.pack(fill='x',pady=(0,8))
        self.category_filter=tk.StringVar(value='All');self.language_filter=tk.StringVar(value='All')
        ttk.Label(filters,text='Category').pack(side='left',padx=(0,6))
        choice=ttk.Combobox(filters,textvariable=self.category_filter,values=('All',*CATEGORIES),state='readonly',width=13);choice.pack(side='left',padx=(0,16));choice.bind('<<ComboboxSelected>>',lambda e:self.populate())
        ttk.Label(filters,text='Language').pack(side='left',padx=(0,6))
        for label in ('All','ENG','JP','Other / shared'):
            ttk.Radiobutton(filters,text=label,value=label,variable=self.language_filter,command=self.populate,style='Toolbutton').pack(side='left',padx=3)
        area=ttk.Frame(wrap);area.pack(fill='both',expand=True)
        columns=('category','character','language','id','name','codec','rate','channels','duration','state')
        self.tree=ttk.Treeview(area,columns=columns,show='headings',selectmode='browse')
        for name,title,width in zip(columns,['Tag','Character','Language','Hash / Track ID','Readable name','Audio format','Sample rate','Channels','Duration','Replacement'],[90,80,100,120,270,115,95,70,80,150]):
            self.tree.heading(name,text=title);self.tree.column(name,width=width,minwidth=65,stretch=name in ('name','state'))
        self.sorter=TableSort(self.tree,numeric=('id','rate','channels','duration'))
        scroll=ttk.Scrollbar(area,orient='vertical',command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True)
        horizontal=ttk.Scrollbar(wrap,orient='horizontal',command=self.tree.xview);horizontal.pack(fill='x');self.tree.configure(xscrollcommand=horizontal.set)
        self.tree.bind('<<TreeviewSelect>>',lambda e:self.selection());self.tree.bind('<Double-1>',lambda e:self.preview() if self.tree.identify_region(e.x,e.y)=='cell' else None)
        self.detail=tk.StringVar(value='Select a track to see the required export settings.')
        ttk.Label(wrap,textvariable=self.detail,wraplength=1000).pack(anchor='w',pady=(12,8))
        actions=ttk.Frame(wrap);actions.pack(fill='x')
        for text,command in [('▶ Preview',self.preview),('Stop',lambda:winsound.PlaySound(None,0)),('Replace from MP3 / WAV / OGG',self.replace)]:
            b=ttk.Button(actions,text=text,command=command);b.pack(side='left',padx=(0,10));self.buttons.append(b)
        style.configure('Important.TButton',font=('Segoe UI',12,'bold'),padding=(18,10))
        style.configure('Important.TCheckbutton',font=('Segoe UI',12,'bold'),padding=(8,10))
        style.configure('Important.TLabelframe.Label',font=('Segoe UI',11,'bold'),foreground='#1769aa')
        panel=ttk.LabelFrame(wrap,text='Volume, save & activate',padding=12,style='Important.TLabelframe');panel.pack(fill='x',pady=(12,8))
        volume=ttk.Frame(panel);volume.pack(fill='x');self.match_volume=tk.BooleanVar(value=True)
        check=ttk.Checkbutton(volume,text='Match original volume on import',variable=self.match_volume,style='Important.TCheckbutton');check.pack(side='left',padx=(0,12));self.buttons.append(check)
        for title,command in [('Apply selected',lambda:self.apply_volume(False)),('Apply all replacements',lambda:self.apply_volume(True))]:
            b=ttk.Button(volume,text=title,command=command,style='Important.TButton');b.pack(side='left',padx=(0,8));self.buttons.append(b)
        publish=ttk.Frame(panel);publish.pack(fill='x',pady=(10,0))
        for title,command in [('Save new bank',self.save),('Sync RRPreview',self.sync)]:
            b=ttk.Button(publish,text=title,command=command,style='Important.TButton');b.pack(side='left',fill='x',expand=True,padx=(0,8));self.buttons.append(b)
        ttk.Label(panel,text='After moving a saved bank into RRPreview: close the game, click Sync RRPreview, then launch.',style='Muted.TLabel').pack(anchor='w',pady=(8,0))
        self.status=tk.StringVar(value='Ready');ttk.Label(wrap,textvariable=self.status,wraplength=1000).pack(anchor='w')
        self.progress=ttk.Progressbar(wrap,mode='indeterminate');self.progress.pack(fill='x',pady=(8,0))
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.poll)

    def library(self):
        from srs_library_ui import LibraryWindow
        self.tabs.select(self.library_page)
        if getattr(self,'library_window',None):return
        self.library_window=LibraryWindow(self,self.library_page)

    def tab_changed(self,event=None):
        if self.busy:return
        if self.tabs.select()==str(self.library_page):
            if not getattr(self,'library_window',None):self.library()
        elif self.doc is None and getattr(self,'library_window',None) and self.library_window.library:
            self.library_window.open_bank()

    def run(self,label,task,done=None):
        if self.busy:return
        self.busy=True;self.status.set(label);self.progress.start()
        for b in self.buttons:b.state(['disabled'])
        def work():
            try:self.events.put((True,task(),done))
            except Exception as e:self.events.put((False,str(e),None))
        threading.Thread(target=work,daemon=True).start()

    def poll(self):
        try:
            ok,result,done=self.events.get_nowait();self.busy=False;self.progress.stop()
            for b in self.buttons:b.state(['!disabled'])
            if ok:
                self.status.set('Ready')
                if done:done(result)
            else:self.status.set('Operation stopped. Original files are unchanged.');messagebox.showerror('SRS Audio Studio',result)
        except queue.Empty:pass
        self.root.after(100,self.poll)

    def selected(self):
        if self.busy:return None
        selected=self.tree.selection()
        if not self.doc or not selected:messagebox.showinfo('Select a track','Open a bank and select an audio track first.');return None
        return int(selected[0],16)

    def populate(self):
        if self.busy:return
        selected=self.tree.selection();self.tree.delete(*self.tree.get_children())
        if not self.doc:return
        query=self.search.get().lower()
        tag=category(self.doc.path.name)
        for fid,row in self.doc.rows.items():
            text=f'0x{fid:08x}';codec=row['codec']
            readable=row.get('name','')
            lang=language(self.doc.path.name,readable,tag)
            chars=', '.join(sorted(set(re.split(r'[^A-Z0-9]+',(self.doc.path.name+' '+readable).upper())) & CHARACTERS))
            if self.category_filter.get() not in ('All',tag) or self.language_filter.get() not in ('All',lang):continue
            if query and query not in (text+' '+readable+' '+codec+' '+chars+' '+tag+' '+lang).lower():continue
            self.tree.insert('', 'end',iid=text,values=(tag,chars,lang,text,readable or '(name unavailable)',codec,str(row.get('rate','—'))+' Hz',row.get('channels','—'),f"{row['seconds']:.2f} s",Path(self.doc.changes[fid]).name if fid in self.doc.changes else 'Original'))
        self.sorter.apply()
        if selected and self.tree.exists(selected[0]):self.tree.selection_set(selected[0])
        self.count.set(f'{len(self.tree.get_children())} / {len(self.doc.rows)} tracks · {len(self.doc.changes)} edited')
        if not self.tree.selection():self.detail.set('Select a visible track. Filters only change the view; all edits are retained.')

    def selection(self):
        if self.busy:return
        ids=self.tree.selection()
        if not self.doc or not ids:return
        row=self.doc.rows[int(ids[0],16)];block=f" · {row['block']}-byte blocks" if 'block' in row else ''
        self.detail.set(f"{ids[0]} — {row.get('name') or 'Name unavailable'}\nTarget: {row['codec']} · {row.get('rate','?')} Hz · {row.get('channels','?')} channel(s){block}. Conversion is automatic.")
        report=self.doc.volume_reports.get(int(ids[0],16))
        if report:self.detail.set(self.detail.get()+' Volume: '+report['status']+(f" ({report['gain_db']:+.1f} dB)" if 'gain_db' in report else ''))

    def accept(self,doc):
        self.tabs.select(self.editor_page)
        self.doc=doc;self.category_filter.set('All');self.language_filter.set('All');self.search.set('');self.bank_label.set(str(doc.path));self.populate()
        children=self.tree.get_children()
        if children:self.tree.selection_set(children[0])
        unsupported=sum(row['codec']=='unsupported' for row in doc.rows.values())
        self.status.set(f'Bank loaded. {unsupported} unsupported tracks are listed but cannot be extracted or replaced.' if unsupported else 'Bank loaded. Preview a track to identify the voice, then choose Replace.')

    def discard(self):return not self.doc or not self.doc.changes or messagebox.askyesno('Unsaved edits','Discard the current unsaved edits?')

    def open(self):
        if not self.discard():return
        path=filedialog.askopenfilename(title='Open an extracted SRSA/SRST bank',filetypes=[('Sound bank pair','*.srsa *.srst')])
        if path:self.open_path(path)

    def open_path(self,path):
        from srs_pairs import choose_inputs
        def choose(title,suffix):return filedialog.askopenfilename(parent=self.root,title=title,filetypes=[('Matching sound bank','*'+suffix)])
        try:bank,pair=choose_inputs(path,choose)
        except Exception as exc:messagebox.showerror('Cannot open bank',str(exc),parent=self.root);return
        self.run('Reading bank…',lambda:Document(bank,pair),self.accept)

    def output(self,suffix):
        options={}
        game=self.installed_game()
        if suffix=='_edited' and game and (game/'REDELBE_LR/RRPreview').is_dir():options['initialdir']=str(game/'REDELBE_LR/RRPreview')
        parent=filedialog.askdirectory(title='Choose a parent folder; a new output folder will be created',**options)
        if not parent:return None
        return Path(parent)/(self.doc.path.stem+suffix+'_'+time.strftime('%Y%m%d_%H%M%S'))

    def save(self):
        if not self.doc:return
        target=self.output('_edited')
        def task():
            self.doc.save(target);game=rrpreview_game(target)
            if game:
                ok,message=synchronize(game)
                return ok,'Saved: '+str(target)+'\n'+message
            return True,'Saved: '+str(target)+' — After placing files in RRPreview, close the game and click Sync RRPreview.'
        def done(result):
            ok,message=result;self.status.set(message)
            if not ok:messagebox.showwarning('Bank saved; activation still needed',message+'\nClose the game and keep only one replacement per bank, then click Sync RRPreview.')
        if target:self.run('Saving and synchronizing RRPreview when applicable…',task,done)

    def installed_game(self):
        game=rrpreview_game(self.doc.path) if self.doc else None
        if game is None and getattr(sys,'frozen',False):
            for candidate in Path(sys.executable).resolve().parents:
                if (candidate/'DOA6LR.exe').is_file():game=candidate;break
        if game is None and getattr(self,'library_window',None) and self.library_window.library and self.library_window.library.is_lr:
            source=self.library_window.library.path
            for candidate in [source,*source.parents]:
                if (candidate/'DOA6LR.exe').is_file():game=candidate;break
        return game

    def sync(self):
        game=self.installed_game()
        if game is None:
            selected=filedialog.askdirectory(title='Select the DOA6LR game folder')
            if not selected:return
            game=Path(selected)
        def done(result):
            ok,message=result;self.status.set(message)
            if not ok:messagebox.showwarning('RRPreview was not activated',message)
        self.run('Synchronizing RRPreview — the game must be closed…',lambda:synchronize(game),done)

    def extract(self):
        if not self.doc:return
        target=self.output('_tracks')
        if target:self.run('Extracting tracks…',lambda:self.doc.export(target),lambda _:self.status.set('Extracted: '+str(target)))

    def replace(self):
        fid=self.selected()
        if fid is None:return
        source=filedialog.askopenfilename(title='Choose replacement audio',filetypes=[('Audio','*.mp3 *.wav *.ogg')])
        match=self.match_volume.get()
        if source:self.run('Converting and matching volume…',lambda:self.doc.replace(fid,source,match),lambda _:(self.populate(),self.selection(),self.status.set('Replacement ready. Preview it, then Save new bank.')))

    def apply_volume(self,all_replacements):
        if self.busy or not self.doc:return
        fid=None if all_replacements else self.selected()
        ids=list(self.doc.changes) if all_replacements else ([fid] if fid is not None else [])
        if not ids:return
        self.run('Matching replacements to their original tracks…',lambda:self.doc.match_replacements(ids),lambda n:(self.populate(),self.selection(),self.status.set(f'Volume matching processed {n} replacement(s). Selected track details show the result. Save new bank to keep changes.')))

    def batch(self):
        if not self.doc:return
        folder=filedialog.askdirectory(title='Choose extracted or replacement audio (readable names or track IDs)')
        if not folder:return
        match=self.match_volume.get()
        def task():
            items=batch_files(folder,self.doc.rows)
            previous=(self.doc.a,self.doc.t,dict(self.doc.changes),dict(self.doc.replacement_inputs),dict(self.doc.volume_reports))
            try:
                for fid,p in items.items():self.doc.replace(fid,p,match)
            except Exception:
                self.doc.a,self.doc.t,self.doc.changes,self.doc.replacement_inputs,self.doc.volume_reports=previous;self.doc.refresh();raise
            return len(items)
        self.run('Converting batch; the window will remain responsive…',task,lambda n:(self.populate(),self.status.set(f'{n} replacements ready. Save new bank to finish.')))

    def preview(self):
        fid=self.selected()
        if fid is None:return
        winsound.PlaySound(None,0)
        def task():
            ext,audio=self.doc.audio(fid);source=Path(self.temp.name)/('preview'+ext);source.write_bytes(audio)
            target=Path(self.temp.name)/'playback.wav'
            ffmpeg(['-y','-i',source,'-c:a','pcm_s16le',target]);return str(target)
        self.run('Preparing preview…',task,lambda path:(winsound.PlaySound(path,winsound.SND_FILENAME|winsound.SND_ASYNC),self.status.set('Playing selected track.')))

    def reset(self):
        if self.doc and self.discard():self.doc.reset();self.populate();self.status.set('All edits undone.')

    def help(self):
        base=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]/'packages/SRS_Audio_Studio_LR'
        path=base/'README.html'
        if path.exists():os.startfile(path)
        else:messagebox.showinfo('Instructions','Open bank → select track → Replace → Save new bank. Keep SRSA/SRST together. See README.md for Audacity settings.')

    def close(self):
        if self.busy:messagebox.showinfo('Working','Please wait for the current operation to finish.');return
        if not self.discard():return
        winsound.PlaySound(None,0);self.temp.cleanup();self.root.destroy()

def main():
    try:
        import ctypes;ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('REDELBE.SRSAudioStudioLR');ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:pass
    from tkinterdnd2 import TkinterDnD
    from srs_dnd import install
    root=TkinterDnD.Tk();app=Studio(root);install(app)
    if len(sys.argv)>1 and sys.argv[1]!='--smoke-test':
        app.tabs.select(app.editor_page)
        path=sys.argv[1];root.after(150,lambda:app.open_path(path))
    if len(sys.argv)>2 and sys.argv[1]=='--smoke-test':
        app.accept(Document(sys.argv[2]));root.update()
        print(json.dumps({'title':root.title(),'rows':len(app.tree.get_children()),'columns':list(app.tree['columns']),'status':app.status.get()}));app.close();return
    if len(sys.argv)==1:root.after(150,app.library)
    app.tabs.bind('<<NotebookTabChanged>>',app.tab_changed)
    root.mainloop()
if __name__=='__main__':main()
