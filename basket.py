import os
import sqlite3
import click

from flask import Flask, render_template, request, session, redirect, url_for, current_app, g, flash
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'testSecretKey'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            os.path.join(app.instance_path, 'BasketPython.sqlite'),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('database.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


app.teardown_appcontext(close_db)
app.cli.add_command(init_db_command)


# Connection function
@app.route('/', methods={"GET", "POST"})
def login():
    if request.method == "POST":
        email = request.form['email']
        pswd = request.form['pswd']
        db = get_db()
        mdp = db.execute('SELECT pswrd FROM user where mail = (?)', (email,)).fetchone()
        # conditions to check password and mail
        if not mdp:
            flash("Votre mail est incorrect !")
        elif check_password_hash(mdp[0], pswd):
            session["email"] = email
        else:
            flash('Votre mot de passe est incorrect !')
        return index()
    else:
        return index()


# homepage, where we see all the games created...
@app.route('/index', methods={"get", "post"})
def index():
    if "email" in session:
        email = session["email"]
        db = get_db()
        id_user = db.execute('SELECT id_user FROM user WHERE mail = (?)', (email,)).fetchone()[0]
        # select id of games where I participate
        mygames_id = db.execute('SELECT id_game FROM player WHERE id_user = (?)', (id_user,)).fetchall()
        # select all games
        allgames = db.execute('SELECT * FROM game').fetchall()
        # games where I participate
        mygames = []
        for id in mygames_id:
            g = db.execute('SELECT * FROM game where id_game =(?)', (id[0],)).fetchall()
            mygames = mygames + g
        # games where I don't participate
        set_games = set(allgames) - set(mygames)
        games = list(set_games)
        return render_template('index.html', games=games)
    else:
        return render_template('login.html')


# New user registration
@app.route('/register', methods={"get", "post"})
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        age = request.form['age']
        # For the registration we generate a hash for the password.
        pswd = generate_password_hash(request.form['pswd'])
        pswd1 = request.form['pswd1']
        db = get_db()
        # check if one user already uses this email
        testEmail = db.execute('SELECT id_user FROM user WHERE mail = (?)', (email,)).fetchall()
        # check if the 2 passwords are not equals
        if not check_password_hash(pswd, pswd1):
            flash('Vos  deux mot de passe sont différents')
            return render_template('register.html')
        # if email not yet used
        elif len(testEmail) == 0:
            db = get_db()
            # We insert the values of the registration into the database
            db.execute('INSERT INTO user (username,pswrd,mail,age) VALUES(?,?,?,?)', (username, pswd, email, age))
            db.commit()
            return render_template('login.html')
        else:
            flash('Mail déja utilisé !')
            return render_template('register.html')
    else:
        return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop("email", None)
    return render_template("login.html")


# Match Creation
@app.route('/creatematch', methods={"get", "post"})
def creatematch():
    if "email" in session:
        if request.method == "POST":
            # We get the values sent by the user
            game_title = request.form['game_title']
            adress = request.form['adress']
            game_day = request.form['game_day']
            game_hour = request.form['game_hour']
            age_Max = request.form['age_Max']
            age_MIN = request.form['age_MIN']
            db = get_db()
            # We insert the values into the database
            db.execute('INSERT INTO game (game_title,adress,game_day,game_hour,age_Max,age_MIN) VALUES(?,?,?,?,?,?)',
                       (game_title, adress, game_day, game_hour, age_Max, age_MIN))
            db.commit()
        return render_template('createMatch.html')
    else:
        return render_template('login.html')


# show the games where the user participate
@app.route('/mygames', methods={"get", "post"})
def mygames():
    if "email" in session:
        email = session['email']
        db = get_db()
        # select the id of the user
        id_user = db.execute('SELECT id_user FROM user WHERE mail = (?)', (email,)).fetchone()[0]
        # select id of games where I participate
        mygames_id = db.execute('SELECT id_game FROM player WHERE id_user = (?)', (id_user,)).fetchall()
        # put those games in a list names mygames
        mygames = []
        # participate to a game (add to table player)
        if request.method == "POST":
            id_game = request.form['id_game']
            db.execute('INSERT INTO player (id_user,id_game) VALUES(?,?)', (id_user, id_game))
            db.commit()
            mygames_id = db.execute('SELECT id_game FROM player WHERE id_user = (?)', (id_user,)).fetchall()
            # Put the games where I participate in my list
            for id in mygames_id:
                g = db.execute('SELECT * FROM game where id_game =(?)', (id[0],)).fetchall()
                mygames = mygames + g
            # send the list to the html
            return render_template('mygames.html', mygames=mygames)
        else:
            # Put the games where I participate in my list
            for id in mygames_id:
                g = db.execute('SELECT * FROM game where id_game =(?)', (id[0],)).fetchall()
                mygames = mygames + g
            # send the list to the html
            return render_template('mygames.html', mygames=mygames)
    else:
        render_template('login.html')


# don't participate to a game anymore
@app.route('/delgame', methods={"get", "post"})
def delgame():
    if "email" in session:
        email = session['email']
        db = get_db()
        # select the id of the user
        id_user = db.execute('SELECT id_user FROM user WHERE mail = (?)', (email,)).fetchone()[0]
        if request.method == "POST":
            # select the id of the game i don't want to participate anymore
            id_game = request.form['id_game']
            # delete the game from the table player
            db.execute('DELETE from player WHERE id_user = (?) AND id_game= (?)', (id_user, id_game))
            db.commit()
            return redirect(url_for('mygames'))
        else:
            return redirect(url_for('mygames'))
    else:
        render_template('login.html')


# show and update the informations (age and username) of an user
@app.route('/aboutme', methods={"get", "post"})
def aboutme():
    if "email" in session:
        email = session['email']
        db = get_db()
        # select username and age of the user
        user = db.execute('SELECT username, age FROM user WHERE mail = (?)', (email,)).fetchall()
        # update infos if user put new ones
        if request.method == "POST":
            username = request.form['username']
            age = request.form['age']
            db.execute('UPDATE user SET username = (?), age = (?) WHERE mail = (?)', (username, age, email))
            db.commit()
            return redirect('index')
        # show infos
        else:
            return render_template('aboutme.html', user=user)
    else:
        return render_template('login.html')
