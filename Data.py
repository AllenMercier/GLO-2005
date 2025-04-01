import os  # Module permettant d’accéder aux variables d’environnement du système

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
