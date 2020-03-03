fid=open('shit.bin','wb')
for n in range(65536):
    fid.write(bytes(0))
    fid.write(bytes(0))
    fid.write(bytes(0))
    fid.write(bytes(0))
fid.close()
