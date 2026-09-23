"""Tk-only loading window; worker threads report progress through Studio's queue."""
from pathlib import Path
import sys,tkinter as tk
from tkinter import ttk

class LoadingWindow:
    def __init__(self,parent,label,determinate=True):
        self.determinate=determinate
        self.window=tk.Toplevel(parent);self.window.title('SRS Audio Studio LR — Loading')
        self.window.resizable(False,False);self.window.transient(parent)
        self.window.configure(background='white');self.window.protocol('WM_DELETE_WINDOW',lambda:None)
        self.closed=False;self.value=0;self.frames=[];self.frame=0;self.timer=None
        asset=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))/'assets/kasumi_loading_frames.png'
        if asset.exists():
            sheet=tk.PhotoImage(master=self.window,file=str(asset))
            for i in range(8):
                frame=tk.PhotoImage(master=self.window,width=240,height=240)
                x,y=(i%4)*240,(i//4)*240
                frame.tk.call(str(frame),'copy',str(sheet),'-from',x,y,x+240,y+240)
                self.frames.append(frame)
        self.picture=tk.Label(self.window,bg='white');self.picture.pack(padx=36,pady=(12,0))
        tk.Label(self.window,text='Loading, please wait.' if determinate else 'Working, please wait.',font=('Segoe UI',16,'bold'),bg='white',fg='#173f70').pack(pady=(4,8))
        self.percent=tk.StringVar(value='0%' if determinate else '')
        tk.Label(self.window,textvariable=self.percent,font=('Segoe UI',23,'bold'),bg='white',fg='#1769aa').pack()
        self.bar=ttk.Progressbar(self.window,maximum=100,length=320,mode='determinate');self.bar.pack(padx=28,pady=10)
        if not determinate:self.bar.configure(mode='indeterminate');self.bar.start(15)
        self.detail=tk.StringVar(value=label)
        tk.Label(self.window,textvariable=self.detail,bg='white',fg='#526171',wraplength=320).pack(padx=22,pady=(0,20))
        self.window.update_idletasks();parent.update_idletasks()
        w,h=self.window.winfo_reqwidth(),self.window.winfo_reqheight()
        x=max(0,parent.winfo_rootx()+(parent.winfo_width()-w)//2)
        y=max(0,parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.window.geometry(f'+{x}+{y}');self.window.grab_set();self.animate()
    def animate(self):
        if self.closed:return
        delay=180
        if self.frames:
            delay=(480,180,180,220,500,220,180,220)[self.frame%8]
            self.picture.configure(image=self.frames[self.frame])
            self.frame=(self.frame+1)%len(self.frames)
        self.timer=self.window.after(delay,self.animate)
    def update(self,value,label):
        if self.closed:return
        self.value=max(self.value,min(100,int(value)));self.bar['value']=self.value
        if self.determinate:self.percent.set(f'{self.value}%')
        self.detail.set(label)
    def close(self):
        if self.closed:return
        self.closed=True
        self.bar.stop()
        if self.timer:self.window.after_cancel(self.timer)
        self.window.grab_release();self.window.destroy()
