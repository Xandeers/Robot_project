# moteur python
from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A,OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent
from ev3dev2.sound import Sound



def avanceMotor(motor, pourcent): 
    print("Moteur {} on {}".format(motor, pourcent))
    motor.on(SpeedPercent(pourcent))


def returnMotor(motor, pourcent):
    avanceMotor(motor,-pourcent)
    

def stopMotor(motor):
    print("Moteur {} off".format(motor))
    motor.stop()

def getVitesse(motor):
    return motor.speed()

def getPosition(motor):
    return motor.position()

#return une liste de l'etat actuelle du motor ['running'], ['holding'], ['stalled']
def getEtat(motor):
    return motor.state()

def boolMotorRuning(motor):
    return motor.is_running()
    
##### Trajectoir uniforme

def avanceVehicule_Uniform(motor_avantD, motor_avantG, motor_arriereD, motor_arriereG, pourcent):
    print("Vehicule on {} \%".format(pourcent))

    avanceMotor(motor_avantD,pourcent)
    avanceMotor(motor_avantG,pourcent)

    returnMotor(motor_arriereD,pourcent)
    returnMotor(motor_arriereG,pourcent)


def reculeVehicule_Uniform(motor_avantD, motor_avantG, motor_arriereD, motor_arriereG, pourcent):
    print("Vehicule on return {} \%".format(pourcent))

    returnMotor(motor_avantD,pourcent)
    returnMotor(motor_avantG,pourcent)

    avanceMotor(motor_arriereD,pourcent)
    avanceMotor(motor_arriereG,pourcent)


def stopVehicule(motor_avantD, motor_avantG, motor_arriereD, motor_arriereG):
    print("Vehicule off")

    stopMotor(motor_avantD)
    stopMotor(motor_avantG)
    stopMotor(motor_arriereD)
    stopMotor(motor_arriereG)

def rotation_Droite(motor_avantD, motor_avantG, motor_arriereD, motor_arriereG):

    #coté droit avance 
    avanceMotor(motor_avantD,100)
    returnMotor(motor_arriereD,100)

    #cote gauche recule
    returnMotor(motor_avantG,100)
    avanceMotor(motor_arriereG,100)

def glissement_Droit(motor_avantD, motor_avantG, motor_arriereD, motor_arriereG):
    
    #mode diagonale
    avanceMotor(motor_avantD,100)
    returnMotor(motor_arriereG,100)


    returnMotor(motor_avantG,100)
    avanceMotor(motor_arriereD,100)

def glissement_Avant_droit(motor_avantD, motor_avantG, motor_arriereD, motor_arriereG):

    #frein a main 
    motor_avantG.stop_action = 'hold'
    motor_arriereD.stop_action ='hold'
    motor_avantG.stop()
    motor_arriereD.stop()

    #mode diagonale
    avanceMotor(motor_avantD,100)
    returnMotor(motor_arriereG,100)



