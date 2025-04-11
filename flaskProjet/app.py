import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from passlib.hash import sha256_crypt

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "maCleSecrete")

# Connexion MySQL
conn = pymysql.connect(
    host=os.environ.get("HOST"),
    user=os.environ.get("USER"),
    password=os.environ.get("PASSWORD"),
    db=os.environ.get("DATABASE"),
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)
cursor = conn.cursor()

# Helpers pour les tests
def get_db():
    return conn

def get_cursor():
    return conn.cursor()

@app.route('/')
def main():
    return render_template('acceuil.html')

@app.route('/acheter', methods=["GET", "POST"])
def acheter():
    game_id = request.args.get("id")
    if game_id:
        # détail d'un jeu
        cursor.execute("SELECT * FROM Jeux WHERE id_jeu = %s;", (game_id,))
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
                flash(f"Une erreur est survenue : {e}", "error")
        return render_template("acheter_detail.html", jeu=jeu)

    # pas de id → GET renvoie page, POST renvoie JSON
    if request.method == "GET":
        cursor.execute("SELECT * FROM Jeux;")
        jeux = cursor.fetchall()
        categories = ['Classique', 'Console', 'Ordinateur', 'Equipement']
        jeux_par_categorie = {cat: [j for j in jeux if j["Categorie"] == cat] for cat in categories}
        return render_template("acheter_liste.html", jeux_par_categorie=jeux_par_categorie)
    else:
        cursor.execute("SELECT * FROM Jeux;")
        jeux = cursor.fetchall()
        return jsonify({"jeux": jeux})

@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        cursor.execute("SELECT Email, Nom, Prenom, Mot_de_passe FROM Utilisateurs WHERE Email = %s", (email,))
        user = cursor.fetchone()
        if user is None:
            error = "Email inconnu"
        elif not sha256_crypt.verify(password, user["Mot_de_passe"]):
            error = "Mot de passe incorrect."
        else:
            session["user_email"] = user["Email"]
            session["user_name"] = f"{user['Prenom']} {user['Nom']}"
            flash("Connexion réussie !", "success")
            return redirect(url_for("main"))
    return render_template("login.html", error=error)

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        email = request.form.get("email")
        date_naissance = request.form.get("date_naissance")
        mot_de_passe = request.form.get("mot_de_passe")
        statut = request.form.get("statut")

        # Tous les champs obligatoires
        if not all([nom, prenom, email, date_naissance, mot_de_passe, statut]):
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for("register"))

        # email déjà utilisé ?
        cursor.execute("SELECT Email FROM Utilisateurs WHERE Email = %s", (email,))
        if cursor.fetchone():
            flash("Email déjà utilisé", "error")
            return redirect(url_for("register"))

        # hachage
        hashed = sha256_crypt.hash(mot_de_passe)
        cursor.execute(
            "INSERT INTO Utilisateurs (Nom, Prenom, Email, Date_de_naissance, Mot_de_passe, Statut) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (nom, prenom, email, date_naissance, hashed, statut)
        )
        flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("login"))

    return render_template("Inscription.html")

@app.route('/ajouter_au_panier', methods=["POST"])
def ajouter_au_panier():
    if "user_email" not in session:
        flash("Vous devez être connecté.", "error")
        return redirect(url_for("login"))

    id_jeu = request.form.get("id_jeu")
    quantite = max(1, int(request.form.get("quantite", 1)))

    cursor.execute("SELECT Nom, Quantite, Prix FROM Jeux WHERE id_jeu = %s", (id_jeu,))
    jeu = cursor.fetchone()
    if not jeu:
        flash("Jeu non trouvé.", "error")
        return redirect(url_for("acheter"))

    if quantite > jeu["Quantite"]:
        flash("Stock insuffisant.", "error")
        return redirect(url_for("acheter", id=id_jeu))

    # ajout panier
    panier = session.setdefault("panier", {})
    panier[id_jeu] = panier.get(id_jeu, 0) + quantite
    session.modified = True

    flash(f"{quantite} {jeu['Nom']} ajouté(s) au panier", "success")
    return redirect(url_for("panier"))

@app.route('/panier')
def panier():
    if "user_email" not in session:
        return redirect(url_for("login"))

    panier = session.get("panier", {})
    articles = []
    total = 0
    if panier:
        ids = tuple(int(i) for i in panier)
        cursor.execute(
            "SELECT id_jeu, Nom, Prix, Quantite FROM Jeux WHERE id_jeu IN %s",
            (ids,)
        )
        jeux = {str(j["id_jeu"]): j for j in cursor.fetchall()}
        for id_jeu, q in panier.items():
            j = jeux.get(id_jeu)
            if j:
                sous = q * j["Prix"]
                articles.append({
                    "id_jeu": id_jeu,
                    "Nom": j["Nom"],
                    "quantite_panier": q,
                    "sous_total": sous
                })
                total += sous

    return render_template("panier.html", articles=articles, total_panier=total)

@app.route('/supprimer_du_panier/<id>', methods=["POST"])
def supprimer_du_panier(id):
    panier = session.get("panier", {})
    if id in panier:
        del panier[id]
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
        panier = session.pop("panier", {})
        for id_jeu, q in panier.items():
            cursor.execute("UPDATE Jeux SET Quantite = Quantite - %s WHERE id_jeu = %s", (q, id_jeu))
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
