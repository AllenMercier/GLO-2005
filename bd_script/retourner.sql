DELIMITER //

CREATE PROCEDURE retourner (
    IN l_id_location INT,
    IN l_id_jeu INT
)
BEGIN
    DECLARE l_date_prevue DATE;
    DECLARE l_jour_retard INT;
    DECLARE l_penalite DOUBLE DEFAULT 0;
    DECLARE l_quantite_location INT;
    DECLARE quantite_jeu INT;
    DECLARE v_quantite_stock INT;

    -- Vérification que la location sans date de retour existe, sinon erreur
    SELECT COUNT(*) INTO quantite_jeu
    FROM location_jeux
    WHERE id_location = l_id_location
      AND id_jeu = l_id_jeu
      AND Date_retournee IS NULL;
    
    IF quantite_jeu = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Aucune location trouvée pour cet id_location et id_jeu.';
    END IF;

    -- Récupération des infos de location
    SELECT Date_retour_prevu, Quantite INTO l_date_prevue, l_quantite_location
    FROM location_jeux
    WHERE id_location = l_id_location
      AND id_jeu = l_id_jeu
      AND Date_retournee IS NULL;

    -- Calcul du nombre de jours en retard
    IF CURDATE() > l_date_prevue THEN
        SET l_jour_retard = DATEDIFF(CURDATE(), l_date_prevue);
        SET l_penalite = l_jour_retard * 5;
    ELSE
        SET l_jour_retard = 0;
    END IF;

    -- mise a jour de la date de retour de la table location_jeux
    UPDATE location_jeux
    SET Date_retournee = CURDATE()
    WHERE id_location = l_id_location
      AND id_jeu = l_id_jeu;

    -- Récupérer le stock actuel
    SELECT Quantite INTO v_quantite_stock
    FROM jeux
    WHERE id_jeu = l_id_jeu;

    -- Mise à jour du stock (version corrigée)
    UPDATE jeux
    SET Quantite = IFNULL(v_quantite_stock, 0) + l_quantite_location
    WHERE id_jeu = l_id_jeu;

    -- Création facture si pénalité
    IF l_penalite > 0 THEN
        INSERT INTO Factures (id_location, date_facture, montant_total)
        VALUES (l_id_location, CURDATE(), l_penalite);
    END IF;
END //

DELIMITER ;

DROP PROCEDURE retourner;


INSERT INTO Utilisateurs (id_user, nom, prenom, email, mot_de_passe, statut)
VALUES (1, 'Dupont', 'Jean', 'jean.dupont@test.com', 'pass123', 1);

-- Jeu
INSERT INTO Jeux (id_jeu, Nom, Categorie, prix, quantite)
VALUES (1, 'Échecs', 'Classique', 15.00, 10);

CALL louer(1, 1, 1); -- Appel de la procédure pour louer le jeu
-- Location

-- Insérer une location (table Locations)
INSERT INTO Locations (id_location, id_user)
VALUES (3, 1);

-- Concerne (location du jeu avec date retour prévue dépassée pour simuler pénalité)
INSERT INTO location_jeux (id_location, id_jeu, date_debut, date_retour_prevu, quantite)
VALUES (3, 1, CURDATE() - INTERVAL 10 DAY, CURDATE() - INTERVAL 3 DAY, 1);


CALL retourner(3, 1); -- Appel de la procédure pour retourner le jeu
UPDATE Jeux
SET Quantite = 9;
/* 
    -Récupèrer la date de retour prévue les articles en location par quantité  -ok
    -Récupérer le plus grand nombre de jour de retard -ok
    -Calculer le la pénalité (5$ par jour de retard) -ok
    -mise a jour de la table location_jeux -ok
    -mise a jour des quantité en stock dans la table jeux -ok
    -fin

 */

