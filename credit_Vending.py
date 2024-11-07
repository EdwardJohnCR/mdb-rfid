import serial
import time
import evdev
import select

# Credit
credit_amount = 0.0  # We initialize with 0; can be adjusted

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
    """Initialize the serial communication."""
    global ser
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.timeout = 50
    ser.port = '/dev/ttyS0'
    ser.open()

def write2Serial(msg):
    """Send a message to the serial port."""
    global ser
    ser.write((msg + "\n").encode())
    ser.flush()

def readSerial():
    """Read incoming data from the serial port."""
    global ser
    s = ser.readline().decode("ascii").strip("\n").strip("\r")
    return s if s else ""

# Function to print to console
def print2Console(msg):
    """Display messages on the console."""
    print("\r" + msg, end="\r")

# Function to read RFID
def read_rfid():
    """Reads RFID input and returns the key code."""
    print2Console("Waiting for RFID scan...")
    device = evdev.InputDevice('/dev/input/event0')  # Adjust device number as needed
    
    # Use select to wait for non-blocking input from the device
    while True:
        r, _, _ = select.select([device.fd], [], [], 1)  # 1-second wait
        if r:
            for event in device.read():
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:  # Key press event
                    key_code = evdev.ecodes.KEY[event.code]
                    return key_code  # Return the pressed key code
        else:
            print2Console("Waiting for RFID scan...")  # Continue waiting

# Initialize Cashless Device
def initCashlessDevice():
    """Set up the cashless device in authorization-first mode."""
    write2Serial("D,1")  # Enable authorization-first mode
    write2Serial("C,1")  # Activate cashless slave mode

# Function to increase or decrease credit
def update_credit(amount):
    """Update the credit amount by adding or subtracting a given amount."""
    global credit_amount
    credit_amount += amount  # Increment or decrement based on the input amount
    print2Console(f"Updated credit amount: {credit_amount:.0f}PT")

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
            vendAmt = float(rcv.split(",")[3])  # c,STATUS,VEND,<amount>,<product_id>
            prodId = rcv.split(",")[4]

            print2Console(f"Product selected: {prodId}. Waiting for RFID payment...")

            # Read RFID instead of waiting for key press
            rfid_code = read_rfid()
            if rfid_code and credit_amount >= vendAmt:  # If RFID read and sufficient credit
                write2Serial(AUTHORIZE_VEND + str(vendAmt))
                update_credit(-vendAmt)  # Deduct the amount from credit
                print2Console(f"Authorized vend for {vendAmt}€; Product ID: {prodId}")
            else:
                write2Serial(DENY_VEND)
                print2Console("Transaction canceled due to insufficient credit or no RFID detected.")

        elif rcv == STATUS["DISPENSED"]:
            print2Console("Product dispensed!")

        elif rcv == STATUS["FAIL2DISPENSE"]:
            print2Console("Product failed to dispense.")

        elif rcv == STATUS["IDLE"]:
            print2Console("Transaction finished.")
        
        else:
            continue
