DELIMITER //
CREATE PROCEDURE louer (
    IN l_id_user INT,
    IN l_id_jeu INT,
    IN l_quantite_desiree INT
)   
    
BEGIN
    DECLARE l_id_location INT;
    DECLARE location_date_debut DATE;
    DECLARE quantite_jeu_louee INT;
    DECLARE l_quantite_disponible INT;
    DECLARE l_prix_unitaire DOUBLE;
    DECLARE l_prix_total DOUBLE;
    DECLARE l_duree INT DEFAULT 2;
    DECLARE l_date_retour DATE;
    DECLARE l_statut BOOLEAN;

    /* Vérifie si le client est abonnée */
    SELECT statut INTO l_statut
    FROM Utilisateurs
    WHERE id_user = l_id_user;

    IF l_statut != 1 THEN
        SIGNAL SQLSTATE "45000" SET MESSAGE_TEXT = 'Vous devez être membre pour louer des jeux';
    END IF;

    /* Vérifie si il existe une location non retournée du même jour */
    SELECT lj.id_location, lj.Date_debut INTO l_id_location, location_date_debut
    FROM location_jeux lj 
    JOIN locations l ON l.id_location = lj.id_location
    WHERE lj.Date_retournee IS null 
    AND l.id_user = l_id_user
    AND DATE(lj.date_debut) = CURDATE()
    LIMIT 1;

    /* Requête pour compter le nombre d'articles loués par le client en ce moment */
    SELECT SUM(lj.Quantite) INTO quantite_jeu_louee
    FROM location_jeux lj
    JOIN locations l ON l.id_location = lj.id_location
    WHERE l.id_user = l_id_user 
    AND lj.date_retournee IS NULL;

    /* Initialise la quantité de jeux loués à 0 si la somme est NULL */  
    IF quantite_jeu_louee IS NULL THEN
        SET quantite_jeu_louee = 0;
    END IF;
 
    /* Requête conditionnelle pour vérifier qu’un client ne dépasse pas 5 articles par location */
    IF quantite_jeu_louee + l_quantite_desiree > 5  THEN
      SIGNAL SQLSTATE "45000" SET MESSAGE_TEXT = 'Vous ne pouvez pas louer plus de 5 jeux à la fois';
    END IF;

    /* Requête pour vérifier la disponibilité du jeu */
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
            SET l_id_location = LAST_INSERT_ID(); /* Récupère l'id de la location insérée */
        END IF;

        /* Calcul le prix total en fonction du prix unitaire (par jour), de la quantité et de la durée de location (par jour).*/
        SET l_prix_total = l_prix_unitaire * l_quantite_desiree * l_duree;

        /* Calcule la date de retour à l'aide de la fonction DATE_ADD, qui permet d’additionner une date et un entier */
        SET l_date_retour = DATE_ADD(CURDATE(), INTERVAL l_duree DAY); 

        /* Insertion de la location dans la table Location_jeux */
        INSERT INTO Location_jeux (id_location, id_jeu, Quantite, Duree, Prix, Penalite, Date_debut, Date_retour_prevu, Date_retournee)
        VALUES (l_id_location, l_id_jeu, l_quantite_desiree, l_duree,  l_prix_total, NULL, CURDATE(), l_date_retour, NULL);

        /* Mise à jour des quantités dans la table Jeux */
        UPDATE Jeux
        SET Quantite = Quantite - l_quantite_desiree
        Where id_jeu = l_id_jeu;
    END IF;
END;
// 
DELIMITER;

/* 
    -vérifie si le client est abonnée -ok
    -vérfie si une location au même jour existe déja -ok
    -vérifie ensuite le nombre d'article louer par le client -ok
    -vérifie si le client n'a pas plus de 5 articles louer pour cette location ok
    Procéder a la location si tout est correcte
        -Vérifier si l'article est en stock -ok
        -si l'id location n'existe pas, insérer une nouvelle location -ok
        -Calculer le prix total -ok
        -Calculer la date de retour -ok
        -insérer la location dans la table location_jeux -ok
        -mise a jour de la quantité dans la table jeux -ok
        -fin
 */


DELIMITER //
CREATE TRIGGER set_location_price
BEFORE INSERT ON Location_jeux
FOR EACH ROW
BEGIN
    DECLARE jeu_prix DOUBLE;
    
    -- Récupère le prix actuel du jeu
    SELECT Prix INTO jeu_prix FROM Jeux WHERE id_jeu = NEW.id_jeu;
    
    -- Calcule et stocke le prix total
    SET NEW.Prix = jeu_prix * NEW.Quantite * NEW.Duree;
END//
DELIMITER ;

DELIMITER //

CREATE TRIGGER calculate_penalty
AFTER INSERT ON Location_jeux
FOR EACH ROW
BEGIN
    DECLARE days_late INT;
    DECLARE penalty DOUBLE;

    -- Calculer le nombre de jours de retard
    IF NEW.Date_retournee > NEW.Date_retour_prevu THEN
        SET days_late = DATEDIFF(NEW.Date_retournee, NEW.Date_retour_prevu);
        SET penalty = days_late * 5; -- Par exemple, 5 unités monétaires par jour de retard
    ELSE
        SET penalty = 0;
    END IF;

    -- Insérer ou mettre à jour la pénalité dans la table Penalites
    INSERT INTO Penalites (id_location, id_jeu, Penalite)
    VALUES (NEW.id_location, NEW.id_jeu, penalty)
    ON DUPLICATE KEY UPDATE Penalite = penalty;
END;
//

DELIMITER ;




DELIMITER //

CREATE TRIGGER check_user_status
BEFORE INSERT ON locations
FOR EACH ROW
BEGIN
    DECLARE user_status BOOLEAN;

    -- Vérifier le statut de l'utilisateur
    SELECT Statut INTO user_status
    FROM Utilisateurs
    WHERE id_user = NEW.id_user;

    -- Si le statut n'est pas 1, lever une erreur
    IF user_status IS NULL OR user_status != 1 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'L\'utilisateur n\'est pas actif et ne peut pas procéder à des locations.';
    END IF;
END;
//

DELIMITER ;