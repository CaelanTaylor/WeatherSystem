import compass
sensor = compass.QMC5883L()
m = sensor.get_bearing()
print(m)