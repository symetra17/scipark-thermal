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

    def change_to_BW():
        if not action_q.full():
            action_q.put('BW')
    def change_to_JET():
        if not action_q.full():
            action_q.put('JET')
    def change_to_HSV():
        if not action_q.full():
            action_q.put('HSV')
    def change_to_RED():
        if not action_q.full():
            action_q.put('RED')
    def quit_func():
        if not action_q.full():
            action_q.put('quit')
    root=tk.Tk()
    root.wm_attributes("-topmost", 1)
    root.geometry("+1550+960")
    root.overrideredirect(True) # removes title bar
    btns = []
    btns.append(tk.Button(root,text='Enter Full',command=thd_up))
    btns.append(tk.Button(root,text='Exit Full',command=thd_down))
    btns.append(tk.Button(root,text='quit',command=quit_func))
    btns.append(tk.Button(root,text='OFFSET-',command=offset_down))

    # try:
    #     fid = open('black_body.cfg','r')
    #     s = fid.read()
    #     USE_BBODY = eval(s)
    #     fid.close()
    # except:
    #     USE_BBODY = False
    USE_BBODY=True
    if USE_BBODY:
       btns.append(tk.Button(root,text='REF L',command=pick_ref_l))
       btns.append(tk.Button(root,text='REF H',command=pick_ref_h))
       btns.append(tk.Button(root,text='REF HEAD',command=pick_ref_head))
       btns.append(tk.Button(root,text='TAPE ON HEAD', command=pick_ref_tape_on_head))
       btns.append(tk.Button(root,text='BW', command=change_to_BW))
       btns.append(tk.Button(root,text='JET', command=change_to_JET))
       btns.append(tk.Button(root,text='HSV', command=change_to_HSV))
       btns.append(tk.Button(root,text='RED HOT', command=change_to_RED))

    for item in btns:
        item.config(width=10)
    btns[0].grid(row=0, column=0, padx=6, pady=4)
    btns[1].grid(row=1, column=0, padx=6, pady=4)
    btns[2].grid(row=0, column=2, padx=6, pady=4)
    btns[3].grid(row=1, column=2, padx=6, pady=4)

    if USE_BBODY:
        btns[4].grid(row=0, column=3, padx=6, pady=4)
        btns[5].grid(row=1, column=3, padx=6, pady=4)
        btns[6].grid(row=0, column=4, padx=6, pady=4)
        btns[7].grid(row=1, column=4, padx=6, pady=4)

    btns[8].grid(row=2,column=0, padx=6, pady=4)
    btns[9].grid(row=2,column=2, padx=6, pady=4)
    btns[10].grid(row=2,column=3, padx=6, pady=4)
    btns[11].grid(row=2,column=4, padx=6, pady=4)
    root.mainloop()
