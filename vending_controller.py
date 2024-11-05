# vending_controller.py
import serial
import time
import evdev
import select

# Diccionario de estado de la máquina
STATUS = {
    "INACTIVE": "c,STATUS,INACTIVE",
    "DISABLED": "c,STATUS,DISABLED",
    "ENABLED": "c,STATUS,ENABLED",
    "VEND": "c,STATUS,VEND",
    "IDLE": "c,STATUS,IDLE",
    "DISPENSED": "c,VEND,SUCCESS",
    "FAIL2DISPENSE": "c,ERR,VEND 3",
}

AUTHORIZE_VEND = "C,VEND,"  # Prefijo para autorizar una solicitud de venta
DENY_VEND = "C,STOP"        # Mensaje para negar una venta

# Configuración del puerto serial
def openSerial():
    global ser
    ser = serial.Serial('/dev/ttyS0', baudrate=115200, timeout=1)
    ser.open()

def write2Serial(msg):
    ser.write((msg + "\n").encode())
    ser.flush()

def readSerial():
    return ser.readline().decode("ascii").strip("\n").strip("\r")

def print2Console(msg):
    print("\r" + msg, end="\r")

# Lectura de RFID (simulado aquí para pruebas)
def read_rfid():
    print2Console("Esperando lectura de RFID...")
    device = evdev.InputDevice('/dev/input/event0')  # Configura el dispositivo
    while True:
        r, _, _ = select.select([device.fd], [], [], 1)
        if r:
            for event in device.read():
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                    return evdev.ecodes.KEY[event.code]  # Código RFID

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
            print2Console("Esperando a la máquina expendedora...")

        elif rcv == STATUS["ENABLED"]:
            print2Console("Seleccione producto en la máquina expendedora.")

        elif STATUS["VEND"] in rcv:
            vendAmt = rcv.split(",")[3]
            prodId = rcv.split(",")[4]
            print2Console(f"Producto seleccionado: {prodId}. Esperando pago RFID...")

            rfid_code = read_rfid()
            if rfid_code:
                write2Serial(AUTHORIZE_VEND + vendAmt)
                print2Console("Esperando dispensación del producto...")
            else:
                write2Serial(DENY_VEND)
                print2Console("Transacción cancelada por falta de RFID.")

        elif rcv == STATUS["DISPENSED"]:
            print2Console("¡Producto dispensado!")

        elif rcv == STATUS["FAIL2DISPENSE"]:
            print2Console("Error en la dispensación del producto.")

        elif rcv == STATUS["IDLE"]:
            print2Console("Transacción finalizada.")
