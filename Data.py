import os  # Module permettant d’accéder aux variables d’environnement du système
from datetime import timedelta

import pymysql  # Bibliothèque pour se connecter à une base de données MySQL
from dotenv import load_dotenv  # Permet de charger les variables d’environnement depuis un fichier .env
from sql_utils import run_sql_file, parse_sql  # Fonctions utilitaires pour lire et exécuter des fichiers SQL

from faker import Faker  # Bibliothèque pour générer de fausses données (importée mais non utilisée ici)
import random  # Module pour générer des valeurs aléatoires (également non utilisé ici)

# Définition d'une classe représentant la connexion à la base de données
class Database:
    def __init__(self):
        load_dotenv()  # Chargement des variables d’environnement depuis le fichier .env

        # Lecture des informations de connexion à partir des variables d’environnement
        self.host = os.environ.get("HOST")
        self.port = int(os.environ.get("PORT"))
        self.user = os.environ.get("USER")
        self.database = os.environ.get("DATABASE")
        self.password = os.environ.get("PASSWORD")

        self._open_sql_connection()  # Appel à la méthode privée pour ouvrir la connexion
        self.migration_counter = 0  # Initialisation d’un compteur (non utilisé ici)

    # Méthode privée pour établir la connexion MySQL
    def _open_sql_connection(self):
        self.connection = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.database,
            autocommit=True  # Validation automatique des transactions après chaque requête
        )
        
        print("Connection opened successfully")  # Message de confirmation

        self.cursor = self.connection.cursor()  # Création du curseur pour exécuter les requêtes SQL

# Fonction utilitaire pour exécuter un fichier SQL ligne par ligne
def run_sql_file(cursor, filename, accept_empty=True):
    """
    Exécute chaque instruction d'un fichier .sql

    :param cursor: un curseur pymysql.cursor ouvert
    :param filename: le fichier .sql à exécuter
    :param accept_empty: si vrai, lance une exception si le fichier est vide
    """
    sql_statements = parse_sql(filename)  # Analyse du fichier pour en extraire les instructions SQL

    if len(sql_statements) == 0 and not accept_empty:
        raise IOError(f"File '{filename}' is empty.")  # Lève une erreur si le fichier est vide et que ce n’est pas permis

    for statement in sql_statements:
        cursor.execute(statement)  # Exécution de chaque instruction SQL

# Instanciation de la classe Database → ouverture de la connexion à la base
db = Database()

# Exécution du script SQL pour supprimer les tables existantes
run_sql_file(db.cursor, 'bd_script/drop.sql')

# Exécution du script SQL pour créer les tables
run_sql_file(db.cursor, 'bd_script/up.sql')

print("Tables created successfully")  # Message de confirmation

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
    date_debut = faker.date_this_year()
    date_retour_prevu = date_debut + timedelta(days=duree)
    date_retournee = date_retour_prevu + timedelta(days=random.choice([0, 1, -1]))
    cursor.execute("""
        INSERT INTO Location_jeux (id_location, id_jeu, Quantite, Duree, Prix, Date_debut, Date_retour_prevu, Date_retournee)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        id_location, id_jeu, quantite, duree, prix,
        date_debut, date_retour_prevu, date_retournee
    ))
    
  # Récupérer toutes les entrées de la table Location_jeux
    cursor.execute("SELECT id_location, id_jeu FROM Location_jeux;")
    location_jeux = cursor.fetchall()

    penalites = []
    for entry in location_jeux:
        id_location = entry[0]
        id_jeu = entry[1]
        
        # Vérifier si la paire existe déjà dans Penalites
        cursor.execute("SELECT COUNT(*) FROM Penalites WHERE id_location = %s AND id_jeu = %s", (id_location, id_jeu))
        if cursor.fetchone()[0] > 0:
            continue  # Passer à la prochaine paire si elle existe déjà

        # Générer une pénalité aléatoire (par exemple, entre 0 et 50)
        penalite = round(random.uniform(0, 50), 2)

        # Ajouter les données à la liste
        penalites.append((id_location, id_jeu, penalite))

    # Insérer les pénalités dans la table Penalites
    if penalites:
        cursor.executemany(
            "INSERT INTO Penalites (id_location, id_jeu, Penalite) VALUES (%s, %s, %s);",
            penalites
        )

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