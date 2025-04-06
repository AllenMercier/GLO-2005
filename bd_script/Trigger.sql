CREATE TRIGGER calcule_penalite
AFTER INSERT ON Location_jeux
FOR EACH ROW
BEGIN
    DECLARE Jour_retard INT;
    DECLARE penalite DOUBLE;

    -- Calculer le nombre de jours de retard
    IF NEW.Date_retournee > NEW.Date_retour_prevu THEN
        SET Jour_retard = DATEDIFF(NEW.Date_retournee, NEW.Date_retour_prevu);
        SET penalite = Jour_retard * 5; -- Par exemple, 5 unités monétaires par jour de retard
    ELSE
        SET penalite = 0;
    END IF;

    -- Insérer ou mettre à jour la pénalité dans la table Penalites
    INSERT INTO Penalites (id_location, id_jeu, Penalite)
    VALUES (NEW.id_location, NEW.id_jeu, penalite)
    ON DUPLICATE KEY UPDATE Penalite = penalite;
END;
//
DELIMITER ;

DELIMITER //

CREATE TRIGGER available_location
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