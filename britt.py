                 
import serial
import os
import time
import evdev

STATUS = {
    "INACTIVE": "c,STATUS,INACTIVE",
    "DISABLED": "c,STATUS,DISABLED",
    "ENABLED": "c,STATUS,ENABLED",
    "VEND": "c,STATUS,VEND",
    "IDLE": "c,STATUS,IDLE",
    "DISPENSED": "c,VEND,SUCCESS",
    "FAIL2DISPENSE": "c,ERR,VEND 3",
}

AUTHORIZE_VEND = "C,VEND,"  # Prefix to send to authorize a vend request
DENY_VEND = "C,STOP"  # Message to send to deny a vend request

# Serial Port functions to interact with MDB USB/Pi Hat
def openSerial():
    global ser
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.timeout = 50
    ser.port = '/dev/ttyS0'
    ser.open()

def write2Serial(msg):
    global ser
    ser.write((msg + "\n").encode())
    ser.flush()

def readSerial():
    global ser
    s = ser.readline().decode("ascii").strip("\n").strip("\r")
    return s if s else ""

# Function to print to console
def print2Console(msg):
    print("\r" + msg, end="\r")

import evdev
import select

# Function to read RFID
def read_rfid():
    print2Console("Esperando lectura de RFID...")
    device = evdev.InputDevice('/dev/input/event0')  # Reemplaza X con el n  mero correcto del dispositivo
    
    # Usamos select para esperar datos sin bloquear el dispositivo
    while True:
        r, _, _ = select.select([device.fd], [], [], 1)  # Espera de 1 segundo
        if r:
            for event in device.read():
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:  # Evento de tecla presionada
                    key_code = evdev.ecodes.KEY[event.code]
                    return key_code  # Retorna el c  digo de la tecla presionada
        else:
            print2Console("Esperando lectura de RFID...")  # Seguimos esperando


def initCashlessDevice():
    write2Serial("C,0")
    write2Serial("C,1")

if __name__ == '__main__':
    openSerial()
    initCashlessDevice()

    while True:
        time.sleep(1)
        rcv = readSerial()

        if rcv == STATUS["INACTIVE"] or rcv == STATUS["DISABLED"]:
            print2Console("Waiting for vending machine...")

        elif rcv == STATUS["ENABLED"]:
            print2Console("Please select product on vending machine.")

        elif STATUS["VEND"] in rcv:
            vendAmt = rcv.split(",")[3]  # c,STATUS,VEND,<amount>,<product_id>
            prodId = rcv.split(",")[4]

            print2Console(f"Product selected: {prodId}. Waiting for RFID payment...")

            # Leer RFID en lugar de esperar la tecla 'v'
            rfid_code = read_rfid()
            if rfid_code:  # Si se ley   un c  digo RFID
                write2Serial(AUTHORIZE_VEND + vendAmt)
                print2Console("Waiting for product dispense...")
                print2Console(f"Amount: {vendAmt}, Product ID: {prodId}")

            else:
                write2Serial(DENY_VEND)
                print2Console("Transaction canceled due to no RFID detected.")

        elif rcv == STATUS["DISPENSED"]:
            print2Console("Product dispensed!")

        elif rcv == STATUS["FAIL2DISPENSE"]:
            print2Console("Product failed to dispense.")
        elif rcv == STATUS["IDLE"]:
            print2Console("Transaction finished.")
        else:
            continue


