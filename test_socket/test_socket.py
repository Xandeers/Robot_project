
from time import sleep
from robot import creer_et_attendre_connexion, envoyer_message, fermer_reseau 


client,connexion = creer_et_attendre_connexion()
message= "la connexion est OK"
envoyer_message(connexion,message)

message2= "fermeture socket dans..."
envoyer_message(connexion,message2)
for i in range(10):
    envoyer_message(connexion,i)
    sleep(1)
    
fermer_reseau(client,connexion)
