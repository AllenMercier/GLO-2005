from flaskProjet.app import app, get_db, get_cursor
from passlib.hash import sha256_crypt

def register(client, data):
    """Helper pour appeler la route /register."""
    return client.post('/register', data=data, follow_redirects=True)

def login(client, data):
    """Helper pour appeler la route /login."""
    return client.post('/login', data=data, follow_redirects=True)

def test_register_and_login(client):
    # Inscription d’un nouvel utilisateur (tous les champs requis sont fournis)
    rv = register(client, {
        'nom': 'Dupont',
        'prenom': 'Alice',
        'email': 'alice@test.com',
        'date_naissance': '1990-01-01',
        'mot_de_passe': 'Secret123',
        'confirmPassword': 'Secret123',
        'statut': '1'
    })
    text = rv.get_data(as_text=True)
    assert "Inscription réussie" in text  # le flash de succès d'inscription apparaît

    # Connexion avec le nouvel utilisateur
    rv2 = login(client, {'email': 'alice@test.com', 'password': 'Secret123'})
    text2 = rv2.get_data(as_text=True)
    # Après la connexion réussie, on est redirigé vers l'accueil
    assert "Accueil" in text2

def test_register_duplicate(client):
    # Inscription d’un utilisateur en double pour tester le message d’erreur
    data = {
        'nom': 'Dupont',
        'prenom': 'Bob',
        'email': 'bob@test.com',
        'date_naissance': '1985-05-05',
        'mot_de_passe': 'Secret123',
        'confirmPassword': 'Secret123',
        'statut': '1'
    }
    register(client, data)  # première inscription réussie
    rv = register(client, data)  # deuxième inscription avec le même email
    # Le message d’erreur pour email déjà utilisé doit apparaître
    assert "Email déjà utilisé" in rv.get_data(as_text=True)

def test_login_bad(client):
    # Tentative de connexion avec des identifiants inconnus
    rv = login(client, {'email': 'inconnu@x.com', 'password': 'pwd'})
    # Le message d’erreur "Email inconnu" (ou équivalent) doit apparaître
    assert "Email inconnu" in rv.get_data(as_text=True)
