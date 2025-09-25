import time
import spidev
import time

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
    """Get wind speed from the anemometer (channel 7)."""
    raw_value = read_channel(7)
    wind_speed = (raw_value / 1023.0) * 30  # Convert to m/s
    wind_speed_knots = wind_speed * 1.94384      # Convert to knots
    return wind_speed_knots

def get_wind_dir():
    """Get wind speed from the anemometer (channel 7)."""
    raw_value = read_channel(1)
    wind_dir = ((raw_value - 200) / 823) * 360  # Convert to degrees
    return wind_dir

print(get_wind_speed())

while True:
    print(get_wind_dir())
    

# Build full message


#payload = f"{windspd} {winddir} {wtemp} {atemp}"

