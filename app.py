from flask import Flask,flash
from flaskext.mysql import MySQL
from flask import request, render_template, redirect, url_for
from flask import session
from flask import Flask, render_template, request
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer,ListTrainer
import functools
import json
import os
import flask
from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.flask_client import OAuth
import google.oauth2.credentials
import googleapiclient.discovery
import google_auth
import google_drive
import time
import nltk
import re
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

time.clock=time.time
nltk.download('averaged_perceptron_tagger')


app = flask.Flask(__name__)
app.secret_key = os.environ.get("my_secret_key", default=False)

app.register_blueprint(google_auth.app)

app.register_blueprint(google_drive.app)

# Set a secret key for the Flask application
app.secret_key = 'my_secret_key'

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'dbit'
app.config['MYSQL_DATABASE_DB'] = 'app'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql = MySQL(app)

@app.route('/')
def show_login():
    return render_template('dashboard.html')

@app.route('/register')
def show_register():
    return render_template('register.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']

        # Check if the username or email already exists in the database
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s OR password = %s', (username, password))
        result = cursor.fetchone()
        
        # validate the user's information
        # check if the username or email already exists in the database
        if result:
            # If the username or email already exists, render the registration page again with an error message
            error="Username or password already exists. Please choose another one."
            return render_template('register.html',error=error)
        # check if name field is not empty and contains only alphabets
        elif not name or not name.isalpha():
            error="Please enter a valid name containing only alphabets"
            return render_template('register.html',error=error)
        # if the information is valid, insert the new user into the database
        else:
            cursor = mysql.get_db().cursor()
            cursor.execute("INSERT INTO users (name, username, password) VALUES (%s, %s, %s)", (name, username, password))
            mysql.get_db().commit()
            return redirect(url_for('login'))
    
    else:
        return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # validate the input fields
        if not username:
            error = 'Username field is required.'
            return render_template('login.html', error=error)
        if not password:
            error = 'Password field is required.'
            return render_template('login.html', error=error)
        if not re.match(r'^[\w.@+-]+$', username):
            error = 'Username contains invalid characters.'
            return render_template('login.html', error=error)

        # check if the username and password match any entries in the database
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            # store the user's information in a session variable
            session['user'] = user
            return redirect(url_for('dashboard'))
        else:
            # display an error message if the login information is invalid
            error = 'Invalid login credentials'
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        # get the name of the logged-in user from the session
        user = session['user']
        name = user[1]  # assuming name is the second column in the users table
        
        # display the dashboard for the logged in user with their name
        return render_template('dashboard.html', name=name)
    else:
        # redirect the user to the login page if they are not logged in
        return redirect(url_for('login.html'))


@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/calender')
def calender():
    return render_template('calendar.html')

@app.route('/colleges')
def colleges():
    return render_template('colleges.html')




bot = ChatBot('EduGuide')
trainer = ListTrainer(bot)

# Create a ChatterBotCorpusTrainer and train it with the corpus data
corpus_trainer = ChatterBotCorpusTrainer(bot)
corpus_trainer.train('chatterbot.corpus.english.greetings')


@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    bot_response = bot.get_response(userText)
    if float(bot_response.confidence) > 0.5:
        return str(bot_response)
    else:
        return "Sorry, I am not sure what you mean.Go ahead and write the number of any query. 😃✨ <br> 1.list of important documents you will be needing to complete your admission process.</br>2.Frequently asked questions regarding admission </br>3.Scholarship related info </br> 4.Top Colleges </br>  5.Engineering Colleges as per your CET Percentile </br> 6.Forms </br> 0. Press 0 for the main Query </br>"

@app.route('/api')
def api():
    if google_auth.is_logged_in():
        drive_fields = "files(id,name,mimeType,createdTime,modifiedTime,shared,webContentLink)"
        items = google_drive.build_drive_api_v3().list(
                        pageSize=20, orderBy="folder", q='trashed=false',
                        fields=drive_fields
                    ).execute()

        return flask.render_template('list.html', files=items['files'], user_info=google_auth.get_user_info())

    else:
        return flask.render_template('login1.html', login_url='/google/login')




if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()

    if 'link' in incoming_msg:
        resp.message("Here is a link to the website: <a href='https://www.example.com'>https://www.example.com</a>")
    else:
        resp.message("I didn't understand your message. Please try again.")

    return str(resp)

if __name__ == '__main__':
    app.run()


