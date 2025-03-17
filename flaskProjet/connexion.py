import pymysql
import pymysql.cursors
conn= pymysql.connect(host='localhost',user='root',password='1234',db='projet_glo_2005')
cursor = conn.cursor()

requete = "SELECT * FROM classiques;"

cursor.execute(requete)
resultat = cursor.fetchall()
for tuple in resultat:
    for attrib in tuple:
        print(attrib+'\t',end='')
    print('\n')

    cursor.close()
    conn.close()