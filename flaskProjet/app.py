from typing import Any

from flask import Flask, render_template
import pymysql
import pymysql.cursors
conn= pymysql.connect(host='localhost',user='root',password='12345',db='projet_glo_2005')
cursor = conn.cursor()

requete = "SELECT * FROM jeux;"

cursor.execute(requete)
resultat = cursor.fetchall()
liste1 = []
for tuple in resultat:
   #for attrib in tuple:
    if "classiques" == tuple[2]:
     #print(tuple[1] , end=' ')
      liste1.append(tuple[1])
print('\n')
print(liste1)

cursor.close()
# conn.close()
app = Flask(__name__)

@app.route('/')

def main():

    return render_template('acceuil.html')
@app.route("/liste")

def liste():

    return render_template('classiques.html', liste=liste1)




if __name__ == '__main__':
    app.run(port=8080)