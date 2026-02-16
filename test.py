#!/usr/bin/env python3
from ev3dev2.motor import *
from ev3dev2.sound import Sound
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.sensor import INPUT_4
import time

m = MediumMotor(OUTPUT_A)
m1 = LargeMotor(OUTPUT_B)
us = UltrasonicSensor(INPUT_4)

speaker = Sound()

print("Lancement de la rotation constante...")
speaker.speak("Motor on", volume=100)

# Allume le moteur à 40% de sa vitesse maximale
# Il restera allumé après cette ligne !
m.on(SpeedPercent(10))
m1.on(SpeedPercent(10))

# On le laisse tourner pendant que le programme fait autre chose
# Ici, on attend simplement 5 secondes
print("Le moteur tourne pendant 5 secondes...")
time.sleep(10)

# On arrête le moteur
print("Arret du moteur.")
m.stop()
time.sleep(10)
m1.stop()
speaker.speak("Motor stop")

try:
    while True:
        # L'ultrason mesure en centimètres
        distance = us.distance_centimeters
        print("Distance : " + str(round(distance, 1)) + " cm")
        
        if distance < 20: # Si un objet est à moins de 20 cm
            print("OBSTACLE !")
            m.stop()
            m1.stop()
            speaker.beep()
            speaker.speak("Obstacle")
            break # On sort de la boucle pour arrêter le programme
            
        time.sleep(0.1)

except KeyboardInterrupt:
    m.stop()
    m1.stop()