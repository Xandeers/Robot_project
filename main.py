#!/usr/bin/env python3

from time import sleep
from ev3dev2.motor import LargeMotor, OUTPUT_A,OUTPUT_B, OUTPUT_C, OUTPUT_D

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

#test socket 
client,connexion = creer_et_attendre_connexion()
message= "la connexion est OK"
envoyer_message=(connexion,message)

message2= "fermeture socket dans..."
envoyer_message(connexion,message2)
for i in range(10):
    envoyer_message(connexion,i)
    sleep(1)

fermer_reseau()



