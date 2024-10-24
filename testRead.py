import evdev

# Reemplaza '/dev/input/event0' con el dispositivo correcto
device = evdev.InputDevice('/dev/input/event0')

# Variable para almacenar el código leído
rfid_code = ""

try:
    print("Esperando lectura de RFID...")
    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            key_event = evdev.categorize(event)
            if key_event.keystate == key_event.key_down:
                # Agregar a rfid_code si es una tecla numérica
                if key_event.keycode.startswith('KEY_') and key_event.keycode[4:].isdigit():
                    # Extraer el número de la tecla (ej. 'KEY_0' -> '0')
                    rfid_code += key_event.keycode[4]  # Obtener el número directamente
                elif key_event.keycode == 'KEY_ENTER':
                    print(f"Código RFID leído: {rfid_code}")
                    rfid_code = ""  # Reiniciar para el siguiente código
except KeyboardInterrupt:
    print("Finalizando...")
