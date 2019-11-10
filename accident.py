import bluetooth
import time
#import bluetooth
import os
#calling for header file which helps in using GPIOs of PI
import picamera, subprocess, os, sys
import threading
MOTOR=21
import datetime
import RPi.GPIO as GPIO

import pyrebase
import signal
import serial
     
 
from random import randrange



def record_audio(dt,s):
    dt1 = "/home/pi/Desktop/" + dt + ".wav"
    # plughw: card 1 device 0 plughw:1,0
    a1 = "arecord -d 5 -D plughw:1,0 " + dt1
    subprocess.call(a1,shell= True)
    s.child(dt+".wav").put(dt1)
    #print("hello")
    exit()
    
def record_video(dt,s):
    dt1 = "/home/pi/Desktop/" + dt 
    a1 = "raspivid -t 5000 -w 640 -h 480 -fps 25 -b 1200000 -vf -p 0,0,640,480 -o " + dt + ".h264"
    subprocess.call(a1,shell= True)
    a2 = "MP4Box -add " + dt + ".h264 " + dt+".mp4"
    subprocess.call(a2,shell= True)
    a3 = "sudo rm "+dt+".h264"
    subprocess.call(a3,shell=True)
    s.child(dt+".mp4").put(dt1+".mp4")
    exit()

if __name__ == "__main__":  
    
    
    
    config = {
    "apiKey" : "AIzaSyCyUfzKLzdBV9HMx69HeMHR1I4F6vPW9Hk",
    "authDomain" : "my-project-1560342120595.firebaseapp.com",
    "databaseURL" : "my-project-1560342120595.firebaseio.com",
    "storageBucket" : "my-project-1560342120595.appspot.com",
    "serviceAccount" : "/home/pi/Desktop/abcd.json"
    }

    firebase = pyrebase.initialize_app(config)
    auth = firebase.auth()
    storage = firebase.storage()
 
    bd_addr = "98:D3:32:30:9E:3A"
    port = 1
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((bd_addr,port))
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(24, GPIO.OUT)
    flag=0
    print("waiting")
    while 1:
            data=sock.recv(1000)
            time.sleep(4)
            print(data)
            #if "A" not in data:
            temp1 = ""
            temp2 = ""
            if "H" in data:
                temp1 = "High"
                flag=1
            if "M" in data:
                temp1 = "Medium"
                flag=1
            if "E" in data:
                temp1 = "Extreme"
                flag=1
            if "1" in data:
                temp2 = "Left Side"
                flag=1
            if "2" in data:
                temp2 = "Front Side"
                flag=1
            if "3" in data:
                temp2 = "Back Side"
                flag=1
            if "4" in data:
                temp2 = "Right Side"
                flag=1
                
            if flag==0:    
                continue
            else:
                flag=0
            #GPIO.setmode(GPIO.BOARD)    
 
# Enable Serial Communication
            port = serial.Serial("/dev/ttyUSB0", baudrate=19200, timeout=1)
 
# Transmitting AT Commands to the Modem
# '\r\n' indicates the Enter key
            port.write('AT'+'\r\n')
            rcv = port.read(10)
            print rcv
            time.sleep(.1)
 
#port.write('ATE0'+'\r\n')      # Disable the Echo
#rcv = port.read(10)
#rint rcv
#time.sleep(.1)

            port.write('AT+CGNSPWR=1'+'\r\n')      # Disable the Echo
            rcv = port.read(10)
            print rcv
            time.sleep(.1)

            port.write('AT+CGNSSEQ=RMC'+'\r\n')      # Disable the Echo
            rcv = port.read(1000)
            print rcv
            time.sleep(.1)

            port.write('AT+CGNSINF'+'\r\n')      # Disable the Echo
            rcv = port.read(1000)
            #print rcv
            time.sleep(.1)
            arr = [None] * 100
            arr1= ""
            j = 0
            for i in rcv:
                if i!= ',':
                    arr1 = arr1 + i
                else:
                    arr[j] = arr1
                    j = j+1
                    arr1 = ""
            print(arr)        

             
            port.write('AT+CMGF=1'+'\r\n')  # Select Message format as Text mode
            rcv = port.read(10)
            print rcv
            time.sleep(.1)
             
            port.write('AT+CNMI=2,1,0,0,0'+'\r\n')   # New SMS Messa                                                                                                                                                                                                                                                                                                                                            ge Indications
            rcv = port.read(10)
            print rcv
            time.sleep(.1)
             
            # Sending a message to a particular Number
            port.write('AT+CMGS="9537692353"'+'\r\n')
            rcv = port.read(10)
            print rcv
            time.sleep(.1)
             
            port.write('Latitude' + arr[3] + 'Longitude' +arr[4] + 'Severity: ' + temp1 + ' Side of impact: '+ temp2 + '\r\n')  # Message
            rcv = port.read(10)
            print rcv
             
            port.write("\x1A") # Enable to send SMS
            for i in range(10):
                rcv = port.read(10)
                print rcv
            
            
            localtime = datetime.datetime.now().strftime("%I:%M%p%B%d_%Y")
            GPIO.output(24, 1)
            time.sleep(2)
            GPIO.output(24, 0)
            #print(localtime)
    
            pid1 = os.fork()
            if pid1 == 0:
                pid2= os.fork()
                if pid2==0:
                    record_audio(localtime,storage)
                else:
                    servoPIN=2
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setup(servoPIN,GPIO.OUT)
                    p=GPIO.PWM(servoPIN,50)
                    p.start(2.5)
                    duty=1
                    p.ChangeDutyCycle(5.95)
                    time.sleep(0.5)
                    p.ChangeDutyCycle(0)
                    time.sleep(2)
                    p.ChangeDutyCycle(5.95)
                    time.sleep(0.5)
                    p.ChangeDutyCycle(0)
                    time.sleep(2)
                    p.ChangeDutyCycle(5.95)
                    time.sleep(0.5)
                    p.ChangeDutyCycle(0)
                    time.sleep(2)
                    p.ChangeDutyCycle(5.95)
                    time.sleep(0.5)
                    p.ChangeDutyCycle(0)
                    time.sleep(2)
                    p.ChangeDutyCycle(13.5)
                    time.sleep(0.5)
                    p.stop()
                    GPIO.cleanup()
                    exit()
                    #os.waitpid(pid2,0)
            
    #'''
            else:
         #pid2 = os.fork()
        # if pid2 == 0:
                record_video(localtime,storage)
                print("Video done")
                os.waitpid(pid1,0)
                print("Audio Recording Done")
                print("Recording Completed")
                dt = "/home/pi/Desktop/" + localtime + ".wav"
                dt1 = "/home/pi/Desktop/" + localtime + ".mp4"
                time.sleep(1)
                sock.close()
                exit()     