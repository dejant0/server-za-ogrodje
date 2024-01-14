import serial
import struct
import time
import redis

# Packet format
r = redis.Redis()

packet_format = '4h'  # 4 int16_t values
packet_size = struct.calcsize(packet_format)

def read_data(ser):

    #ser = serial.Serial('COM5', 115200)

    while ser.in_waiting >= packet_size:
        packet = ser.read(packet_size)
        data = struct.unpack(packet_format, packet)
        if data[2]>=3500 and data[3]<3500:
            print("levo")
            r.set("leftHand", 1)
            r.set("rightHand", 0)

            #return("levo")
        elif data[2]<3500 and data[3]>=3500:
            print("desno")
            r.set("leftHand", 0)
            r.set("rightHand", 1)
            #return("desno")
        elif data[2]>=3500 and data[3]>=3500:
            print("oba")
            r.set("leftHand", 1)
            r.set("rightHand", 1)
            #return("oba")
        elif data[2]<3500 and data[3]<3500:
            r.set("leftHand", 0)
            r.set("rightHand", 0)
            print("false")
            #return("false")
def main():
    ser = serial.Serial('COM5', 115200)

    try:
        while True:
            read_data(ser)
            time.sleep(0.1)  # Small delay
    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
