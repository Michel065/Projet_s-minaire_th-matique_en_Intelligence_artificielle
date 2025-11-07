import csv

def recup_nbr_theme(aff=True):
    source_d_info = "./MovieGenre.csv"
    liste_des_genre=[]
    with open(source_d_info, newline='', encoding='latin1') as f:
        reader = list(csv.DictReader(f))
        for ligne in reader:
            genres = ligne["Genre"].split("|")
            for genre in genres:
                if(genre != '' and genre not in liste_des_genre):
                    liste_des_genre.append(genre)

    if(aff):    
        print()
        print("liste des genres:",liste_des_genre)
        print("nbr de genres:",len(liste_des_genre))
    return liste_des_genre

recup_nbr_theme()


"""
apres execution on obtient :
liste des genres: 
['Animation', 'Adventure', 'Comedy',
 'Action', 'Family', 'Romance', 'Drama',
  'Crime', 'Thriller', 'Fantasy', 'Horror', 
  'Biography', 'History', 'Mystery', 'Sci-Fi', 
  'War', 'Sport', 'Music', 'Documentary', 'Musical', 
  'Western', 'Short', 'Film-Noir', 'Talk-Show', 
  'News', 'Adult', 'Reality-TV', 'Game-Show'] 

soit 28 themes 
"""