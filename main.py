#!/usr/bin/env python3

from time import sleep
from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A,OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.sensor import INPUT_4 

from src.moteur import avanceMotor, stopMotor
from src.socket import creer_et_attendre_connexion, envoyer_message, fermer_reseau


m1= LargeMotor(OUTPUT_A)
m2= LargeMotor(OUTPUT_B)
m3= LargeMotor(OUTPUT_C)
m4= LargeMotor(OUTPUT_D)

print("Initialisation du robot...")

avanceMotor(m1,100)
avanceMotor(m2,100)
avanceMotor(m3,100)
avanceMotor(m4,100) 

sleep(50)

stopMotor(m1)
stopMotor(m2)
stopMotor(m3)
stopMotor(m4)
