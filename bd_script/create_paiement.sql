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
