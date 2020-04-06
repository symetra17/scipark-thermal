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
            remove_oldest(10)
        cleanup_by_date(14)
        generate_video()
        sleep(30)

def remove_oldest_video(nfile):
    print('Removing old video records')
    cwd = os.getcwd()
    files = glob(os.path.join(cwd, 'record','*.mp4'))
    files.sort(key=os.path.getmtime)
    print('Number of files', len(files))
    print(files[0])
    for n in range(nfile):
        if len(files) > n:
            os.remove(files[n])

def cleanup_by_date(day):
    cwd = os.getcwd()
    files = glob(os.path.join(cwd, 'record','*.mp4'))
    for f in files:
        tf = os.path.getmtime(f)
        if (time() - tf)/(60*60*24) > day:
            print('Removing ', f)
            os.remove(f)
            sleep(0.05)

def generate_video():
  cwd = os.getcwd()
  files = glob(os.path.join(cwd, 'record', '*.jpg'))
  files.sort(key=os.path.getmtime)
  MAX_LEN = 2000
  for loop in range(5):
    if len(files) > MAX_LEN:
        batch = files[0:MAX_LEN]
        del files[0:MAX_LEN]
    else:
        break
    fn = os.path.split(batch[0])[-1]
    month = int(fn[2:4])
    day = int(fn[4:6])
    hour = int(fn[7:9])
    min = int(fn[9:11])
    sec = int(fn[11:13])
    if len(batch) > 0:
        fid = open('jpglist.txt','w')
        for f in batch:
            fid.write('file '+ "'" + f + "'" + '\n')
            fid.write("duration 0.1\n")
        fid.close()
        cm = 'ffmpeg -f concat -safe 0 -i jpglist.txt -y -c:v h264_nvenc -preset slow -qp 18 -pix_fmt yuv420p '
        cm += 'record\\record_20%02d%02d-%02d%02d%02d.mp4'%(month,day,hour,min,sec)
        x = os.system(cm)
        for f in batch:
            os.remove(f)

if __name__=='__main__':
    generate_video()
