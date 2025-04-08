-- Active: 1739460525589@@127.0.0.1@3306@projet
-- Indique l’environnement actif : identifiant de connexion à la base de données "projet" sur localhost
USE projet;  
-- Utilise la base de données "projet"

-- Création de la table Utilisateurs si elle n'existe pas
CREATE TABLE IF NOT EXISTS Utilisateurs (
    id_user INT PRIMARY KEY AUTO_INCREMENT,      
    Nom VARCHAR(50),                             
    Prenom VARCHAR(50),                          -- Prénom de l'utilisateur
    Email VARCHAR(100) UNIQUE,                   -- Email unique (clé candidate)
    Date_de_naissance DATE,                      -- Date de naissance
    Mot_de_passe VARCHAR(255),                   -- Mot de passe (non chiffré ici, attention)
    Statut BOOLEAN                               -- Statut de l'utilisateur (actif/inactif)
);

-- Création de la table Locations si elle n'existe pas
CREATE TABLE IF NOT EXISTS Locations (
    id_location INT AUTO_INCREMENT PRIMARY KEY,  -- Identifiant unique de la location (clé primaire auto-incrémentée)
    id_user INT,                                 -- Référence vers l'utilisateur ayant effectué la location
    FOREIGN KEY (id_user) REFERENCES Utilisateurs(id_user)  -- Clé étrangère vers la table Utilisateurs
);

-- Création de la table Jeux si elle n'existe pas
CREATE TABLE IF NOT EXISTS Jeux (
    id_jeu INT AUTO_INCREMENT PRIMARY KEY,       -- Identifiant unique du jeu
    Nom VARCHAR(50),                             -- Nom du jeu
    Categorie ENUM('Classique', 'Console', 'Ordinateur', 'Equipement'),  -- Catégorie du jeu
    Prix DOUBLE,                                 -- Prix du jeu
    Quantite INT,                                -- Quantité disponible
    UNIQUE (Nom, Categorie)                      -- Contrainte d’unicité sur la combinaison Nom + Catégorie
);

-- Création de la table Factures si elle n'existe pas
CREATE TABLE IF NOT EXISTS Factures (
    id_facture INT PRIMARY KEY AUTO_INCREMENT,   -- Identifiant unique de la facture
    id_location INT,                             -- Référence vers la location concernée
    Date_facture DATE,                           -- Date d’émission de la facture
    montant_total DOUBLE,                        -- Montant total à payer
    UNIQUE (id_facture, id_location),            -- Contrainte d’unicité combinée (peut être redondante ici)
    FOREIGN KEY (id_location) REFERENCES Locations(id_location) ON DELETE CASCADE  -- Suppression en cascade si location supprimée
);

-- Création de la table Paiments si elle n'existe pas
CREATE TABLE IF NOT EXISTS Paiments (
    id_paiment INT PRIMARY KEY AUTO_INCREMENT,   -- Identifiant unique du paiement
    id_facture INT,                              -- Référence vers la facture associée
    id_user INT,                                 -- Référence vers l'utilisateur qui a payé
    No_carte VARCHAR(19),                        -- Numéro de carte (non chiffré ici)
    Banque ENUM('RBC', 'Desjardins', 'National Bank', 'Tangerine', 'BMO'),  -- Banque utilisée pour le paiement
    Date_paiment DATE,                           -- Date du paiement
    FOREIGN KEY (id_facture) REFERENCES Factures(id_facture) ON DELETE CASCADE,  -- Suppression en cascade si facture supprimée
    FOREIGN KEY (id_user) REFERENCES Utilisateurs(id_user) ON DELETE CASCADE     -- Suppression en cascade si utilisateur supprimé
);

-- Création de la table Location_jeux si elle n'existe pas
CREATE TABLE IF NOT EXISTS Location_jeux (
    id_location INT,                             -- Référence vers la location
    id_jeu INT,                                  -- Référence vers le jeu loué
    Quantite INT,                                -- Quantité de jeux loués
    Duree INT DEFAULT 2,                         -- Durée de location en jours (par défaut : 2)
    Prix DOUBLE,                                 -- Prix de la location par jour 
    Date_debut DATE,                             -- Date de début de la location
    Date_retour_prevu DATE,                      -- Date de retour prévue
    Date_retournee DATE,                         -- Date de retour réelle
    PRIMARY KEY (id_location, id_jeu),           -- Clé primaire composée : une ligne par jeu loué dans une location
    FOREIGN KEY (id_location) REFERENCES Locations(id_location) ON DELETE CASCADE,  -- Clé étrangère vers Locations
    FOREIGN KEY (id_jeu) REFERENCES Jeux(id_jeu) ON DELETE CASCADE       
);
