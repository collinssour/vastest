from flask import Flask, request, abort
from flask import Flask, request, session, render_template, redirect, url_for, jsonify
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
import random as r
import dateutil.parser


app = Flask(__name__)

app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# @app.route("/")
# def hello_world():
#     html = f"<h1>Deployed with Zeet!!</h1>"
#     return html
	
def getLoginDetails():
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
            userId = 0
        else:
            loggedIn = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = ?", (session['email'], ))
            userId, firstName = cur.fetchone()
            cur.execute("SELECT count(productId) FROM kart WHERE userId = ?", (userId, ))
            noOfItems = cur.fetchone()[0]
    conn.close()
    return (loggedIn, firstName, noOfItems, userId)

@app.route("/")
def root():
    loggedIn, firstName, noOfItems, userId = getLoginDetails()
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock FROM products')
        itemData = cur.fetchall()
        cur.execute('SELECT categoryId, name FROM categories')
        categoryData = cur.fetchall()
    itemData = parser(itemData)   
    return render_template('index.html', itemData=itemData,userId=userId, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryData=categoryData)


if __name__ == '__main__':
	app.run(host="0.0.0.0", port=3000)
