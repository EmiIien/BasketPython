import os
import sqlite3
import click

from flask import Flask,render_template,request,session,redirect,url_for,current_app,g
from flask.cli import with_appcontext

app = Flask(__name__)
app.secret_key = 'testsecretkey'

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

@app.route('/',methods={"GET","POST"})
def login():
    if request.method=="POST":
        email=request.form['email']
        pswd=request.form['pswd']
        db = get_db()
        mdp = db.execute('SELECT pswrd FROM user where mail = (?)',(email,)).fetchone()[0]
        if(check_password_hash(mdp, pswd)):
            session["email"]=email
            return redirect(url_for('index'))
        else:
            return ("mdp ou mail incorrect")
    else:
        return render_template('login.html')


@app.route('/index',methods={"get","post"})
def index():
    if "email" in session:
        email=session["email"]
        db=get_db()
        users = (db.execute('SELECT * FROM user')).fetchall()
        return render_template('index.html',mail=email,users = users)
    else:
        return render_template('login.html')    


@app.route('/register',methods={"get","post"})
def register():
    if request.method=="POST":
        username=request.form['username']
        email=request.form['email']
        age=request.form['age']
        pswd=generate_password_hash(request.form['pswd'])
        db=get_db()
        testmail = db.execute('SELECT id_user FROM user WHERE mail = (?)',(email,)).fetchall()
        if len(testmail)==0:
            db = get_db()
            db.execute('INSERT INTO user (username,pswrd,mail,age) VALUES(?,?,?,?)',(username,pswd,email,age))
            db.commit()
            return render_template('login.html')
        else:
            return ("mail déjà utilisé")
    else:
        return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop("email", None)
    return render_template("login.html")