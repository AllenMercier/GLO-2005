from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import pymysql.cursors
import os
from dotenv import load_dotenv
import hashlib

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "maCleSecrete")

try:
    conn = pymysql.connect(
        host=os.environ.get("HOST"),
        user=os.environ.get("USER"),
        password=os.environ.get("PASSWORD"),
        db=os.environ.get("DATABASE"),
        cursorclass=pymysql.cursors.DictCursor
    )
except Exception as e:
    print("Erreur de connexion à la base de données :", e)
    raise

cursor = conn.cursor()

@app.route('/')
def main():
    return render_template('acceuil.html')

@app.route('/acheter', methods=["GET", "POST"])
def acheter():
    game_id = request.args.get("id")
    if game_id:
        query = "SELECT * FROM Jeux WHERE id = %s;"
        cursor.execute(query, (game_id,))
        jeu = cursor.fetchone()
        if not jeu:
            flash("Jeu non trouvé.", "error")
            return redirect(url_for("acheter"))
        if request.method == "POST":
            try:
                quantite = int(request.form.get("quantite"))
                if quantite < 1 or quantite > jeu["Quantite"]:
                    flash("Quantité invalide.", "error")
                else:
                    flash(f"Achat de {quantite} exemplaire(s) de {jeu['Nom']} confirmé.", "success")
                    return redirect(url_for("acheter"))
            except Exception as e:
                flash(f"Une erreur est survenue : {str(e)}", "error")
        return render_template("acheter_detail.html", jeu=jeu)
    else:
        query = "SELECT * FROM Jeux;"
        cursor.execute(query)
        jeux = cursor.fetchall()
        categories = ['Classique', 'Console', 'Ordinateur', 'Equipement']
        jeux_par_categorie = {}
        for cat in categories:
            jeux_par_categorie[cat] = [jeu for jeu in jeux if jeu["Categorie"] == cat]
        return render_template("acheter_liste.html", jeux_par_categorie=jeux_par_categorie)

@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        try:
            query = "SELECT id, Nom, Prenom, Mot_de_passe FROM Utilisateurs WHERE Email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            if user is None:
                error = "Utilisateur non trouvé."
            elif user["Mot_de_passe"] != hashed_password:
                error = "Mot de passe incorrect."
            else:
                session["user_id"] = user["id"]
                session["user_name"] = f"{user['Prenom']} {user['Nom']}"
                flash("Connexion réussie !", "success")
                return redirect(url_for("main"))
        except Exception as e:
            error = f"Une erreur s'est produite : {str(e)}"
    return render_template("login.html", error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("main"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
