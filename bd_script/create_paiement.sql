DELIMITER //  -- Changement du délimiteur pour définir une procédure stockée

-- Définition de la procédure "create_paiement"
CREATE PROCEDURE create_paiement(
    IN l_id_facture INT,  -- Paramètre d'entrée : identifiant de la facture
    IN l_id_user INT,     -- Paramètre d'entrée : identifiant de l'utilisateur
    IN l_no_carte varchar(50),  -- Paramètre d'entrée : numéro de carte bancaire
    IN l_banque ENUM('RBC', 'Desjardins', 'National Bank', 'Tangerine', 'BMO') -- Banque choisie
)
BEGIN
    /* Vérification de l'existence de la facture */
    IF NOT EXISTS (SELECT facture FROM Factures WHERE id_facture = l_id_facture) THEN
        -- Si aucune facture ne correspond, on lève une erreur
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Facture inexistante';
    END IF;

    -- Vérification si la facture a déjà été payée
    IF EXISTS (SELECT id_facture FROM Paiement  WHERE id_facture = l_id_facture) THEN
        -- Si un paiement existe déjà pour cette facture, on lève une erreur
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Facture déja payée';
    END IF;

    /* Enregistrement du paiement */
    INSERT INTO Paiements (id_facture, id_user, No_carte, Banque, Date_paiment)
    VALUES (l_id_facture, l_id_user, l_no_carte, l_banque, CURDATE());  -- Insertion dans la table Paiements
END;
//  -- Fin de la procédure
DELIMITER ;  -- Retour au délimiteur standard

/* 
    - Vérifier l'existence de la facture - ok
    - Vérification si la facture a déjà été payée - ok
    - Enregistrer le paiement - ok
    - fin
*/

INSERT INTO Utilisateurs (id_user, Nom, Prenom, Email, Date_de_naissance, Mot_de_passe, Statut)
VALUES 
(1, 'Dupont', 'Jean', 'jean.dupont@example.com', '1990-01-01', 'password123', TRUE),
(2, 'Martin', 'Sophie', 'sophie.martin@example.com', '1985-05-15', 'password456', TRUE);

INSERT INTO locations (id_location, id_user)
VALUES 
(1, 1),
(2, 2);

INSERT INTO jeux (id_jeu, Nom, Categorie, Prix, Quantite)
VALUES 
(1, 'Monopoly', 'Classique', 20.00, 10),
(2, 'Mario Kart', 'Console', 50.00, 5);

INSERT INTO location_jeux (id_location, id_jeu, Quantite, Duree, Prix, Date_debut, Date_retour_prevu, Date_retournee)
VALUES 
(1, 1, 2, 5, 40.00, '2025-04-01', '2025-04-10', '2025-04-15');

INSERT INTO location_jeux (id_location, id_jeu, Quantite, Duree, Prix, Date_debut, Date_retour_prevu, Date_retournee)
VALUES 
(2, 2, 1, 3, 50.00, '2025-04-01', '2025-04-05', '2025-04-05');

INSERT INTO Factures (id_facture, id_location, Date_facture, montant_total)
VALUES 
(1, 1, '2025-04-15', 100.00),
(2, 2, '2025-04-05', 50.00);

CALL create_paiement(3, 1, '1234-5678-9012-3456', 'RBC');
-- Devrait lever une erreur : "Facture inexistante"

CALL create_paiement(1, 1, '1234-5678-9012-3456', 'RBC');
-- Devrait lever une erreur : "Facture déjà payée"