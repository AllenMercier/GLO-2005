<div style="border: 1px solid #ccc; padding: 16px; border-radius: 8px; background-color: #f9f9f9; font-family: monospace;">
<pre><code>
# GLO-2005

## 📦 Installation des dépendances
Assurez-vous d'installer les librairies Python nécessaires avec la commande suivante :

    pip install -r requirements.txt

## ⚙️ Configuration de l'environnement
Créez un fichier .env à la racine du projet, puis ajoutez-y les variables suivantes :

    HOST=votre-hôte
    USER=votre-utilisateur
    PASSWORD=votre-mot-de-passe
    DATABASE=votre-base-de-données
    PORT=port-de-la-base-de-données
    
    # Configuration Stripe pour les paiements
    STRIPE_SECRET_KEY=votre-clé-secrète-stripe
    STRIPE_PUBLISHABLE_KEY=votre-clé-publique-stripe

## 💳 Configuration de Stripe
1. Créez un compte sur [Stripe](https://stripe.com)
2. Récupérez vos clés API dans la section Dashboard > Developers > API keys
3. Ajoutez ces clés dans votre fichier .env comme indiqué ci-dessus
4. En mode développement, vous pouvez utiliser les cartes de test suivantes :
   - Numéro: 4242 4242 4242 4242
   - Date: n'importe quelle date future
   - CVC: n'importe quel code à 3 chiffres

## 🗄️ Initialisation de la base de données
Avant de lancer l'application, il faut initialiser la base de données avec les tables requises et les données de test :

    python Data.py

Cette commande crée toutes les tables nécessaires, les procédures stockées et insère un ensemble de données de test.

## 🚀 Lancement de l'application
Après avoir initialisé la base de données, exécutez l'application Flask avec la commande suivante :

    python flaskProjet/app.py

## 🌐 Accès à l'application
Ouvrez votre navigateur et accédez à :

    http://127.0.0.1:8080
</code></pre>
</div>
