import os  # Module permettant de manipuler les chemins de fichiers et d’interagir avec le système d’exploitation

# Fonction pour lire et découper les instructions SQL contenues dans un fichier
def parse_sql(filename):
    """
    Lit un fichier .sql et retourne chaque instruction dans une liste de chaînes de caractères
    """
    current_dir = os.path.dirname(__file__)
    abs_file_path = os.path.join(current_dir, filename)

    with open(abs_file_path, 'r', encoding='utf-8') as file:
        data = file.readlines()
        
    stmts = []
    delimiter = ';'
    stmt = ''
        
    for lineno, line in enumerate(data, 1):
        # Supprimer les commentaires qui suivent le code SQL
        if '--' in line:
            comment_pos = line.find('--')
            line = line[:comment_pos]
            
        line = line.strip()
        
        # Ignorer les lignes vides
        if not line:
            continue
            
        # Gérer les changements de délimiteur
        if line.upper().startswith('DELIMITER'):
            parts = line.split()
            if len(parts) > 1:
                delimiter = parts[1]
            continue
        
        # Vérifier si la ligne se termine par le délimiteur (même avec des espaces)
        line_without_spaces = line.rstrip()
        if line_without_spaces.endswith(delimiter):
            # Ajouter la ligne sans le délimiteur
            ending_position = line_without_spaces.rfind(delimiter)
            stmt += line[:ending_position]
            # N'ajouter que si l'instruction n'est pas vide
            if stmt.strip():
                stmts.append(stmt.strip())
            stmt = ''
        else:
            stmt += line + ' '
            
    # Ajouter la dernière instruction si non vide
    if stmt.strip():
        stmts.append(stmt.strip())
        
    return stmts

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
