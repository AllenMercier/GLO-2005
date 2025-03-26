
DELIMITER //
CREATE PROCEDURE create_facture(
    IN l_id_location INT
)
BEGIN 
    DECLARE l_montant_total Double;
    DECLARE l_penalite DOUBLE;
    DECLARE location_en_cours INT;
    DECLARE l_max_date_retard INT;

    /* Compter le nombre total de factures pour la location */
    SELECT COUNT(*) INTO l_nb_facture
    FROM Factures 
    WHERE id_location = l_id_location;

    /* Affiche un erreur si il y a plus de 2 factures pour la location  */
    IF l_nb_facture + 1 > 2 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Un clien ne peut avoir plus de 2 factures, une pour le paiement initial, et une autre en cas de pénalité';
    END IF;

    /* Cas 1: Facturation de la location seulement (indicateur: Date de retour = NULL)  */
    SELECT COUNT(*) INTO location_en_cours
    FROM location_jeux
    WHERE id_location = l_id_location
        AND Date_retournee IS NULL;
    
    IF location_en_cours > 0 THEN 
        SELECT SUM(Prix) INTO l_montant_total
        FROM location_jeux
        WHERE id_location = l_id_location
            AND Date_retournee IS NULL;
    
    ELSE 
        /* Cas 2 : Facturation de la pénalité (indicateur : le plus grand retard parmi toutes les relations de location dans la table location_jeux)  */
        SELECT MAX(DATEDIFF(Date_retournee, Date_retour_prevu)) INTO l_max_date_retard 
        FROM location_jeux
        Where id_location = l_id_location;

        /* Calcul du montant total des pénalités */
        IF l_max_date_retard > 0 THEN
            SET l_penalite = l_max_date_retard * 5;
        END IF;

        set l_montant_total = l_penalite;
    END IF;

    /* Génération de la facture */
    INSERT INTO Factures (id_location, Date_facture, montant_total)
    VALUES (p_id_location, CURDATE(), v_montant_total);
END;
//
DELIMITER ;

/* 
    -Récupérer le nombre total de facture pour la location( doit être <2)-ok
    Création de la facture
        CAS 1: Création de la facture de location (date retour nulle pour tous les articles)
            -Calculer le montant total de la location -ok
            -Insérer la facture dans la table facture -ok
        CAS 2: Création de la facture de pénalité de retard (date retour non nulle pour tous les articles)
            -Calculer le plus grand nombre de jour de retard -ok
            -Calculer le montant de la pénalité -ok
            -Assigné le montant de la pénalité au montant_total -ok
            -Inséré la facture de pénalité -ok
            -fin

    Erreur potentiel: le nombre d'article retourné n'est pas égal au nombre d'article loué
*/



