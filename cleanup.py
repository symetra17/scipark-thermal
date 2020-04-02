import psutil
import time
import os
import os.path
import glob

def cleanup(arg):
    while True:
        hdd = psutil.disk_usage('/')
        space_mb = hdd.free//(1024*1024)
        if space_mb < 1000:
            print('Removing old image records')
            cwd = os.getcwd()
            files = glob.glob(os.path.join(cwd, 'record','*.*'))
            files.sort(key=os.path.getmtime)
            print(len(files))
            print(files[0])
            for n in range(10000):
                if len(files) > n:
                    os.remove(files[n])
        time.sleep(60*3)
