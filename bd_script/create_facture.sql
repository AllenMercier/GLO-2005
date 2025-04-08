DELIMITER //  -- Changement du délimiteur pour définir une procédure stockée

-- Début de la définition de la procédure stockée "create_facture"
CREATE PROCEDURE create_facture(
    IN l_id_location INT  -- Paramètre d'entrée : identifiant de la location
)
BEGIN 
    DECLARE l_montant_total Double;       -- Variable pour stocker le montant total à facturer
    DECLARE l_penalite DOUBLE;            -- Variable pour stocker le montant de la pénalité
    DECLARE location_en_cours INT;        -- Variable pour vérifier s'il y a encore des jeux non retournés
    DECLARE l_max_date_retard INT;        -- Variable pour stocker le maximum de jours de retard
    DECLARE l_nb_facture INT;             -- Variable pour stocker le nombre de facture
    /* Compter le nombre total de factures pour la location */
    SELECT COUNT(*) INTO l_nb_facture
    FROM Factures 
    WHERE id_location = l_id_location;

    /* Affiche une erreur si le client a déjà deux factures */
    IF l_nb_facture + 1 > 2 THEN
        SIGNAL SQLSTATE '45000'  -- Déclenche une erreur personnalisée
        SET MESSAGE_TEXT = 'Un clien ne peut avoir plus de 2 factures, une pour le paiement initial, et une autre en cas de pénalité';
    END IF;

    /* Cas 1: Facturation de la location seulement (si Date_retournee est NULL) */
    SELECT COUNT(*) INTO location_en_cours
    FROM location_jeux
    WHERE id_location = l_id_location
        AND Date_retournee IS NULL;
    
    IF location_en_cours > 0 THEN 
        -- Si des jeux ne sont pas encore retournés, on calcule la somme des prix
        SELECT SUM(Prix) INTO l_montant_total
        FROM location_jeux
        WHERE id_location = l_id_location
            AND Date_retournee IS NULL;
    
    ELSE 
        /* Cas 2 : Facturation de la pénalité (si tous les jeux ont été retournés) */
        SELECT MAX(DATEDIFF(Date_retournee, Date_retour_prevu)) INTO l_max_date_retard 
        FROM location_jeux
        Where id_location = l_id_location;

        /* Calcul du montant total des pénalités */
        IF l_max_date_retard > 0 THEN
            SET l_penalite = l_max_date_retard * 5;  -- 5 unités de pénalité par jour de retard
        END IF;

        SET l_montant_total = l_penalite;  -- Affectation du montant total avec la pénalité
    END IF;

    /* Génération de la facture */
    INSERT INTO Factures (id_location, Date_facture, montant_total)
    VALUES (l_id_location, CURDATE(), l_montant_total);  -- Insertion dans la table Factures
END;
//  -- Fin de la procédure
DELIMITER ;  -- Retour au délimiteur SQL standard

/* 
    - Récupérer le nombre total de factures pour la location (doit être <2) - ok
    - Création de la facture :
        CAS 1 : Création de la facture de location (si tous les articles n'ont pas été retournés)
            - Calculer le montant total de la location - ok
            - Insérer la facture dans la table Factures - ok
        CAS 2 : Création de la facture de pénalité de retard (si tous les articles ont été retournés)
            - Calculer le plus grand nombre de jours de retard - ok
            - Calculer le montant de la pénalité - ok
            - Assigner le montant de la pénalité au montant_total - ok
            - Insérer la facture de pénalité - ok
            - Fin

    Erreur potentielle : le nombre d'articles retournés n'est pas égal au nombre d'articles loués
*/


