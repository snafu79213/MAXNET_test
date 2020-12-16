#!/usr/bin/python
import serial
import sys
import time


def writeToPort(s):
    ser.write(bytes('\n' + s, 'utf-8'))

def readFromPort():
    return str(ser.readline())[2:-3]

def configMotor(mtr):
    writeToPort('A' + mtr + '\n')
    writeToPort('PSE\n')
    writeToPort('VL10\n')

def runMotor(mtr, steps, direction):
    if direction is not '-':
        direction = ''

    time.sleep(0.1)
    writeToPort('A' + mtr + '\n')
    time.sleep(0.1)
    writeToPort('MR' + direction + steps + '\n')
    time.sleep(0.1)
    writeToPort('GO\n')
    time.sleep(0.1)

def testMotor(mtr, direction):

    limit_flag = ""

    if (mtr == 'X'):
        limit_flag = '000 00000100'
    elif (mtr == 'Y'):
        limit_flag = '000 00000200'
    elif (mtr == 'Z'):
        limit_flag = '000 00000400'
    elif (mtr == 'T'):
        limit_flag = '000 00000800'
    elif (mtr == 'U'):
        limit_flag = '000 00001000'

    print("testing " + mtr + " motor in " + direction + " direction ... ", end="")
    runMotor(mtr, '51', direction)  # 50 steps hits a limit, 51 trips overtravel from maxnet

    ser.timeout = 10
    res = str(ser.readline())[3:-3]

    if res == limit_flag:
        print("... passed")
        return True

    else:
        print("... failed")

    return False

def printUsage():
    print("usage is 'python maxnet <COM PORT> <MTR or ENC or AUX> <X or Y or Z or T or U>'")

if len(sys.argv) < 4:
    printUsage()
    exit()

print("connecting...")
ser = serial.Serial(sys.argv[1], 115200, timeout=10)
print("...done.")
maxnet = {}
writeToPort('wy')
line = readFromPort();

while line == '000 01000000':       #error feedback from maxnet, need to put this somewhere and handle it better
    writeToPort('\n')
    writeToPort('wy')
    line = readFromPort();

line = line.split(", ")

maxnet['name'] = str(line[0].split(' ')[0])

if maxnet['name'] == 'MAXXn-5000':
    print("wrong port")
    quit()

maxnet['serial number'] = line[0].split(":")[1]
maxnet['firmware'] = line[2]

writeToPort('#NM?')
maxnet['mac address'] = readFromPort()[1:]

print("setting back to factory defaults...")
writeToPort('RDF\n')    # factory defaults
writeToPort('APP\n')    # save to flash
print("...done.")

print("configuring motor...")
configMotor(sys.argv[3])
print('...done.')


if str(sys.argv[2]).upper() == 'MTR':
    print("beginning tests...")
    testMotor(sys.argv[3].upper(), '+')

    time.sleep(1)

    testMotor(sys.argv[3].upper(), '-')
    print("...done.")
else:
    printUsage()
    exit()
