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

try:
    while True:
        # Read all 8 channels
        for ch in range(8):
            value = read_channel(ch)
            voltage = value * 3.3 / 1023  # Convert to voltage (Vref=3.3V)
            print(f"Channel {ch}: {value} ({voltage:.2f} V)")
        time.sleep(1)

except KeyboardInterrupt:
    spi.close()
    print("\nExiting...")
