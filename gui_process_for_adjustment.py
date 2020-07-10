import tkinter as tk

def gui_process(action_q):
    def offset_x_up():
        if not action_q.full():
            action_q.put('offset_x_+')
    def offset_x_down():
        if not action_q.full():
            action_q.put('offset_x_-')

    def offset_y_up():
        if not action_q.full():
            action_q.put('offset_y_+')
    def offset_y_down():
        if not action_q.full():
            action_q.put('offset_y_-')

    def offset_x_up_10():
        if not action_q.full():
            action_q.put('offset_x_+_10')
    def offset_x_down_10():
        if not action_q.full():
            action_q.put('offset_x_-_10')

    def offset_y_up_10():
        if not action_q.full():
            action_q.put('offset_y_+_10')
    def offset_y_down_10():
        if not action_q.full():
            action_q.put('offset_y_-_10')

    root=tk.Tk()
    root.wm_attributes("-topmost", 1)
    root.geometry("+1550+960")
    root.overrideredirect(True) # removes title bar
    btns = []
    btns.append(tk.Button(root,text='OFFSET_X+',command=offset_x_up))
    btns.append(tk.Button(root,text='OFFSET_X-',command=offset_x_down))
    btns.append(tk.Button(root,text='OFFSET_Y+',command=offset_y_up))
    btns.append(tk.Button(root,text='OFFSET_Y-',command=offset_y_down))
    btns.append(tk.Button(root,text='OFFSET_X+10',command=offset_x_up_10))
    btns.append(tk.Button(root,text='OFFSET_X-10',command=offset_x_down_10))
    btns.append(tk.Button(root,text='OFFSET_Y+10',command=offset_y_up_10))
    btns.append(tk.Button(root,text='OFFSET_Y-10',command=offset_y_down_10))

    for item in btns:
        item.config(width=10)
    btns[0].grid(row=0, column=0, padx=6, pady=4)
    btns[1].grid(row=1, column=0, padx=6, pady=4)
    btns[2].grid(row=0, column=2, padx=6, pady=4)
    btns[3].grid(row=1, column=2, padx=6, pady=4)
    btns[4].grid(row=0, column=4, padx=6, pady=4)
    btns[5].grid(row=1, column=4, padx=6, pady=4)
    btns[6].grid(row=0, column=6, padx=6, pady=4)
    btns[7].grid(row=1, column=6, padx=6, pady=4)


    root.mainloop()
