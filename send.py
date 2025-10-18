import time
import spidev
import socket
import compass
from math import exp
import datetime

cmp = compass.QMC5883L()

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)  # (bus 0, device 0 → CE0)
spi.max_speed_hz = 1350000  # 1.35 MHz

def read_channel(channel):
    """Read analog value from the MCP3008 ADC (channel 0-7)."""
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be 0-7")
    
    # MCP3008 protocol: start bit, single-ended mode, channel selection
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) | adc[2]  # Combine bytes to get 10-bit value
    return data

def get_wind_speed():
    """Get wind speed from the ZTS-3000-FSJT-V05 sensor (channel 7)."""
    raw_value = read_channel(7)
    wind_speed = (raw_value / 1023.0) * 30  # Linear mapping: 0–1023 → 0–30 m/s
    wind_speed_knots = wind_speed * 1.94384 * 1.5  # Convert to knots and apply calibration factor
    # Round to 4 significant figures
    wind_speed_knots = float(f"{wind_speed_knots:.4g}")
    return wind_speed_knots

def get_wind_dir():
    """Get true wind direction using wind vane and corrected compass heading."""
    raw_value = read_channel(1)
    # Map raw value to 0–360°
    relative_wind_dir = ((raw_value - 199) / (1014 - 199)) * 360
    compass_heading = cmp.get_bearing()  # 0–360°
    corrected_heading = (compass_heading) % 360
    true_wind_dir = (relative_wind_dir + corrected_heading) % 360  # Wrap result
    # Ensure 360 degrees becomes 0 degrees
    true_wind_dir = (true_wind_dir % 360)
    # Round to nearest 45°
    wind_dir_rounded = int((true_wind_dir / 45) + 0.5) * 45
    return wind_dir_rounded

wtemp = 0
atemp = 0

# Send data over socket
HOST = '192.168.192.186'
PORT = 50000

while True:
    time.sleep(1)  # Wait for 5 seconds between readings
    data_list = [get_wind_speed(), get_wind_dir(), wtemp, atemp]
    data_str = ','.join(str(x) for x in data_list)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)  # Optional: timeout after 3 seconds
            s.connect((HOST, PORT))
            s.sendall(data_str.encode('utf-8'))
    except Exception:
        pass
