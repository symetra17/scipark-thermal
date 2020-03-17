from scipy import interpolate
import cv2

class reference_pair(object):

    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.x_l = 0.1         # x position, unit in ratio
        self.y_l = 0.1         # y position, unit in ratio
        self.temp_l = 35.0     # in degree
        self.raw_l = 0         # in sensor output scale, 0-65535
        self.x_h = 0.2
        self.y_h = 0.1
        self.temp_h = 42.0     # in degree
        self.raw_h = 0         # in sensor output scale, 0-65535
        self.pick_l = False
        self.pick_h = False
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

    def click(self,inp):
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

    def save_l(self):
        fid=open('x_l.cfg','w')
        fid.write('%.2f'%self.x_l)
        fid.close()
        fid=open('y_l.cfg','w')
        fid.write('%.2f'%self.y_l)
        fid.close()

    def save_h(self):
        fid=open('x_h.cfg','w')
        fid.write('%.2f'%self.x_h)
        fid.close()
        fid=open('y_h.cfg','w')
        fid.write('%.2f'%self.y_h)
        fid.close()

    def update(self, img):
        ycoor = int(self.y_l * img.shape[0])
        xcoor = int(self.x_l * img.shape[1])
        
        val = img[ycoor-1:ycoor+2, xcoor-1:xcoor+2].mean()  # get mean value of 9 pixels
        self.raw_l = 0.8 * self.raw_l + 0.2 * val

        

        ycoor = int(self.y_h * img.shape[0])
        xcoor = int(self.x_h * img.shape[1])
        val = img[ycoor-1:ycoor+2, xcoor-1:xcoor+2].mean()
        self.raw_h = 0.8 * self.raw_h + 0.2 * val
        
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

    def draw(self, im_8):
        s = 5     # rectangle size = s*2
        w = im_8.shape[1]
        h = im_8.shape[0]
        if self.pick_l:
            color = (120,120,120)
        else:
            color = (255, 255, 28)
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
        cv2.putText(im_8, 'BLACKBODY REF',
                (15, 55), self.font, 0.5, (255,255,255), 1, cv2.LINE_AA)
