from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, DecimalField
from passlib.hash import sha256_crypt
from functools import wraps
import pickle
import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

model = pickle.load(open("iris_predictor", 'rb'))

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_PORT'] = 3307
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)


Articles = Articles()

@app.route('/')

#index
def home():
    return render_template('home.html')

@app.route('/about')

#about
def about():
    return render_template('about.html')

@app.route('/articles')

#articles
def articles():
    return render_template('articles.html', articles= Articles)

@app.route('/article/<string:id>/')

#article
def article(id):
    return render_template('article.html', id=id)

#register form class
class RegisterForm(Form) :
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=60)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])

    confirm = PasswordField('Confirm Password')

#register
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s,%s,%s)", (name, email, username, password))

        mysql.connection.commit()

        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

#user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        #Get form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create cursor
        cur = mysql.connection.cursor()

        # Get User by username
        result = cur.execute("SELECT * FROM users WHERE username = %s",  [username])

        if result > 0:
            # Get hashed stored password
            data = cur.fetchone()
            password = data['password']

            #Compare password
            if sha256_crypt.verify(password_candidate, password):

                session['logged_in'] = True
                session['username'] = username

                flash('Login Successful', 'success')
                return redirect(url_for('dashboard'))

            else:

                error = 'Wrong Password'
                return render_template('login.html', error=error)

        else:
            error = 'Username Not Found'
            return render_template('login.html', error=error)

        cur.close()


    return render_template('login.html')



#Check login

def if_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


#dashboard
@app.route('/dashboard')
@if_logged_in
def dashboard():
    return render_template('dashboard.html')

#add articles form class
class ArticleForm(Form) :
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=10)])

@app.route('/add_article', methods=['GET','POST'])
@if_logged_in
def add_article():
   form = ArticleForm(request.form)
   if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        cur = mysql.connection.cursor()

        cur.execute("insert into articles(title, body, author) values(%s, %s, %s)",(title, body, session['username']))

        mysql.connection.commit()

        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

   return render_template('add_article.html', form=form)

# # class PredictorForm(Form) :
# #     sepal_length = DecimalField("Sepal Length ", [validators.DataRequired()])
# #     sepal_width = DecimalField("Sepal Width ", [validators.DataRequired()])
# #     petal_length = DecimalField("Petal Length ", [validators.DataRequired()])
# #     petal_width = DecimalField("Petal Width ", [validators.DataRequired()])
#
# #iris_predictor
# @app.route('/iris_predictor', methods=['GET', 'POST'])
# # @if_logged_in
# def iris_predictor():
#     form = PredictorForm(request.form)
#     result = ""
#     if request.method == 'POST' and form.validate():
#
#         sepal_length = form.sepal_width.data
#         sepal_width = form.sepal_width.data
#         petal_length = form.petal_length.data
#         petal_width = form.petal_width.data
#
#         test = np.array([[sepal_length, sepal_width, petal_length, petal_width]])
#         names = ["Iris-Setosa", "Iris-Versicolor", "Iris-Virginica"]
#         prediction = model.predict(test)
#
#         result = names[prediction[0]]
#
#     return render_template('iris_predictor.html', form=form, result=result)

#logout


#iris_predictor
@app.route('/iris_predictor', methods=['GET', 'POST'])
@if_logged_in
def iris_predictor():
    result = ""
    sepal_length = 5
    sepal_width = 5
    petal_length = 5
    petal_width = 5

    if request.method == 'POST':
        sepal_length = request.form['sepal_length']
        sepal_width = request.form['sepal_width']
        petal_length = request.form['petal_length']
        petal_width = request.form['petal_width']

        test = np.array([[sepal_length, sepal_width, petal_length, petal_width]])
        names = ["Iris-Setosa", "Iris-Versicolor", "Iris-Virginica"]
        prediction = model.predict(test)

        result = names[prediction[0]]

    return render_template('iris_predictor.html', result=result,sepal_length=sepal_length, sepal_width=sepal_width, petal_length=petal_length, petal_width=petal_width )

@app.route('/logout')
@if_logged_in
def logout():
    session.clear()
    flash('Logged Out', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)