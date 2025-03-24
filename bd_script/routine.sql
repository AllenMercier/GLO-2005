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
        SELECT MAX(id_location) INTO l_id_location FROM Locations;

        /* Calcul le prix total en fonction du prix unitaire (par jour), de la quantité et de la duree de location (par jour).*/
        SET l_prix_total = l_prix_unitaire * l_quantite_desiree * l_duree;

        /* Calcul la date de retour a l'aide de la fonction DATE_ADD qui permet d'Additionner un type DATE et INT ensemble */
        SET l_date_retour = DATE_ADD(CURDATE(), INTERVAL l_duree DAY); 

        /* Insertion de la Location dans la table Location_jeux */
        INSERT INTO Location_jeux (id_location, id_jeu, Quantite, Duree, Prix, Penalite, Date_debut, Date_retour_prevu, Date_retournee)
        VALUES (l_id_location, l_id_jeu, l_quantite_desiree, l_duree,  l_prix_total, 0, CURDATE(), l_date_retour, NULL);

        /* si id_location rien est inséré dans la table Locations */
        IF EXISTS (SELECT l_id_location FROM locations WHERE id_location = l_id_location) THEN     
            INSERT INTO Locations (id_location, id_user) VALUES (l_id_location, l_id_user);
        END IF;

        /* Mise a jour des quantité dans la table jeux */
        UPDATE Jeux
        SET Quantite = Quantite - l_quantite_desiree
        Where id_jeu = l_id_jeu;
    END IF;
END;

// 
DELIMITER;


INSERT INTO Utilisateurs (Nom, Prenom, Email, Date_de_naissance, Mot_de_passe, Statut)
VALUES ('Dupont', 'Jean', 'jean.dupont@email.com', '1995-06-15', 'password123', 1);
INSERT INTO Jeux (Nom, Categorie, Prix, Quantite)
VALUES ('Monopoly', 'Classique', 15.00, 10);

INSERT INTO Jeux (Nom, Categorie, Prix, Quantite)
VALUES ('Monopolyiiii', 'Classique', 15.00, 10);



