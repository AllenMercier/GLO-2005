from typing import Any  # Import optionnel pour des annotations de type (non utilisé ici)
from flask import Flask, render_template  # Importation de Flask et de la fonction de rendu de template HTML
import pymysql  # Bibliothèque de connexion à MySQL
import pymysql.cursors  # Module de gestion de curseurs MySQL
from faker import Faker  # Bibliothèque pour générer des données fictives
import random  # Module pour les tirages aléatoires
from dotenv import load_dotenv  # Pour charger les variables d’environnement depuis un fichier .env
from datetime import timedelta  # Pour effectuer des opérations sur les dates
import os  # Pour interagir avec les variables d’environnement du système
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import pymysql.cursors
import os
from dotenv import load_dotenv
import hashlib

# Chargement des variables d’environnement (.env)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "maCleSecrete")

try:
    conn = pymysql.connect(
        host=os.environ.get("HOST"),
        user=os.environ.get("USER"),
        password=os.environ.get("PASSWORD"),
        db=os.environ.get("DATABASE"),
        cursorclass=pymysql.cursors.DictCursor  # Permet de récupérer les résultats sous forme de dictionnaire
    )
except Exception as e:
    print("Erreur de connexion à la base de données :", e)
    raise

cursor = conn.cursor() 

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

@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Hachage du mot de passe soumis
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        try:
            # Requête pour retrouver l'utilisateur par email
            query = "SELECT id, Nom, Prenom, Mot_de_passe FROM Utilisateurs WHERE Email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            if user is None:
                error = "Utilisateur non trouvé."
            elif user["Mot_de_passe"] != hashed_password:
                error = "Mot de passe incorrect."
            else:
                # Connexion réussie : stockage des informations dans la session
                session["user_id"] = user["id"]
                session["user_name"] = f"{user['Prenom']} {user['Nom']}"
                flash("Connexion réussie !", "success")
                return redirect(url_for("main"))
        except Exception as e:
            error = f"Une erreur s'est produite : {str(e)}"
            app.logger.error("Erreur lors du login : %s", str(e))
    return render_template("login.html", error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("main"))



# Lancement de l’application Flask en mode debug sur le port 8080
if __name__ == '__main__':
    app.run(debug=True, port=8080)
