from passlib.hash import sha256_crypt
from flaskProjet.app import app, get_db, get_cursor

def test_ajouter_au_panier_requires_login(client):
    # Insérer un jeu de test dans la base de données (sans utilisateur connecté)
    with client.application.app_context():
        db = get_db()
        cur = get_cursor()
        cur.execute(
            "INSERT INTO Jeux (Nom, Categorie, Prix, Quantite) VALUES (%s, %s, %s, %s)",
            ("GamePanier", "Classique", 10.0, 5)
        )
        db.commit()
        game_id = cur.lastrowid

    # Tenter d’ajouter le jeu au panier sans être authentifié
    rv = client.post('/ajouter_au_panier', data={'id_jeu': str(game_id), 'quantite': '1'}, follow_redirects=True)
    text = rv.get_data(as_text=True)
    # Vérifier que l’utilisateur est redirigé vers la page de login avec le message approprié
    assert "Vous devez être connecté" in text

def test_ajouter_au_panier_success(client):
    # Insérer un utilisateur et un jeu de test dans la base de données
    with client.application.app_context():
        db = get_db()
        cur = get_cursor()
        # Création d’un utilisateur de test avec mot de passe haché
        hashed_pwd = sha256_crypt.hash("Secret123")
        cur.execute(
            "INSERT INTO Utilisateurs (Nom, Prenom, Email, Date_de_naissance, Mot_de_passe, Statut) VALUES (%s, %s, %s, %s, %s, %s)",
            ("Test", "User", "test@panier.com", "2000-01-01", hashed_pwd, 1)
        )
        # Création d’un jeu de test
        cur.execute(
            "INSERT INTO Jeux (Nom, Categorie, Prix, Quantite) VALUES (%s, %s, %s, %s)",
            ("GamePanier2", "Classique", 20.0, 3)
        )
        game_id = cur.lastrowid
        db.commit()

    # Se connecter avec l’utilisateur de test
    login_data = {'email': 'test@panier.com', 'password': 'Secret123'}
    rv_login = client.post('/login', data=login_data, follow_redirects=True)
    assert rv_login.status_code == 200  # la connexion doit réussir (redirection vers accueil)

    # Ajouter le jeu de test au panier en tant qu’utilisateur connecté
    rv = client.post('/ajouter_au_panier', data={'id_jeu': str(game_id), 'quantite': '2'}, follow_redirects=True)
    text = rv.get_data(as_text=True)
    # Vérifier que la page panier affiche le jeu ajouté et le message de succès
    assert "GamePanier2" in text  # le nom du jeu doit apparaître dans le panier
    assert "ajouté(s) au panier" in text  # message de confirmation d’ajout au panier
