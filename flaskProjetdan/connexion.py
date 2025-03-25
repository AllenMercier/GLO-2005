import pymysql
import pymysql.cursors
from pymysql import Connection
from pymysql.cursors import Cursor

connection= pymysql.connect(host="localhost",user="root",password="12345",db="projet_glo_2005", autocommit=True)
cursor = connection.cursor()


    #cursor.close()
    #conn.close()

def select_classique():
    requete = "SELECT id_c, nom, prix  FROM jeux WHERE catégorie = 'classiques'"
    cursor.execute(requete)
    resultat = cursor.fetchall()
    listeC = []
   # numero = []
    for tuple in resultat:

       # if "classiques" == tuple[2]:

            listeC.append(tuple)
           # numero.append(tuple[0])
    #classiques = [entry[0] for entry in cursor.fetchall()]

    return listeC

def insert_todo(text):
    request = f"""INSERT INTO test (choix) VALUES ("{text}");"""
    cursor.execute(request)


def select_todos():
    request = "SELECT text FROM todo;"
    cursor.execute(request)

    todos = [entry[0] for entry in cursor.fetchall()]

    return todos