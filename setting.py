import tkinter as tk
from tkinter import ttk
from tkinter import *
from PIL import Image, ImageTk
from os.path import join as opjoin
import os
from tkinter import font  as tkfont # python 3


class SampleApp(tk.Tk): #frame
    def __init__(self, msg_q):
        tk.Tk.__init__(self)
        self.msg_q = msg_q                
        self.title('AIBTSS Settings Login')
        self.geometry('500x280')   
        self.iconphoto(False, tk.PhotoImage(file=opjoin('icons',"sq-logo.png")))
        self.lang_path = opjoin('cfg','lang.cfg')
        self.blue_bg      = '#3C6D9E'
        self.dark_blue_bg = '#344454'
        self.white_fg     = '#FFFFFF'
        self.attributes('-topmost', True)
        self.config(bg = self.blue_bg)
        self.resizable(0,0)

        temp        = Image.open(opjoin('icons','20200716',"temp-detection.png"))
        bb          = Image.open(opjoin('icons','20200716',"bb-calibration.png"))
        head        = Image.open(opjoin('icons','20200716',"frame-alignment.png"))
        face        = Image.open(opjoin('icons','20200716','face-blurring.png'))
        fm          = Image.open(opjoin('icons','20200716','fm.png'))
        record      = Image.open(opjoin('icons','20200716','alert-review.png'))
        mask        = Image.open(opjoin('icons','20200716',"masking.png"))
        colour      = Image.open(opjoin('icons','20200716','color-mode.png')) 
        temp_a      = Image.open(opjoin('icons','20200716',"temp-detection-action.png"))
        bb_a        = Image.open(opjoin('icons','20200716',"bb-calibration-action.png"))
        head_a      = Image.open(opjoin('icons','20200716',"frame-alignment-action.png"))
        face_a      = Image.open(opjoin('icons','20200716','face-blurring-action.png'))
        record_a    = Image.open(opjoin('icons','20200716','alert-review-action.png'))
        mask_a      = Image.open(opjoin('icons','20200716',"masking-action.png"))
        colour_a    = Image.open(opjoin('icons','20200716','color-mode-action.png'))
        fm_a        =Image.open(opjoin('icons','20200716','fm-a.png'))
        db          = Image.open(opjoin('icons','dark_b.png'))
        line        = Image.open(opjoin('icons', 'line.png'))

        self.icon_temp          = ImageTk.PhotoImage(temp)
        self.icon_bb            = ImageTk.PhotoImage(bb)
        self.icon_head          = ImageTk.PhotoImage(head)
        self.icon_mask          = ImageTk.PhotoImage(mask)
        self.icon_fm            = ImageTk.PhotoImage(fm)
        self.icon_face          = ImageTk.PhotoImage(face)
        self.icon_colour        = ImageTk.PhotoImage(colour)
        self.icon_record        = ImageTk.PhotoImage(record)
        self.icon_temp_a        = ImageTk.PhotoImage(temp_a)
        self.icon_bb_a          = ImageTk.PhotoImage(bb_a)
        self.icon_head_a        = ImageTk.PhotoImage(head_a)
        self.icon_mask_a        = ImageTk.PhotoImage(mask_a)
        self.icon_fm_a          = ImageTk.PhotoImage(fm_a)
        self.icon_face_a        = ImageTk.PhotoImage(face_a)
        self.icon_colour_a      = ImageTk.PhotoImage(colour_a)
        self.icon_record_a      = ImageTk.PhotoImage(record_a)
        self.icon_db            = ImageTk.PhotoImage(db)
        self.icon_line          = ImageTk.PhotoImage(line)

        container = tk.Frame(self)
        container.grid()

        self.frames = {}
        self.frames["StartPage"]    = StartPage(parent=container, controller=self)
        self.frames["PageOne"]      = PageOne(parent=container, controller=self)
        self.frames["PageTwo"]      = PageTwo(parent=container, controller=self)
        self.frames["PageThree"]    = PageThree(parent=container, controller=self)
        self.frames["PageFour"]    = PageFour(parent=container, controller=self)
        self.frames["PageFive"]    = PageFive(parent=container, controller=self)
        self.frames["PageSix"]    = PageSix(parent=container, controller=self)
        self.frames["PageSeven"]    = PageSeven(parent=container, controller=self)
        self.frames["PageEight"]    = PageEight(parent=container, controller=self)

        self.frames["StartPage"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageOne"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageTwo"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageThree"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageFour"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageFive"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageSix"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageSeven"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageEight"].grid(row=0, column=0, sticky="nsew")

        self._frame = None
        self.switch_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.load_cfg()
        frame.create_widgets()
        frame.tkraise()

    def switch_frame(self, page_name):
        """Destroys current frame and replaces it with a new one.""" 
        new_frame = self.frames[page_name]
        new_frame.load_cfg()
        new_frame.create_widgets()
        try:
            new_frame.setting()
        except:
            pass
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.tkraise()

    def apply(self, text, adj):
        if not self.msg_q.full():
            self.msg_q.put([text,adj])
    
class StartPage(tk.Frame): #cover
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.grid_columnconfigure(0,minsize = 100)
        self.grid_columnconfigure(1,minsize = 300)
        self.grid_columnconfigure(2,minsize = 100)
        self.grid_rowconfigure(3,minsize = 30)
        self.grid_rowconfigure(5,minsize = 60)
        self.config(bg=controller.white_fg)

    def load_cfg(self):
        login_chi = Image.open(opjoin('icons','tc.buttons','login.png'))
        login_ind = Image.open(opjoin('icons','ind.buttons','login.png'))
        login_eng = Image.open(opjoin('icons','en.buttons','login.png'))
        under   = Image.open(opjoin('icons','cover_underline.png'))
        self.icon_under = ImageTk.PhotoImage(under)
        self.icon_go_chi = ImageTk.PhotoImage(login_chi)
        self.icon_go_ind = ImageTk.PhotoImage(login_ind)
        self.icon_go_eng = ImageTk.PhotoImage(login_eng)
        self.chi_path  = opjoin('words','chi.txt')
        self.eng_path  = opjoin('words','eng.txt')
        self.ind_path  = opjoin('words','ind.txt') 
        pw_path = opjoin('cfg','pw.cfg')
        f = open(pw_path, 'r')
        self.pw_get = str(f.read())
        f.close()

        f = open(self.controller.lang_path,'r')
        self.lang_get = f.read()
        f.close()

        try:
            if self.lang_get =='chi':
                f = open(self.chi_path,'r', encoding="utf8")
            elif self.lang_get =='eng':
                f = open(self.eng_path,'r', encoding="utf8")
            elif self.lang_get =='ind':
                f = open(self.ind_path,'r', encoding="utf8")

            word = eval(f.read())  
            self.cover_txt  = word['cover_txt']
            self.PW_txt     = word['PW_txt']
            self.msg_txt    = word['msg_txt']
            self.font_style = word['font_style']
            btn_f = word['btn_file']
            login   = Image.open(opjoin('icons',btn_f,'login.png'))
            self.icon_go = ImageTk.PhotoImage(login)
            self.cover_font = tkfont.Font(family=self.font_style, size=30)
            self.content_font = tkfont.Font(family=self.font_style, size=12)
            f.close()
        except:
            f = open(self.eng_path,'r', encoding="utf8")
            word = eval(f.read())  
            self.cover_txt  = word['cover_txt']
            self.PW_txt     = word['PW_txt']
            self.msg_txt    = word['msg_txt']
            self.font_style = word['font_style']
            btn_f = word['btn_file']
            login   = Image.open(opjoin('icons',btn_f,'login.png'))
            self.icon_go = ImageTk.PhotoImage(login)
            f.close()
        
    def create_widgets(self):
        self.white_fg           = '#FFFFFF'
        self.green              = '#A5C73C'
        self.dark_blue_bg       = '#344454'

        self.cover_wd = tk.Label(self, text = self.cover_txt, bg = self.white_fg, #配置頁面
                              fg = self.green, font=(self.cover_font))
        self.cover_wd.grid(row = 0, column =1, sticky = S, pady = 20)

        self.PW = tk.Label(self,text = self.PW_txt, bg=self.white_fg, fg= self.dark_blue_bg, font=(self.content_font))         #密碼
        self.PW.grid(row = 1, column = 1,sticky = W)    

        eny = StringVar()
        self.password = tk.Entry(self, show = "*",textvariable = eny, width=37, bd = 0)  #
        self.password.grid(row = 1, column = 1, sticky = E)    
        self.password.bind('<Return>',lambda event=None: self.login_btn.invoke())
        self.password.focus()

        underline = tk.Label(self,image  = self.icon_under, bg = self.white_fg,width = 300, height = 2)
        underline.grid(row = 2, column = 1, sticky = N)

        self.msg = tk.Label(self,text = self.msg_txt, bg = self.white_fg, fg = 'red', font=(self.content_font))
        self.msg.grid_forget()

        self.login_btn = tk.Button(self, image = self.icon_go, relief = FLAT, bd = 0,command=self.password_validation)
        self.login_btn.image = self.icon_go
        self.login_btn.grid(row = 5, column = 1)

        self.lang_cbb = ttk.Combobox(self,values = ['ENG','IND','中'], state = 'readonly', width = 46)
        self.lang_cbb.grid(row = 4, column = 1)
        self.lang_cbb.bind('<<ComboboxSelected>>', self.lang)
        if self.lang_get =='eng':
            self.lang_cbb.set('ENG')
        elif self.lang_get =='ind':
            self.lang_cbb.set('IND')
        elif self.lang_get =='chi':
            self.lang_cbb.set('中')

    def lang(self, event=None):
        get = str(self.lang_cbb.get())
        if get =='ENG':
            f = open(self.eng_path,'r', encoding="utf8")
            word = eval(f.read()) 
            cover_font = tkfont.Font(family=word['font_style'], size=30)
            content_font = tkfont.Font(family=word['font_style'], size=12)
            self.cover_wd.config(text = word['cover_txt'], font=(cover_font))
            self.PW.config(text = word['PW_txt'], font=(content_font))
            self.msg.config(text = word['msg_txt'], font=(content_font))
            self.login_btn.config(image = self.icon_go_eng)
            self.login_btn.image = self.icon_go_eng
            f.close()
            f = open(self.controller.lang_path,'w+')
            f.write('eng')
            f.close()
        elif get =="IND":
            f = open(self.ind_path,'r', encoding="utf8")
            word = eval(f.read()) 
            cover_font = tkfont.Font(family=word['font_style'], size=30)
            content_font = tkfont.Font(family=word['font_style'], size=12)
            self.cover_wd.config(text = word['cover_txt'], font=(cover_font))
            self.PW.config(text = word['PW_txt'], font=(content_font))
            self.msg.config(text = word['msg_txt'], font=(content_font))
            self.login_btn.config(image = self.icon_go_ind)
            self.login_btn.image = self.icon_go_ind
            f.close()
            f = open(self.controller.lang_path,'w+')
            f.write('ind')
            f.close()
        elif get == '中':
            f = open(self.chi_path,'r', encoding="utf8")
            word = eval(f.read()) 
            cover_font = tkfont.Font(family=word['font_style'], size=30)
            content_font = tkfont.Font(family=word['font_style'], size=12)
            self.cover_wd.config(text = word['cover_txt'], font=(cover_font))
            self.PW.config(text = word['PW_txt'], font=(content_font))
            self.msg.config(text = word['msg_txt'], font=(content_font))
            self.login_btn.config(image = self.icon_go_chi)
            self.login_btn.image = self.icon_go_chi
            f.close()
            f = open(self.controller.lang_path,'w+')
            f.write('chi')
            f.close()

    def password_validation(self):
        if str(self.password.get()) == self.pw_get:
            self.controller.switch_frame("PageOne")
            self.controller.apply('password','login')
        else:
            self.msg.grid(row = 3, column = 1,stick = SW )
            self.controller.apply('password','wrong_password')

