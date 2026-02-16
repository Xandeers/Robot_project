# moteur python
from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A,OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent
from ev3dev2.sound import Sound



def avanceMotor(motor, pourcent): 
    print("Moteur {} on {}".format(motor, pourcent))
    motor.on(SpeedPercent(pourcent))

def stopMotor(motor):
    print("Moteur {} off".format(motor))
    motor.stop()


