# vending_simulator.py
import serial
import time

# Configura el puerto serial (asegúrate de que coincide con el controlador)
ser = serial.Serial(port='/dev/ttyS1', baudrate=115200, timeout=1)

# Diccionario de estados simulados de la máquina de vending
VENDING_STATES = [
    "c,STATUS,INACTIVE",
    "c,STATUS,DISABLED",
    "c,STATUS,ENABLED",
    "c,STATUS,VEND,10,101",  # Ejemplo: producto de $10 con ID 101
    "c,VEND,SUCCESS",        # Producto dispensado con éxito
    "c,STATUS,IDLE"          # Transacción terminada
]

def simulate_vending():
    print("Simulando máquina expendedora...")
    for state in VENDING_STATES:
        ser.write((state + "\n").encode())
        print(f"Simulación: Enviando estado '{state}'")
        time.sleep(2)  # Espera 2 segundos para simular tiempo real

    ser.close()

if __name__ == '__main__':
    simulate_vending()
