import mmap
import time
import numpy as np
import cv2

fid = open("hello.txt", "r+")

map = mmap.mmap(fid.fileno(), 0)
size = 1280*720*3
while True:
    npa = np.frombuffer(map[0:size], dtype=np.uint8)
    npa = npa.reshape((720,1280,3))
    npa = cv2.resize(npa, (720,480), interpolation=cv2.INTER_NEAREST)
    cv2.imshow('', npa)
    cv2.waitKey(50)
map.close()
