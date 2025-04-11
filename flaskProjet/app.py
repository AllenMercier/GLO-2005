from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import pymysql.cursors
import os
from dotenv import load_dotenv
from passlib.hash import sha256_crypt
import csv



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
        try:
            query = "SELECT Email, Nom, Prenom, Mot_de_passe FROM Utilisateurs WHERE Email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            if user is None:
                error = "Utilisateur non trouvé."
            elif not sha256_crypt.verify(password, user["Mot_de_passe"]):
                error = "Mot de passe incorrect."
            else:
                session["user_email"] = user["Email"]
                session["user_name"] = f"{user['Prenom']} {user['Nom']}"
                flash("Connexion réussie !", "success")
                return redirect(url_for("main"))
        except Exception as e:
            error = f"Une erreur s'est produite : {str(e)}"
    return render_template("login.html", error=error)

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            # Récupérer les données du formulaire
            nom = request.form.get("nom")
            prenom = request.form.get("prenom")
            email = request.form.get("email")
            date_naissance = request.form.get("date_naissance")
            mot_de_passe = request.form.get("mot_de_passe")
            statut = request.form.get("statut")  # 1 pour actif, 0 pour inactif

            # Vérifier que tous les champs sont remplis
            if not all([nom, prenom, email, date_naissance, mot_de_passe, statut]):
                flash("Tous les champs sont obligatoires.", "error")
                return redirect(url_for("register"))

            # Vérifier si l'email existe déjà
            cursor.execute("SELECT Email FROM Utilisateurs WHERE Email = %s", (email,))
            if cursor.fetchone():
                flash("Cet email est déjà utilisé. Veuillez en choisir un autre.", "error")
                return redirect(url_for("register"))

            # Hachage du mot de passe avec passlib
            hashed_password = sha256_crypt.hash(mot_de_passe)

            # Insérer les données dans la base de données
            cursor.execute("""
                INSERT INTO Utilisateurs (Nom, Prenom, Email, Date_de_naissance, Mot_de_passe, Statut)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nom, prenom, email, date_naissance, hashed_password, statut))
            conn.commit()

            flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            # Gestion des erreurs
            flash(f"Une erreur s'est produite lors de l'inscription : {str(e)}", "error")
            return redirect(url_for("register"))
    
    return render_template("Inscription.html")

@app.route('/ajouter_au_panier', methods=["POST"])
def ajouter_au_panier():
     if "user_email" not in session:
         flash("Vous devez être connecté.", "error")
         return redirect(url_for("login"))
 
     try:
         id_jeu = str(request.form.get("id_jeu")) 
         quantite = max(1, int(request.form.get("quantite", 1)))
         action = request.form.get("action", "ajouter_panier")
 
         cursor.execute("SELECT Nom, Quantite, Prix FROM Jeux WHERE id_jeu = %s", (id_jeu,))
         jeu = cursor.fetchone()
         
         if not jeu:
             flash("Jeu non trouvé.", "error")
             return redirect(url_for("acheter"))
 
         if quantite > jeu["Quantite"]:
             flash("Stock insuffisant.", "error")
             return redirect(url_for("acheter", id_jeu=id_jeu))
 
         if action == "ajouter_panier":
             if "panier" not in session:
                 session["panier"] = {}
             
             session["panier"][id_jeu] = session["panier"].get(id_jeu, 0) + quantite
             session.modified = True  
             
             flash(f"{quantite} {jeu['Nom']} ajouté(s) au panier", "success")
             return redirect(url_for("panier"))
 
 
     except ValueError:
         flash("Données invalides", "error")
         return redirect(url_for("acheter"))
     except Exception as e:
         app.logger.error(f"Erreur panier: {str(e)}")
         flash("Erreur technique", "error")
         return redirect(url_for("acheter"))
     
@app.route('/panier')
def panier():
     if "user_email" not in session:
         return redirect(url_for("login"))
 
     panier = session.get("panier", {})
     app.logger.info(f"DEBUG - Panier session: {panier}") 
 
     try:
         if panier:
             ids = tuple(int(id) for id in panier.keys())
             cursor.execute("""
                 SELECT id_jeu, Nom, Prix, Quantite 
                 FROM Jeux 
                 WHERE id_jeu IN %s
             """, (ids,))
             
             jeux = {str(jeu["id_jeu"]): jeu for jeu in cursor.fetchall()}
             
             articles = [
                 {
                     "id_jeu": id_jeu,
                     "Nom": jeux[id_jeu]["Nom"],
                     "Prix": jeux[id_jeu]["Prix"],
                     "quantite_panier": quantite,
                     "sous_total": quantite * jeux[id_jeu]["Prix"]
                 }
                 for id_jeu, quantite in panier.items()
                 if id_jeu in jeux
             ]
             
             total = sum(art["sous_total"] for art in articles)
         else:
             articles = []
             total = 0
 
         return render_template("panier.html", 
                                articles=articles,
                                total_panier=total)
 
     except Exception as e:
         app.logger.error(f"Erreur panier: {str(e)}")
         return render_template("panier.html", articles=[], total_panier=0)
     
@app.route('/supprimer_du_panier/<id>', methods=["POST"])
def supprimer_du_panier(id):
     panier = session.get("panier", {})
     
     if id in panier:
         del panier[id]
         session["panier"] = panier
         session.modified = True
         flash("Article supprimé du panier.", "success")
     else:
         flash("Article introuvable dans le panier.", "error")
     
     return redirect(url_for("panier"))
     
@app.route('/paiement', methods=["GET", "POST"])
def paiement():
    if "user_email" not in session:
        flash("Vous devez être connecté pour effectuer un paiement.", "error")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        panier = session.get("panier", {})
        for id_jeu, quantite in panier.items():
            cursor.execute("SELECT Quantite FROM Jeux WHERE id = %s", (id_jeu,))
            jeu = cursor.fetchone()
            if not jeu or quantite > jeu["Quantite"]:
                flash("Stock insuffisant pour un ou plusieurs articles.", "error")
                return redirect(url_for("panier"))
            
            cursor.execute(
                "UPDATE Jeux SET Quantite = Quantite - %s WHERE id = %s",
                (quantite, id_jeu)
            )
        
        session.pop("panier", None)
        conn.commit()
        flash("Paiement effectué avec succès !", "success")
        return redirect(url_for("acheter"))
    
    return render_template("paiement.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("main"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
