import os
import stripe
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from passlib.hash import sha256_crypt
from datetime import datetime

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
            
        # Si utilisateur connecté, utiliser la procédure stockée louer
        if 'user_email' in session:
            # Obtenir l'id utilisateur à partir de l'email
            cursor.execute("SELECT id_user FROM Utilisateurs WHERE Email = %s", (session['user_email'],))
            user_data = cursor.fetchone()
            
            if user_data:
                try:
                    # Appeler la procédure stockée louer
                    cursor.callproc('louer', (user_data['id_user'], id, 1))
                    flash(f"Location réussie pour {jeu['Nom']} ! À retourner dans 2 jours.", 'success')
                except pymysql.err.InternalError as e:
                    error_msg = str(e)
                    if "45000" in error_msg:  # Code d'erreur personnalisé dans la procédure
                        # Extraire le message d'erreur personnalisé
                        error_msg = error_msg.split("'")[-2] if "'" in error_msg else error_msg
                        flash(f"Impossible de louer : {error_msg}", 'error')
                    else:
                        raise e
            else:
                flash("Utilisateur non trouvé", 'error')
        else:
            flash("Vous devez être connecté pour louer un jeu", 'error')
            return redirect(url_for('login'))
        
    except Exception as e:
        print(f"Erreur lors de la finalisation: {str(e)}")
        flash(f"Erreur lors de la finalisation de la location: {str(e)}", 'error')
        
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
            # Générer un nouvel ID de session unique
            import uuid
            session.clear()  # Effacer toute session existante
            session["_id"] = str(uuid.uuid4())  # ID unique pour cette session
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

@app.route('/ajouter-au-panier/<int:id>', methods=['POST'])
def ajouter_au_panier(id):
    # Vérifier si le produit existe
    cursor.execute("SELECT id_jeu, Nom, Prix, Quantite FROM Jeux WHERE id_jeu = %s", (id,))
    jeu = cursor.fetchone()
    
    if not jeu:
        flash("Ce jeu n'existe pas", "error")
        return redirect(url_for('acheter'))
    
    # Vérifier le stock
    if jeu['Quantite'] <= 0:
        flash("Ce jeu n'est plus en stock", "error")
        return redirect(url_for('acheter'))
    
    # Initialiser le panier s'il n'existe pas
    if 'panier' not in session:
        session['panier'] = []
    
    # Récupérer le panier actuel
    panier = session.get('panier', [])
    
    # Afficher le panier actuel pour déboguer
    print("Panier avant ajout:", panier)
    
    # Vérifier si l'article est déjà dans le panier
    item_exists = False
    total_items = sum(item.get('quantity', 0) for item in panier)
    
    # Vérifier la limite de 5 articles
    if total_items >= 5:
        flash("Vous ne pouvez pas avoir plus de 5 articles dans votre panier", "error")
        return redirect(url_for('acheter_detail', id=id))
    
    # Chercher si l'article existe déjà dans le panier - utiliser l'ID pour la comparaison
    for i, item in enumerate(panier):
        # S'assurer que la comparaison est faite avec des entiers
        if int(item.get('id')) == int(id):
            # Vérifier si l'augmentation dépasse la limite ou le stock
            if total_items >= 5:
                flash("Limite de 5 articles atteinte", "error")
            elif item['quantity'] >= jeu['Quantite']:
                flash("Stock maximum atteint pour cet article", "error")
            else:
                panier[i]['quantity'] += 1
                flash(f"{jeu['Nom']} ajouté au panier", "success")
            
            item_exists = True
            break
    
    # Si l'article n'existe pas dans le panier, l'ajouter
    if not item_exists:
        panier.append({
            'id': int(id),  # Stocker comme entier pour éviter les problèmes de comparaison
            'name': jeu['Nom'],
            'price': float(jeu['Prix']),
            'quantity': 1
        })
        flash(f"{jeu['Nom']} ajouté au panier", "success")
    
    # Afficher le panier après ajout pour déboguer
    print("Panier après ajout:", panier)
    
    # Mettre à jour la session
    session['panier'] = panier
    
    # Rediriger vers la page précédente ou la liste des jeux
    referer = request.referrer
    if referer:
        return redirect(referer)
    return redirect(url_for('acheter'))

@app.route('/supprimer-panier/<int:id>')
def supprimer_panier(id):
    if 'panier' in session:
        panier = session['panier']
        # Convertir id en int pour la comparaison
        panier = [item for item in panier if item['id'] != id]
        session['panier'] = panier
        flash("Article supprimé du panier", "success")
    
    return redirect(url_for('panier'))

@app.route('/vider-panier')
def vider_panier():
    if 'panier' in session:
        session.pop('panier')
        flash("Panier vidé", "success")
    
    return redirect(url_for('panier'))

@app.route('/vider-panier-api', methods=['POST'])
def vider_panier_api():
    if 'panier' in session:
        session.pop('panier')
        print("Session panier vidée via API")
    return jsonify({"success": True}), 200

