from ev3dev2.sensor.lego import UltrasonicSensor

DISTMIN=20

#en centimetre
def getvalue(sensor) :

    return sensor.distance_centimeters

def boolColision(sensor):
    if(getvalue(sensor) <= DISTMIN): 
        return True
    else:
        return False
    

