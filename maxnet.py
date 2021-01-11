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

    writeToPort('A' + mtr + '\n')
    time.sleep(0.1)
    writeToPort('MR' + direction + steps + '\n')
    time.sleep(0.1)
    writeToPort('GO\n')
    time.sleep(0.1)


def jogMotor(mtr, speed, direction):
    if direction is not '-':
        direction = ''

    writeToPort('A' + mtr + '\n')
    time.sleep(0.1)
    writeToPort('MR' + direction + speed + '\n')
    time.sleep(0.1)
    writeToPort('GO\n')
    time.sleep(0.1)

def testMTR(mtr, direction):
    limit_flag = getLimitFlag(mtr)

    print("testing " + mtr + " motor in " + direction + " direction ... ")

    # runMotor(mtr, '51', direction)  #
    writeToPort('A' + mtr + '\n')
    time.sleep(0.1)
    writeToPort('ABH\n')
    time.sleep(0.1)
    jogMotor(mtr, '10', direction)  # 10 pulses a second
    writeToPort('A' + mtr + '\n')
    time.sleep(0.1)
    writeToPort('ABL\n')
    time.sleep(0.1)
    ser.timeout = 2
    res = str(ser.readline())[3:-3]

    if res == limit_flag:
        return True
    return False

def testENC(enc):
    print("testing " + enc + " encoder... ")

    writeToPort('A' + enc + '\n')
    time.sleep(0.1)
    writeToPort('RE\n')     # read encoder
    time.sleep(0.1)
    ser.timeout = 2
    a = readFromPort()
    time.sleep(1)
    writeToPort('RE\n')     # read encoder
    time.sleep(0.1)
    b = readFromPort()

    if a.isnumeric() is False or b.isnumeric() is False:
        return False

    c = int(b) - int(a)
    if c > 0:
        return True

    return False

def testAUX(aux):
    print("testing " + aux + " auxillary... ")
    if aux == 'X' or aux == 'Y':
        if aux == 'X':
            writeToPort('AI0\n')
        elif aux == 'Y':
            writeToPort('AI1\n')
        a = readFromPort()[4:]
        if a is "":
            return False

        b = float(a)
        if 2 < b < 3:       # the masxnet analog input draws > 250mA for some reason why it draws so much.
            writeToPort('BL0\n')
            return True     # the controller has a hard time with keeping the voltage up. I should look into this.
        return False

    if aux == 'Z':
        return True

    if aux == 'T' or aux == 'U':
        writeToPort('BX\n')
        a = readFromPort()
        if a != 'ff':
            return True
        return False
    return False

def getLimitFlag(mtr):
    if mtr == 'X':
        return '000 00000100'
    elif mtr == 'Y':
        return '000 00000200'
    elif mtr == 'Z':
        return '000 00000400'
    elif mtr == 'T':
        return '000 00000800'
    elif mtr == 'U':
        return '000 00001000'
    else:
        return '0'

def printUsage():
    print("usage is 'python maxnet <COM PORT> <MTR or ENC or AUX> <X or Y or Z or T or U>'")


if len(sys.argv) < 4:
    printUsage()
    exit()

ser = serial.Serial(sys.argv[1], 115200, timeout=2)
maxnet = {}
writeToPort('wy')
line = readFromPort()

while line == '000 01000000':  # error feedback from maxnet, need to put this somewhere and handle it better
    writeToPort('\n')
    writeToPort('wy')
    line = readFromPort()

line = line.split(", ")

maxnet['name'] = str(line[0].split(' ')[0])

if maxnet['name'] != 'MAXn-5000':
    print("check port")
    quit()

maxnet['firmware'] = line[0].split(":")[1]
maxnet['serial number'] = line[2]

writeToPort('#NM?')
maxnet['mac address'] = readFromPort()[1:]

writeToPort('RDF\n')  # factory defaults
writeToPort('APP\n')  # save to flash

writeToPort('BDA7\n')   # 'set 1010 0111' '1' is output, '0' is input, pin 4 on rj45 always output high
writeToPort('BH0\n')
writeToPort('BH1\n')
writeToPort('BH2\n')
#writeToPort('BL3\n')
#writeToPort('BL4\n')
writeToPort('BH5')
#writeToPort('BL6')
writeToPort('BH7')


writeToPort('DOV0,0\n')     # 0v to dac just in case it's grounded.
                            # (usually reads 1.7v floating so reading 0v would be distinguishable enough)

configMotor(sys.argv[3])

x = str(sys.argv[2].upper())

# test motor
if str(sys.argv[2]).upper() == 'MTR':
    if testMTR(sys.argv[3].upper(), '+') is True:
        print("\t... step_pos/step_neg/dir_pos passed")
    else:
        print("\t... step_pos/step_neg/dir_pos failed")

    time.sleep(1)

    if testMTR(sys.argv[3].upper(), '-') is True:
        print("\t... enable/dir_neg passed")
    else:
        print("\t... enable/dir_neg failed")

elif str(sys.argv[2]).upper() == 'ENC':
    if testENC(sys.argv[3].upper()) is True:
        print("\t... encoder passed")
    else:
        print("\t... encoder failed")

elif str(sys.argv[2]).upper() == 'AUX':
    if testAUX(sys.argv[3].upper()) is True:
        print("\t... auxillary passed")
    else:
        print("\t... not implemented")

elif str(sys.argv[2]).upper() == 'INFO':
    if str(sys.argv[3]).upper() == 'SN':
        print(maxnet['serial number'])

    elif str(sys.argv[3]).upper() == 'MAC':
        print(maxnet['mac address'])

    elif str(sys.argv[3]).upper() == 'FW':
        print(maxnet['firmware'])

    else:
        printUsage()

    exit()

else:
    printUsage()
    exit()
