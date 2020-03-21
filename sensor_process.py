import pyftdi.serialext

def sensor_proc(sensor_q):
    while True:
        try:
            print("Establishing USB connection")
            blackbody = pyftdi.serialext.serial_for_url('ftdi://ftdi:4232h/0', baudrate=57600)
            data = bytes()
            while True:
                try:
                    data += blackbody.read(1)
                    if data[-1] == ord('\n'):       #'L032.63H032.63\x1f\r\n'
                        temp_l = float(data[1:7])+0.3
                        temp_h = float(data[8:14])
                        cs = 0
                        for n in range(14):
                            cs += int(data[n])
                        cs = cs%256
                        if data[14] == cs:
                            if not sensor_q.full():
                                sensor_q.put((temp_l, temp_h))
                        else:
                            print('CS INVALID')
                        data = bytes()
                except Exception as e:
                    print(e)
                    data = bytes()
        except Exception as e:
            print(e)
            time.sleep(30)
