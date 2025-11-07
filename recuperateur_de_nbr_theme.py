import requests, re, os
import csv

def recup_nbr_theme():
    source_d_info = "./MovieGenre.csv"

    liste_des_genre=[]

    with open(source_d_info, newline='', encoding='latin1') as f:
        reader = list(csv.DictReader(f))
        for ligne in reader:
            genres = ligne["Genre"]
            print(genres)

    print()
    print("liste des genres:",liste_des_genre)

recup_nbr_theme()
