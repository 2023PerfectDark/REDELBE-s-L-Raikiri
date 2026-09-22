"""Clickable column sorting that keeps track identities and selection intact."""
class TableSort:
    def __init__(self,tree,numeric=()):
        self.tree=tree;self.numeric=set(numeric);self.column=None;self.reverse=False
        self.titles={c:tree.heading(c,'text') for c in tree['columns']}
        for c in self.titles:tree.heading(c,command=lambda column=c:self.click(column))
        self.drag_column=None;self.dragged=False
        tree.bind('<ButtonPress-1>',self.press,add='+')
        tree.bind('<B1-Motion>',self.motion,add='+')
        tree.bind('<ButtonRelease-1>',self.release,add='+')

    def order(self):
        columns=self.tree['displaycolumns']
        return list(self.tree['columns']) if columns==('#all',) else list(columns)

    def at(self,x):
        display=self.tree.identify_column(x)
        index=int(display[1:])-1 if display else -1
        order=self.order()
        return order[index] if 0<=index<len(order) else None

    def press(self,event):
        self.drag_column=None;self.dragged=False
        if self.tree.identify_region(event.x,event.y)=='heading':
            self.drag_column=self.at(event.x);self.start_x=event.x
            return 'break'

    def motion(self,event):
        if self.drag_column is None:return
        if abs(event.x-self.start_x)>6:self.dragged=True
        if self.dragged:
            target=self.at(event.x)
            if target and target!=self.drag_column:
                order=self.order();index=order.index(target);order.remove(self.drag_column);order.insert(index,self.drag_column)
                self.tree.configure(displaycolumns=order)
        return 'break'

    def release(self,event):
        if self.drag_column is None:return
        column=self.drag_column;self.drag_column=None
        if not self.dragged:self.click(column)
        return 'break'

    def click(self,column):
        self.reverse=not self.reverse if self.column==column else False
        self.column=column;self.apply()
        self.tree.yview_moveto(0)

    def apply(self):
        if self.column is None:return
        column=self.column
        def value(iid):
            text=self.tree.set(iid,column).strip()
            if column in self.numeric:
                try:return float(int(text,16)) if text.lower().startswith('0x') else float(text.split()[0])
                except (ValueError,IndexError):return float('-inf')
            return text.casefold()
        rows=list(self.tree.get_children())
        # Keep unnamed character codes at the bottom in either direction.
        filled=[iid for iid in rows if self.tree.set(iid,column).strip()]
        empty=[iid for iid in rows if not self.tree.set(iid,column).strip()]
        for index,iid in enumerate(sorted(filled,key=value,reverse=self.reverse)+empty):self.tree.move(iid,'',index)
        for c,title in self.titles.items():self.tree.heading(c,text=title+(' ▼' if self.reverse else ' ▲') if c==column else title)
