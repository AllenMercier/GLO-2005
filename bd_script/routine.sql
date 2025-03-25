-- Active: 1739460525589@@127.0.0.1@3306@projet
USE projet;
DELIMITER //
CREATE PROCEDURE louer (
    IN l_id_user INT,
    IN l_id_jeu INT,
    IN l_quantite_desiree INT
)   
    
BEGIN

    /* Declaration de variable */
    DECLARE l_id_location INT;
    DECLARE location_date_debut DATE;
    DECLARE quantite_jeu_louee INT;
    DECLARE l_quantite_disponible INT;
    DECLARE l_prix_unitaire DOUBLE;
    DECLARE l_prix_total DOUBLE;
    DECLARE l_duree INT DEFAULT 2;
    DECLARE l_date_retour DATE;



    /* vérifie s'il existe une location non retournée du même jour */
    SELECT lj.id_location, lj.Date_debut INTO l_id_location, location_date_debut
    FROM location_jeux lj 
    JOIN locations l ON l.id_location = lj.id_location
    WHERE lj.Date_retournee IS null 
    AND l.id_user = l_id_user
    AND DATE(lj.date_debut) = CURDATE()
    LIMIT 1;

    /* Requête pour compter le nombre d'article louer par le client en ce moment*/
    SELECT SUM(lj.Quantite) INTO quantite_jeu_louee
    FROM location_jeux lj
    JOIN locations l ON l.id_location = lj.id_location
    WHERE l.id_user = l_id_user 
    AND lj.date_retournee IS NULL;
 
    /* Requête conditionnel vérifier qu'un client ne peut pas avoir plus de 5 items par location */
    IF quantite_jeu_louee + l_quantite_desiree > 5  THEN
      SIGNAL SQLSTATE "45000" SET MESSAGE_TEXT = 'Vous ne pouvez pas louer plus de 5 jeux à la fois';
    END IF;

    /* Reqête pour vérifier la disponibilité du jeux */
    SELECT Quantite, prix INTO l_quantite_disponible, l_prix_unitaire
    FROM jeux
    WHERE id_jeu = l_id_jeu;

    /* Requête conditionnel 
       si la quantité est inssufisante en stock, un message d'erreur est affiché.
    */
    IF l_quantite_disponible < l_quantite_desiree THEN
        SIGNAL SQLSTATE "45000" SET MESSAGE_TEXT = 'Quantité en stock inssufisante';
    ELSE
        
        /* Si id_location existe rien est inséré dans la table Locations */
        IF l_id_location IS NULL THEN   
            INSERT INTO Locations (id_user) VALUES (l_id_user);
        END IF;

        SELECT MAX(id_location) INTO l_id_location FROM Locations;

        /* Calcul le prix total en fonction du prix unitaire (par jour), de la quantité et de la duree de location (par jour).*/
        SET l_prix_total = l_prix_unitaire * l_quantite_desiree * l_duree;

        /* Calcul la date de retour a l'aide de la fonction DATE_ADD qui permet d'Additionner un type DATE et INT ensemble */
        SET l_date_retour = DATE_ADD(CURDATE(), INTERVAL l_duree DAY); 

        /* Insertion de la Location dans la table Location_jeux */
        INSERT INTO Location_jeux (id_location, id_jeu, Quantite, Duree, Prix, Penalite, Date_debut, Date_retour_prevu, Date_retournee)
        VALUES (l_id_location, l_id_jeu, l_quantite_desiree, l_duree,  l_prix_total, 0, CURDATE(), l_date_retour, NULL);

        /* Mise a jour des quantité dans la table jeux */
        UPDATE Jeux
        SET Quantite = Quantite - l_quantite_desiree
        Where id_jeu = l_id_jeu;
    END IF;
END;

// 
DELIMITER;

DELIMITER//
CREATE PROCEDURE retourner (
    IN l_id_location INT,
    IN l_id_jeu INT
)
BEGIN
    DECLARE l_date_prevue Date;
    DECLARE l_jour_retard INT;
    DECLARE l_penalite DOUBLE DEFAULT 0;
    DECLARE l_quantite INT;

    /* Requête pour récupérer la date de retour prévue et la quantité d'article non retournée */
    SELECT Date_retour_prevu, Quantite INTO l_date_prevue, l_quantite
    FROM location_jeux
    WHERE id_location = l_id_location
        AND id_jeu = l_id_jeu
        AND Date_retournee IS NULL;

    /* Calculer le nombre de jour de retard */
    SET l_jour_retard = ABS(DATEDIFF(CURDATE(), l_date_prevue));

    /* Si il y a un retard, calculer 5$ par jour de retard */
    IF l_jour_retard > 0 THEN
        SET l_penalite = l_jour_retard * 5;
    END IF;

    /* Mise a jour de la table location_jeux */
    UPDATE location_jeux
    SET DATE_retournee = CURDATE(),
        Penalite = l_penalite
    WHERE id_location = l_id_location
        AND id_jeu = l_id_jeu;
    
    /* Remettre l'article retournée en stock */
    UPDATE jeux
    SET Quantite = Quantite + l_quantite
    WHERE id_jeu = l_id_jeu;

END;
//


DELIMITER //
CREATE PROCEDURE create_facture(
    IN l_id_location INT
)
BEGIN 
    DECLARE l_montant_total Double;
    DECLARE l_nb_facture INT;
    DECLARE l_penalite DOUBLE;
    DECLARE location_en_cours INT;
    DECLARE l_max_date_retard INT;

    /* Compte du montant total de facture pour la location */
    SELECT COUNT(*) INTO l_nb_facture
    FROM Factures 
    WHERE id_location = l_id_location;

    /* Affiche une erreur si il y a plus de 2 facture pour une location  */
    IF l_nb_facture > 2 THEN
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
        /* Cas 2: Facturation de la pénalité (indicateur: la plus grande date de retard parmi tous les relation location de la table location_jeux)  */
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

DELIMITER //
CREATE PROCEDURE create_paiement(
    IN l_id_facture INT,
    IN l_id_user INT,
    IN l_no_carte varchar(50),
    IN l_banque ENUM('RBC', 'Desjardins', 'National Bank', 'Tangerine', 'BMO')
)
BEGIN
    /* Vérification de l'existance de la facture */
    IF NOT EXISTS (SELECT facture FROM Factures WHERE id_facture = l_id_facture) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Facture inexistante';
    END IF;

    /* Enregistrement du paiement*/
    INSERT INTO Paiements (id_facture, id_user, No_carte, Banque, Date_paiment)
    VALUES (p_id_facture, p_id_user, p_no_carte, p_banque, CURDATE());
END;
//
DELIMITER ;



INSERT INTO Utilisateurs (Nom, Prenom, Email, Date_de_naissance, Mot_de_passe, Statut)
VALUES ('Dupont', 'Jean', 'jean.dupont@email.com', '1995-06-15', 'password123', 1);
INSERT INTO Jeux (Nom, Categorie, Prix, Quantite)
VALUES ('Monopoly', 'Classique', 15.00, 10);

INSERT INTO Jeux (Nom, Categorie, Prix, Quantite)
VALUES ('Monopolyiiii', 'Classique', 15.00, 10);

CALL louer(1, 1, 2);
CALL louer(1, 2, 1);

CALL retourner(3, 1);

DROP PROCEDURE louer;

DROP PROCEDURE retourner;




