DELIMITER //
CREATE PROCEDURE create_paiement(
    IN l_id_facture INT,
    IN l_id_user INT,
    IN l_no_carte varchar(50),
    IN l_banque ENUM('RBC', 'Desjardins', 'National Bank', 'Tangerine', 'BMO')
)
BEGIN
    /* Vérification de l'existence de la facture */
    IF NOT EXISTS (SELECT facture FROM Factures WHERE id_facture = l_id_facture) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Facture inexistante';
    END IF;

    IF EXISTS (SELECT id_facture FROM Paiement  WHERE id_facture = l_id_facture) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Facture déja payée';
    END IF;

    /* Enregistrement du paiement*/
    INSERT INTO Paiements (id_facture, id_user, No_carte, Banque, Date_paiment)
    VALUES (p_id_facture, p_id_user, p_no_carte, p_banque, CURDATE());
END;
//
DELIMITER ;


/* 
    -Vérifier l'existence de la facture -ok
    -Vérification si la facture a déja été payée -ok
    -Enregistrer le paiement -ok
    -fin

*/
