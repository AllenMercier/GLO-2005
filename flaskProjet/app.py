import os
import stripe
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

# Configuration de Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_votreCleSecrete")

# Helpers pour les tests
def get_db():
    return conn

def get_cursor():
    return conn.cursor()

@app.route('/check-stripe')
def check_stripe():
    try:
        # Tester la connexion à Stripe
        stripe.PaymentIntent.list(limit=1)
        return "Configuration Stripe OK"
    except Exception as e:
        return f"Erreur Stripe: {str(e)}"

@app.route('/')
def main():
    return render_template('acceuil.html')

@app.route('/acheter')
def acheter():
    # Modifier cette requête pour ne pas utiliser la table Categories
    cursor.execute("""
        SELECT * FROM Jeux
    """)
    jeux = cursor.fetchall()
    
    # Regrouper les jeux - sans catégorie
    jeux_par_categorie = {'Tous les jeux': jeux}
    
    return render_template('acheter_liste.html', jeux_par_categorie=jeux_par_categorie)

@app.route('/acheter/<int:id>', methods=['GET', 'POST'])
def acheter_detail(id):
    print(f"Route acheter_detail appelée avec id={id}, method={request.method}")
    
    if request.method == 'POST':
        print("POST détecté, tentative de création de session Stripe")
        try:
            # Récupérer les informations du jeu
            cursor.execute("SELECT * FROM Jeux WHERE id_jeu = %s", (id,))
            jeu = cursor.fetchone()
            
            if not jeu:
                flash("Ce jeu n'existe pas", 'error')
                return redirect(url_for('main'))
                
            # Vérifier le stock
            if jeu['Quantite'] <= 0:
                flash("Ce jeu n'est plus en stock", 'error')
                return redirect(url_for('main'))
                
            # Créer la session de paiement Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': jeu['Nom'],
                            'description': f"Jeu vidéo: {jeu['Nom']}",
                        },
                        'unit_amount': int(float(jeu['Prix']) * 100),  # Stripe utilise les centimes
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.host_url + f'paiement/success/{id}',
                cancel_url=request.host_url + 'acheter',
            )
            
            print(f"Session Stripe créée: {checkout_session.id}")
            print(f"URL de redirection: {checkout_session.url}")
            
            # Rediriger vers la page de paiement Stripe
            return redirect(checkout_session.url, code=303)
            
        except Exception as e:
            print(f"Erreur Stripe: {str(e)}")
            flash(f"Erreur lors du paiement: {str(e)}", 'error')
            return redirect(url_for('main'))
    else:
        # GET request - afficher le détail du jeu
        cursor.execute("SELECT * FROM Jeux WHERE id_jeu = %s", (id,))
        jeu = cursor.fetchone()
        if not jeu:
            flash("Ce jeu n'existe pas", 'error')
            return redirect(url_for('main'))
        return render_template('acheter_detail.html', jeu=jeu)

@app.route('/paiement/success/<int:id>')
def paiement_success(id):
    try:
        # Récupérer les informations du jeu
        cursor.execute("SELECT * FROM Jeux WHERE id_jeu = %s", (id,))
        jeu = cursor.fetchone()
        
        if not jeu:
            flash("Le jeu n'existe pas", 'error')
            return redirect(url_for('main'))
            
        # Mettre à jour le stock
        cursor.execute("UPDATE Jeux SET Quantite = Quantite - 1 WHERE id_jeu = %s AND Quantite > 0", (id,))
        
        # Si utilisateur connecté, enregistrer l'achat
        if 'user_email' in session:
            cursor.execute("""
                INSERT INTO achats (email_utilisateur, id_jeu, date_achat) 
                VALUES (%s, %s, NOW())
            """, (session['user_email'], id))
        
        flash(f"Paiement réussi pour {jeu['Nom']} !", 'success')
    except Exception as e:
        print(f"Erreur lors de la finalisation: {str(e)}")
        flash(f"Erreur lors de la finalisation de l'achat: {str(e)}", 'error')
        
    return redirect(url_for('main'))

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

@app.route('/panier')
def panier():
    return render_template('panier.html')

# Implémentation de la route pour le paiement du panier
@app.route('/paiement', methods=['POST'])
def paiement():
    try:
        data = request.json
        if not data or len(data) == 0:
            return jsonify({'error': 'Panier vide'}), 400
            
        line_items = []
        total_amount = 0
        
        for item in data:
            # Vérifier le stock disponible
            cursor.execute("""
                SELECT Nom, Prix, Quantite FROM Jeux 
                WHERE id_jeu = %s
            """, (item['id'],))
            jeu = cursor.fetchone()
            
            if not jeu:
                return jsonify({'error': f'Jeu non trouvé: {item["name"]}'}), 400
                
            if jeu['Quantite'] < item['quantity']:
                return jsonify({'error': f'Stock insuffisant pour {jeu["Nom"]}'}), 400
                
            # Ajouter l'article à la liste
            line_items.append({
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': jeu['Nom'],
                    },
                    'unit_amount': int(float(jeu['Prix']) * 100),  # En centimes
                },
                'quantity': item['quantity'],
            })
            total_amount += float(jeu['Prix']) * item['quantity']
        
        # Créer la session de paiement Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.host_url + 'paiement/panier/success',
            cancel_url=request.host_url + 'panier',
        )
        
        return jsonify({'checkout_url': checkout_session.url})
        
    except Exception as e:
        print(f"Erreur paiement: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/paiement/panier/success')
def panier_success():
    try:
        # Dans ce cas, nous ne pouvons pas mettre à jour le stock directement car
        # nous n'avons pas d'ID spécifique (le panier peut contenir plusieurs articles)
        # La solution est d'utiliser les webhooks Stripe pour une implémentation complète
        
        # Pour l'exemple, affichons simplement un message de succès
        flash("Paiement réussi ! Vos articles seront bientôt expédiés.", "success")
        
        # En production, vous devriez:
        # 1. Vérifier la session Stripe pour confirmer le paiement
        # 2. Mettre à jour le stock dans la base de données
        # 3. Enregistrer l'historique des achats
        # 4. Envoyer un email de confirmation, etc.
    except Exception as e:
        flash(f"Erreur lors de la finalisation: {str(e)}", "error")
    
    return redirect(url_for('main'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("main"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
