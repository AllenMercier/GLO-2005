DELIMITER//

CREATE PROCEDURE retourner (
    IN l_id_location INT,
    IN l_id_jeu INT
)
BEGIN
    DECLARE l_date_prevue Date;
    DECLARE l_id_jeu INT;
    DECLARE l_jour_retard INT;
    DECLARE l_penalite DOUBLE DEFAULT 0;
    DECLARE l_quantite INT;

    /* Requête pour récupérer la date de retour prévue et la quantité d'articles non retournée */
    SELECT Date_retour_prevu, id_jeux, Quantite INTO l_date_prevue, l_id_jeu, l_quantite
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

    /* Mise a jour de la table location_jeux pas d'index puisque PRIMARY KEY(id_location, id_jeu) */
    UPDATE location_jeux
    SET DATE_retournee = CURDATE(),
        Penalite = l_penalite
    WHERE id_location = l_id_location
        AND id_jeu = l_id_jeu;
    
    /* Remettre l'article retourné en stock */
    UPDATE jeux
    SET Quantite = Quantite + l_quantite
    WHERE id_jeu = l_id_jeu;

END;
//

DELIMITER;


/* 
    -Récupèrer la date de retour prévue les articles en location par quantité  -ok
    -Récupérer le plus grand nombre de jour de retard -ok
    -Calculer le la pénalité (5$ par jour de retard) -ok
    -mise a jour de la table location_jeux -ok
    -mise a jour des quantité en stock dans la table jeux -ok
    -fin

 */

