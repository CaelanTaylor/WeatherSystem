import compass
sensor = compass.QMC5883L()
m = sensor.get_magnet()
print(m)