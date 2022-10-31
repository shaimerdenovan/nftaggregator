#app.py
from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2 #pip install psycopg2 
import psycopg2.extras
import collections
import re
from time import sleep
from json2html import * 
import requests, psycopg2, json 
from flask_mail import Mail, Message
import smtplib
from werkzeug.security import generate_password_hash, check_password_hash
 

url = "https://solana-gateway.moralis.io/nft/mainnet/{}/metadata"

headers = {
    "accept": "application/json",
    "X-API-Key": "Pd4PYmtSlrXbWeFRBCvaqCAWCuwHzfvwyx3AOZH9EAc3xVGBwmwJXd9wEZFWApgV"
}

app = Flask(__name__)

app.secret_key = 'cairocoders-ednalan'
 
DB_HOST = "127.0.0.1"
DB_NAME = "NFT1_db"
DB_USER = "postgres"
DB_PASS = "new_password"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
 
@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
    
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
 
@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        print(password)
 
        # Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        # Fetch one record and return result
        account = cursor.fetchone()
 
        if account:
            password_rs = account['password']
            print(password_rs)
            # If account exists in users table in out database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password')
 
    return render_template('login.html')
 
  
























@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
 
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        message = "you have registered"
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("gmail", "password")
        server.sendmail("gmail", email, message)

        _hashed_password = generate_password_hash(password)
 
        #Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        print(account)
        # If account exists show error and validation checks
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email:
            flash('Please fill out the form!')
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            cursor.execute("INSERT INTO users (fullname, username, password, email) VALUES (%s,%s,%s,%s)", (fullname, username, _hashed_password, email))
            conn.commit()
            flash('You have successfully registered!')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    # Show registration form with message (if any)
    return render_template('register.html')
   
   
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))
  
@app.route('/profile')
def profile(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
 
@app.route("/nft", methods=['GET', 'POST'])
def nft(): 


    if request.method == 'POST':
        address = request.form.get('address')

        # Checking if the nft table exists in our database
        cur = conn.cursor()
        cur.execute("select * from information_schema.tables where table_name='nft_table'")
        check1 = bool(cur.rowcount)
        check2 = False
        # Checking if our table has this particular address
        if check1:
            cur.execute("SELECT mint FROM nft_table WHERE mint = %s", (address,))
            check2 = (cur.fetchone() is not None)   

        # If this address is already in our table, let's try to display it
        if check2:

            # The code below converts our record from the database to JSON, similar to what we get from Moralis API
            cur.execute('''SELECT * FROM nft_table LEFT JOIN multiplex_table USING(metaplex_id) 
                LEFT JOIN owners ON nft_table.mint = owners.nft_address WHERE mint=%s''', (address,))
            rows = cur.fetchall()

            owners = []
            for owner in rows:
                o = collections.OrderedDict()
                o["address"] = owner[11]
                o["share"] = owner[14]
                o["verified"] = owner[13]
                owners.append(o)

            m = collections.OrderedDict()
            m["isMutable"] = rows[0][9]
            m["masterEdition"] = rows[0][10]
            m["metadatauri"] = rows[0][5]
            m["owners"] = owners
            m["primarySaleHappened"] = rows[0][8]
            m["sellerFeeBasisPoints"] = rows[0][7]
            m["updateauthority"] = rows[0][6]
            
            n = collections.OrderedDict()
            n["mint"] = rows[0][1]
            n["name"] = rows[0][2]
            n["standard"] = rows[0][3]
            n["symbol"] = rows[0][4]
            n['metaplex'] = m

            j = json.dumps(n)
            return render_template('nftresult.html', table = json2html.convert(json = j))
        # If nft address is not in our table, try to get it through Moralis API
        else:
            response = requests.get(url.format(address), headers=headers).json()
            sleep(3)

            # In case of Bad Request
            if 'statusCode' in response:
                return '''<h1>NFT with this address not found</h1>'''

            # If the Bad Request did not occur, Moralis will return JSON with information about the NFT 
            # The code below saves this information to the DB
            with conn.cursor() as cur:
                cur.execute(""" CREATE TABLE IF NOT EXISTS owners(
                    owner_address text, nft_address text, verified integer, share integer, PRIMARY KEY (owner_address, nft_address)) """)
                query_sql = """ INSERT INTO owners(owner_address, nft_address, verified, share) VALUES(%s, %s, %s, %s) """
                for o in response['metaplex']['owners']:
                    cur.execute(query_sql, (o['address'], response['mint'], o['verified'], o['share'],))
                conn.commit()

                cur.execute(""" CREATE TABLE IF NOT EXISTS multiplex_table(
                    metaplex_id serial, metadataUri text, updateAuthority text, sellerFeeBasisPoints integer, primarySaleHappened integer, 
                    isMutable boolean, masterEdition boolean, PRIMARY KEY (metaplex_id)) """)
                query_sql = """ INSERT INTO multiplex_table(metadataUri, updateAuthority, sellerFeeBasisPoints, primarySaleHappened, 
                    isMutable, masterEdition) VALUES(%s, %s, %s, %s, %s, %s) """
                cur.execute(query_sql, (response['metaplex']['metadataUri'], response['metaplex']['updateAuthority'], 
                    response['metaplex']['sellerFeeBasisPoints'], response['metaplex']['primarySaleHappened'],
                    response['metaplex']['isMutable'], response['metaplex']['masterEdition'],))
                conn.commit() 

                cur.execute(""" CREATE TABLE IF NOT EXISTS nft_table(
                    mint text, name text, standard text, symbol text, metaplex_id serial, PRIMARY KEY (mint),
                    FOREIGN KEY (metaplex_id) REFERENCES multiplex_table(metaplex_id)) """)
                query_sql = """ INSERT INTO nft_table(mint, name, standard, symbol) VALUES(%s, %s, %s, %s) """ 
                cur.execute(query_sql, (response['mint'], response['name'], response['standard'], response['symbol'],))
                conn.commit()
            
            return render_template('nftresult.html', table = json2html.convert(json = response))

    return render_template('nft.html')












 
if __name__ == "__main__":
    app.run(debug=True)