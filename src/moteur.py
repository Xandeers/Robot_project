# moteur python
from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A,OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent
from ev3dev2.sound import Sound



def avanceMotor(motor, pourcent): 
    print("Moteur {} on {}".format(motor, pourcent))
    motor.on(SpeedPercent(pourcent))

def stopMotor(motor):
    print("Moteur {} off".format(motor))
    motor.stop()


def avanceVehicule_Uniform(motor_avantD, motor_avantG, motor_arriereD, motor_arriereG, pourcent):
    print("Vehicule on {} \%".format(pourcent))
    
    avanceMotor(motor_avantD,pourcent)
    avanceMotor(motor_avantG,pourcent)

    avanceMotor(motor_arriereD,-pourcent)
    avanceMotor(motor_arriereG,-pourcent)




