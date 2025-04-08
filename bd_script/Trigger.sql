
DELIMITER //

CREATE TRIGGER available_location
BEFORE INSERT ON Locations
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
END //

DELIMITER ;