@app.route('/panier')
def panier():
    # Récupérer le panier depuis la session
    panier_items = session.get('panier', [])
    
    # Si le panier est vide côté serveur mais qu'il a un compteur (potentiellement désynchronisé)
    if not panier_items and session.get('cart_count', 0) > 0:
        # Réinitialiser le compteur du panier côté serveur
        session['cart_count'] = 0
        print("Réinitialisation du compteur de panier côté serveur")
    
    # Calculer le total
    total_panier = sum(item['price'] * item['quantity'] for item in panier_items) if panier_items else 0
    
    # Debug: Afficher le contenu du panier dans la console
    print(f"Panier items: {panier_items}")
    print(f"Total panier: {total_panier}")
    
    return render_template('panier.html', panier_items=panier_items, total_panier=total_panier)

@app.route('/paiement', methods=['POST'])
def paiement():
    try:
        # Déboguer le contenu de la requête
        print("Form data:", request.form)
        
        # Vérifier si l'utilisateur est connecté
        if 'user_email' not in session:
            flash("Veuillez vous connecter pour finaliser l'achat", "error")
            return redirect(url_for('login'))
        
        # Récupérer les items du panier depuis le formulaire
        items_from_form = request.form.getlist('items[]')
        print("Items from form:", items_from_form)
        
        if not items_from_form:
            flash("Votre panier est vide", "error")
            return redirect(url_for('panier'))
        
        # Traiter les données du formulaire
        panier_items = []
        for item_str in items_from_form:
            parts = item_str.split(':')
            if len(parts) == 4:  # Vérifier que le format est correct
                id, name, price, quantity = parts
                panier_items.append({
                    'id': int(id),
                    'name': name,
                    'price': float(price),
                    'quantity': int(quantity)
                })
        
        if not panier_items:
            flash("Erreur lors du traitement des articles du panier", "error")
            return redirect(url_for('panier'))
        
        # Créer les line_items pour Stripe
        line_items = []
        for item in panier_items:
            line_items.append({
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': item['name'],
                    },
                    'unit_amount': int(float(item['price']) * 100),  # Stripe utilise les centimes
                },
                'quantity': item['quantity'],
            })
        
        # Créer la session Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.host_url + 'paiement/panier/success',
            cancel_url=request.host_url + 'panier',
        )
        
        # Stocker les IDs des articles dans la session pour pouvoir les traiter après le paiement
        session['pending_purchase'] = [{'id': item['id'], 'quantity': item['quantity']} for item in panier_items]
        
        # Rediriger vers Stripe
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        print(f"Erreur paiement: {str(e)}")
        flash(f"Erreur lors du paiement: {str(e)}", "error")
        return redirect(url_for('panier'))

@app.route('/paiement/panier/success')
def panier_success():
    try:
        # Récupérer les articles en attente de la session
        pending_items = session.get('pending_purchase', [])
        
        if not pending_items:
            flash("Aucun article à traiter", "error")
            return redirect(url_for('panier'))
            
        # Si utilisateur connecté, utiliser la procédure stockée louer pour chaque article
        if 'user_email' in session:
            # Obtenir l'id utilisateur à partir de l'email
            cursor.execute("SELECT id_user FROM Utilisateurs WHERE Email = %s", (session['user_email'],))
            user_data = cursor.fetchone()
            
            if user_data:
                user_id = user_data['id_user']
                success_count = 0
                error_messages = []
                
                # Traiter chaque article individuellement avec la procédure louer
                for item in pending_items:
                    id_jeu = item['id']
                    quantite = item['quantity']
                    
                    try:
                        # Appeler la procédure stockée louer pour cet article
                        cursor.callproc('louer', (user_id, id_jeu, quantite))
                        success_count += 1
                    except pymysql.err.InternalError as e:
                        error_msg = str(e)
                        if "45000" in error_msg:  # Code d'erreur personnalisé dans la procédure
                            error_msg = error_msg.split("'")[-2] if "'" in error_msg else error_msg
                            error_messages.append(f"Erreur pour l'article {id_jeu}: {error_msg}")
                        else:
                            raise e
                
                # Afficher un message de succès ou d'erreur
                if success_count > 0:
                    flash(f"Location réussie pour {success_count} article(s) ! À retourner dans 2 jours.", "success")
                
                # Afficher les erreurs s'il y en a
                for error in error_messages:
                    flash(error, "error")
            else:
                flash("Utilisateur non trouvé", "error")
        else:
            flash("Vous devez être connecté pour louer des jeux", "error")
            return redirect(url_for('login'))
        
        # Vider le panier et les articles en attente
        if 'panier' in session:
            session.pop('panier')
        if 'pending_purchase' in session:
            session.pop('pending_purchase')
        
    except Exception as e:
        print(f"Erreur lors de la finalisation: {str(e)}")
        flash(f"Erreur lors de la finalisation de la location: {str(e)}", "error")
    
    return redirect(url_for('main'))

