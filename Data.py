import os

import pymysql
from dotenv import load_dotenv
from sql_utils import run_sql_file, parse_sql

from faker import Faker
import random

class Database:
    def __init__(self):
        load_dotenv()

        self.host = os.environ.get("HOST")
        self.port = int(os.environ.get("PORT"))
        self.database = os.environ.get("DATABASE")
        self.password = os.environ.get("PASSWORD")

        self._open_sql_connection()
        self.migration_counter = 0

    def _open_sql_connection(self):
        self.connection = pymysql.connect(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.database,
            autocommit=True
        )
        
        print("Connection opened successfully")

        self.cursor = self.connection.cursor()

def run_sql_file(cursor, filename, accept_empty=True):
    """
    Exécute chaque instruction d'un fichier .sql

    :param cursor: un curseur pymysql.cursor ouvert
    :param filename: le fichier .sql à exécuter
    :param accept_empty: si vrai, lance une exception si le fichier est vide
    """
    sql_statements = parse_sql(filename)

    if len(sql_statements) == 0 and not accept_empty:
        raise IOError(f"File '{filename}' is empty.")

    for statement in sql_statements:
        cursor.execute(statement)

db = Database()
run_sql_file(db.cursor, 'bd_script/drop.sql')
run_sql_file(db.cursor, 'bd_script/up.sql')
print("Tables created successfully")






