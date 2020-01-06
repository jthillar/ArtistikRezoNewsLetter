# -*- coding: utf-8 -*-

from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)
app.config.from_object('config')
client = MongoClient(app.config['MONGO_URI'])
db = client.get_database(app.config['MONGO_DBNAME'])

@app.route('/', methods=['POST', 'GET'])
def register():
    description ="Pour vous abonner à la newsletter, renseignez votre email ci-dessous :"
    if request.method == 'POST':
        users = db.users
        existing_user = users.find_one({'email': request.form['email']})
        if existing_user is None:
            users.insert_one({'email': request.form['email']})
            description = """Vous êtes abonné à la newsletter ! Vous la recevrez tous les jours à midi, si de nouveaux évènements sont apparus sur le
                club ou si les dates d'un évènement ont évolué."""
            return render_template('registered.html', description=description)

        description = "Vous êtes déjà abonné."
        return render_template('registered.html', description=description)

    return render_template('index.html', description=description)

@app.route('/unregister/', methods=['POST', 'GET'])
def unregister():
    description = """Pour vous désabonner, veuillez remplir le champ suivant avec votre adresse e-mail"""
    if request.method == 'POST':
        users = db.users
        existing_user = users.find_one({'email': request.form['email']})
        if existing_user is not None:
            users.delete_one({'email': request.form['email']})
            description = """Vous ne recevrez plus la newsletter."""
            return render_template('registered.html', description=description)

        description = "Cette adresse email nous est inconnue."
        return render_template('registered.html', description=description)

    return render_template('unregister.html', description=description)


if __name__ == "__main__":
    app.run()