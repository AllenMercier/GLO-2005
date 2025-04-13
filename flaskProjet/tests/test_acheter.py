from flaskProjet.app import app, get_db, get_cursor

def test_acheter_list(client):
    # Insérer un jeu dans la base de données (contexte de l’application)
    with client.application.app_context():
        db = get_db()
        cur = get_cursor()
        cur.execute(
            "INSERT INTO Jeux (Nom, Categorie, Prix, Quantite) VALUES (%s, %s, %s, %s)",
            ("GameTest", "Classique", 10.0, 5)
        )
        db.commit()

    # Appeler la route /acheter (méthode GET) pour récupérer la liste des jeux
    rv = client.get('/acheter')
    text = rv.get_data(as_text=True)
    # Vérifier que le jeu inséré apparaît dans la page
    assert "GameTest" in text

def test_acheter_post_returns_list(client):
    # La requête POST sur /acheter (sans paramètre id) doit retourner la liste des jeux en JSON
    rv = client.post('/acheter', data={'quantite': '1'}, follow_redirects=True)
    assert rv.status_code == 200
    data = rv.get_json()
    # Vérifier que la réponse JSON contient bien la clé "jeux" avec une liste
    assert "jeux" in data
    assert isinstance(data["jeux"], list)
