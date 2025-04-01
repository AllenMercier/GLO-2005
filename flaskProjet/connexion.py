import pymysql  # Importation du module pymysql pour se connecter à une base de données MySQL
import pymysql.cursors  # Importation des curseurs pour l’exécution des requêtes SQL

# Connexion à la base de données MySQL locale avec les identifiants spécifiés
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='K@mwanga17071997',
    db='projet'
)

cursor = conn.cursor()  # Création d’un curseur pour exécuter les requêtes SQL

requete = "SELECT * FROM classiques;"  # Requête SQL pour sélectionner toutes les lignes de la table "classiques"

cursor.execute(requete)  # Exécution de la requête
resultat = cursor.fetchall()  # Récupération de toutes les lignes résultantes de la requête

# Boucle pour parcourir chaque ligne du résultat
for tuple in resultat:
    # Boucle pour afficher chaque attribut de la ligne, séparé par une tabulation
    for attrib in tuple:
        print(attrib + '\t', end='')  # Affiche chaque attribut sur la même ligne avec des tabulations
    print('\n')  # Saut de ligne après chaque tuple

    cursor.close()  # Fermeture du curseur (⚠️ cette ligne est indentée à l’intérieur de la boucle)
    conn.close()    # Fermeture de la connexion à la base de données (⚠️ elle aussi dans la boucle)
