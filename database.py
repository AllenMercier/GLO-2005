import os

import pymysql
import dotenv


class Database:
    def __init__(self):
        self.host = "sql5.freemysqlhosting.net"
        self.port = 3306
        self.database = "sql5700124"
        self.user = "sql5700124"
        self.password = "AnrAI7AlIc"
        self.migration_counter = 0

    def _open_sql_connection(self):
        self.connection = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.database,
            autocommit=True
        )

        self.cursor = self.connection.cursor()

    def _close_sql_connection(self):
        self.connection.close()

    def verifyConnexion(self, req):
        self._open_sql_connection()
        self.cursor.execute(req)
        result = self.cursor.fetchone()
        self.cursor.close()
        self._close_sql_connection()
        return result

    def addValuestoDb(self, req):
        self._open_sql_connection()
        self.cursor.execute(req)
        self.cursor.close()
        self._close_sql_connection()

    def select_genres(self):
        self._open_sql_connection()
        self.cursor.execute("SELECT * FROM genres")
        genres = [x[0] for x in self.cursor.fetchall()]
        self.cursor.close()
        self._close_sql_connection()
        return genres

    def get_table_columns(self, table):
        self._open_sql_connection()
        self.cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' AND TABLE_SCHEMA = '{self.database}' ORDER BY ORDINAL_POSITION;")
        res = [x[0] for x in self.cursor.fetchall()]
        self.cursor.close()
        self._close_sql_connection()
        return res

    def get_table_data(self, table, nomfilm,genre,sousgenre,annee,acteur,nbvote,note, saison):
        self._open_sql_connection()
        if (table == "films") :
            req = f"CALL filtrerFilms('%{nomfilm}%', '%{genre}%', '%{sousgenre}%', '%{annee}%', '%{acteur}%', {nbvote}, {note})"
        else :
            req = f"CALL filtrerSeries('%{nomfilm}%', '%{genre}%', '%{sousgenre}%', '%{annee}%', '%{acteur}%', '%{saison}%', {nbvote}, {note})"

        self.cursor.execute(req)
        liste = [list(x) for x in self.cursor.fetchall()]
        self.cursor.close()
        self._close_sql_connection()
        return liste

    def get_table_data_user(self, table, nomfilm,genre,sousgenre,annee,acteur,nbvote,note, saison, username):
        self._open_sql_connection()
        if (table == "films") :
            req = f"CALL filtrerFilmsUtilisateur('%{nomfilm}%', '%{genre}%', '%{sousgenre}%', '%{annee}%', '%{acteur}%', {nbvote}, {note}, {username})"
        else :
            req = f"CALL filtrerSeriesUtilisateur('%{nomfilm}%', '%{genre}%', '%{sousgenre}%', '%{annee}%', '%{acteur}%', '%{saison}%', {nbvote}, {note}, {username})"

        self.cursor.execute(req)
        liste = [list(x) for x in self.cursor.fetchall()]
        self.cursor.close()
        self._close_sql_connection()
        return liste

    def get_table_data_research(self, table, nomfilm):
        self._open_sql_connection()
        if (table == "films") :
            req = f"CALL rechercherFilms('%{nomfilm}%');"
        else :
            req = f"CALL rechercherSeries('%{nomfilm}%');"

        self.cursor.execute(req)
        liste = [list(x) for x in self.cursor.fetchall()]
        self.cursor.close()
        self._close_sql_connection()
        return liste

    def get_movieserie_data(self, table, id):
        self._open_sql_connection()
        if (table == "films"):
            req = f"SELECT * FROM films WHERE idFilm = '{id}';"
        else :
            req = f"SELECT * FROM series WHERE idSerie = '{id}';"
        self.cursor.execute(req)
        liste = [list(x) for x in self.cursor.fetchall()]
        self.cursor.close()
        self._close_sql_connection()
        return liste

    def verifieVoteUser(self, user, id, table):
        self._open_sql_connection()
        if (table == "films"):
            req = f"SELECT * FROM votesFilms WHERE nomUtilisateur = {user} AND idFilm = '{id}';"
        else:
            req = f"SELECT * FROM votesSeries WHERE nomUtilisateur = {user} AND idSerie = '{id}';"

        self.cursor.execute(req)
        liste = [list(x) for x in self.cursor.fetchall()]
        self.cursor.close()
        self._close_sql_connection()
        return liste

    def get_comments_movieserieUser(self, table, id):
        self._open_sql_connection()
        if (table == "films"):
            req = f"SELECT contenu FROM commentairesFilms WHERE id = '{id}';"
        else:
            req = f"SELECT contenu FROM commentairesSeries WHERE id = '{id}';"

        self.cursor.execute(req)
        liste = [list(x) for x in self.cursor.fetchall()]
        self.cursor.close()
        self._close_sql_connection()
        return liste

    def get_comments_movieserie(self, table, id):
        self._open_sql_connection()
        if (table=="films"):
            req = f"CALL voirCommentairesNotesUtilisateursFilms('{id}');"
        else:
            req = f"CALL voirCommentairesNotesUtilisateursSeries('{id}');"

        self.cursor.execute(req)
        liste = [list(x) for x in self.cursor.fetchall()]
        self.cursor.close()
        self._close_sql_connection()
        return liste

    def voter_film_serie(self, table, user, note, commentaire, film):
        self._open_sql_connection()
        if (table=="films"):
            req = f'CALL rajouterVoteFilm({user},"{film}","{note}","{commentaire}");'
        else:
            req = f'CALL rajouterVoteSerie({user},"{film}","{note}","{commentaire}");'

        self.cursor.execute(req)
        self.cursor.close()
        self._close_sql_connection()

    def ajouterFilm(self, nom, annee, genre, sousgenre, acteurs):
        self._open_sql_connection()
        self.cursor.execute(f'CALL creerFilm("{nom}", "{annee}", "{genre}", "{sousgenre}", "{acteurs}")')
        self.cursor.close()
        self._close_sql_connection()

    def ajouterSerie(self, nom, annee, genre, sousgenre, acteurs, saison):
        self._open_sql_connection()
        self.cursor.execute(f'CALL creerSerie("{nom}", "{annee}", "{genre}", "{sousgenre}", "{acteurs}", "{saison}")')
        self.cursor.close()
        self._close_sql_connection()

    def ajouterGenre(self, nom):
        self._open_sql_connection()
        self.cursor.execute(f'CALL creerGenre("{nom}")')
        self.cursor.close()
        self._close_sql_connection()

    def ajouterActeur(self, prenom, nom, ddn, sexe, nationnalite):
        self._open_sql_connection()
        self.cursor.execute(f'CALL creerActeur("{prenom}", "{nom}", "{ddn}", "{sexe}", "{nationnalite}")')
        self.cursor.close()
        self._close_sql_connection()