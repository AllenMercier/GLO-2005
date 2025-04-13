import os
import sys
import pytest

# Retirer le hack de version Werkzeug – plus nécessaire avec les versions récentes
# import werkzeug
# werkzeug.__version__ = getattr(werkzeug, "__version__", "2.0.0")
import werkzeug
werkzeug.__version__ = getattr(werkzeug, "__version__", "2.0.0")

# Permet d’importer app.py du projet Flask
# Permet d’importer le package flaskProjet depuis son parent
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )
)


from flaskProjet.app import app, get_db, get_cursor

@pytest.fixture
def client():
    app.config['TESTING'] = True

    # Initialiser un contexte d’application pour nettoyer la base de données
    with app.app_context():
        db = get_db()
        cur = get_cursor()
        # Désactiver temporairement les contraintes de clé étrangère
        cur.execute("SET FOREIGN_KEY_CHECKS=0;")
        # Vider les tables liées afin d’éviter les conflits de FK
        for t in ["Paiments", "Factures", "Location_jeux", "Locations", "Jeux", "Utilisateurs"]:
            cur.execute(f"TRUNCATE TABLE {t};")
        cur.execute("SET FOREIGN_KEY_CHECKS=1;")
        db.commit()

    # Créer et retourner le client de test Flask
    with app.test_client() as c:
        yield c