@app.route('/mes-locations')
def mes_locations():
    # Vérifier si l'utilisateur est connecté
    if 'user_email' not in session:
        flash("Veuillez vous connecter pour voir vos locations.", "error")
        return redirect(url_for('login'))
    
    try:
        # Obtenir l'id_user à partir de l'email
        cursor.execute("SELECT id_user FROM Utilisateurs WHERE Email = %s", (session['user_email'],))
        user_data = cursor.fetchone()
        
        if not user_data:
            flash("Utilisateur non trouvé.", "error")
            return redirect(url_for('main'))
        
        user_id = user_data['id_user']
        
        # Récupérer toutes les locations de l'utilisateur
        cursor.execute("""
            SELECT l.id_location, lj.Date_debut, lj.Date_retour_prevu, lj.Date_retournee, 
                   j.Nom as nom_jeu, j.Prix as prix_jeu, lj.Prix as prix_location,
                   lj.Quantite, lj.Duree,
                   CASE 
                       WHEN lj.Date_retournee IS NOT NULL THEN 'terminée'
                       WHEN lj.Date_retour_prevu < CURDATE() THEN 'en retard'
                       ELSE 'active'
                   END as status
            FROM Locations l
            JOIN Location_jeux lj ON l.id_location = lj.id_location
            JOIN Jeux j ON lj.id_jeu = j.id_jeu
            WHERE l.id_user = %s
            ORDER BY 
                CASE 
                    WHEN lj.Date_retournee IS NULL AND lj.Date_retour_prevu >= CURDATE() THEN 0
                    WHEN lj.Date_retournee IS NULL AND lj.Date_retour_prevu < CURDATE() THEN 1
                    ELSE 2 
                END,
                lj.Date_debut DESC
        """, (user_id,))
        
        locations = cursor.fetchall()
        
        return render_template('mes_locations.html', locations=locations)
        
    except Exception as e:
        print(f"Erreur lors de l'accès aux locations: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Une erreur s'est produite: {str(e)}", "error")
        return redirect(url_for('main'))

@app.route('/retourner-location', methods=['POST'])
def retourner_location():
    # Vérifier si l'utilisateur est connecté
    if 'user_email' not in session:
        flash("Veuillez vous connecter pour retourner un jeu.", "error")
        return redirect(url_for('login'))
    
    try:
        id_location = request.form.get('id_location')
        
        if not id_location:
            flash("ID de location manquant", "error")
            return redirect(url_for('mes_locations'))
        
        # Vérifier que la location appartient bien à cet utilisateur
        cursor.execute("""
            SELECT l.*, lj.id_jeu, lj.Date_retour_prevu, lj.Date_retournee, lj.Prix as prix_location,
                   lj.Quantite, j.Nom as nom_jeu 
            FROM Locations l
            JOIN Location_jeux lj ON l.id_location = lj.id_location
            JOIN Jeux j ON lj.id_jeu = j.id_jeu
            JOIN Utilisateurs u ON l.id_user = u.id_user
            WHERE l.id_location = %s AND u.Email = %s
        """, (id_location, session['user_email']))
        
        location = cursor.fetchone()
        
        if not location:
            flash("Location non trouvée ou non autorisée", "error")
            return redirect(url_for('mes_locations'))
        
        # Vérifier que la location n'est pas déjà retournée
        if location.get('Date_retournee'):
            flash("Cette location a déjà été retournée", "error")
            return redirect(url_for('mes_locations'))
        
        # Effectuer le retour
        today = datetime.now().date()
        
        # Mettre à jour la date de retour
        cursor.execute("""
            UPDATE Location_jeux 
            SET Date_retournee = %s
            WHERE id_location = %s
        """, (today, id_location))
        
        # Remettre le jeu en stock
        cursor.execute("""
            UPDATE Jeux
            SET Quantite = Quantite + (
                SELECT Quantite FROM Location_jeux WHERE id_location = %s AND id_jeu = %s
            )
            WHERE id_jeu = %s
        """, (id_location, location['id_jeu'], location['id_jeu']))
        
        # Calculer les frais de retard si applicable
        date_retour_prevue = location['Date_retour_prevu']
        if today > date_retour_prevue:
            jours_retard = (today - date_retour_prevue).days
            frais_par_jour = location['prix_location'] * 0.1  # 10% du prix par jour de retard
            frais_retard = frais_par_jour * jours_retard * location['Quantite']
            
            flash(f"Retard de {jours_retard} jour(s). Frais supplémentaires: {frais_retard:.2f}$", "warning")
            
            # Enregistrer les frais de retard (optionnel)
            cursor.execute("""
                INSERT INTO Factures (id_location, Date_facture, montant_total)
                VALUES (%s, %s, %s)
            """, (id_location, today, frais_retard))
        
        flash(f"Merci! Votre jeu '{location['nom_jeu']}' a été retourné avec succès.", "success")
        return redirect(url_for('mes_locations'))
        
    except Exception as e:
        print(f"Erreur lors du retour de location: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Erreur lors du retour: {str(e)}", "error")
        return redirect(url_for('mes_locations'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("main"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
