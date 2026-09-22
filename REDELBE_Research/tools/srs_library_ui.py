"""Tagged audio browser; original archive is always read-only."""
from pathlib import Path
import json,os,sys,time,tkinter as tk
from tkinter import ttk,filedialog,messagebox
import winsound
from srs_library import Library,CATEGORIES
from srs_audio_core import Document,ffmpeg
from srs_table import TableSort

def settings_path():return Path(os.environ.get('LOCALAPPDATA',Path.home()))/'SRS Audio Studio LR'/'library.json'

class LibraryWindow:
    def __init__(self,studio,parent=None):
        self.studio=studio;self.library=None;self.visible=[]
        self.embedded=parent is not None
        self.root=studio.root if self.embedded else tk.Toplevel(studio.root)
        if not self.embedded:self.root.title('Audio library — DOA6LR');self.root.geometry('1180x720')
        frame=ttk.Frame(parent if self.embedded else self.root,padding=16);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Audio library',font=('Segoe UI',18,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Browse LR audio first. Original DOA6 archives are optional and can be opened manually.').pack(anchor='w',pady=8)
        sources=ttk.Frame(frame);sources.pack(fill='x')
        ttk.Button(sources,text='Choose LR folder',command=self.choose_lr).pack(side='left')
        ttk.Button(sources,text='Open DOA6 archive…',command=self.choose).pack(side='left',padx=6)
        self.source=tk.StringVar(value='Choose your DOA6LR game folder. Extracted SRSA files can also be opened from the main editor.')
        ttk.Label(frame,textvariable=self.source,wraplength=1100).pack(anchor='w',pady=8)
        top=ttk.Frame(frame);top.pack(fill='x',pady=(0,8))
        self.tag=tk.StringVar(value='All');self.query=tk.StringVar()
        ttk.Label(top,text='Category').pack(side='left',padx=(16,6))
        box=ttk.Combobox(top,textvariable=self.tag,values=('All',*CATEGORIES),state='readonly',width=14);box.pack(side='left');box.bind('<<ComboboxSelected>>',lambda e:self.populate())
        ttk.Label(top,text='Find name / character code / hash').pack(side='left',padx=(16,6))
        ttk.Entry(top,textvariable=self.query,width=32).pack(side='left');self.query.trace_add('write',lambda *a:self.populate())
        languages=ttk.Frame(frame);languages.pack(fill='x',pady=(0,8))
        self.language=tk.StringVar(value='All')
        ttk.Label(languages,text='Language').pack(side='left',padx=(0,8))
        for text in ('All','ENG','JP','Other / shared'):
            ttk.Radiobutton(languages,text=text,value=text,variable=self.language,command=self.populate,style='Toolbutton').pack(side='left',padx=3)
        ttk.Label(languages,text='Click headings to sort; drag headings to move columns.').pack(side='right')
        area=ttk.Frame(frame);area.pack(fill='both',expand=True)
        cols=('category','character','language','name','id','bank','codec')
        self.tree=ttk.Treeview(area,columns=cols,show='headings',selectmode='browse')
        for c,title,width in zip(cols,('Tag','Character','Language','Readable name','Hash','Bank','Format'),(90,80,100,300,105,260,100)):
            self.tree.heading(c,text=title);self.tree.column(c,width=width,minwidth=65,stretch=c in ('name','bank'))
        self.sorter=TableSort(self.tree,numeric=('id',))
        from srs_dnd import attach_tree
        attach_tree(studio,self.tree,self)
        scroll=ttk.Scrollbar(area,orient='vertical',command=self.tree.yview);scroll.pack(side='right',fill='y');self.tree.configure(yscrollcommand=scroll.set);self.tree.pack(fill='both',expand=True)
        self.tree.bind('<Double-1>',lambda e:self.preview() if self.tree.identify_region(e.x,e.y)=='cell' else None)
        self.count=tk.StringVar();ttk.Label(frame,textvariable=self.count).pack(anchor='w',pady=8)
        actions=ttk.Frame(frame);actions.pack(fill='x')
        for title,command in [('Preview',self.preview),('Stop',lambda:winsound.PlaySound(None,0)),('Extract selected track',self.extract_one),('Extract filtered tracks',self.extract_filtered),('Open bank in editor',self.open_bank)]:
            ttk.Button(actions,text=title,command=command).pack(side='left',padx=(0,8))
        ttk.Label(frame,textvariable=studio.status,wraplength=1100).pack(anchor='w',pady=10)
        if not self.embedded:self.root.protocol('WM_DELETE_WINDOW',self.close)
        candidates=[]
        if getattr(sys,'frozen',False):candidates.extend(Path(sys.executable).resolve().parents)
        try:candidates.append(Path(json.loads(settings_path().read_text(encoding='utf8'))['lr_folder']))
        except (OSError,ValueError,KeyError):pass
        for candidate in candidates:
            if (candidate/'DOA6LR.exe').is_file() and (candidate/'fdata_package').is_dir():self.load(candidate);break
    def close(self):
        if self.studio.busy:return
        if self.embedded:return
        self.root.destroy();self.studio.library_window=None
    def choose(self):
        if self.studio.busy:return
        p=filedialog.askopenfilename(parent=self.root,title='Choose original DOA6 RRPreview.rdb',filetypes=[('RDB archive','*.rdb')])
        if p:self.load(p)
    def choose_lr(self):
        if self.studio.busy:return
        p=filedialog.askdirectory(parent=self.root,title='Choose the DOA6LR game folder')
        if p:self.load(p)
    def load(self,p):
        def done(library):
            self.library=library;label='DOA6LR' if library.is_lr else 'Original DOA6'
            if not self.embedded:self.root.title('Audio library — '+label)
            self.source.set(label+' — '+str(library.path));self.populate()
            try:
                if library.is_lr:
                    settings_path().parent.mkdir(parents=True,exist_ok=True);settings_path().write_text(json.dumps({'lr_folder':str(library.path)}),encoding='utf8')
            except OSError:pass
            if library.errors:messagebox.showwarning('Some banks could not be indexed','\n'.join(library.errors),parent=self.root)
            if self.embedded and self.studio.tabs.select()==str(self.studio.editor_page) and self.studio.doc is None:self.open_bank()
        self.studio.run('Indexing audio banks and readable track names…',lambda:Library(p),done)
    def populate(self):
        if not self.library:return
        self.tree.delete(*self.tree.get_children());q=self.query.get().lower();tag=self.tag.get()
        self.visible=[r for r in self.library.rows if (tag=='All' or r['category']==tag) and (not q or q in (r['name']+' '+r['bank_name']+' '+r['character']+f" 0x{r['id']:08x}").lower())]
        self.visible=[r for r in self.visible if self.language.get()=='All' or r['language']==self.language.get()]
        for i,r in enumerate(self.visible):self.tree.insert('','end',iid=str(i),values=(r['category'],r['character'],r['language'],r['name'] or '(name unavailable)',f"0x{r['id']:08x}",r['bank_name'],r['codec']))
        self.sorter.apply()
        self.count.set(f'{len(self.visible):,} shown / {len(self.library.rows):,} tracks · {len(self.library.banks)} banks · {len(self.library.errors)} bank errors')
    def selected(self):
        if self.studio.busy:return None
        ids=self.tree.selection()
        return self.visible[int(ids[0])] if ids else None
    def preview(self):
        row=self.selected()
        if row is None:return
        winsound.PlaySound(None,0)
        def task():
            ext,data=self.library.audio(row);source=Path(self.studio.temp.name)/('library_preview'+ext);source.write_bytes(data)
            target=Path(self.studio.temp.name)/'library_playback.wav';ffmpeg(['-y','-i',source,'-c:a','pcm_s16le',target]);return str(target)
        self.studio.run('Preparing library preview…',task,lambda p:winsound.PlaySound(p,winsound.SND_FILENAME|winsound.SND_ASYNC))
    def extract_one(self):
        row=self.selected()
        if row:self.extract([row])
    def extract_filtered(self):
        if not self.studio.busy and self.visible:self.extract(list(self.visible))
    def extract(self,rows):
        parent=filedialog.askdirectory(parent=self.root,title=f'Extract {len(rows)} tracks into a new folder')
        if not parent:return
        target=Path(parent)/('Audio_tracks_'+time.strftime('%Y%m%d_%H%M%S'))
        self.studio.run(f'Extracting {len(rows)} tracks…',lambda:self.library.export_tracks(rows,target),lambda _:self.studio.status.set('Extracted: '+str(target)))
    def open_bank(self):
        row=self.selected()
        if row is None and self.library:
            row=next((r for r in self.library.rows if r['category']=='Announcer'),next(iter(self.library.rows),None))
        if row is None or not self.studio.discard():return
        import uuid
        target=Path(self.studio.temp.name)/('bank_'+uuid.uuid4().hex)
        def task():return Document(self.library.export_bank(row['bank'],target))
        def done(doc):
            self.studio.accept(doc);iid=f"0x{row['id']:08x}"
            if self.studio.tree.exists(iid):self.studio.tree.selection_set(iid);self.studio.tree.see(iid)
            self.studio.root.lift()
        self.studio.run('Reading the selected game bank into the editor…',task,done)
