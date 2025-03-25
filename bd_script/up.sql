-- Active: 1739460525589@@127.0.0.1@3306@projet
DELIMITER // 
CREATE PROCEDURE create_table()
BEGIN
    CREATE TABLE IF NOT EXISTS Utilisateurs (   id_user INT PRIMARY KEY AUTO_INCREMENT,
                                                Nom VARCHAR(50), 
                                                Prenom VARCHAR(50), 
                                                Email VARCHAR(100) UNIQUE, 
                                                Date_de_naissance DATE,
                                                Mot_de_passe VARCHAR(50), 
                                                Statut BOOLEAN);

    CREATE TABLE IF NOT EXISTS Locations (     id_location INT AUTO_INCREMENT PRIMARY KEY,
                                                id_user INT,
                                                FOREIGN KEY (id_user) REFERENCES Utilisateurs(id_user));

    CREATE TABLE IF NOT EXISTS Jeux (       id_jeu INT AUTO_INCREMENT PRIMARY KEY,
                                            Nom VARCHAR(50), 
                                            Categorie ENUM('Classique', 'Console', 'Ordinateur', 'Equipement'),
                                            Prix DOUBLE,
                                            Quantite INT,
                                            UNIQUE (Nom, Categorie));

    CREATE TABLE IF NOT EXISTS Factures (   id_facture INT PRIMARY KEY AUTO_INCREMENT,
                                            id_location INT,
                                            Date_facture DATE,
                                            montant_total DOUBLE,
                                            UNIQUE (id_facture, id_location),
                                            FOREIGN KEY (id_location) REFERENCES Locations(id_location) ON DELETE CASCADE);

    CREATE TABLE IF NOT EXISTS Paiments (   id_paiment INT PRIMARY KEY AUTO_INCREMENT,
                                            id_facture INT,
                                            id_user INT,
                                            No_carte VARCHAR(19),
                                            Banque ENUM('RBC', 'Desjardins', 'National Bank', 'Tangerine', 'BMO'),
                                            Date_paiment DATE,
                                            FOREIGN KEY (id_facture) REFERENCES Factures(id_facture) ON DELETE CASCADE,
                                            FOREIGN KEY (id_user) REFERENCES Utilisateurs(id_user) ON DELETE CASCADE);

    CREATE TABLE IF NOT EXISTS Location_jeux (  id_location INT,
                                                id_jeu INT,
                                                Quantite INT,
                                                Duree INT,
                                                Prix DOUBLE,
                                                Penalite Double,
                                                Date_debut DATE,
                                                Date_retour_prevu DATE,
                                                Date_retournee DATE,
                                                PRIMARY KEY (id_location, id_jeu),
                                                FOREIGN KEY (id_location) REFERENCES Locations(id_location) ON DELETE CASCADE,
                                                FOREIGN KEY (id_jeu) REFERENCES Jeux(id_jeu) ON DELETE CASCADE);
    END
//
DELIMITER ;

CALL create_table();


