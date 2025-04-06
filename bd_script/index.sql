
/* Index pour retrouver la location d'un utilisateur */
CREATE INDEX idx_user ON Locations(id_user);

/* Index pour la jointure de la tables locations et locations_jeux et pour retrouver un jeux non retourné */
CREATE INDEX idx_location_retour ON Location_jeux(id_location, Date_retournee);

/* Index pour retrouver accélérer la recherche d'information sur un jeu non retournée */
CREATE INDEX idx_location_jeu_retour ON Location_jeux(id_location, id_jeu, Date_retournee);

/* Index pour retrouver la facture d'une location */
CREATE INDEX idx_location ON Factures(id_location); 

/* Index pour retrouver les informations sur la location d'un jeu*/
CREATE INDEX idx_location ON Location_jeux(id_location);

/* Index pour retrouver un paimement de factures*/
CREATE INDEX idx_facture ON Paiments(id_facture);