class PageOne(tk.Frame):#temperature setting
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller        
        
        for i in range(14):
          self.grid_rowconfigure([i],minsize = 40)        
        self.grid_rowconfigure(0,minsize = 65)
        self.grid_rowconfigure(14,minsize = 40)    
        self.config(bg=controller.blue_bg)
        self.cfg_count = 0
        self.create_count = 0
        
        row = 0
        column = 0

        left_dark_blue = tk.Label(self, image = controller.icon_db, bd =0)
        left_dark_blue.grid(row = 0, column = 0, rowspan = 100)

        line = tk.Label(self, image = controller.icon_line, bd = 0)
        line.grid(row = 0, column = 1, sticky = SW, padx = 10, pady = 20, columnspan = 3 )

        temp_icon = tk.Label(self, image = controller.icon_temp_a, bg = controller.dark_blue_bg, bd = 0)
        temp_icon.grid(row = row, column = column)

        button2 = tk.Button(self, image = controller.icon_bb, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageTwo"))
        button2.grid(row = row+1, column = column, rowspan = 2)
        button3 = tk.Button(self, image = controller.icon_head, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageThree"))
        button3.grid(row = row+3, column = column, rowspan = 2)
        button4 = tk.Button(self, image = controller.icon_mask, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFour"))
        button4.grid(row = row+5, column = column, rowspan = 2)
        button8 = tk.Button(self, image = controller.icon_fm, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageEight"))
        button8.grid(row = row+7, column = column, rowspan = 2)
        button5 = tk.Button(self, image = controller.icon_face, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFive"))
        button5.grid(row = row+9, column = column, rowspan = 2)
        button6 = tk.Button(self, image = controller.icon_colour, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSix"))
        button6.grid(row = row+11, column = column, rowspan = 2)
        button7 = tk.Button(self, image = controller.icon_record, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSeven"))
        button7.grid(row = row+13, column = column, rowspan = 2)

        

    def load_cfg(self):
        if self.cfg_count ==0:
            thd_path         = opjoin('cfg','thd_cels.cfg')
            emv_path         = opjoin('cfg','emissivity.cfg')
            temp_offset_path = opjoin('cfg','temp_offset.cfg')
            f = open(thd_path, 'r')
            self.output_degree = f.read()
            f.close()
            f = open(emv_path, 'r')
            self.output_emv =  '%.2f' % eval(f.read())
            f.close()   
            f = open(temp_offset_path, 'r')
            self.output_offset = f.read()
            f.close()
            
            f = open(self.controller.lang_path,'r')
            lang = f.read()
            f.close()
            txt_path = opjoin('words',lang+'.txt')
            f = open(txt_path, encoding='utf8')
            word = eval(f.read())  
            self.temp_txt   = word['temp_txt']
            self.thd_txt    = word['thd_txt']
            self.emv_txt    = word['emv_txt']
            self.unit_txt   = word['unit_txt']
            self.font_style = word['font_style']
            self.thd2_txt   = word['thd2_txt']
            btn_f = word['btn_file']
            f.close()
            
            q           = Image.open(opjoin('icons','18-question-icon.png'))
            plus_blue   = Image.open(opjoin('icons',"28-plus-blue.png"))    
            minus_blue  = Image.open(opjoin('icons',"28-minus-blue.png"))    
            C_71        = Image.open(opjoin('icons',"71C.png"))
            F_71        = Image.open(opjoin('icons',"71F.png"))
            temp_hint     = Image.open(opjoin('icons',btn_f,'300Help-temp.png'))
            self.icon_q           = ImageTk.PhotoImage(q)
            self.icon_plus        = ImageTk.PhotoImage(plus_blue)
            self.icon_minus       = ImageTk.PhotoImage(minus_blue)
            self.icon_C           = ImageTk.PhotoImage(C_71)
            self.icon_F           = ImageTk.PhotoImage(F_71)
            self.icon_temp_hint   = ImageTk.PhotoImage(temp_hint)

            self.unit         = '°C'
            self.title_font = tkfont.Font(family=self.font_style, size=16, weight="bold")
            self.content_font = tkfont.Font(family=self.font_style, size=11, weight = 'normal')
            self.display_font = tkfont.Font(family=self.font_style, size=20)
            self.cfg_count = self.cfg_count+1

    def create_widgets(self):
        if self.create_count ==0:
            self.blue_bg      = '#3C6D9E'
            self.dark_blue_bg = '#344454'
            self.org_fg       = '#EDB529'
            self.white_fg     = '#FFFFFF'
            self.green        = '#A5C73C'

            temp_row = 0
            temp_column = 0        

            self.temp_Q = tk.Label(self, image = self.icon_q, bg = self.blue_bg)
            self.temp_Q.grid(row = temp_row, column = temp_column+3, sticky = NE, pady = 18, padx = 9)
            self.temp_Q.bind('<Enter>', self.temp_enter)
            self.temp_Q.bind('<Leave>', self.temp_close)

            self.temp_title = tk.Label(self, text =self.temp_txt, bg=self.blue_bg, #溫度及相關設定
                                        fg= self.green, font=(self.title_font))
            self.temp_title.grid(row = temp_row, column = temp_column+1, sticky = NW, padx = 10, pady = 12)

            self.thd = tk.Label(self, text =self.thd_txt, bg=self.blue_bg,       #測溫門檻 (30°C-40°C):
                                            fg= self.white_fg, font=(self.content_font))
            self.thd.grid(row = temp_row+1, column = temp_column+1, sticky = W, padx = 10) 

            self.degree = tk.Label(self, text = self.output_degree + self.unit, bg=self.blue_bg, 
                                                fg= self.org_fg,font=(self.display_font))
            self.degree.grid(row = temp_row+2, column = temp_column+1, 
                                            sticky = W, padx = 10)
            self.output_degree = round(eval(self.output_degree),1)

            self.emv = tk.Label(self, text =self.emv_txt, bg=self.blue_bg, bd = 0, #放射率 (30°C-40°C):
                                            fg= self.white_fg,font=(self.content_font))
            self.emv.grid(row = temp_row+3, column = temp_column+1, sticky = W, padx = 10)  
                
            self.emv_degree = tk.Label(self, text = self.output_emv, bg=self.blue_bg, 
                                                fg= self.org_fg,font=(self.display_font))
            self.emv_degree.grid(row = temp_row+4, column = temp_column+1, 
                                            sticky = W, padx = 10)
            self.output_emv = round(eval(self.output_emv),2)
        
            self.unit_label = tk.Label(self, text = self.unit_txt, bg=self.blue_bg, bd = 0, #溫度單位: 
                                    fg= self.white_fg, font=(self.content_font))
            self.unit_label.grid(row = temp_row+6, column = temp_column+1, sticky = W, padx = 10)

            self.thd2 = tk.Label(self, text =self.thd2_txt, bg=self.blue_bg,       #測溫門檻 (30°C-40°C):
                                            fg= self.white_fg, font=(self.content_font))
            self.thd2.grid(row = temp_row+7, column = temp_column+1, sticky = W, padx = 10) 

            self.offset = tk.Label(self, text = self.output_offset, bg=self.blue_bg, 
                                                fg= self.org_fg,font=(self.display_font))
            self.offset.grid(row = temp_row+8, column = temp_column+1,
                                            sticky = W, padx = 10)
            self.output_offset = round(eval(self.output_offset),1)

            thd_inc_btn = tk.Button(self,image = self.icon_plus, width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg, bg = self.blue_bg, command = self.thd_inc)  ##'%.1f' 
            thd_inc_btn.grid(row = temp_row+2, column = temp_column+3, sticky = E, padx = 10, pady = 4)
            thd_dec_btn = tk.Button(self,image = self.icon_minus,width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg, bg = self.blue_bg, command = self.thd_dec)
            thd_dec_btn.grid(row = temp_row+2, column = temp_column+3, sticky = W, padx = 10, pady = 4)

            emv_inc_btn = tk.Button(self,image = self.icon_plus,width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg, bg = self.blue_bg, command = self.emv_inc)  ##'%.2f'
            emv_inc_btn.grid(row = temp_row+4, column = temp_column+3, sticky = E, padx = 10, pady = 4)
            emv_dec_btn = tk.Button(self,image = self.icon_minus, width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg, bg = self.blue_bg, command = self.emv_dec)
            emv_dec_btn.grid(row = temp_row+4, column = temp_column+3, sticky = W, padx = 10, pady = 4)

            self.unit_switch = tk.Button(self, image = self.icon_C, width=71, height=32,relief=FLAT,
                                        bg=self.blue_bg, command = self.switch)
            self.unit_switch.image = self.icon_C
            self.unit_switch.grid(row = temp_row+6,column = temp_column+3)

            offset_inc_btn = tk.Button(self,image = self.icon_plus, width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg, bg = self.blue_bg, command = self.offset_inc)  ##'%.1f' 
            offset_inc_btn.grid(row = temp_row+8, column = temp_column+3, sticky = E, padx = 10, pady = 4)
            offset_dec_btn = tk.Button(self,image = self.icon_minus,width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg, bg = self.blue_bg, command = self.offset_dec)
            offset_dec_btn.grid(row = temp_row+8, column = temp_column+3, sticky = W, padx = 10, pady = 4)

            self.create_count = self.create_count+1
        
    def temp_enter(self, event=None):
      x = y = 0
      x, y, cx, cy = self.temp_Q.bbox("insert")
      x += self.temp_Q.winfo_rootx() + 25
      y += self.temp_Q.winfo_rooty() + 20
      self.temp_tw = tk.Toplevel(self.temp_Q)
      self.temp_tw.wm_overrideredirect(True)
      self.temp_tw.wm_geometry("+%d+%d" % (x, y))
      self.temp_tw.wm_attributes('-topmost', True)
      label = tk.Label(self.temp_tw, image = self.icon_temp_hint,bg = self.dark_blue_bg)
      label.grid(row = 0 ,column = 0 )

    def temp_close(self, event=None):
        if self.temp_tw:
          self.temp_tw.destroy()        

    def switch (self):
        if self.unit_switch.image == self.icon_C:
            self.unit_switch.config(image=self.icon_F)
            self.unit_switch.image = self.icon_F
            self.unit = '°F'
            out = float(self.output_degree)*1.8 + 32
            self.degree.config(text ='%.1f' % out + self.unit )
        else:
            self.unit_switch.config(image=self.icon_C)
            self.unit_switch.image = self.icon_C
            self.unit = '°C'
            self.degree.config(text ='%.1f' % self.output_degree+ self.unit )
    
    def thd_inc(self):
        thd = self.output_degree
        out = thd
        if thd < 40:
          if self.unit == '°F':
            thd = (thd + 0.1)*1.8 + 32
            out = thd
            thd = (thd-32)/1.8
          else:
            thd = thd + 0.1
            out = thd
        elif self.unit == '°F':
          out = (thd)*1.8 + 32
        thd = round(thd,1)
        self.output_degree = thd
        self.degree.config(text ='%.1f' % out + self.unit)
        self.controller.apply('thd',thd)

    def thd_dec(self):
        thd = self.output_degree
        out = thd
        if thd > 30 :
          if self.unit == '°F':        
            thd = (thd - 0.1)*1.8 + 32
            out = thd
            thd = (thd-32)/1.8
          else:
            thd = thd - 0.1
            out = thd
        elif self.unit == '°F':
          out = (thd)*1.8 + 32
        thd = round(thd,1)
        self.output_degree = thd
        self.degree.config(text ='%.1f' % out + self.unit)
        self.controller.apply('thd',thd)

    def emv_inc(self):    
        emv = self.output_emv
        if emv < 1:
          emv = emv + 0.01
        emv = round(emv,2)
        self.output_emv = emv
        self.emv_degree.config(text ='%.2f' % emv)
        self.controller.apply('emv', emv)

    def emv_dec(self):    
        emv = self.output_emv
        if emv > 0.90:
          emv = emv - 0.01    
        emv = round(emv,2)
        self.output_emv = emv
        self.emv_degree.config(text ='%.2f' % emv)
        self.controller.apply('emv', emv)

    def offset_inc(self):    
        fs = self.output_offset
        if fs < 3:
          fs = fs + 0.1
        fs = round(fs,1)
        self.output_offset = fs
        self.offset.config(text ='%.1f' % fs)
        self.controller.apply('temp', fs)

    def offset_dec(self):    
        fs = self.output_offset
        if fs > 0:
          fs = fs - 0.1
        fs = round(fs,1)
        self.output_offset = fs
        self.offset.config(text ='%.1f' % fs)
        self.controller.apply('temp', fs)

    
    def setting(self):
        self.controller.geometry('400x645')
        self.controller.title('AIBTSS Settings')
        
class PageTwo(tk.Frame):#BB REF
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        for i in range(14):
          self.grid_rowconfigure([i],minsize = 40)
        self.grid_rowconfigure(0,minsize = 65)
        self.grid_rowconfigure(14,minsize = 40)    
        self.config(bg=controller.blue_bg)
        self.cfg_count = 0
        self.create_count = 0

        row = 0
        column = 0

        left_dark_blue = tk.Label(self, image = controller.icon_db, bd =0)
        left_dark_blue.grid(row = 0, column = 0, rowspan = 100)

        line = tk.Label(self, image = controller.icon_line, bd = 0)
        line.grid(row = 0, column = 1, sticky = SW, padx = 10, pady = 20, columnspan = 3 )

        
        button1 = tk.Button(self, image = controller.icon_temp, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageOne"))
        button1.grid(row = row, column = column)
        bb_icon = tk.Label(self, image = controller.icon_bb_a, bg = controller.dark_blue_bg)
        bb_icon.grid(row = row+1, column = column, rowspan = 2)        
        button3 = tk.Button(self, image = controller.icon_head, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageThree"))
        button3.grid(row = row+3, column = column, rowspan = 2)
        button4 = tk.Button(self, image = controller.icon_mask, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFour"))
        button4.grid(row = row+5, column = column, rowspan = 2)
        button8 = tk.Button(self, image = controller.icon_fm, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageEight"))
        button8.grid(row = row+7, column = column, rowspan = 2)
        button5 = tk.Button(self, image = controller.icon_face, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFive"))
        button5.grid(row = row+9, column = column, rowspan = 2)
        button6 = tk.Button(self, image = controller.icon_colour, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSix"))
        button6.grid(row = row+11, column = column, rowspan = 2)
        button7 = tk.Button(self, image = controller.icon_record, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSeven"))
        button7.grid(row = row+13, column = column, rowspan = 2)

    def load_cfg(self):
        if self.cfg_count ==0:
            bb_high_path     = opjoin('cfg','ref_h.cfg')
            bb_low_path      = opjoin('cfg','ref_l.cfg')
            emv_path         = opjoin('cfg','bbody_emv_h.cfg')
            emv_path2         = opjoin('cfg','bbody_emv_l.cfg')

            f = open(bb_high_path, 'r')
            self.output_bb_high = f.read()
            f.close()

            f = open(bb_low_path, 'r')
            self.output_bb_low = f.read()
            f.close()

            f = open(emv_path, 'r')
            self.output_emv =  '%.2f' % eval(f.read())
            f.close()  

            f = open(emv_path2, 'r')
            self.output_emv2 =  '%.2f' % eval(f.read())
            f.close()  

            f = open(self.controller.lang_path,'r')
            lang = f.read()
            f.close()

            txt_path = opjoin('words',lang+'.txt')
            f = open(txt_path, encoding='utf8')
            word = eval(f.read())
            self.bb_txt     = word['bb_txt']
            self.high_txt   = word['high_txt']
            self.low_txt    = word['low_txt']
            self.emv_h_txt    = word['high_emv_txt']
            self.emv_l_txt    = word['low_emv_txt']
            self.font_style = word['font_style']
            btn_f = word['btn_file']
            f.close()
            
            q_18           = Image.open(opjoin('icons','18-question-icon.png'))
            plus_blue   = Image.open(opjoin('icons',"28-plus-blue.png"))    
            minus_blue  = Image.open(opjoin('icons',"28-minus-blue.png"))
            bb_hint     = Image.open(opjoin('icons',btn_f,'300Help-bb.png'))
            pick       = Image.open(opjoin('icons',btn_f,'pick.png'))
            done_long   = Image.open(opjoin('icons',btn_f,'done-long.png'))
            
            self.icon_q           = ImageTk.PhotoImage(q_18)
            self.icon_plus        = ImageTk.PhotoImage(plus_blue)
            self.icon_minus       = ImageTk.PhotoImage(minus_blue)
            self.icon_bb_hint     = ImageTk.PhotoImage(bb_hint)
            self.icon_pick        = ImageTk.PhotoImage(pick)
            self.icon_done_long   = ImageTk.PhotoImage(done_long)
            self.title_font = tkfont.Font(family=self.font_style, size=16, weight="bold")
            self.content_font = tkfont.Font(family=self.font_style, size=11)
            self.display_font = tkfont.Font(family=self.font_style, size=20)
            self.cfg_count = self.cfg_count+1

    def create_widgets(self):
        if self.create_count ==0:
            self.blue_bg      = '#3C6D9E'
            self.dark_blue_bg = '#344454'
            self.org_fg       = '#EDB529'
            self.white_fg     = '#FFFFFF'
            self.green        = '#A5C73C'

            bb_row = 0
            bb_column = 0        

            self.bb_title = tk.Label(self, text = self.bb_txt, bg=self.blue_bg, #黑體校正
                                        fg= self.green, font=(self.title_font))
            self.bb_title.grid(row = bb_row ,column =bb_column+1, sticky = NW, padx = 10, pady = 12, columnspan = 3)

            self.bb_Q = tk.Label(self, image = self.icon_q, bg = self.blue_bg)
            self.bb_Q.grid(row = bb_row, column = bb_column+3, sticky = NE, pady = 18, padx = 9)
            self.bb_Q.bind('<Enter>', self.bb_enter)
            self.bb_Q.bind('<Leave>', self.bb_close)

            self.bb_high = tk.Label(self, text = self.high_txt, bg=self.blue_bg, #高溫黑體 (30°C - 45°C):
                                        fg= self.white_fg, font=(self.content_font))
            self.bb_high.grid(row = bb_row+1 ,column =bb_column+1, sticky = W, padx = 10)

            self.bb_high_output = tk.Label(self, text = self.output_bb_high + '°C', bg=self.blue_bg, 
                                                fg= self.org_fg,font=(self.display_font))
            self.bb_high_output.grid(row = bb_row+2 ,column =bb_column+1,sticky = W,padx = 10)
            self.output_bb_high = round(eval(self.output_bb_high),1)

            self.bb_low = tk.Label(self, text = self.low_txt, bg=self.blue_bg, bd = 0,  #低溫黑體 (30°C - 45°C):
                                        fg= self.white_fg, font=(self.content_font))
            self.bb_low.grid(row = bb_row+6 ,column =bb_column+1, sticky = W, padx = 10)

            self.bb_low = tk.Label(self, text = self.output_bb_low + '°C', bg=self.blue_bg, 
                                                fg= self.org_fg,font=(self.display_font))
            self.bb_low.grid(row = bb_row+7,column =bb_column+1,sticky = W,padx = 10)
            self.output_bb_low = round(eval(self.output_bb_low),1)

            self.emv = tk.Label(self, text =self.emv_h_txt, bg=self.blue_bg, bd = 0, #放射率 (30°C-40°C):
                                            fg= self.white_fg,font=(self.content_font))
            self.emv.grid(row = bb_row+3, column = bb_column+1, sticky = W, padx = 10)  
                
            self.emv_degree = tk.Label(self, text = self.output_emv, bg=self.blue_bg, 
                                                fg= self.org_fg,font=(self.display_font))
            self.emv_degree.grid(row = bb_row+4, column = bb_column+1, 
                                            sticky = W, padx = 10)
            self.output_emv = round(eval(self.output_emv),2) 

            self.emv2 = tk.Label(self, text =self.emv_l_txt, bg=self.blue_bg, bd = 0, #放射率 (30°C-40°C):
                                            fg= self.white_fg,font=(self.content_font))
            self.emv2.grid(row = bb_row+8, column = bb_column+1, sticky = W, padx = 10)  
                
            self.emv_degree2 = tk.Label(self, text = self.output_emv2, bg=self.blue_bg, 
                                                fg= self.org_fg,font=(self.display_font))
            self.emv_degree2.grid(row = bb_row+9, column = bb_column+1, 
                                            sticky = W, padx = 10)
            self.output_emv2 = round(eval(self.output_emv2),2)        
            
            bb_high_dec_btn = tk.Button(self, image = self.icon_minus, width=28,height=28,relief=FLAT,
                                        activebackground = self.blue_bg, bd = 0, bg = self.blue_bg, command = self.bb_high_dec)
            bb_high_dec_btn.grid(row = bb_row+2 ,column =bb_column+3, sticky = W)

            bb_high_inc_btn = tk.Button(self, image = self.icon_plus, width=28,height=28,relief=FLAT,
                                        activebackground = self.blue_bg, bd = 0, bg = self.blue_bg, command = self.bb_high_inc)
            bb_high_inc_btn.grid(row = bb_row+2 ,column =bb_column+3, sticky = W, padx = 40) 

            bb_high_pick_btn = tk.Button(self, image = self.icon_pick, relief = FLAT,
                                            bd = 0, bg = self.blue_bg, command = self.bb_high_pick)
            bb_high_pick_btn.grid(row = bb_row+2, column = bb_column+3, sticky = E)


            bb_low_dec_btn = tk.Button(self, image = self.icon_minus, width=28,height=28,relief=FLAT,
                                       activebackground = self.blue_bg, bd = 0, bg = self.blue_bg, command = self.bb_low_dec)
            bb_low_dec_btn.grid(row = bb_row+7 ,column =bb_column+3, sticky = W)

            bb_low_inc_btn = tk.Button(self, image = self.icon_plus, width=28,height=28,relief=FLAT,
                                       activebackground = self.blue_bg, bd = 0, bg = self.blue_bg, command = self.bb_low_inc)
            bb_low_inc_btn.grid(row = bb_row+7 ,column =bb_column+3, sticky = W, padx = 40) 

            bb_low_pick_btn = tk.Button(self, image = self.icon_pick, relief = FLAT,
                                            bd = 0, bg = self.blue_bg, command = self.bb_low_pick)
            bb_low_pick_btn.grid(row = bb_row+7, column = bb_column+3, sticky = E)

            bb_done_btn = tk.Button(self, image = self.icon_done_long, bg = self.blue_bg, relief=FLAT, bd = 0,
                                            command = self.bb_done)
            bb_done_btn.grid(row = bb_row+10,column = bb_column+3, sticky = S)

            
            emv_dec_btn = tk.Button(self,image = self.icon_minus, width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg,     bg = self.blue_bg, command = self.emv_dec)
            emv_dec_btn.grid(row = bb_row+4, column = bb_column+3, sticky = W) #sticky = W, padx = 40

            emv_inc_btn = tk.Button(self,image = self.icon_plus,width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg,     bg = self.blue_bg, command = self.emv_inc)  ##'%.2f'
            emv_inc_btn.grid(row = bb_row+4, column = bb_column+3, sticky = W, padx = 40) #sticky = E, padx = 44

            emv_dec_btn2 = tk.Button(self,image = self.icon_minus, width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg, bg = self.blue_bg, command = self.emv_dec2)
            emv_dec_btn2.grid(row = bb_row+9, column = bb_column+3, sticky = W)

            emv_inc_btn2 = tk.Button(self,image = self.icon_plus,width=28,height=28,relief=FLAT, bd = 0,
                                    activebackground = self.blue_bg, bg = self.blue_bg, command = self.emv_inc2)  ##'%.2f'
            emv_inc_btn2.grid(row = bb_row+9, column = bb_column+3, sticky = W, padx = 40)
            self.create_count = self.create_count+1


    def bb_enter(self, event=None):
      x = y = 0
      x, y, cx, cy = self.bb_Q.bbox("insert")
      x += self.bb_Q.winfo_rootx() + 25
      y += self.bb_Q.winfo_rooty() + 20
      self.bb_tw = tk.Toplevel(self.bb_Q)
      self.bb_tw.wm_overrideredirect(True)
      self.bb_tw.wm_geometry("+%d+%d" % (x, y))
      self.bb_tw.wm_attributes('-topmost', True)
      label = tk.Label(self.bb_tw, image = self.icon_bb_hint,bg = self.dark_blue_bg)
      label.grid(row = 0 ,column = 0 )

    def bb_close(self, event=None):
        if self.bb_tw:
          self.bb_tw.destroy()

    def bb_high_inc(self):    
        high = self.output_bb_high
        if high < 45:
          high = high + 0.1    
        high = round(high,1)    
        self.output_bb_high = high
        self.bb_high_output.config(text = '%.1f' % high + '°C')    

    def bb_high_dec(self):    
        high = self.output_bb_high
        if high > 30:
          high = high - 0.1    
        high = round(high,1)    
        self.output_bb_high = high
        self.bb_high_output.config(text = '%.1f' % high + '°C')

    def bb_low_inc(self):    
        low = self.output_bb_low
        if low < 45:
          low = low + 0.1    
        low = round(low,1)
        self.output_bb_low = low
        self.bb_low.config(text = '%.1f' % low + '°C')

    def bb_low_dec(self):    
        low = self.output_bb_low
        if low > 30:
          low = low - 0.1    
        low = round(low,1)    
        self.output_bb_low = low
        self.bb_low.config(text = '%.1f' % low + '°C')

    def bb_high_pick(self):
        self.controller.apply('high',self.output_bb_high)

    def bb_low_pick(self):
        self.controller.apply('low', self.output_bb_low)
    
    def bb_done(self):
        self.controller.apply('done',0)

    def emv_inc(self):    
        emv = self.output_emv
        if emv < 1:
          emv = emv + 0.01
        emv = round(emv,2)
        self.output_emv = emv
        self.emv_degree.config(text ='%.2f' % emv)
        self.controller.apply('bbody_emv_h', emv)

    def emv_dec(self):    
        emv = self.output_emv
        if emv > 0.90:
          emv = emv - 0.01    
        emv = round(emv,2)
        self.output_emv = emv
        self.emv_degree.config(text ='%.2f' % emv)
        self.controller.apply('bbody_emv_h', emv)

    def emv_inc2(self):    
        emv = self.output_emv2
        if emv < 1:
          emv = emv + 0.01
        emv = round(emv,2)
        self.output_emv2 = emv
        self.emv_degree2.config(text ='%.2f' % emv)
        self.controller.apply('bbody_emv_l', emv)

    def emv_dec2(self):
        emv = self.output_emv2
        if emv > 0.90:
          emv = emv - 0.01
        emv = round(emv,2)
        self.output_emv2 = emv
        self.emv_degree2.config(text ='%.2f' % emv)
        self.controller.apply('bbody_emv_l', emv)

class PageThree(tk.Frame):#frame alignment
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        for i in range(14):
          self.grid_rowconfigure([i],minsize = 40)
        self.grid_rowconfigure(0,minsize = 65)
        self.grid_rowconfigure(14,minsize = 40)    
        self.config(bg=controller.blue_bg)
        self.cfg_count = 0
        self.create_count = 0

        row = 0
        column = 0

        left_dark_blue = tk.Label(self, image = controller.icon_db, bd =0)
        left_dark_blue.grid(row = 0, column = 0, rowspan = 100)

        line = tk.Label(self, image = controller.icon_line, bd = 0)
        line.grid(row = 0, column = 1, sticky = SW, padx = 10, pady = 20, columnspan = 3 )
        
        button1 = tk.Button(self, image = controller.icon_temp, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageOne"))
        button1.grid(row = row, column = column)
        button2 = tk.Button(self, image = controller.icon_bb, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageTwo"))
        button2.grid(row = row+1, column = column, rowspan = 2)
        head_icon = tk.Label(self, image = controller.icon_head_a, bg = controller.dark_blue_bg)
        head_icon.grid(row = row+3, column = column, rowspan = 2)
        button4 = tk.Button(self, image = controller.icon_mask, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFour"))
        button4.grid(row = row+5, column = column, rowspan = 2)
        button8 = tk.Button(self, image = controller.icon_fm, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageEight"))
        button8.grid(row = row+7, column = column, rowspan = 2)
        button5 = tk.Button(self, image = controller.icon_face, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFive"))
        button5.grid(row = row+9, column = column, rowspan = 2)
        button6 = tk.Button(self, image = controller.icon_colour, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSix"))
        button6.grid(row = row+11, column = column, rowspan = 2)
        button7 = tk.Button(self, image = controller.icon_record, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSeven"))
        button7.grid(row = row+13, column = column, rowspan = 2)
    
    def load_cfg(self):
        if self.cfg_count ==0:
            offset_x_path    = opjoin('cfg','detection_offset_x.cfg')
            offset_y_path    = opjoin('cfg','detection_offset_y.cfg')

            f = open(offset_x_path, 'r')
            self.output_x = eval(f.read())
            f.close()

            f = open(offset_y_path, 'r')
            self.output_y = eval(f.read())
            f.close()

            f = open(self.controller.lang_path,'r')
            lang = f.read()
            f.close()

            txt_path = opjoin('words',lang+'.txt')
            f = open(txt_path, encoding='utf8')
            word = eval(f.read())
            self.frame_txt  = word['frame_txt']
            self.x_txt      = word['x_txt']
            self.y_txt      = word['y_txt']
            self.font_style = word['font_style']
            btn_f = word['btn_file']
            f.close()

            q_18        = Image.open(opjoin('icons','18-question-icon.png'))
            hd_hint     = Image.open(opjoin('icons',btn_f,'300Help-frame.png'))
            reset       = Image.open(opjoin('icons',btn_f,"reset.png"))

            self.icon_q           = ImageTk.PhotoImage(q_18)
            self.icon_hd_hint     = ImageTk.PhotoImage(hd_hint)
            self.icon_reset       = ImageTk.PhotoImage(reset)
            self.title_font = tkfont.Font(family=self.font_style, size=16, weight="bold")
            self.content_font = tkfont.Font(family=self.font_style, size=11)
            self.display_font = tkfont.Font(family=self.font_style, size=20)        
            self.cfg_count = self.cfg_count+1

    def create_widgets(self):
        if self.create_count ==0:
            self.blue_bg      = '#3C6D9E'
            self.dark_blue_bg = '#344454'
            self.org_fg       = '#EDB529'
            self.white_fg     = '#FFFFFF'
            self.green        = '#A5C73C'
            self.blue_btn     = '#6EC1E4'        

            head_row = 0
            head_column = 0        

            head_title = tk.Label(self, text = self.frame_txt, bg = self.blue_bg, #偵測框校正
                                        fg= self.green, font=(self.title_font))
            head_title.grid(row = head_row, column = head_column+1, sticky = NW, padx = 10, pady = 12)

            self.head_Q = tk.Label(self, image = self.icon_q, bg = self.blue_bg)
            self.head_Q.grid(row = head_row, column = head_column+3, sticky = NE, padx = 9, pady =18)
            self.head_Q.bind('<Enter>', self.head_enter)
            self.head_Q.bind('<Leave>', self.head_close)

            adj_x = tk.Label(self, text = self.x_txt, bg=self.blue_bg, bd = 0,  #橫軸 (左/右):
                                    fg= self.white_fg, font=(self.content_font))
            adj_x.grid(row = head_row+1, column = head_column+1, sticky = W, padx = 10)

            self.frame_scl_x = tk.Scale(self, from_ = -40, to = 40, orient=HORIZONTAL, length = 180,relief = FLAT, bd = 0,
                                    highlightbackground =self.blue_bg,troughcolor = self.green ,bg = self.blue_bg, 
                                    width = 13, fg = self.white_fg, command = self.scl_x)
            self.frame_scl_x.grid(row = head_row+2, column = head_column+1, sticky = W, padx = 10, columnspan = 3)
            self.frame_scl_x.set(self.output_x)
            
            adj_y = tk.Label(self, text = self.y_txt, bg=self.blue_bg, bd = 0,  #緃軸(上/下):
                                    fg= self.white_fg, font=(self.content_font))
            adj_y.grid(row = head_row+4, column = head_column+1, sticky = W, padx = 10)

            self.frame_scl_y = tk.Scale(self, from_ = -40, to = 40, orient=HORIZONTAL, length = 180,relief = FLAT, bd = 0,
                                    highlightbackground =self.blue_bg,troughcolor = self.blue_btn ,bg = self.blue_bg, 
                                    width = 13, fg = self.white_fg, command = self.scl_y)
            self.frame_scl_y.grid(row = head_row+5, column = head_column+1, sticky = W, padx = 10, columnspan = 3)
            self.frame_scl_y.set(self.output_y)
            
            set_x_zero_btn = tk.Button(self, image = self.icon_reset, relief = FLAT, bg = self.blue_bg,
                                        bd = 0, command = self.set_x_zero)
            set_x_zero_btn.grid(row = head_row+2, column = head_column+3, sticky = S)

            set_y_zero_btn = tk.Button(self, image = self.icon_reset, relief = FLAT, bg = self.blue_bg,
                                        bd = 0, command = self.set_y_zero)
            set_y_zero_btn.grid(row = head_row+5, column = head_column+3, sticky = S)
            self.create_count = self.create_count+1        

    def head_enter(self, event=None):
      x = y = 0
      x, y, cx, cy = self.head_Q.bbox("insert")
      x += self.head_Q.winfo_rootx() + 25
      y += self.head_Q.winfo_rooty() + 20
      self.head_tw = tk.Toplevel(self.head_Q)      
      self.head_tw.wm_overrideredirect(True)
      self.head_tw.wm_geometry("+%d+%d" % (x, y))
      self.head_tw.wm_attributes('-topmost', True)
      label = tk.Label(self.head_tw, image = self.icon_hd_hint,bg = self.dark_blue_bg)
      label.grid(row = 0 ,column = 0 )

    def head_close(self, event=None):
        if self.head_tw:
            self.head_tw.destroy()

    def scl_x(self,val):
        self.controller.apply('offset_x',val)

    def scl_y(self,val):
        self.controller.apply('offset_y',val)
    
    def set_x_zero(self):
        self.frame_scl_x.set(0)

    def set_y_zero(self):
        self.frame_scl_y.set(0)
        
class PageFour(tk.Frame):#masking
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        for i in range(14):
          self.grid_rowconfigure([i],minsize = 40)
        self.grid_rowconfigure(0,minsize = 65)
        self.grid_rowconfigure(14,minsize = 40)    
        self.config(bg=controller.blue_bg)
        self.cfg_count = 0
        self.create_count = 0

        row = 0
        column = 0

        left_dark_blue = tk.Label(self, image = controller.icon_db, bd =0)
        left_dark_blue.grid(row = 0, column = 0, rowspan = 100)

        line = tk.Label(self, image = controller.icon_line, bd = 0)
        line.grid(row = 0, column = 1, sticky = SW, padx = 10, pady = 20, columnspan = 3 )
        
        button1 = tk.Button(self, image = controller.icon_temp, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageOne"))
        button1.grid(row = row, column = column)
        button2 = tk.Button(self, image = controller.icon_bb, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageTwo"))
        button2.grid(row = row+1, column = column, rowspan = 2)
        button3 = tk.Button(self, image = controller.icon_head, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageThree"))
        button3.grid(row = row+3, column = column, rowspan = 2)
        mask_icon = tk.Label(self, image = controller.icon_mask_a, bg = controller.dark_blue_bg)
        mask_icon.grid(row = row+5, column = column, rowspan = 2)
        button8 = tk.Button(self, image = controller.icon_fm, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageEight"))
        button8.grid(row = row+7, column = column, rowspan = 2)
        button5 = tk.Button(self, image = controller.icon_face, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFive"))
        button5.grid(row = row+9, column = column, rowspan = 2)
        button6 = tk.Button(self, image = controller.icon_colour, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSix"))
        button6.grid(row = row+11, column = column, rowspan = 2)
        button7 = tk.Button(self, image = controller.icon_record, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSeven"))
        button7.grid(row = row+13, column = column, rowspan = 2)

    def load_cfg(self):
        if self.cfg_count ==0:
            f = open(self.controller.lang_path,'r')
            lang = f.read()
            f.close()

            txt_path = opjoin('words',lang+'.txt')
            f = open(txt_path, encoding='utf8')
            word = eval(f.read())
            self.msk_txt    = word['msk_txt']
            self.sta_txt    = word['sta_txt']
            self.edit_txt   = word['edit_txt']
            self.saved_txt  = word['saved_txt']
            btn_f = word['btn_file']
            self.font_style = word['font_style']
            f.close()

            q_18        = Image.open(opjoin('icons','18-question-icon.png'))
            mk_hint     = Image.open(opjoin('icons',btn_f,'300Help-masking.png'))
            edit        = Image.open(opjoin('icons',btn_f,'edit.png'))
            done        = Image.open(opjoin('icons',btn_f,'done.png'))

            self.icon_q           = ImageTk.PhotoImage(q_18)
            self.icon_mk_hint     = ImageTk.PhotoImage(mk_hint)
            self.icon_edit        = ImageTk.PhotoImage(edit)
            self.icon_done        = ImageTk.PhotoImage(done)

            self.title_font = tkfont.Font(family=self.font_style, size=16, weight="bold")
            self.content_font = tkfont.Font(family=self.font_style, size=11)
            self.display_font = tkfont.Font(family=self.font_style, size=20)
            self.cfg_count = self.cfg_count+1

    def create_widgets(self):
        if self.create_count ==0:
            self.blue_bg      = '#3C6D9E'
            self.dark_blue_bg = '#344454'
            self.org_fg       = '#EDB529'
            self.white_fg     = '#FFFFFF'
            self.green        = '#A5C73C'        

            mask_row = 0
            mask_column = 0

            self.mask_Q = tk.Label(self, image = self.icon_q, bg = self.blue_bg)
            self.mask_Q.grid(row = mask_row, column = mask_column+3, sticky = NE, pady = 18, padx= 9)
            self.mask_Q.bind('<Enter>', self.mask_enter)
            self.mask_Q.bind('<Leave>', self.mask_close)

            mask_title = tk.Label(self, text = self.msk_txt, bg = self.blue_bg, #濾鏡設定
                                        fg= self.green, font=(self.title_font))
            mask_title.grid(row = mask_row, column = mask_column+1, sticky = NW, padx = 10, pady = 12)

            mask_stat = tk.Label(self, text =self.sta_txt, bg = self.blue_bg, 
                                        fg = self.white_fg, font = self.content_font )
            mask_stat.grid(row = mask_row+1, column = mask_column+1, sticky = W, padx = 10)

            self.mask_sign = tk.Label(self, text = '', bg=self.blue_bg, fg= self.org_fg, bd = 0,
                                            font=(self.display_font))
            self.mask_sign.grid(row = mask_row+2,column = mask_column+1,sticky = W, padx = 10)        

            mask_edit_btn = tk.Button(self,image = self.icon_edit,relief = FLAT,bg = self.blue_bg, bd = 0,
                                    command = self.mask_edit)
            mask_edit_btn.grid(row = mask_row+2 ,column = mask_column+3)

            mask_done_btn = tk.Button(self,image = self.icon_done,relief = FLAT, bg = self.blue_bg, bd = 0,
                                    command = self.mask_done)
            mask_done_btn.grid(row = mask_row+3,column = mask_column+3)
            self.create_count = self.create_count+1
    
    def mask_enter(self,event=None):
        x = y = 0
        x, y, cx, cy = self.mask_Q.bbox("insert")
        x += self.mask_Q.winfo_rootx() + 25
        y += self.mask_Q.winfo_rooty() + 20
        self.mask_tw = tk.Toplevel(self.mask_Q)
        self.mask_tw.wm_overrideredirect(True)
        self.mask_tw.wm_geometry("+%d+%d" % (x, y))
        self.mask_tw.wm_attributes('-topmost', True)
        label = tk.Label(self.mask_tw, image = self.icon_mk_hint,bg = self.dark_blue_bg)
        label.grid(row = 0 ,column = 0 )

    def mask_close(self,event=None):
        if self.mask_tw:
            self.mask_tw.destroy()

    def mask_edit(self): #編輯中
        self.mask_sign.config(text = self.edit_txt)
        self.controller.apply('mask',True)

    def mask_done(self):     #已保存
        self.mask_sign.config(text = self.saved_txt)
        self.controller.apply('mask',False)

class PageEight(tk.Frame):#facial mask
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        for i in range(14):
          self.grid_rowconfigure([i],minsize = 40)
        self.grid_rowconfigure(0,minsize = 65)   
        self.grid_rowconfigure(14,minsize = 40)       
        self.config(bg=controller.blue_bg)
        self.cfg_count = 0
        self.create_count = 0
        row = 0
        column = 0

        left_dark_blue = tk.Label(self, image = controller.icon_db, bd =0)
        left_dark_blue.grid(row = 0, column = 0, rowspan = 100)

        line = tk.Label(self, image = controller.icon_line, bd = 0)
        line.grid(row = 0, column = 1, sticky = SW, padx = 10, pady = 20, columnspan = 3 )
        
        button1 = tk.Button(self, image = controller.icon_temp, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageOne"))
        button1.grid(row = row, column = column)
        button2 = tk.Button(self, image = controller.icon_bb, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageTwo"))
        button2.grid(row = row+1, column = column, rowspan = 2)
        button3 = tk.Button(self, image = controller.icon_head, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageThree"))
        button3.grid(row = row+3, column = column, rowspan = 2)
        button4 = tk.Button(self, image = controller.icon_mask, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFour"))
        button4.grid(row = row+5, column = column, rowspan = 2)        
        fm_icon = tk.Label(self, image = controller.icon_fm_a, bg = controller.dark_blue_bg)
        fm_icon.grid(row = row+7, column = column, rowspan = 2)
        button5 = tk.Button(self, image = controller.icon_face, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFive"))
        button5.grid(row = row+9, column = column, rowspan = 2)
        button6 = tk.Button(self, image = controller.icon_colour, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSix"))
        button6.grid(row = row+11, column = column, rowspan = 2)
        button7 = tk.Button(self, image = controller.icon_record, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSeven"))
        button7.grid(row = row+13, column = column, rowspan = 2)

    def load_cfg(self):
        if self.cfg_count ==0:
            f = open(self.controller.lang_path,'r')
            lang = f.read()
            f.close()

            txt_path = opjoin('words',lang+'.txt')
            f = open(txt_path, encoding='utf8')
            word = eval(f.read())
            self.mktt_txt   = word['f_msk_txt']
            self.on_txt     = word['on_txt']
            self.off_txt    = word['off_txt'] 
            self.font_style = word['font_style']
            self.sta_txt    = word['sta_txt']
            btn_f = word['btn_file']
            f.close()
            msk_path        = opjoin('cfg','on_mask.cfg')

            f  = open(msk_path)
            self.output_msk = f.read()
            f.close()       
            if self.output_msk =='True':
                self.msk_txt = self.on_txt
            else:
                self.msk_txt = self.off_txt 

            q_18        = Image.open(opjoin('icons','18-question-icon.png'))
            f_hint      = Image.open(opjoin('icons',btn_f,'300Help-facial-mask.png'))
            on          = Image.open(opjoin('icons',btn_f,'on.png'))
            off         = Image.open(opjoin('icons',btn_f,'off.png'))

            self.icon_q         = ImageTk.PhotoImage(q_18)
            self.icon_fm_hint   = ImageTk.PhotoImage(f_hint)
            self.icon_on        = ImageTk.PhotoImage(on)
            self.icon_off       = ImageTk.PhotoImage(off)

            self.title_font = tkfont.Font(family=self.font_style, size=16, weight="bold")
            self.content_font = tkfont.Font(family=self.font_style, size=11)
            self.display_font = tkfont.Font(family=self.font_style, size=20)
            self.cfg_count = self.cfg_count+1

    def create_widgets(self):
        if self.create_count ==0:
            self.blue_bg      = '#3C6D9E'
            self.dark_blue_bg = '#344454'
            self.org_fg       = '#EDB529'
            self.white_fg     = '#FFFFFF'
            self.green        = '#A5C73C'
            
            msk_row = 0
            msk_column = 0
            
            self.msk_Q = tk.Label(self, image = self.icon_q, bg = self.blue_bg)
            self.msk_Q.grid(row = msk_row, column = msk_column+3, sticky = NE, pady = 18, padx = 9)
            self.msk_Q.bind('<Enter>', self.msk_enter)
            self.msk_Q.bind('<Leave>', self.msk_close)

            msk_title = tk.Label(self, text = self.mktt_txt, bg = self.blue_bg, 
                                        fg= self.green, font=(self.title_font))
            msk_title.grid(row = msk_row, column = msk_column+1, sticky = NW, padx = 10, pady = 12, columnspan = 3)
            
            msk_title2 = tk.Label(self, text = self.sta_txt, bg = self.blue_bg, 
                                        fg= self.white_fg, font=(self.content_font))
            msk_title2.grid(row = msk_row+1, column = msk_column+1, sticky = W, padx = 10)
            self.msk_sign = tk.Label(self, text = self.msk_txt, bg=self.blue_bg, fg= self.org_fg,
                                            font=(self.display_font))
            self.msk_sign.grid(row = msk_row+2,column = msk_column+1,sticky = W, padx = 10, columnspan = 3)
            msk_on_btn = tk.Button(self,image = self.icon_on,relief = FLAT,bg = self.blue_bg,
                                        bd = 0, command = self.msk_rgb)
            msk_on_btn.grid(row = msk_row+2 ,column = msk_column+3)    
            msk_off_btn = tk.Button(self,image = self.icon_off,relief = FLAT, bg = self.blue_bg,
                                        bd = 0,command = self.msk_mono)
            msk_off_btn.grid(row = msk_row+3,column = msk_column+3)
            self.create_count = self.create_count+1
            
    
    def msk_rgb(self):   
        self.msk_sign.config(text  = self.on_txt)
        self.controller.apply('off_mask','True')
        
    def msk_mono(self): 
        self.msk_sign.config(text  = self.off_txt)
        self.controller.apply('off_mask','False')

    def msk_enter(self,event=None):
        x = y = 0
        x, y, cx, cy = self.msk_Q.bbox("insert")
        x += self.msk_Q.winfo_rootx() + 25
        y += self.msk_Q.winfo_rooty() + 20
        self.msk_tw = tk.Toplevel(self.msk_Q)      
        self.msk_tw.wm_overrideredirect(True)
        self.msk_tw.wm_geometry("+%d+%d" % (x, y))
        self.msk_tw.wm_attributes('-topmost', True)
        label = tk.Label(self.msk_tw, image = self.icon_fm_hint,bg = self.dark_blue_bg)
        label.grid(row = 0 ,column = 0 )

    def msk_close(self, event=None):
        if self.msk_tw:
            self.msk_tw.destroy()

class PageFive(tk.Frame):#face blur
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        for i in range(14):
          self.grid_rowconfigure([i],minsize = 40)
        self.grid_rowconfigure(0,minsize = 65)
        self.grid_rowconfigure(14,minsize = 40)    
        self.config(bg=controller.blue_bg)
        self.cfg_count = 0
        self.create_count = 0

        row = 0
        column = 0

        left_dark_blue = tk.Label(self, image = controller.icon_db, bd =0)
        left_dark_blue.grid(row = 0, column = 0, rowspan = 100)

        line = tk.Label(self, image = controller.icon_line, bd = 0)
        line.grid(row = 0, column = 1, sticky = SW, padx = 10, pady = 20, columnspan = 3 )
        
        button1 = tk.Button(self, image = controller.icon_temp, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageOne"))
        button1.grid(row = row, column = column)
        button2 = tk.Button(self, image = controller.icon_bb, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageTwo"))
        button2.grid(row = row+1, column = column, rowspan = 2)
        button3 = tk.Button(self, image = controller.icon_head, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageThree"))
        button3.grid(row = row+3, column = column, rowspan = 2)
        button4 = tk.Button(self, image = controller.icon_mask, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFour"))
        button4.grid(row = row+5, column = column, rowspan = 2)
        button8 = tk.Button(self, image = controller.icon_fm, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageEight"))
        button8.grid(row = row+7, column = column, rowspan = 2)
        face_icon = tk.Label(self, image = controller.icon_face_a, bg = controller.dark_blue_bg)
        face_icon.grid(row = row+9, column = column, rowspan = 2)
        button6 = tk.Button(self, image = controller.icon_colour, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSix"))
        button6.grid(row = row+11, column = column, rowspan = 2)
        button7 = tk.Button(self, image = controller.icon_record, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSeven"))
        button7.grid(row = row+13, column = column, rowspan = 2)
        
        

    def load_cfg(self):
        if self.cfg_count ==0:
            blur_path        = opjoin('cfg','blur.cfg')
            f = open(self.controller.lang_path,'r')
            lang = f.read()
            f.close()
            f = open(blur_path,'r')
            self.output_blur = f.read()
            f.close()

            txt_path = opjoin('words',lang+'.txt')
            f = open(txt_path, encoding='utf8')
            word = eval(f.read())
            self.blur_txt   = word['blur_txt']
            self.on_txt     = word['on_txt']
            self.off_txt    = word['off_txt']
            self.stat_txt   = word['sta_txt']
            self.font_style = word['font_style']
            btn_f = word['btn_file']
            f.close()

            q_18        = Image.open(opjoin('icons','18-question-icon.png'))
            f_hint      = Image.open(opjoin('icons',btn_f,'300Help-face-blurring.png'))
            blur        = Image.open(opjoin('icons',btn_f,'on.png'))
            not_blur    = Image.open(opjoin('icons',btn_f,'off.png'))

            self.icon_q           = ImageTk.PhotoImage(q_18)
            self.icon_f_hint      = ImageTk.PhotoImage(f_hint)
            self.icon_blur        = ImageTk.PhotoImage(blur)
            self.icon_not_blur    = ImageTk.PhotoImage(not_blur)

            self.title_font = tkfont.Font(family=self.font_style, size=16, weight="bold")
            self.content_font = tkfont.Font(family=self.font_style, size=11)
            self.display_font = tkfont.Font(family=self.font_style, size=20)
            self.cfg_count = self.cfg_count+1

    def create_widgets(self):
        if self.create_count ==0:
            self.blue_bg      = '#3C6D9E'
            self.dark_blue_bg = '#344454'
            self.org_fg       = '#EDB529'
            self.white_fg     = '#FFFFFF'
            self.green        = '#A5C73C'

            face_row = 0
            face_column = 0

            if self.output_blur == 'True':
                b_txt = self.on_txt
            else:
                b_txt = self.off_txt    

            self.face_Q = tk.Label(self, image = self.icon_q, bg = self.blue_bg)
            self.face_Q.grid(row = face_row, column = face_column+3, sticky = NE, pady = 18, padx = 9)
            self.face_Q.bind('<Enter>', self.face_enter)
            self.face_Q.bind('<Leave>', self.face_close)    

            face_title = tk.Label(self, text = self.blur_txt, bg = self.blue_bg, #濾鏡設定
                                        fg= self.green, font=(self.title_font))
            face_title.grid(row = face_row, column = face_column+1, sticky = NW, padx = 10, pady = 12)

            face_stat = tk.Label(self, text = self.stat_txt, bg = self.blue_bg,
                                fg= self.white_fg, font=(self.content_font))
            face_stat.grid(row = face_row+1, column = face_column+1, sticky = W, padx = 10)

            self.face_sign = tk.Label(self, text = b_txt, bg=self.blue_bg, fg= self.org_fg,
                                            font=(self.display_font))
            self.face_sign.grid(row = face_row+2,column = face_column+1,sticky = W, padx = 10)

            face_blur_btn = tk.Button(self, image = self.icon_blur, relief = FLAT, bg = self.blue_bg, bd = 0, 
                                    command = self.blur)
            face_blur_btn.grid(row = face_row+2,column = face_column+3)

            face_not_blur_btn = tk.Button(self, image = self.icon_not_blur, relief = FLAT, bg = self.blue_bg, bd = 0, 
                                    command = self.not_blur)
            face_not_blur_btn.grid(row = face_row+3,column = face_column+3)
            self.create_count = self.create_count+1

    def blur(self):
        self.face_sign.config(text = self.on_txt)
        self.controller.apply('blur',True)

    def not_blur(self):     
        self.face_sign.config(text = self.off_txt)
        self.controller.apply('blur',False)

    def face_enter(self,event=None):
        x = y = 0
        x, y, cx, cy = self.face_Q.bbox("insert")
        x += self.face_Q.winfo_rootx() + 25
        y += self.face_Q.winfo_rooty() + 20
        self.face_tw = tk.Toplevel(self.face_Q)      
        self.face_tw.wm_overrideredirect(True)
        self.face_tw.wm_geometry("+%d+%d" % (x, y))
        self.face_tw.wm_attributes('-topmost', True)
        label = tk.Label(self.face_tw, image = self.icon_f_hint,bg = self.dark_blue_bg)
        label.grid(row = 0 ,column = 0 )

    def face_close(self, event=None):
        if self.face_tw:
            self.face_tw.destroy()

class PageSix(tk.Frame):#thermal
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        for i in range(14):
          self.grid_rowconfigure([i],minsize = 40)
        self.grid_rowconfigure(0,minsize = 65)
        self.grid_rowconfigure(14,minsize = 40)    
        self.config(bg=controller.blue_bg)
        self.cfg_count = 0
        self.create_count = 0
        row = 0
        column = 0

        left_dark_blue = tk.Label(self, image = controller.icon_db, bd =0)
        left_dark_blue.grid(row = 0, column = 0, rowspan = 100)

        line = tk.Label(self, image = controller.icon_line, bd = 0)
        line.grid(row = 0, column = 1, sticky = SW, padx = 10, pady = 20, columnspan = 3 )
        
        button1 = tk.Button(self, image = controller.icon_temp, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageOne"))
        button1.grid(row = row, column = column)
        button2 = tk.Button(self, image = controller.icon_bb, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageTwo"))
        button2.grid(row = row+1, column = column, rowspan = 2)
        button3 = tk.Button(self, image = controller.icon_head, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageThree"))
        button3.grid(row = row+3, column = column, rowspan = 2)
        button4 = tk.Button(self, image = controller.icon_mask, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFour"))
        button4.grid(row = row+5, column = column, rowspan = 2)
        button8 = tk.Button(self, image = controller.icon_fm, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageEight"))
        button8.grid(row = row+7, column = column, rowspan = 2)
        button5 = tk.Button(self, image = controller.icon_face, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFive"))
        button5.grid(row = row+9, column = column, rowspan = 2)
        colour_icon = tk.Label(self, image = controller.icon_colour_a, bg = controller.dark_blue_bg)
        colour_icon.grid(row = row+11, column = column, rowspan = 2)
        button7 = tk.Button(self, image = controller.icon_record, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSeven"))
        button7.grid(row = row+13, column = column, rowspan = 2)

    def load_cfg(self):
        if self.cfg_count ==0:
            f = open(self.controller.lang_path,'r')
            lang = f.read()
            f.close()

            txt_path = opjoin('words',lang+'.txt')
            f = open(txt_path, encoding='utf8')
            word = eval(f.read())
            self.tone_txt   = word['tone_txt']
            self.mono_txt   = word['mono_txt']
            self.rgb_txt    = word['rgb_txt'] 
            self.font_style = word['font_style']
            self.tone2_txt  = word['tone2_txt']
            btn_f = word['btn_file']
            f.close()
            clr_path         = opjoin('cfg','tone.cfg')

            f  = open(clr_path)
            self.output_clr = f.read()
            f.close()       
            if self.output_clr =='BW':
                self.clr_txt = self.mono_txt
            else:
                self.clr_txt = self.rgb_txt 

            mono        = Image.open(opjoin('icons',btn_f,'monochrome.png'))
            rgb         = Image.open(opjoin('icons',btn_f,'pseudo.png'))

            self.icon_mono        = ImageTk.PhotoImage(mono)
            self.icon_rgb         = ImageTk.PhotoImage(rgb)

            self.title_font = tkfont.Font(family=self.font_style, size=16, weight="bold")
            self.content_font = tkfont.Font(family=self.font_style, size=11)
            self.display_font = tkfont.Font(family=self.font_style, size=20)
            self.cfg_count = self.cfg_count+1

    def create_widgets(self):
        if self.create_count ==0:
            self.blue_bg      = '#3C6D9E'
            self.dark_blue_bg = '#344454'
            self.org_fg       = '#EDB529'
            self.white_fg     = '#FFFFFF'
            self.green        = '#A5C73C'
            
            colour_row = 0
            colour_column = 0
            
            
            colour_title = tk.Label(self, text = self.tone_txt, bg = self.blue_bg, #熱感影像設定
                                        fg= self.green, font=(self.title_font))
            colour_title.grid(row = colour_row, column = colour_column+1, sticky = NW, padx = 10, pady = 12)
            
            colour_title2 = tk.Label(self, text = self.tone2_txt, bg = self.blue_bg, #熱感影像設定
                                        fg= self.white_fg, font=(self.content_font))
            colour_title2.grid(row = colour_row+1, column = colour_column+1, sticky = W, padx = 10)
            self.colour_sign = tk.Label(self, text = self.clr_txt, bg=self.blue_bg, fg= self.org_fg,
                                            font=(self.display_font))
            self.colour_sign.grid(row = colour_row+2,column = colour_column+1,sticky = W, padx = 10, columnspan = 3)
            colour_rgb_btn = tk.Button(self,image = self.icon_rgb,relief = FLAT,bg = self.blue_bg,
                                        bd = 0, command = self.colour_rgb)
            colour_rgb_btn.grid(row = colour_row+2 ,column = colour_column+3)    
            colour_mono_btn = tk.Button(self,image = self.icon_mono,relief = FLAT, bg = self.blue_bg,
                                        bd = 0,command = self.colour_mono)
            colour_mono_btn.grid(row = colour_row+3,column = colour_column+3)
            self.create_count = self.create_count+1
            
    
    def colour_rgb(self):   #熱感
        self.colour_sign.config(text  = self.rgb_txt)
        self.controller.apply('JET', 0)
        
    def colour_mono(self): #黑白
        self.colour_sign.config(text  = self.mono_txt)
        self.controller.apply('BW', 0)

class PageSeven(tk.Frame):#review
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        for i in range(14):
          self.grid_rowconfigure([i],minsize = 40)
        self.grid_rowconfigure(0,minsize = 65)
        self.grid_rowconfigure(14,minsize = 40)    
        self.config(bg=controller.blue_bg)
        self.cfg_count = 0
        self.create_count = 0

        row = 0
        column = 0

        left_dark_blue = tk.Label(self, image = controller.icon_db, bd =0)
        left_dark_blue.grid(row = 0, column = 0, rowspan = 100)

        line = tk.Label(self, image = controller.icon_line, bd = 0)
        line.grid(row = 0, column = 1, sticky = SW, padx = 10, pady = 20, columnspan = 3 )
        
        button1 = tk.Button(self, image = controller.icon_temp, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageOne"))
        button1.grid(row = row, column = column)
        button2 = tk.Button(self, image = controller.icon_bb, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageTwo"))
        button2.grid(row = row+1, column = column, rowspan = 2)
        button3 = tk.Button(self, image = controller.icon_head, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageThree"))
        button3.grid(row = row+3, column = column, rowspan = 2)
        button4 = tk.Button(self, image = controller.icon_mask, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFour"))
        button4.grid(row = row+5, column = column, rowspan = 2)        
        button8 = tk.Button(self, image = controller.icon_fm, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageEight"))
        button8.grid(row = row+7, column = column, rowspan = 2)
        button5 = tk.Button(self, image = controller.icon_face, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageFive"))
        button5.grid(row = row+9, column = column, rowspan = 2)
        button6 = tk.Button(self, image = controller.icon_colour, bg = controller.dark_blue_bg, relief=FLAT, bd = 0,
                           activebackground = controller.dark_blue_bg, command=lambda: controller.show_frame("PageSix"))
        button6.grid(row = row+11, column = column, rowspan = 2)
        record_icon = tk.Label(self, image = controller.icon_record_a, bg = controller.dark_blue_bg)
        record_icon.grid(row = row+13, column = column, rowspan = 2)
        
    def load_cfg(self):
        if self.cfg_count ==0:
            self.record_path = 'record'
            f = open(self.controller.lang_path,'r')
            lang = f.read()
            f.close()

            txt_path = opjoin('words',lang+'.txt')
            f = open(txt_path, encoding='utf8')
            word = eval(f.read())
            self.record_txt = word['record_txt']
            self.font_style = word['font_style']
            btn_f = word['btn_file']
            f.close()

            review      = Image.open(opjoin('icons',btn_f,'review.png'))
            self.icon_open        = ImageTk.PhotoImage(review)

            self.title_font = tkfont.Font(family=self.font_style, size=16, weight="bold")
            self.content_font = tkfont.Font(family=self.font_style, size=11)
            self.display_font = tkfont.Font(family=self.font_style, size=20)
            self.cfg_count = self.cfg_count+1

    def create_widgets(self):
        if self.create_count ==0:
            self.blue_bg      = '#3C6D9E'
            self.green        = '#A5C73C'

            record_row = 0
            record_column = 0

            record_title = tk.Label(self, text = self.record_txt, bg = self.blue_bg,     #記錄
                                        fg= self.green, font=(self.title_font))
            record_title.grid(row = record_row, column = record_column+1, sticky = NW, padx = 10, pady = 12)

            record_open_btn = tk.Button(self, image = self.icon_open, bg = self.blue_bg, relief = FLAT,
                                        bd = 0, command = self.record_open)
            record_open_btn.grid(row = record_row+1, column = record_column+1, sticky = W, padx = 10)
            self.create_count = self.create_count+1
        
    def record_open(self):
        if os.path.isdir(self.record_path):
            os.startfile(self.record_path)
        else:
            os.mkdir(self.record_path)
            os.startfile(self.record_path)    
    


def func1(msg_q):
    app = SampleApp(msg_q)
    app.mainloop()

if __name__ == "__main__":
    import queue
    msg_q = queue.Queue(5)    
    func1(msg_q)