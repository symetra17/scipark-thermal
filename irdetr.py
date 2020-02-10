#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import cv2
import mask
import geoinfomap2
from base64conv import *
import sqlite3
from postype import *
import traceback
import evnrec
import uuid
import sys
import os


class Irdetector:

    def __init__(self, frame_size, segment, thres_info, distance_info, fov, cfg_path, geoinfo_path):
        """
        :type frame_size: size2i
        :type segment: size2i
        :type thres_info: numpy.ndarray
        :type distance_info: numpy.ndarray
        :type fov: angle2f
        """
        self.cfg_path = cfg_path
        cfg = self.load_config(cfg_path)
        self.sensitivity = float(cfg['sensitivity'])

        self.fov = fov
        self.hseg = segment.x
        self.vseg = segment.y

        width = frame_size.x
        height = frame_size.y

        # mask hasn't support independent segx and segy
        self.mask = mask.ImageMask(segment.x, "irmask", fov.va, fov.ha, width, height, cfg_path)

        self.geoinfo = geoinfomap2.Geoinfomap(fov.ha, fov.va)
        self.geoinfo.setDistThd(distance_info, thres_info)
        
        self.origin_geoinfomap = geoinfomap2.Geoinfomap(fov.ha, fov.va)
        self.origin_geoinfomap.setDistThd(distance_info, thres_info)
        
        try:
            path = os.path.join(geoinfo_path, 'ir')
            self.geoinfo.loadDistFile(path)
            self.geoinfo.generateThdMap()
        except:
            traceback.print_exc()
            
        try:
            path = os.path.join(geoinfo_path, 'originir')
            self.origin_geoinfomap.loadDistFile(path)
            self.origin_geoinfomap.generateThdMap()
        except:
            traceback.print_exc()

        self.width = width
        self.height = height
        self.evn_rec = evnrec.EventRecords()

    @staticmethod
    def load_config(cfg_path):
        """
        :rtype:dict
        """        
        if not os.path.exists(cfg_path):
            print 'Error: db file not found'
            quit()
        conn = sqlite3.connect(cfg_path)
        cfg = {}
        c = conn.cursor()
        for row in c.execute('SELECT NAME,VALUE FROM infrared'):
            cfg.update({row[0]: row[1].strip(' \n\t\r')})
        conn.close()
        return cfg

    def save_sensitivity(self):
        # save sensitivity to config database
        try:
            conn = sqlite3.connect(self.cfg_path)
            c = conn.cursor()
            sqlcmd = "update infrared set value = %.2f where name = '%s'" % (self.sensitivity, 'sensitivity')
            c.execute(sqlcmd)
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    def split_result(self, cell_map, center, w, h):
        """
        :type cell_map: numpy.ndarray
        :type center: angle2f
        :type w: int
        :type h: int
        :rtype: list
        """
        
        # split detected objects into multiple of events
        map8 = cell_map.astype(np.uint8)
        
        # append 1 pixel outline around the map because findContour function doesn't detect edges
        vseg = map8.shape[0]
        hseg = map8.shape[1]
        
        lat_map, lon_map, alt_map = self.geoinfo.getLatLonAlt(center, hseg, vseg)
        dist_map = self.geoinfo.getDistanceByAngle(center, hseg, vseg)
                
        map8_wborder = np.zeros((vseg + 2, hseg + 2), dtype=np.uint8)
        map8_wborder[1:vseg+1, 1:hseg+1] = map8

        contr, dummy = cv2.findContours(
                           map8_wborder, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        for obj in contr:
            for pt in obj:
                pt[0] = pt[0] - (1, 1)
        
        results = []
        for obj in contr:
            rs_map = np.zeros_like(cell_map, dtype=np.uint8)
            # fill up contour because cv2.find contour returns outline only, 
            # it looks better in UI to fill it up
            cv2.fillPoly(rs_map, pts=[obj], color=(1))
            n_cell = cv2.countNonZero(rs_map)
            rs_map = rs_map.astype(dtype=np.bool)

            rep_pt = pos2i(obj[0][0][0], obj[0][0][1])    # get first point as representative
            
            dis_val = dist_map[rep_pt.y, rep_pt.x]
            alt_val = alt_map[rep_pt.y, rep_pt.x]
            lat_val = lat_map[rep_pt.y, rep_pt.x]
            lon_val = lon_map[rep_pt.y, rep_pt.x]
            
            if dis_val > 20.0:
                dist_sl = self.geoinfo.getDistanceSkyline(center, hseg)
                lat_sl, lon_sl, alt_sl = self.geoinfo.getLatLonAltSkyline(center, hseg)
                dis_val = dist_sl[0, rep_pt.x]
                lat_val = lat_sl[0, rep_pt.x]
                lon_val = lon_sl[0, rep_pt.x]
                alt_val = alt_sl[0, rep_pt.x]
            
            hangle = center.ha + (self.fov.ha * (float(rep_pt.x) - float(hseg)/2.0)/hseg)
            vangle = center.va - (self.fov.va * (float(rep_pt.y) - float(vseg)/2.0)/vseg)
            dist_meter = dis_val * 1000.0
            area = float(dist_meter * self.fov.ha/hseg * self.fov.va/vseg * n_cell)
            
            dict1 = {
                'type'    : 'irevent',
                'eid'     : str(uuid.uuid4()),
                'width'   : str(w), 
                'height'  : str(h),
                'hseg'    : str(hseg), 
                'vseg'    : str(vseg),
                'map'     : rs_map,
                'dismiss' : False,
                'lat'     : '%.7f' % lat_val, 
                'lon'     : '%.7f' % lon_val, 
                'alt'     : '%d' % alt_val,
                'distance': '%.3f' % dis_val,
                'firearea': '%.1f' % area,
                'hangle'  : '%.3f' % hangle, 
                'vangle'  : '%.3f' % vangle}
            results.append(dict1)
        
        return results

    def detect(self, center, hvidx, rawdata, detection_en=True):
        """
        :type center: angle2f
        :type hvidx: pos2i
        :type rawdata: numpy.ndarray
        :type detection_en: bool
        :rtype: list[dict], float, float
        """
        
        if not detection_en:
            return False, []
            
        if rawdata.dtype != np.uint16 and rawdata.dtype != np.uint32:
            print 'rawdata.dtype', rawdata.dtype
            raise Exception("input raw data is not in uint16 or uint32 type")

        h_raw = rawdata.shape[0]
        w_raw = rawdata.shape[1]

        if w_raw != self.width or h_raw != self.height:
            raise Exception('raw data shape not match with configuration')

        thd = self.geoinfo.getThresholdByAngle(center, w_raw, h_raw)/self.sensitivity
        thd = thd.astype(np.uint16)

        min_thd = float(np.amin(thd))
        max_thd = float(np.amax(thd))

        mask8 = self.mask.getMaskMapByAngle(center)
        mask8 = np.logical_not(mask8)
        mask16 = mask8.astype(np.uint16)
        mask16 = cv2.resize(mask16, (w_raw, h_raw), interpolation=cv2.INTER_NEAREST)
        rawdata = np.multiply(rawdata, mask16)

        if rawdata.shape != thd.shape:
            msg = 'Error: raw data and thd shape not matched'
            print msg
            raise Exception('Error: raw data and thd shape not matched')

        bool_result = False        
        outmap = np.zeros((self.vseg, self.hseg), dtype=np.bool)
        hmul = w_raw/self.hseg    # 4
        vmul = h_raw/self.vseg
        for x in range(w_raw):
            for y in range(h_raw):
                if rawdata[y, x] > thd[y, x]:
                    outmap[y/vmul, x/hmul] = True
                    bool_result = True
        
        objects = self.split_result(outmap, center, w_raw, h_raw)

        for n in reverse_index(objects):
            cord = (objects[n]['lat'], objects[n]['lon'], objects[n]['alt'])
            hvangle = (objects[n]['hangle'], objects[n]['vangle'])
            np_map = objects[n]['map']
            eid = objects[n]['eid']
            #center_ang = objects[n]['centerangle']
            fevn = evnrec.FireEvent(hvidx, cord, hvangle, np_map, eid)
            if self.evn_rec.exiting(fevn):
                self.evn_rec.mark_keep(fevn)
                del objects[n]            # not a new event
            else:
                self.evn_rec.add(fevn)    # a new event
        dism_list = self.evn_rec.pop_discarding_eids(hvidx)

        for item in dism_list:
            """
            :type item: evnrec.FireEvent
            """
            objects.append(dict({'eid': item.eid, 'dismiss': True, 'type': 'irevent',
                                 'lat': item.cord[0], 'lon': item.cord[1], 'alt': item.cord[2],
                                 'hangle': item.hvangle[0], 'vangle': item.hvangle[1]}))
        
        for n in range(len(objects)):
            if 'map' in objects[n]:
                objects[n]['eventpoints'] = numpy2str(objects[n]['map'])
                objects[n].pop('map')

        # min_thd, max_thd are for field test only, these would not be shown in IG
        return objects, min_thd, max_thd

    def getDistanceByAngle(self, center, seg=size2i(384, 288)):
        """
        :type center: angle2f
        :type seg: size2i
        :rtype: numpy.ndarray
        """
        return self.geoinfo.getDistanceByAngle(center, seg.x, seg.y)
    
    def setDistanceByAngle(self, center, smallmap):
        """
        :type center: angle2f
        :type smallmap: numpy.ndarray
        :rtype:None
        """
        self.geoinfo.setDistanceByAngle(center, smallmap)
        self.geoinfo.generateThdMap()

    def getOriginDistByAgl(self, center, seg=size2i(384, 288)):
        """
        :type center:angle2f
        :type seg:size2i
        :rtype:numpy.ndarray
        """
        return self.origin_geoinfomap.getDistanceByAngle(center, seg.x, seg.y)
    
    def modifyMask(self, cmd):
        """
        :type cmd:dict
        :rtype:dict
        """
        return self.mask.UIMaskEvent(cmd)

    def get_dist_lat_lon_alt(self, center):      # with clipping to skyline
        """
        :type center: angle2f
        :rtype: (float, float, float, int)
        """
        dist_map = self.geoinfo.getDistanceByAngle(center, self.hseg, self.vseg)
        dist = float(dist_map[self.vseg/2, self.hseg/2])
        lat_map, lon_map, alt_map = self.geoinfo.getLatLonAlt(center, self.hseg, self.vseg)
        lat = float(lat_map[self.vseg/2, self.hseg/2])
        lon = float(lon_map[self.vseg/2, self.hseg/2])
        alt = int(alt_map[self.vseg/2, self.hseg/2])
        
        if dist > 20.0:
            dist_sl = self.geoinfo.getDistanceSkyline(center, self.hseg)
            lat_sl, lon_sl, alt_sl = self.geoinfo.getLatLonAltSkyline(center, self.hseg)
            dist = float(dist_sl[0, self.hseg/2])
            lat = float(lat_sl[0, self.hseg/2])
            lon = float(lon_sl[0, self.hseg/2])
            alt = int(alt_sl[0, self.hseg/2])
        
        return dist, lat, lon, alt
        
    def set_sensitivity(self, sens):
        # sens should be close to 1.0
        """
        :type sens: float
        """
        self.sensitivity = sens
        self.save_sensitivity()


def reverse_index(in_list):
    return range(len(in_list)-1, -1, -1)

