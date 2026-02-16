# moteur python
from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A, OUTPUT_D, SpeedPercent
from ev3dev2.sound import Sound

m = MediumMotor(OUTPUT_A)
m1 = LargeMotor(OUTPUT_D)
speaker = Sound()


def avanceMotor(motor, pourcent):
    print(f"Moteur {motor} on {pourcent}%")
    motor.on(SpeedPercent(pourcent))
    


def stopMotor(motor):
    print(f"Moteur {motor} off")
    motor.stop
    
    