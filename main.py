#!/usr/bin/env python3

from time import sleep
from ev3dev2.motor import LargeMotor, OUTPUT_A,OUTPUT_B, OUTPUT_C, OUTPUT_D

from src.moteur import *
from src.socket import creer_et_attendre_connexion, envoyer_message, fermer_reseau

from src.ultrasonicSensor import *
from ev3dev2.sensor import INPUT_4

from ev3dev2.sound import Sound

#motor
m1= LargeMotor(OUTPUT_A)
m2= LargeMotor(OUTPUT_B)
m3= LargeMotor(OUTPUT_C)
m4= LargeMotor(OUTPUT_D)

#ultrasonCapteur
sensor = UltrasonicSensor(INPUT_4)

#Speaker
speaker= Sound()


print("Initialisation du robot...")

avanceVehicule_Uniform(m1,m2,m3,m4,100)
sleep(10)
stopVehicule(m1,m2,m3,m4)
rotation_Droite(m1,m2,m3,m4)
sleep(5)
avanceVehicule_Uniform(m1,m2,m3,m4,100)
sleep(5)
glissement_Avant_droit(m1,m2,m3,m4)


#test colision 

while True : 
    if (boolColision(sensor)):
        speaker.beep()

    break


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



