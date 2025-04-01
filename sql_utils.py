import os  # Module permettant de manipuler les chemins de fichiers et d’interagir avec le système d’exploitation

# Fonction pour lire et découper les instructions SQL contenues dans un fichier
def parse_sql(filename):
    """
    Lit un fichier .sql et retourne chaque instruction dans une liste de chaînes de caractères

    :param filename: le fichier .sql
    :return: liste d'instructions
    """

    current_dir = os.path.dirname(__file__)  # Récupère le répertoire courant du fichier Python
    abs_file_path = os.path.join(current_dir, filename)  # Construit le chemin absolu du fichier SQL

    data = open(abs_file_path, 'r').readlines()  # Lit toutes les lignes du fichier SQL
    stmts = []  # Liste pour stocker les instructions SQL complètes
    DELIMITER = ';'  # Délimiteur par défaut des instructions SQL
    stmt = ''  # Variable pour construire une instruction multi-ligne

    # Parcourt ligne par ligne le contenu du fichier SQL
    for lineno, line in enumerate(data):
        if not line.strip():
            continue  # Ignore les lignes vides

        if line.startswith('--'):
            continue  # Ignore les commentaires SQL

        if 'DELIMITER' in line:
            DELIMITER = line.split()[1]  # Change le délimiteur si spécifié
            continue

        if DELIMITER not in line:
            stmt += line.replace(DELIMITER, ';')  # Construit l’instruction multi-ligne
            continue

        if stmt:
            stmt += line  # Complète l’instruction en cours
            stmts.append(stmt.strip())  # Ajoute l’instruction à la liste
            stmt = ''  # Réinitialise la variable pour la prochaine instruction
        else:
            stmts.append(line.strip())  # Ligne simple : ajout direct
    return stmts  # Retourne la liste des instructions SQL

# Fonction pour exécuter toutes les instructions SQL d’un fichier donné
def run_sql_file(cursor, filename, accept_empty=True):
    """
    Exécute chaque instruction d'un fichier .sql

    :param cursor: un curseur pymysql.cursor ouvert
    :param filename: le fichier .sql à exécuter
    :param accept_empty: si vrai, lance une exception si le fichier est vide
    """
    sql_statements = parse_sql(filename)  # Appelle la fonction pour extraire les instructions SQL

    if len(sql_statements) == 0 and not accept_empty:
        raise IOError(f"File '{filename}' is empty.")  # Erreur si le fichier est vide et que ce n’est pas autorisé

    for statement in sql_statements:
        cursor.execute(statement)  # Exécution de chaque instruction SQL une à une
