import os
import stripe
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from passlib.hash import sha256_crypt
from datetime import datetime
from functools import wraps

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "maCleSecrete")

# Variable globale pour la connexion à la base de données
conn = None
cursor = None

# Fonction pour assurer une connexion valide à la base de données
def ensure_connection():
    global conn, cursor
    try:
        # Tester si la connexion est active
        if conn is None or not conn.open:
            # Recréer la connexion si elle n'est pas active
            conn = pymysql.connect(
                host=os.environ.get("HOST"),
                user=os.environ.get("USER"),
                password=os.environ.get("PASSWORD"),
                db=os.environ.get("DATABASE"),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            cursor = conn.cursor()
            print("Nouvelle connexion à la base de données établie")
        else:
            # Test simple pour vérifier que la connexion est opérationnelle
            cursor.execute("SELECT 1")
            print("Connexion à la base de données vérifiée et active")
    except pymysql.Error as e:
        # En cas d'erreur, recréer la connexion
        print(f"Erreur de connexion à la base de données: {str(e)}")
        conn = pymysql.connect(
            host=os.environ.get("HOST"),
            user=os.environ.get("USER"),
            password=os.environ.get("PASSWORD"),
            db=os.environ.get("DATABASE"),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        cursor = conn.cursor()
        print("Connexion à la base de données rétablie")

# Initialiser la connexion au lancement de l'application
ensure_connection()

# Configuration de Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_votreCleSecrete")

# Helpers pour les tests
def get_db():
    return conn

def get_cursor():
    return conn.cursor()

# Middleware pour vérifier les retards et bloquer la navigation si nécessaire
def check_late_returns(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ne vérifier que si l'utilisateur est connecté
        if 'user_email' in session:
            # Ne pas bloquer l'accès à la page de paiement des pénalités
            if request.path == '/payer-penalites' or request.path == '/paiement/penalites/success':
                return f(*args, **kwargs)
                
            # Vérifier s'il existe des retards non payés
            user_id = get_user_id_from_email(session['user_email'])
            late_returns = get_unpaid_late_returns(user_id) if user_id else []
            
            if late_returns:
                flash("Vous avez des pénalités de retard à payer avant de pouvoir continuer à naviguer sur le site.", "error")
                session['redirect_after_payment'] = request.path  # Sauvegarder la page demandée
                return redirect(url_for('payer_penalites'))
        
        return f(*args, **kwargs)
    return decorated_function

# Fonction utilitaire pour récupérer l'ID utilisateur à partir de l'email
def get_user_id_from_email(email):
    cursor.execute("SELECT id_user FROM Utilisateurs WHERE Email = %s", (email,))
    user_data = cursor.fetchone()
    return user_data['id_user'] if user_data else None

# Fonction pour récupérer les retards non payés d'un utilisateur
def get_unpaid_late_returns(user_id):
    cursor.execute("""
        SELECT l.id_location, j.Nom as nom_jeu, lj.Date_retour_prevu, 
               DATEDIFF(CURDATE(), lj.Date_retour_prevu) as jours_retard,
               lj.Prix as prix_location, lj.Quantite
        FROM Locations l
        JOIN Location_jeux lj ON l.id_location = lj.id_location
        JOIN Jeux j ON lj.id_jeu = j.id_jeu
        LEFT JOIN Factures f ON l.id_location = f.id_location AND f.montant_total > 0
        LEFT JOIN Paiments p ON f.id_facture = p.id_facture
        WHERE l.id_user = %s 
          AND lj.Date_retournee IS NULL
          AND lj.Date_retour_prevu < CURDATE()
          AND (p.id_paiment IS NULL OR f.id_facture IS NULL)
    """, (user_id,))
    
    late_returns = cursor.fetchall()
    
    # Regrouper les locations en retard par id_location
    locations_by_id = {}
    for late in late_returns:
        if late['id_location'] not in locations_by_id:
            locations_by_id[late['id_location']] = []
        locations_by_id[late['id_location']].append(late)
    
    # Calculer les pénalités: 5$ * nombre maximum de jours de retard par location
    for location_id, items in locations_by_id.items():
        # Trouver le nombre maximum de jours de retard pour cette location
        max_days_late = max(item['jours_retard'] for item in items)
        # Calculer la pénalité: 5$ * jours de retard max (une seule fois par location)
        penalty = 5 * max_days_late
        
        # Appliquer cette pénalité à chaque article dans cette location
        for item in items:
            item['penalite'] = round(penalty, 2)
    
    # Aplatir la liste à nouveau
    return [item for items in locations_by_id.values() for item in items]

# Fonction pour compter le nombre de locations actives d'un utilisateur
def count_active_rentals(user_id):
    cursor.execute("""
        SELECT COUNT(*) as count_active
        FROM Locations l
        JOIN Location_jeux lj ON l.id_location = lj.id_location
        WHERE l.id_user = %s 
          AND lj.Date_retournee IS NULL
    """, (user_id,))
    result = cursor.fetchone()
    return result['count_active'] if result else 0

# Appliquer le middleware à toutes les routes sauf celles spécifiées
@app.before_request
def before_request():
    ensure_connection()
    # Liste des routes exemptées du contrôle des retards
    exempt_routes = ['/login', '/register', '/logout', '/static']
    
    # Ne pas appliquer le middleware aux routes exemptées
    for route in exempt_routes:
        if request.path.startswith(route):
            return None

    # Si l'utilisateur n'est pas connecté, ne pas vérifier les retards
    if 'user_email' not in session:
        return None
        
    # Ne pas bloquer l'accès à la page de paiement des pénalités
    if request.path == '/payer-penalites' or request.path.startswith('/paiement/penalites'):
        return None
        
    # Vérifier s'il existe des retards non payés
    user_id = get_user_id_from_email(session['user_email'])
    late_returns = get_unpaid_late_returns(user_id) if user_id else []
    
    if late_returns:
        flash("Vous avez des pénalités de retard à payer avant de pouvoir continuer à naviguer sur le site.", "error")
        session['redirect_after_payment'] = request.path  # Sauvegarder la page demandée
        return redirect(url_for('payer_penalites'))

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
    
    if request.method == 'POST':
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
            
            # Durée fixe de location (2 jours)
            duree_location = 2
            
            # Récupérer la quantité demandée
            quantite = int(request.form.get('quantite', 1))
            
            # Calculer le prix total pour 2 jours (prix unitaire * durée)
            prix_unitaire = float(jeu['Prix'])
            prix_total = prix_unitaire * duree_location         
            
            # Créer la session de paiement Stripe en utilisant le PRIX TOTAL
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'CAD',
                        'product_data': {
                            'name': f"{jeu['Nom']} - Location {duree_location} jours",
                            'description': f"Location pour {duree_location} jours (Prix journalier: {prix_unitaire}$ × {duree_location} = {prix_total}$)",
                        },
                        'unit_amount': int(prix_total * 100),  # PRIX TOTAL en centimes
                    },
                    'quantity': quantite,
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
        
        # Ajouter la durée et le prix total pour 2 jours
        duree_location = 2
        jeu['prix_total'] = float(jeu['Prix']) * duree_location
        
        return render_template('acheter_detail.html', jeu=jeu, duree_location=duree_location)

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
                    user_id = user_data['id_user']
                    # Appeler la procédure stockée louer
                    cursor.callproc('louer', (user_id, id, 1))
                    
                    # Récupérer l'ID de la dernière facture créée pour cet utilisateur et cette location
                    cursor.execute("""
                        SELECT f.id_facture, l.id_location FROM Factures f
                        JOIN Locations l ON f.id_location = l.id_location
                        WHERE l.id_user = %s
                        ORDER BY f.id_facture DESC LIMIT 1
                    """, (user_id,))
                    facture_data = cursor.fetchone()
                    
                    if facture_data:
                        # Sécuriser les informations de paiement
                        # Ne stocker que les 4 derniers chiffres dans un environnement réel
                        last_four_digits = "1234"  # À récupérer depuis Stripe
                        no_carte = f"****-****-****-{last_four_digits}"  
                        banque = "Desjardins"  # Dans une vraie application, récupérer depuis le formulaire
                        
                        # Appeler la procédure pour enregistrer le paiement
                        cursor.callproc('create_paiement', (
                            facture_data['id_facture'],
                            user_id,
                            no_carte,
                            banque
                        ))
                        
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
    
    # Vérifier si l'utilisateur est connecté
    if 'user_email' not in session:
        flash("Veuillez vous connecter pour ajouter des articles au panier", "error")
        return redirect(url_for('login'))
    
    # Vérifier si l'utilisateur a déjà 5 locations actives
    user_id = get_user_id_from_email(session['user_email'])
    active_rentals = count_active_rentals(user_id)
    if active_rentals >= 5:
        flash("Vous avez déjà 5 locations actives. Veuillez retourner des jeux avant d'en louer de nouveaux.", "error")
        return redirect(url_for('mes_locations'))
    
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
    
    # Vérifier que le total des locations actives + les articles dans le panier ne dépasse pas 5
    if active_rentals + total_items >= 5:
        # Si le jeu est déjà dans le panier, on peut mettre à jour sa quantité
        in_cart = False
        for item in panier:
            if int(item.get('id')) == int(id):
                in_cart = True
                break
        
        if not in_cart:
            flash(f"Limite atteinte: vous avez {active_rentals} locations actives et {total_items} articles dans votre panier. Le maximum est de 5 articles au total.", "error")
            return redirect(url_for('acheter_detail', id=id))
    
    # Chercher si l'article existe déjà dans le panier - utiliser l'ID pour la comparaison
    for i, item in enumerate(panier):
        # S'assurer que la comparaison est faite avec des entiers
        if int(item.get('id')) == int(id):
            # Vérifier si l'augmentation dépasse la limite ou le stock
            if active_rentals + total_items >= 5:
                flash("Limite atteinte: le total de vos locations actives et des articles dans votre panier ne peut pas dépasser 5", "error")
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
    # Si le panier n'existe pas, l'initialiser avec un élément pour les tests
    if 'panier' not in session:
        # Pour déboguer uniquement - à retirer en production
        print("Initialisation d'un panier de ")
        session['panier'] = [{
            'id': 1,
            'name': 'Jeu test',
            'price': 15.99,
            'quantity': 1
        }]
    
    #
    panier_items = session.get('panier', [])
    
    # Si le panier est vide côté serveur mais qu'il a un compteur (potentiellement désynchronisé)
    if not panier_items and session.get('cart_count', 0) > 0:
        # Réinitialiser le compteur du panier côté serveur
        session['cart_count'] = 0
    
    # Durée de location fixe (2 jours)
    duree_location = 2
    
    # Ajouter informations sur le prix calculé pour 2 jours et calculer le total
    total_panier = 0
    for item in panier_items:
        item['prix_journalier'] = item['price']
        item['prix_total'] = item['price'] * duree_location  # Prix pour un seul article
        total_panier += item['prix_total'] * item['quantity']  # Puis multiplier par la quantité
    
    # Debug: Afficher le contenu du panier dans la console
    print(f"Panier items: {panier_items}")
    print(f"Total panier: {total_panier}")
    
    return render_template('panier.html', 
                           panier_items=panier_items, 
                           total_panier=total_panier,
                           duree_location=duree_location)

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
        
        # Définir la durée de location en jours
        duree_location = 2  # Durée fixe de 2 jours pour chaque location
        
        # Créer les line_items pour Stripe
        line_items = []
        for item in panier_items:
            # Calculer le prix total pour la durée de location (obligatoirement multiplié par 2)
            prix_total = item['price'] * duree_location
            
            line_items.append({
                'price_data': {
                    'currency': 'cad',
                    'product_data': {
                        'name': f"{item['name']} - Location {duree_location} jours",
                        'description': f"Location pour {duree_location} jours",
                    },
                    'unit_amount': int(prix_total * 100),  # Stripe utilise les centimes
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
                
                # Après avoir traité tous les articles, récupérer les factures créées
                if success_count > 0:
                    # Récupérer les factures récentes de cet utilisateur
                    cursor.execute("""
                        SELECT f.id_facture, f.id_location FROM Factures f
                        JOIN Locations l ON f.id_location = l.id_location
                        WHERE l.id_user = %s
                        ORDER BY f.id_facture DESC
                        LIMIT %s
                    """, (user_id, success_count))
                    
                    factures = cursor.fetchall()
                    
                    # Enregistrer les paiements pour chaque facture créée
                    if factures:
                        # Informations de paiement sécurisées
                        # Ne stocker que les 4 derniers chiffres masqués
                        last_four_digits = "5678"  # À récupérer depuis Stripe
                        no_carte = f"****-****-****-{last_four_digits}"
                        banque = "Desjardins"  # Dans une vraie application, récupérer depuis le formulaire
                        
                        for facture in factures:
                            try:
                                # Appeler la procédure pour enregistrer le paiement
                                cursor.callproc('create_paiement', (
                                    facture['id_facture'],
                                    user_id,
                                    no_carte,
                                    banque
                                ))
                                print(f"Paiement enregistré pour la facture {facture['id_facture']}")
                            except pymysql.err.InternalError as e:
                                error_msg = str(e)
                                if "45000" in error_msg:
                                    error_msg = error_msg.split("'")[-2] if "'" in error_msg else error_msg
                                    print(f"Erreur lors de l'enregistrement du paiement: {error_msg}")
                                else:
                                    raise e
                    
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
        
        # Rediriger vers une page de confirmation qui videra aussi le localStorage
        return render_template('paiement_success.html')
        
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

@app.route('/payer-penalites')
def payer_penalites():
    # Vérifier si l'utilisateur est connecté
    if 'user_email' not in session:
        flash("Veuillez vous connecter pour accéder à cette page.", "error")
        return redirect(url_for('login'))
    
    try:
        user_id = get_user_id_from_email(session['user_email'])
        late_returns = get_unpaid_late_returns(user_id) if user_id else []
        
        if not late_returns:
            flash("Vous n'avez pas de pénalités à payer.", "info")
            return redirect(url_for('main'))
            
        # Calculer le total des pénalités
        total_penalites = sum(late['penalite'] for late in late_returns)
        
        # Création directe de la session Stripe pour payer les pénalités
        try:
            # Créer une session de paiement Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'cad',
                        'product_data': {
                            'name': 'Paiement des pénalités de retard',
                            'description': f"Paiement pour {len(late_returns)} location(s) en retard",
                        },
                        'unit_amount': int(total_penalites * 100),  # Stripe utilise les centimes
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.host_url + 'paiement/penalites/success',
                cancel_url=request.host_url + 'mes-locations',
            )
            
            # Stocker les IDs des locations en retard dans la session
            session['pending_penalties'] = [{'id_location': late['id_location'], 'penalite': late['penalite']} for late in late_returns]
            
            # Rediriger directement vers Stripe
            return redirect(checkout_session.url, code=303)
            
        except Exception as e:
            print(f"Erreur lors de la création de la session Stripe: {str(e)}")
            # En cas d'erreur, afficher la page d'information sur les pénalités
            return render_template('payer_penalites.html', 
                                late_returns=late_returns, 
                                total_penalites=total_penalites)
                              
    except Exception as e:
        print(f"Erreur lors du chargement des pénalités: {str(e)}")
        flash(f"Une erreur s'est produite: {str(e)}", "error")
        return redirect(url_for('main'))

@app.route('/proceder-paiement-penalites', methods=['POST'])
def proceder_paiement_penalites():
    if 'user_email' not in session:
        flash("Veuillez vous connecter pour accéder à cette page.", "error")
        return redirect(url_for('login'))
        
    try:
        user_id = get_user_id_from_email(session['user_email'])
        late_returns = get_unpaid_late_returns(user_id) if user_id else []
        
        if not late_returns:
            flash("Vous n'avez pas de pénalités à payer.", "info")
            return redirect(url_for('main'))
            
        # Calculer le total des pénalités
        total_penalites = sum(late['penalite'] for late in late_returns)
        
        # Créer une session de paiement Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'cad',
                    'product_data': {
                        'name': 'Paiement des pénalités de retard',
                        'description': f"Paiement pour {len(late_returns)} location(s) en retard",
                    },
                    'unit_amount': int(total_penalites * 100),  # Stripe utilise les centimes
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + 'paiement/penalites/success',
            cancel_url=request.host_url + 'payer-penalites',
        )
        
        # Stocker les IDs des locations en retard dans la session
        session['pending_penalties'] = [{'id_location': late['id_location'], 'penalite': late['penalite']} for late in late_returns]
        
        # Rediriger vers Stripe
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        print(f"Erreur lors du paiement des pénalités: {str(e)}")
        flash(f"Erreur lors du paiement: {str(e)}", "error")
        return redirect(url_for('payer-penalites'))

@app.route('/paiement/penalites/success')
def paiement_penalites_success():
    try:
        # Récupérer les locations en retard depuis la session
        pending_penalties = session.get('pending_penalties', [])
        
        if not pending_penalties:
            flash("Aucune pénalité à traiter", "error")
            return redirect(url_for('main'))
            
        # Traiter chaque pénalité
        if 'user_email' in session:
            user_id = get_user_id_from_email(session['user_email'])
            
            if user_id:
                for penalty in pending_penalties:
                    id_location = penalty['id_location']
                    montant = penalty['penalite']
                    
                    # 1. Récupérer les informations sur les jeux associés à cette location
                    cursor.execute("""
                        SELECT lj.id_jeu
                        FROM Location_jeux lj
                        WHERE lj.id_location = %s AND lj.Date_retournee IS NULL
                    """, (id_location,))
                    
                    jeux_location = cursor.fetchall()
                    
                    # 2. Appeler la procédure retourner pour chaque jeu de la location
                    for jeu in jeux_location:
                        try:
                            # Appel de la procédure retourner pour marquer le jeu comme retourné
                            cursor.callproc('retourner', (id_location, jeu['id_jeu']))
                            print(f"Jeu {jeu['id_jeu']} retourné avec succès pour la location {id_location}")
                        except pymysql.err.InternalError as e:
                            error_msg = str(e)
                            print(f"Erreur lors du retour du jeu {jeu['id_jeu']}: {error_msg}")
                    
                    # 3. Créer une facture pour la pénalité
                    cursor.execute("""
                        INSERT INTO Factures (id_location, Date_facture, montant_total)
                        VALUES (%s, CURDATE(), %s)
                    """, (id_location, montant))
                    
                    # 4. Récupérer l'ID de la facture créée
                    cursor.execute("SELECT LAST_INSERT_ID() as id_facture")
                    facture_id = cursor.fetchone()['id_facture']
                    
                    # 5. Sécuriser les informations de paiement
                    last_four_digits = "9999"  # En production, récupérer depuis Stripe
                    no_carte = f"****-****-****-{last_four_digits}"
                    banque = "Desjardins"  # En production, récupérer depuis le formulaire
                    
                    # 6. Enregistrer le paiement avec la procédure create_paiement
                    try:
                        cursor.callproc('create_paiement', (
                            facture_id,
                            user_id,
                            no_carte,
                            banque
                        ))
                    except pymysql.err.InternalError as e:
                        error_msg = str(e)
                        print(f"Erreur lors de l'enregistrement du paiement: {error_msg}")
                
                flash(f"Paiement des pénalités réussi ! Vos jeux ont été correctement retournés.", "success")
                
                # 7. Rediriger vers la page demandée avant le paiement (débloque l'accès)
                redirect_path = session.pop('redirect_after_payment', url_for('main'))
                
                # 8. Nettoyer la session
                if 'pending_penalties' in session:
                    session.pop('pending_penalties')
                
                return redirect(redirect_path)
                
            else:
                flash("Utilisateur non trouvé", "error")
                return redirect(url_for('login'))
        else:
            flash("Vous devez être connecté pour payer des pénalités", "error")
            return redirect(url_for('login'))
        
    except Exception as e:
        print(f"Erreur lors de la finalisation du paiement des pénalités: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Erreur lors de la finalisation du paiement: {str(e)}", "error")
        return redirect(url_for('payer-penalites'))

@app.route('/mes-retards')
def mes_retards():
    # Vérifier si l'utilisateur est connecté
    if 'user_email' not in session:
        flash("Veuillez vous connecter pour voir vos retards.", "error")
        return redirect(url_for('login'))
    
    try:
        user_id = get_user_id_from_email(session['user_email'])
        late_returns = get_unpaid_late_returns(user_id) if user_id else []
        
        return render_template('mes_retards.html', late_returns=late_returns)
        
    except Exception as e:
        print(f"Erreur lors de l'accès aux retards: {str(e)}")
        flash(f"Une erreur s'est produite: {str(e)}", "error")
        return redirect(url_for('main'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("main"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
