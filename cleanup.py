import psutil
from time import sleep, time
import os
import os.path
from glob import glob

def cleanup(arg):
    while True:
        hdd = psutil.disk_usage('/')
        space_mb = hdd.free//(1024*1024)
        if space_mb < 2000:
            print('Removing old image records')
            cwd = os.getcwd()
            files = glob(os.path.join(cwd, 'record','*.*'))
            files.sort(key=os.path.getmtime)
            print('Number of files', len(files))
            print(files[0])
            for n in range(10000):
                if len(files) > n:
                    os.remove(files[n])
        sleep(60*3)

def cleanup_by_date(arg):
    while True:
        #sleep(60*60)
        sleep(1)
        cwd = os.getcwd()
        files = glob(os.path.join(cwd, 'record','*.*'))
        for f in files:
            tf = os.path.getmtime(f)
            if (time() - tf)/(60*60*24) > 14:
                print('Removing ', f)
                os.remove(f)
                sleep(0.05)

if __name__=='__main__':
    cleanup_by_date(None)