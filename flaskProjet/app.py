from typing import Any  # Import optionnel pour des annotations de type (non utilisé ici)
from flask import Flask, render_template  # Importation de Flask et de la fonction de rendu de template HTML
import pymysql  # Bibliothèque de connexion à MySQL
import pymysql.cursors  # Module de gestion de curseurs MySQL
from faker import Faker  # Bibliothèque pour générer des données fictives
import random  # Module pour les tirages aléatoires
from dotenv import load_dotenv  # Pour charger les variables d’environnement depuis un fichier .env
from datetime import timedelta  # Pour effectuer des opérations sur les dates
import os  # Pour interagir avec les variables d’environnement du système

# Chargement des variables d’environnement (.env)
load_dotenv()

# Connexion à la base de données MySQL à partir des variables d’environnement
conn = pymysql.connect(
    host=os.environ.get("HOST"),
    user=os.environ.get("USER"),
    password=os.environ.get("PASSWORD"),
    db=os.environ.get("DATABASE")
)
cursor = conn.cursor()  # Création du curseur pour exécuter les requêtes SQL

# ----------- Peuplement de la base -----------
faker = Faker()  # Instanciation de Faker
NB_ENTREES = 300  # Nombre de lignes à insérer dans chaque table

# Insertion d'utilisateurs fictifs
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
    user_ids.append(cursor.lastrowid)  # Récupération de l’ID inséré

# Insertion de jeux fictifs
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
    
    # Vérifie si cette combinaison nom/catégorie existe déjà dans la BD
    cursor.execute("SELECT COUNT(*) FROM Jeux WHERE Nom = %s AND Categorie = %s", (nom_jeu, categorie))
    if cursor.fetchone()[0] > 0:
        continue
    
    used_pairs.add(pair)
    
    cursor.execute(
        "INSERT INTO Jeux (Nom, Categorie, Prix, Quantite) VALUES (%s, %s, %s, %s)",
        (nom_jeu, categorie, prix, quantite)
    )    
    id_jeu = cursor.lastrowid
    jeu_ids.append(id_jeu)

# Insertion de locations liées à des utilisateurs
location_ids = []
for _ in range(NB_ENTREES):
    id_user = random.choice(user_ids)
    cursor.execute("INSERT INTO Locations (id_user) VALUES (%s)", (id_user,))
    location_ids.append(cursor.lastrowid)

# Insertion dans Location_jeux avec des paires (id_location, id_jeu) uniques
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

# Insertion de factures liées aux locations
facture_ids = []
for id_location in location_ids[:NB_ENTREES]:
    date_facture = faker.date_this_year()
    montant = round(random.uniform(20, 100), 2)
    cursor.execute(
        "INSERT INTO Factures (id_location, Date_facture, montant_total) VALUES (%s, %s, %s)",
        (id_location, date_facture, montant)
    )
    facture_ids.append(cursor.lastrowid)

# Insertion de paiements aléatoires liés à des factures et utilisateurs
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

conn.commit()  # Validation des transactions
print(" 300 entrées insérées dans chaque table avec succès.")  # Message de confirmation

# ----------- Récupération des jeux par catégorie -----------

# Fonction pour récupérer les noms de jeux selon une catégorie donnée
def get_jeux_par_catégorie(categorie):
    requete = "SELECT Nom FROM jeux WHERE Categorie= %s;"
    cursor.execute(requete, (categorie,))
    resultat = cursor.fetchall()
    return [tuple[0] for tuple in resultat]  # Retourne une liste des noms de jeux

# ----------- Application Flask -----------

app = Flask(__name__)  # Création de l'application Flask

@app.route('/')  # Page d’accueil
def main():
    return render_template('acceuil.html')

@app.route('/liste')  # Route pour les jeux classiques
def liste():
    return render_template('classiques.html', liste=get_jeux_par_catégorie('Classique'))

@app.route('/console')  # Route pour les jeux de console
def console():
    return render_template('consoles.html', liste=get_jeux_par_catégorie('Console'))

@app.route('/ordinateur')  # Route pour les jeux d’ordinateur
def ordinateur():
    return render_template('ordinateur.html', liste=get_jeux_par_catégorie('Ordinateur'))

@app.route('/equipement')  # Route pour les équipements
def equipement():
    return render_template('equipement.html', liste=get_jeux_par_catégorie('Equipement'))

# Lancement de l’application Flask en mode debug sur le port 8080
if __name__ == '__main__':
    app.run(debug=True, port=8080)
