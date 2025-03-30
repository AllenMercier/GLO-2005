from typing import Any
from flask import Flask, render_template
import pymysql
import pymysql.cursors
from faker import Faker
import random
from dotenv import load_dotenv
from datetime import timedelta
import os

# Connexion à MySQL local
load_dotenv()

# Connexion à MySQL local
conn = pymysql.connect(
    host=os.environ.get("HOST"),
    user=os.environ.get("USER"),
    password=os.environ.get("PASSWORD"),
    db=os.environ.get("DATABASE")
)
cursor = conn.cursor()

# ----------- Peuplement de la base -----------
faker = Faker()
NB_ENTREES = 300

# Utilisateurs
user_ids = []
for _ in range(NB_ENTREES):
    cursor.execute(
        "INSERT INTO Utilisateurs (Nom, Prenom, Email, Date_de_naissance, Mot_de_passe, Statut) VALUES (%s, %s, %s, %s, %s, %s)",
        (
            faker.last_name(),
            faker.first_name(),
            f"{faker.user_name()}{random.randint(1000, 999999)}@example.com",
            faker.date_of_birth(minimum_age=18, maximum_age=60),
            faker.password(),
            random.choice([0, 1])
        )
    )
    user_ids.append(cursor.lastrowid)

# Jeux
jeu_ids = []
categories = ['Classique', 'Console', 'Ordinateur', 'Equipement'] 
used_pairs = set()
used_noms = set()
while len(used_pairs) < NB_ENTREES:
    nom_jeu = faker.word().capitalize()
    categorie = random.choice(categories)
    prix = round(random.uniform(5, 30), 2)
    quantite = random.randint(1, 10)
    
    pair = (nom_jeu, categorie)
    if pair in used_pairs:
        continue
    
    cursor.execute("SELECT COUNT(*) FROM Jeux WHERE Nom = %s AND Categorie = %s", (nom_jeu, categorie))
    if cursor.fetchone()[0] > 0:  # Si la combinaison existe déjà, passe à la prochaine itération
        continue
    
    used_pairs.add(pair)
    
    cursor.execute(
        "INSERT INTO Jeux (Nom, Categorie, Prix, Quantite) VALUES (%s, %s, %s, %s)",
        (nom_jeu, categorie, prix, quantite)
    )    
    id_jeu= cursor.lastrowid
    jeu_ids.append(id_jeu)
    
    
# Locations
location_ids = []
for _ in range(NB_ENTREES):
    id_user = random.choice(user_ids)
    cursor.execute("INSERT INTO Locations (id_user) VALUES (%s)", (id_user,))
    location_ids.append(cursor.lastrowid)

# Location_jeux avec paires (id_location, id_jeu) uniques

used_pairs = set()
while len(used_pairs) < NB_ENTREES:
    id_location = random.choice(location_ids)
    id_jeu = random.choice(jeu_ids)
    pair = (id_location, id_jeu)
    if pair in used_pairs:
        continue
    used_pairs.add(pair)

    quantite = random.randint(1, 3)
    duree = random.randint(1, 10)
    prix = round(random.uniform(5, 50), 2)
    penalite = round(random.uniform(0, 10), 2)
    date_debut = faker.date_this_year()
    date_retour_prevu = date_debut + timedelta(days=duree)
    date_retournee = date_retour_prevu + timedelta(days=random.choice([0, 1, -1]))
    cursor.execute("""
        INSERT INTO Location_jeux (id_location, id_jeu, Quantite, Duree, Prix, Penalite, Date_debut, Date_retour_prevu, Date_retournee)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        id_location, id_jeu, quantite, duree, prix,
        penalite, date_debut, date_retour_prevu, date_retournee
    ))

# Factures
facture_ids = []
for id_location in location_ids[:NB_ENTREES]:
    date_facture = faker.date_this_year()
    montant = round(random.uniform(20, 100), 2)
    cursor.execute(
        "INSERT INTO Factures (id_location, Date_facture, montant_total) VALUES (%s, %s, %s)",
        (id_location, date_facture, montant)
    )
    facture_ids.append(cursor.lastrowid)

# Paiments
for _ in range(NB_ENTREES):
    id_facture = random.choice(facture_ids)
    id_user = random.choice(user_ids)
    no_carte = faker.credit_card_number()
    banque = random.choice(['RBC', 'Desjardins', 'National Bank', 'Tangerine', 'BMO'])
    date_paiement = faker.date_this_year()
    cursor.execute("""
        INSERT INTO Paiments (id_facture, id_user, No_carte, Banque, Date_paiment)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_facture, id_user, no_carte, banque, date_paiement))

conn.commit()
print(" 300 entrées insérées dans chaque table avec succès.")

# ----------- Récupération des jeux par catégorie -----------
def get_jeux_par_catégorie(categorie):
    requete = "SELECT Nom FROM jeux WHERE Categorie= %s;"
    cursor.execute(requete, (categorie,))
    resultat = cursor.fetchall()
    return [tuple[0] for tuple in resultat] 



# ----------- Application Flask -----------
app = Flask(__name__)

@app.route('/')
def main():
    return render_template('acceuil.html')

@app.route('/liste')
def liste():
    return render_template('classiques.html', liste=get_jeux_par_catégorie('Classique'))

@app.route('/console')
def console():
    return render_template('consoles.html', liste=get_jeux_par_catégorie('Console'))

@app.route('/ordinateur')
def ordinateur():
    return render_template('ordinateur.html', liste=get_jeux_par_catégorie('Ordinateur'))

@app.route('/equipement')
def equipement():
    return render_template('equipement.html', liste=get_jeux_par_catégorie('Equipement'))



if __name__ == '__main__':
    app.run(debug=True, port=8080)