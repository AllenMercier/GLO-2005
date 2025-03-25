from flask import Flask, render_template,request,jsonify,Response
from connexion import select_classique, insert_todo, select_todos


app = Flask(__name__)

@app.route('/')

def main():

    return render_template('acceuil.html')

@app.route("/add-todo/", methods=["POST"])
def add_todo():
    data = request.json

    insert_todo(data["text"])

    response = {
        "status": 200
    }

    return jsonify(response)
@app.route("/liste")

def classiques():

    listeC = select_classique()

    return render_template("classiques.html", liste=listeC)

@app.route("/listeChoixClassique")
def choixC():

    return render_template('choix_classiques.html', liste=liste1)


if __name__ == '__main__':
    app.run(port=8080)