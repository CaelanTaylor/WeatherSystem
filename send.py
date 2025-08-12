from sx126x import sx126x
import time

SERIAL_PORT = "/dev/serial0"
FREQ_MHZ = 433
DEST_ADDR = 0x0022

# Create LoRa object (this node = addr 0x01)
lora = sx126x(
    serial_num=SERIAL_PORT,
    freq=FREQ_MHZ,
    addr=0x0001,
    power=22,
    rssi=False,
    air_speed=2400
)

# Construct header
dest_high = (DEST_ADDR >> 8) & 0xFF
dest_low = DEST_ADDR & 0xFF
freq_offset = FREQ_MHZ - 410  # For 433 MHz → 23 → 0x17

# Build full message
payload = b"\n\n\nHello node 0x22!"
message = bytes([dest_high, dest_low, freq_offset]) + payload

# Send
lora.send(message)
print("Sent to 0x%04X:" % DEST_ADDR, payload.decode())
