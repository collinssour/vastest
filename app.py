from flask import Flask, request, session, render_template, redirect, url_for, jsonify
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
import random as r
from twilio.rest import Client


app = Flask(__name__)

app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    itemData = parse(itemData)   
    return render_template('index.html', itemData=itemData,userId=userId, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryData=categoryData)

@app.route("/add")
def admin():
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT categoryId, name FROM categories")
        categories = cur.fetchall()
    conn.close()
    return render_template('add.html', categories=categories)

@app.route("/addItem", methods=["GET", "POST"])
def addItem():
    if request.method == "POST":
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        categoryId = int(request.form['category'])

        #Uploading image procedure
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        imagename = filename
        with sqlite3.connect('db.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute('''INSERT INTO products (name, price, description, image, stock, categoryId) VALUES (?, ?, ?, ?, ?, ?)''', (name, price, description, imagename, stock, categoryId))
                conn.commit()
                msg="added successfully"
            except:
                msg="error occured"
                conn.rollback()
        conn.close()
        print(msg)
        return redirect(url_for('dashboard'))

@app.route("/remove")
def remove():
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock FROM products')
        data = cur.fetchall()
    conn.close()
    return render_template('remove.html', data=data)

@app.route("/removeItem")
def removeItem():
    productId = request.args.get('productId')
    with sqlite3.connect('db.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM products WHERE productID = ?', (productId, ))
            conn.commit()
            msg = "Deleted successsfully"
        except:
            conn.rollback()
            msg = "Error occured"
    conn.close()
    print(msg)
    return redirect(url_for('dashboard'))

@app.route("/removeCat")
def removeCat():
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM categories')
        data = cur.fetchall()
    conn.close()
    return render_template('removecategory.html', data=data)


@app.route("/removeCategory")
def removeCategory():
    categoryId = request.args.get('categoryId')
    with sqlite3.connect('db.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM categories WHERE categoryId = ?', (categoryId, ))
            conn.commit()
            msg = "Deleted successsfully"
        except:
            conn.rollback()
            msg = "Error occured"
    conn.close()
    print(msg)
    return redirect(url_for('dashboard'))

# removing the user
@app.route("/removeUser")
def removeUser():
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users')
        data = cur.fetchall()
    conn.close()
    return render_template('removeuser.html', data=data)


@app.route("/removeUsr")
def removeUsr():
    userId = request.args.get('userId')
    with sqlite3.connect('db.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM users WHERE userId = ?', (userId, ))
            conn.commit()
            msg = "Deleted successsfully"
        except:
            conn.rollback()
            msg = "Error occured"
    conn.close()
    print(msg)
    return redirect(url_for('dashboard'))




@app.route("/displayCategory")
def displayCategory():
        loggedIn, firstName, noOfItems,userId = getLoginDetails()
        categoryId = request.args.get("categoryId")
        with sqlite3.connect('db.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT products.productId, products.name, products.price, products.image, categories.name FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = ?", (categoryId, ))
            data = cur.fetchall()
        conn.close()
        categoryName = data[0][4]
        data = parse(data)
        return render_template('displayCategory.html', data=data, userId=userId, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryName=categoryName)

@app.route("/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems, userId = getLoginDetails()
    return render_template("profileHome.html", userId=userId, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems,userId = getLoginDetails()
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone, code, ucode FROM users WHERE email = ?", (session['email'], ))
        profileData = cur.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profileData, userId=userId, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        with sqlite3.connect('db.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, password FROM users WHERE email = ?", (session['email'], ))
            userId, password = cur.fetchone()
            if (password == oldPassword):
                try:
                    cur.execute("UPDATE users SET password = ? WHERE userId = ?", (newPassword, userId))
                    conn.commit()
                    msg="Changed successfully"
                except:
                    conn.rollback()
                    msg = "Failed"
                return render_template("profileHome.html", msg=msg)
            else:
                msg = "Wrong password"
        conn.close()
        return render_template("changePassword.html", msg=msg)
    else:
        return render_template("changePassword.html")

@app.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        with sqlite3.connect('db.db') as con:
                try:
                    cur = con.cursor()
                    cur.execute('UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, state = ?, country = ?, phone = ? WHERE email = ?', (firstName, lastName, address1, address2, zipcode, city, state, country, phone, email))

                    con.commit()

                except:
                    con.rollback()

        con.close()
        return render_template("profileHome.html")
    
@app.route("/profile/view")
def viewProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems,userId = getLoginDetails()
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (session['email'], ))
        profileData = cur.fetchone()
    conn.close()
    print('----------------',profileData)
    return render_template("profile.html", profileData=profileData,userId=userId, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('login.html', error=error)

@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems,userId = getLoginDetails()
    productId = request.args.get('productId')
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock FROM products WHERE productId = ?', (productId, ))
        productData = cur.fetchone()
    conn.close()
    return render_template("productDescription.html", data=productData, userId=userId, loggedIn = loggedIn, firstName = firstName, noOfItems = noOfItems)

@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        productId = int(request.args.get('productId'))
        with sqlite3.connect('db.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (session['email'], ))
            userId = cur.fetchone()[0]
            try:
                cur.execute("INSERT INTO kart (userId, productId) VALUES (?, ?)", (userId, productId))
                conn.commit()

            except:
                conn.rollback()

        conn.close()
        return redirect(url_for('root'))

@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems,userId = getLoginDetails()
    email = session['email']
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]
        cur.execute("SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = ?", (userId, ))
        products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
    return render_template("cart.html", products = products, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    productId = int(request.args.get('productId'))
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]
        try:
            cur.execute("DELETE FROM kart WHERE userId = ? AND productId = ?", (userId, productId))
            conn.commit()

        except:
            conn.rollback()

    conn.close()
    return redirect(url_for('root'))

@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))

def is_valid(email, password):
    con = sqlite3.connect('db.db')
    cur = con.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        #Parse form data    
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        code = request.form['code']
        ucode = request.form['ucode']



        with sqlite3.connect('db.db') as con:
            try:
                cur = con.cursor()
                cur.execute('INSERT INTO users (password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone, code, ucode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (hashlib.md5(password.encode()).hexdigest(), email, firstName, lastName, address1, address2, zipcode, city, state, country, phone, code, ucode))
                
                con.commit()
                
            except:
                con.rollback()

        con.close()
        return redirect(url_for('dashboard'))

@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")

@app.route("/details")
def details():
    return render_template("detail.html")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
        print(j)
    return ans


@app.route('/pass_val',methods = ['POST', 'GET'])
def pass_val():
    global mobile
    mobile =request.args.get('value')
    print('name',mobile)
    otpgen(mobile)
    return jsonify({'reply':'success'})


otp = '0'

def otpgen(mobile):
    global otp
    for i in range(5):
        print(i, end=", ")
        otp +=  str(r.randint(1,9))
    send_sms(mobile,otp)
    return otp


def send_sms(mobile,otp):
    account_sid = 'AC77140ee2d91748224da609a3a61a6dc8'
    auth_token = '1daed45cb3c78d1066ab2f78498a5e88'

    twilio_number = '14066238105'
    target_number = '91'+mobile
    print('--------------target number ******** -------',target_number,)
    print('--------------otp value ******** -------',otp) 
    print('-------------account_sid--------------',account_sid)
    print('-------------auth_token----------------',auth_token)
    print('---------------twilio_number-----------',twilio_number)

    # client = Client(account_sid, auth_token)

    # message = client.messages.create(
    #                           from_= twilio_number,
    #                           body = 'One Time Password For Registration' +otp,
    #                           to = target_number
    #                       ) 
    # print(message.sid)

@app.route('/otp_val',methods = ['POST', 'GET'])
def otp_val():
    global ootp
    ootp =request.args.get('value')
    print('name',ootp)
    print('--------',otp)
    if(otp == ootp):
        return jsonify({'reply':'success'})
    else:
        return jsonify({'reply':'failed'})


#adding category
@app.route("/addCat")
def adminCat():
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT categoryId, name FROM categories")
        categories = cur.fetchall()
    conn.close()
    return render_template('addCategory.html', categories=categories)

@app.route("/addCategory", methods=["GET", "POST"])
def addCategory():
    if request.method == "POST":
        name = request.form['catName']
        categoryId = int(request.form['catId'])
        with sqlite3.connect('db.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute('''INSERT INTO categories (name,categoryId) VALUES (?, ? )''', (name, categoryId))
                conn.commit()
                msg="added Category successfully"
            except:
                msg="error occured"
                conn.rollback()
        conn.close()
        print(msg)
        return redirect(url_for('dashboard'))
    

@app.route("/dashboard")
def dashboard():
    with sqlite3.connect('db.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT *  FROM users")
        users = cur.fetchall()
        ucount = len(users)

        cur.execute("SELECT *  FROM products")
        products = cur.fetchall()
        pcount = len(products)

        cur.execute("SELECT *  FROM categories")
        categories = cur.fetchall()
        ccount = len(categories)

    conn.close()
    return render_template('dash.html', users=users,ucount=ucount,pcount=pcount,ccount=ccount,products=products,categories=categories)
   

if __name__ == '__main__':
    app.run(debug=False)
