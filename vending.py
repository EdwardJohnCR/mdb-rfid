import serial
import time
import evdev
import select

# Define the various statuses for the vending machine and card reader
STATUS = {
    "INACTIVE": "c,STATUS,INACTIVE",  # Reader is connected but inactive
    "DISABLED": "c,STATUS,DISABLED",  # Reader is disabled
    "ENABLED": "c,STATUS,ENABLED",    # Reader is enabled and ready
    "CREDIT": "d,STATUS,CREDIT",      # Credit has been authorized
    "VEND": "d,STATUS,VEND",          # Machine is ready to vend
    "DISPENSED": "c,VEND,SUCCESS",    # Product dispensed successfully
    "FAIL2DISPENSE": "c,ERR,VEND 3",  # Failed to dispense product
    "IDLE": "c,STATUS,IDLE"           # Machine has finished the transaction
}

# Constants for sending vending authorization or cancellation commands
AUTHORIZE_VEND = "C,VEND,"  # Prefix to authorize a vend request
DENY_VEND = "C,STOP"        # Message to cancel the vend request

# Function to initialize the serial connection for communication with the MDB Pi Hat
def openSerial():
    global ser
    ser = serial.Serial()
    ser.baudrate = 115200  # Set baud rate to match MDB Pi Hat
    ser.timeout = 50       # Set a timeout for the serial connection
    ser.port = '/dev/ttyS0'  # Specify the serial port (adjust if needed)
    ser.open()  # Open the serial connection

# Function to send a message to the serial port
def write2Serial(msg):
    global ser
    ser.write((msg + "\n").encode())  # Encode the message and send it
    ser.flush()  # Flush to ensure the message is fully sent

# Function to read a message from the serial port
def readSerial():
    global ser
    s = ser.readline().decode("ascii").strip("\n").strip("\r")  # Decode and clean the response
    return s if s else ""  # Return the response if available, otherwise empty string

# Function to display a message on the console
def print2Console(msg):
    print("\r" + msg, end="\r")  # Print the message on the same line

# Function to read RFID input from the RFID device
def read_rfid():
    print2Console("Waiting for RFID scan...")
    device = evdev.InputDevice('/dev/input/event0')  # Set the correct RFID input device

    # Use select to wait for input without blocking
    while True:
        r, _, _ = select.select([device.fd], [], [], 1)  # Wait for 1 second
        if r:
            for event in device.read():  # Read RFID events
                # Check for key press event from RFID
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                    key_code = evdev.ecodes.KEY[event.code]
                    return key_code  # Return the RFID key code
        else:
            print2Console("Waiting for RFID scan...")  # Continue waiting

# Function to initialize the cashless device in "Authorization First" mode
def initCashlessDevice():
    write2Serial("C,0")   # Reset the reader to prepare for initialization
    write2Serial("D,1")   # Activate "Authorization First" mode on vending machine
    time.sleep(1)         # Pause for a moment
    write2Serial("C,1")   # Enable the card reader in cashless mode

# Main section of the script
if __name__ == '__main__':
    openSerial()  # Open serial communication
    initCashlessDevice()  # Initialize device in Authorization First mode

    # Continuously monitor and process vending machine responses
    while True:
        time.sleep(1)  # Short pause between reads
        rcv = readSerial()  # Read from serial port

        # Check status and display messages based on vending machine response
        if rcv == STATUS["INACTIVE"] or rcv == STATUS["DISABLED"]:
            print2Console("Waiting for vending machine...")

        elif rcv == STATUS["ENABLED"]:
            print2Console("Authorization mode active. Waiting for RFID payment...")

            # Wait for an RFID scan to authorize credit
            rfid_code = read_rfid()
            if rfid_code:  # If RFID detected, authorize 1€ credit
                write2Serial("C,START,500")
                print2Console("500pt credit authorized. Waiting for product selection...")
            else:
                # If no RFID detected, deny the vend request
                write2Serial(DENY_VEND)
                print2Console("Authorization canceled due to lack of RFID.")

        elif STATUS["CREDIT"] in rcv:
            # Parse the credit amount and product ID
            vendAmt = rcv.split(",")[3]  # Amount of credit
            prodId = rcv.split(",")[4]   # Product ID selected
            print2Console(f"Credit confirmed: {vendAmt}€ for product {prodId}")

            # Send vend request with specified amount and product ID
            write2Serial(f"D,REQ,{vendAmt},{prodId}")
            print2Console("Vend request sent. Waiting for vending status...")

        elif rcv == STATUS["VEND"]:
            print2Console("Waiting for vending machine to process payment...")

        elif STATUS["DISPENSED"] in rcv:
            print2Console("Product successfully dispensed.")

        elif STATUS["FAIL2DISPENSE"] in rcv:
            print2Console("Error: Failed to dispense product.")

        elif rcv == STATUS["IDLE"]:
            print2Console("Transaction completed.")
        
        else:
            continue  # Ignore unhandled statuses
