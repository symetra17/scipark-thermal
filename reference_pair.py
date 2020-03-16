from scipy import interpolate
import cv2

class reference_pair(object):

    def __init__(self):
        self.x_l = 10
        self.y_l = 10
        self.temp_l = 35.0     # in degree
        self.raw_l = 0        # in sensor output scale, 0-65535
        self.x_h = 40
        self.y_h = 10
        self.temp_h = 42.0    # in degree
        self.raw_h = 0       # in sensor output scale, 0-65535
        self.pick_l = False
        self.pick_h = False
        try:
            fid=open('x_l.cfg','r')
            self.x_l = int(fid.read())
            fid.close()
            fid=open('y_l.cfg','r')
            self.y_l = int(fid.read())
            fid.close()
        except:
            self.save_l()

        try:
            fid=open('x_h.cfg','r')
            self.x_h = int(fid.read())
            fid.close()
            fid=open('y_h.cfg','r')
            self.y_h = int(fid.read())
            fid.close()
        except:
            self.save_h()

    def click(self,x,y):
        if self.pick_l:
            self.x_l = x
            self.y_l = y
            self.pick_l = False
            self.save_l()
        elif self.pick_h:
            self.x_h = x
            self.y_h = y
            self.pick_h = False
            self.save_h()

    def save_l(self):
        fid=open('x_l.cfg','w')
        fid.write('%d'%self.x_l)
        fid.close()
        fid=open('y_l.cfg','w')
        fid.write('%d'%self.y_l)
        fid.close()

    def save_h(self):
        fid=open('x_h.cfg','w')
        fid.write('%d'%self.x_h)
        fid.close()
        fid=open('y_h.cfg','w')
        fid.write('%d'%self.y_h)
        fid.close()

    def update(self, img):
        val = img[self.y_l-1:self.y_l+2, self.x_l-1:self.x_l+2].mean()  # get mean value of 9 pixels
        self.raw_l = 0.8 * self.raw_l + 0.2 * val
        val = img[self.y_h-1:self.y_h+2, self.x_h-1:self.x_h+2].mean()
        self.raw_h = 0.8 * self.raw_h + 0.2 * val

    def interp_temp(self, inp_raw):
        f = interpolate.interp1d([self.low_raw, self.high_raw], [temp_l, temp_h], 
                        fill_value='extrapolate')
        return f(inp_raw)

        #emissitivity_different

    def draw(self, im_8):
        if self.pick_l:
            color = (120,120,120)
        else:
            color = (255, 255, 28)

        cv2.rectangle(im_8, (self.x_l-5, self.y_l-5), (self.x_l+5, self.y_l+5),
                color, 2)

        if self.pick_h:
            color = (120,120,120)
        else:
            color = (255, 0, 248)

        cv2.rectangle(im_8, (self.x_h-5, self.y_h-5), (self.x_h+5, self.y_h+5),
                color, 2)
