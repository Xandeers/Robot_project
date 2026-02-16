#!/usr/bin/env python3

from time import sleep
from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A,OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent

from src.moteur import *
from src.socket import creer_et_attendre_connexion, envoyer_message, fermer_reseau


m1= LargeMotor(OUTPUT_A)
m2= LargeMotor(OUTPUT_B)
m3= LargeMotor(OUTPUT_C)
m4= LargeMotor(OUTPUT_D)

print("Initialisation du robot...")

avanceVehicule_Uniform(m1,m2,m3,m4,100)
sleep(20)
stopVehicule(m1,m2,m3,m4)
rotation_180(m1,m2,m3,m4)


