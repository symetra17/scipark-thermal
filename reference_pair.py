from scipy import interpolate
import cv2


class ref_point(object):
    def __init__(self):
        self.x = 0.1
        self.y = 0.1
        self.raw = 10000
        self.c = 21.0
        self.show = False
        self.name = 'refpoint'
        self.picking = False

class reference_pair(object):

    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.x_l = 0.1         # x position, unit in ratio
        self.y_l = 0.1         # y position, unit in ratio
        self.temp_l = 36     # in degree
        self.raw_l = 0         # in sensor output scale, 0-65535
        self.x_h = 0.2
        self.y_h = 0.1
        self.temp_h = 40.0     # in degree
        self.raw_h = 0         # in sensor output scale, 0-65535
        self.pick_l = False
        self.pick_h = False
        self.temp_offset = 0.0   # offset between taped human head and humnan head        
        self.head = ref_point()
        self.head_tape = ref_point()

        try:
            fid=open('x_l.cfg','r')
            self.x_l = float(fid.read())
            fid.close()
            fid=open('y_l.cfg','r')
            self.y_l = float(fid.read())
            fid.close()
        except:
            self.save_l()

        try:
            fid=open('x_h.cfg','r')
            self.x_h = float(fid.read())
            fid.close()
            fid=open('y_h.cfg','r')
            self.y_h = float(fid.read())
            fid.close()
        except:
            self.save_h()

    def pick_head(self):
        self.head.picking = True

    def pick_head_cancel(self):
        self.head.picking = False

    def pick_head_tape(self):
        self.head_tape.picking = True

    def pick_head_tape_cancel(self):
        self.head_tape.picking = False

    def click(self, inp):
        if self.pick_l:
            self.x_l = inp['x ratio']
            self.y_l = inp['y ratio']
            self.pick_l = False
            self.save_l()
        elif self.pick_h:
            self.x_h = inp['x ratio']
            self.y_h = inp['y ratio']
            self.pick_h = False
            self.save_h()
        elif self.head.picking:
            self.head.x = inp['x ratio']
            self.head.y = inp['y ratio']
            self.head.picking = False
            self.head.show = True
        elif self.head_tape.picking:
            self.head_tape.x = inp['x ratio']
            self.head_tape.y = inp['y ratio']
            self.head_tape.picking = False
            self.head_tape.show = True

    def save_l(self):
        fid=open('x_l.cfg','w')
        fid.write('%.3f'%self.x_l)
        fid.close()
        fid=open('y_l.cfg','w')
        fid.write('%.3f'%self.y_l)
        fid.close()

    def save_h(self):
        fid=open('x_h.cfg','w')
        fid.write('%.3f'%self.x_h)
        fid.close()
        fid=open('y_h.cfg','w')
        fid.write('%.3f'%self.y_h)
        fid.close()

    def update(self, img):
        h = img.shape[0]
        w = img.shape[1]

        ycoor = int(self.y_l * h)
        xcoor = int(self.x_l * w)
        val = img[ycoor-1:ycoor+2, xcoor-1:xcoor+2].mean()  # get mean value of 9 pixels
        self.raw_l = 0.8 * self.raw_l + 0.2 * val

        ycoor = int(self.y_h * h)
        xcoor = int(self.x_h * w)
        val = img[ycoor-1:ycoor+2, xcoor-1:xcoor+2].mean()
        self.raw_h = 0.8 * self.raw_h + 0.2 * val
        
        ycoor = int(self.head.y * h)
        xcoor = int(self.head.x * w)
        val = img[ycoor-1:ycoor+2, xcoor-1:xcoor+2].mean()
        self.head.c = self.interp_temp(val)

        ycoor = int(self.head_tape.y * h)
        xcoor = int(self.head_tape.x * w)
        val = img[ycoor-1:ycoor+2, xcoor-1:xcoor+2].mean()
        self.head_tape.c = self.interp_temp(val)

    def interp_temp(self, inp_raw):
        if self.raw_l == self.raw_h:
            raw_h = self.raw_h + 1
        else:
            raw_h = self.raw_h
        raw_l = self.raw_l
        f = interpolate.interp1d([raw_l, raw_h], [self.temp_l, self.temp_h], 
                        fill_value='extrapolate')
        #print 'ref val', 'low', raw_l, 'hi', raw_h, 'low', '%.1f'%self.temp_l, 'hi', '%.1f'%self.temp_h
        return f(inp_raw)

        #emissitivity_different

    def temp2raw(self, inp):
        if self.raw_l == self.raw_h:
            raw_h = self.raw_h + 1
        else:
            raw_h = self.raw_h
        raw_l = self.raw_l
        f = interpolate.interp1d([self.temp_l, self.temp_h], [raw_l, raw_h],
                        fill_value='extrapolate')
        return f(inp)

    def draw(self, im_8):
        s = 5     # rectangle size = s*2
        w = im_8.shape[1]
        h = im_8.shape[0]
        if self.pick_l:
            color = (120,120,120)
        else:
            color = (255, 255, 0)
        ycoor = int(self.y_l * h)
        xcoor = int(self.x_l * w)
        cv2.rectangle(im_8, (xcoor-s, ycoor-s), (xcoor+s, ycoor+s), color, 2)

        if self.pick_h:
            color = (120,120,120)
        else:
            color = (255, 0, 248)
        ycoor = int(self.y_h * h)
        xcoor = int(self.x_h * w)
        cv2.rectangle(im_8, (xcoor-s, ycoor-s), (xcoor+s, ycoor+s), color, 2)
        cv2.putText(im_8, 'BLK BODY REF LO %.2f  HI %.2f'%(self.temp_l, self.temp_h),
                (15, 55), self.font, 0.5, (255,255,255), 1, cv2.LINE_AA)

        cv2.putText(im_8, 'HEAD %.2fc'%self.head.c,
                (15, 75), self.font, 0.5, (255,255,255), 1, cv2.LINE_AA)

        cv2.putText(im_8, 'TAPE %.2fc'%self.head_tape.c,
                (15, 95), self.font, 0.5, (255,255,255), 1, cv2.LINE_AA)

        if self.head.show:
            ycoor = int(self.head.y * h)
            xcoor = int(self.head.x * w)
            color = (30, 255, 255)
            cv2.rectangle(im_8, (xcoor-s, ycoor-s), (xcoor+s, ycoor+s), color, 2)
            #print xcoor, ycoor

        if self.head_tape.show:
            ycoor = int(self.head_tape.y * h)
            xcoor = int(self.head_tape.x * w)
            color = (255, 255, 255)
            cv2.rectangle(im_8, (xcoor-s, ycoor-s), (xcoor+s, ycoor+s), color, 2)

    def sensor_feed(self, inp):
        self.temp_l = inp[0]
        self.temp_h = inp[1]
