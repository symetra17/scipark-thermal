import tkinter as tk

def gui_process(action_q):
    def thd_up():
        if not action_q.full():
            action_q.put('thd+')
    def thd_down():
        if not action_q.full():
            action_q.put('thd-')

    def thd2_up():
        if not action_q.full():
            action_q.put('thd2+')
    def thd2_down():
        if not action_q.full():
            action_q.put('thd2-')

    def offset_up():
        if not action_q.full():
            action_q.put('offset+')
    def offset_down():
        if not action_q.full():
            action_q.put('offset-')

    def pick_ref_l():
        if not action_q.full():
            action_q.put('refl')

    def pick_ref_h():
        if not action_q.full():
            action_q.put('refh')

    def pick_ref_head():
        if not action_q.full():
            action_q.put('ref head')

    def pick_ref_tape_on_head():
        if not action_q.full():
            action_q.put('ref head tape')

    root=tk.Tk()
    root.wm_attributes("-topmost", 1)
    root.geometry("+1550+960")
    root.overrideredirect(True) # removes title bar
    btns = []
    btns.append(tk.Button(root,text='THD+',command=thd_up))
    btns.append(tk.Button(root,text='THD-',command=thd_down))
    btns.append(tk.Button(root,text='OFFSET+',command=offset_up))
    btns.append(tk.Button(root,text='OFFSET-',command=offset_down))
    btns.append(tk.Button(root,text='REF L',command=pick_ref_l))
    btns.append(tk.Button(root,text='REF H',command=pick_ref_h))
    btns.append(tk.Button(root,text='REF HEAD',command=pick_ref_head))
    btns.append(tk.Button(root,text='TAPE ON HEAD', command=pick_ref_tape_on_head))

    for item in btns:
        item.config(width=10)
    btns[0].grid(row=0, column=0, padx=6, pady=4)
    btns[1].grid(row=1, column=0, padx=6, pady=4)
    btns[2].grid(row=0, column=2, padx=6, pady=4)
    btns[3].grid(row=1, column=2, padx=6, pady=4)
    btns[4].grid(row=0, column=3, padx=6, pady=4)
    btns[5].grid(row=1, column=3, padx=6, pady=4)
    btns[6].grid(row=0, column=4, padx=6, pady=4)
    btns[7].grid(row=1, column=4, padx=6, pady=4)
    root.mainloop()
