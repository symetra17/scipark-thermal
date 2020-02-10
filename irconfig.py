import os
import sqlite3

# replacing dictionary format config because dictionary is TOXIC


class Irconfig:           

    def __init__(self):
        self.camwidth = None
        self.camheight = None
        self.camsegment = None
        self.cambrand = None
        self.ipaddr = None
        self.port = None
        self.username = None
        self.password = None
        self.fovh = None
        self.fovv = None
        self.nucperiod = None
        self.thresholdinfo = None
        self.distanceinfo = None
        self.dataPath = None
        
    def read_db(self, path):
        conn = sqlite3.connect(path)
        c = conn.cursor()
        cfg_dict = {}
        try:
            c.execute('''SELECT value FROM MAIN WHERE NAME = "datapath"''')
            data_path = c.fetchone()
            self.dataPath = os.path.normpath(data_path[0].strip(' \n\t\r').encode('utf-8'))
        except Exception as e:
            print e.message

        try:
            c.execute(''' SELECT name, value FROM INFRARED''')
            for row in c:
                cfg_dict.update({row[0]: row[1].strip(' \n\t\r')})
            conn.close()
        except Exception as e:
            print e.message

        self.camwidth = int(cfg_dict['ircamwidth'])
        self.camheight = int(cfg_dict['ircamheight'])
        self.camsegment = int(cfg_dict['ircamsegment'])
        self.cambrand = cfg_dict['ircambrand']
        self.ipaddr = str(cfg_dict['ircamaddr'])
        self.port = str(cfg_dict['ircamport'])
        self.username = str(cfg_dict['ircamusername'])
        self.password = str(cfg_dict['ircampassword'])
        self.fovh = float(cfg_dict['irfovh'])
        self.fovv = float(cfg_dict['irfovv'])
        self.nucperiod = int(cfg_dict['ircamnucperiod'])
        self.thresholdinfo = cfg_dict['ircamthresholdinfo']
        self.distanceinfo = cfg_dict['ircamdistanceinfo']
