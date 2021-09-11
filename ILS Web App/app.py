from flask import Flask, redirect, url_for, render_template, request, session, flash
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker
import pandas as pd

from flaskext.mysql import MySQL
from flask_mysqldb import MySQL

from flask_pymongo import PyMongo
from pymongo import MongoClient
import re
import datetime
from datetime import datetime

app = Flask(__name__)
app.secret_key = "bt2102"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Placeholder'
app.config['MYSQL_DB'] = 'ILS'
app.config["MONGO_URI"] = "mongodb://localhost:27017/ILS"

mysql = MySQL(app)
mongo = PyMongo(app)

engine = create_engine('mysql+mysqlconnector://root:Placeholder@localhost/ILS')
Session = sessionmaker(bind=engine)
sqlsession = Session()

#JSON Data Processing for cleaner display
collection = mongo.db['books']
displayall = list(collection.find({}))
#Remove brackets/only take %YYYY-%MM-%%DD
for each in displayall:
    date = each['publishedDate'][11:21]
    datequery = {"publishedDate": each["publishedDate"]}
    newdate = {"$set": {"publishedDate": date}}

    author = each["authors"][1:-1]
    authorquery = {"authors": each["authors"]}
    newauthor = {"$set": {"authors": author}}


    category = each["categories"][1:-1]
    categoryquery = {"categories": each["categories"]}
    newcategory = {"$set": {"categories": category}}
    
    if date != "":
        collection.update(datequery, newdate)
        collection.update(authorquery, newauthor)
        collection.update(categoryquery, newcategory)
    
#Flask Program
@app.route("/", methods=["POST", "GET"])
def home():
    return render_template("index.html")

@app.route("/signup", methods=["POST", "GET"])
def signup():
    #session.pop('_flashes', None)
    if request.method == "POST":
        connection = engine.connect()
        user = request.form["username"]
        #check if username is used in USER
        query = text("SELECT * FROM USER WHERE userID =:x")
        resultuser = connection.execute(query, x=user)
        resultuser = resultuser.rowcount
        #check if username is used in ADMIN
        query = text("SELECT * FROM ADMIN WHERE userID =:x")
        resultadmin = connection.execute(query, x=user)
        resultadmin = resultadmin.rowcount
        if resultuser == 0 and resultadmin == 0:
            password = request.form["password"]
            query = "INSERT INTO USER VALUES (:x, :y)"
            query_data = {'x': user, 'y': password}
            sqlsession.execute(query, query_data)
            sqlsession.commit()
            flash("Sign up successful")
            return redirect(url_for("login"))
        else:
            flash("Username in use")
    return render_template("signup.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    connection = engine.connect()
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]
        query = text("SELECT * FROM USER WHERE userID = :x")
        resultuser = connection.execute(query, x=user)
        query = text("SELECT * FROM ADMIN WHERE userID = :x")
        resultadmin = connection.execute(query, x=user)
        if resultuser.rowcount == 1:
            for row in resultuser:
                #check if userID and password match database
                if row['userID'] == user and row['password'] == password:
                    flash("Login Successful!")
                    session["user"] = user
                    session["password"] = password
                    session["usertype"] = "MEMBER"
                    connection.close()
                    return redirect(url_for("user"))
        else:
            for row in resultadmin:
                #check if userID and password match database
                if row['userID'] == user and row['password'] == password:
                    flash("Login Successful!")
                    session["user"] = user
                    session["password"] = password
                    session["usertype"] = "ADMIN"
                    connection.close()
                    return redirect(url_for("admin"))
        flash("Invalid username or password.")
        connection.close()
        return render_template("login.html")
    else:
        if "user" in session and session["usertype"] != "ADMIN":
            flash("Already Logged In!")
            return redirect(url_for("user"))
        elif "user" in session and session["usertype"] == "ADMIN":
            flash("Already Logged In!")
            return redirect(url_for("admin"))
        return render_template("login.html")

@app.route("/booksearch", methods=["POST", "GET"])
def booksearch():
    if "user" in session and session["usertype"] != "ADMIN":
        connect = engine.connect()
        user = session["user"]
        collection = mongo.db['books']
        displayall = list(collection.find({}))

        #Retrieve status from book sql
        queryid = text("SELECT 'AVAILABLE' AS status, bookID FROM BOOK WHERE bookID NOT IN (SELECT bookID FROM LOAN WHERE dateTimeReturned IS NULL);")
        resultproxy = connect.execute(queryid)
        #Convert resultproxy into a list
        d, a = {}, []
        for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
            for column, value in rowproxy.items():
                # build up the dictionary
                d = {**d, **{column: value}}
            a.append(d)
        queryid = text("SELECT 'NOT AVAILABLE' AS status, bookID FROM LOAN WHERE dateTimeReturned IS NULL")
        resultproxy = connect.execute(queryid)
        for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
            for column, value in rowproxy.items():
                # build up the dictionary
                d = {**d, **{column: value}}
            a.append(d)
        queryid = text("SELECT 'RESERVED' AS status, bookID FROM BOOKRESERVATION;")
        resultproxy = connect.execute(queryid)
        for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
            for column, value in rowproxy.items():
                # build up the dictionary
                d = {**d, **{column: value}}
            a.append(d)
        newA = []
        for d in a:
            newA.append((d["bookID"], d["status"]))
            
        #Retrieve dateDue, bookID and dateReturned from loan sql
        queryid = text("SELECT dateTimeDue, bookID, dateTimeReturned, userID FROM loan")
        resultproxy = connect.execute(queryid)
        #Convert resultproxy into a list
        d, b = {}, []
        for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
            for column, value in rowproxy.items():
                # build up the dictionary
                d = {**d, **{column: value}}
            b.append(d)
            
        newB = []
        for d in b:
            if d["dateTimeReturned"] == None:
                newB.append((d["bookID"], d["dateTimeDue"]))
        
        for i in range(len(displayall)):
            for bookID, status in newA:
                if int(displayall[i]["_id"]) == bookID:
                    displayall[i]["bookstatus"] = status
                displayall[i]["dateTimeDue"] = ""
                for bookId, due in newB:
                    if int(displayall[i]["_id"]) == bookId:
                        dateDue = due
                        displayall[i]["dateTimeDue"] = dateDue
        
        if request.method == "POST":
            title = request.form["title"]
            myquery = {"title": { '$regex': title, '$options': 'i' }}
            results = list(mongo.db.books.find(myquery))
            resultsCount = len(results)
            for i in range(len(results)):
                for bookID, status in newA:
                    if int(results[i]["_id"]) == bookID:
                        results[i]["status"] = status
                results[i]["dateTimeDue"] = ""
                for bookId, due in newB:
                    if int(results[i]["_id"]) == bookId:
                        dateDue = due
                        results[i]["dateTimeDue"] = dateDue

            return render_template('books.html', results=results, count = resultsCount)
        else:
            return render_template('booksearch.html', results=displayall)
    else:
        flash("You are not logged in")
        return redirect(url_for("login"))

@app.route("/advancedsearch", methods=["POST", "GET"])
def advancedsearch():
    if "user" in session and session["usertype"] != "ADMIN":
        if request.method == "POST":
            connect = engine.connect()
            user = session["user"]
            author = request.form["author"]
            category = request.form["category"]
            year = request.form["publishedyear"]
            myquery = { "$and":[
                        {"authors":{ "$regex": author, "$options": 'i' }},
                        {"categories":{ "$regex": category, "$options": 'i'} },
                        {"publishedDate":{ "$regex": year, "$options": 'i' }}
                         ] }
            results = list(mongo.db.books.find(myquery))
            resultsCount = len(results)

            #Retrieve status from book sql
            queryid = text("SELECT 'AVAILABLE' AS status, bookID FROM BOOK WHERE bookID NOT IN (SELECT bookID FROM LOAN WHERE dateTimeReturned IS NULL);")
            resultproxy = connect.execute(queryid)
            #Convert resultproxy into a list
            d, a = {}, []
            for rowproxy in resultproxy:
            # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
                for column, value in rowproxy.items():
                    # build up the dictionary
                    d = {**d, **{column: value}}
                a.append(d)
            queryid = text("SELECT 'NOT AVAILABLE' AS status, bookID FROM LOAN WHERE dateTimeReturned IS NULL")
            resultproxy = connect.execute(queryid)
            for rowproxy in resultproxy:
            # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
                for column, value in rowproxy.items():
                    # build up the dictionary
                    d = {**d, **{column: value}}
                a.append(d)
            queryid = text("SELECT 'RESERVED' AS status, bookID FROM BOOKRESERVATION;")
            resultproxy = connect.execute(queryid)
            for rowproxy in resultproxy:
            # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
                for column, value in rowproxy.items():
                    # build up the dictionary
                    d = {**d, **{column: value}}
                a.append(d)
            newA = []
            for d in a:
                newA.append((d["bookID"], d["status"]))
            
            #Retrieve dateDue, bookID and dateReturned from loan sql
            queryid = text("SELECT dateTimeDue, bookID, dateTimeReturned, userID FROM loan")
            resultproxy = connect.execute(queryid)
            #Convert resultproxy into a list
            d, b = {}, []
            for rowproxy in resultproxy:
            # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
                for column, value in rowproxy.items():
                    # build up the dictionary
                    d = {**d, **{column: value}}
                b.append(d)
            
            newB = []
            for d in b:
                if d["dateTimeReturned"] == None:
                    newB.append((d["bookID"], d["dateTimeDue"]))

            for i in range(len(results)):
                for bookID, status in newA:
                    if int(results[i]["_id"]) == bookID:
                        results[i]["status"] = status
                results[i]["dateTimeDue"] = "None"
                for bookId, due in newB:
                    if int(results[i]["_id"]) == bookId:
                        dateDue = due
                        results[i]["dateTimeDue"] = dateDue
            return render_template("books.html", results = results, count = resultsCount)
        else:
            return render_template("advancedsearch.html")
    else:
        return redirect(url_for("login"))

@app.route("/loan/<bookid>/<action>")
def loan(bookid, action):
    session.pop('_flashes', None)
    if "user" in session and session["usertype"] != "ADMIN":
        message = ""
        connection = engine.connect()
        user = session["user"]
        #check if loancount <= 4
        query = text("SELECT * FROM LOAN WHERE userID = :x and dateTimeReturned is NULL")
        result = connection.execute(query, x=user)
        loancount = result.rowcount
        #check if user has outstanding loan
        query = text("SELECT * FROM PAYMENT WHERE userID = :x AND paymentDate IS NULL")
        result = connection.execute(query, x=user)
        finecount = result.rowcount
        #check if book is on loan
        query = text("SELECT * FROM LOAN WHERE bookID = :x and dateTimeReturned is NULL")
        result = connection.execute(query, x=bookid)
        onloan = result.rowcount
        #check if book is reserved
        query = text("SELECT * FROM BOOKRESERVATION WHERE bookID =:x AND userID NOT IN (:y)")
        result = connection.execute(query, x=bookid, y=user)
        reserved = result.rowcount
        #check if user has bookreservation
        query = text("SELECT * FROM BOOKRESERVATION WHERE userID =:x ")
        result = connection.execute(query, x=user)
        bookreservation = result.rowcount
        if loancount < 4 and finecount == 0 and onloan == 0:
            #only allow loan if reserved == 0 or user converts reservation to loan
            if action == "reserve" or reserved == 0:
                query = "INSERT INTO LOAN (dateTimeDue, userID, bookID) VALUES (DATE_ADD(CURDATE(), INTERVAL 28 DAY), :x, :y)"
                query_data = {'x': user, 'y': bookid}
                sqlsession.execute(query, query_data)
                sqlsession.commit()
                if bookreservation > 0:
                    query = "DELETE FROM BOOKRESERVATION WHERE bookID = :x"
                    query_data = {'x': bookid}
                    sqlsession.execute(query, query_data)
                    sqlsession.commit()
                if action == "reserve":
                    #delete reservation record when user converts reservation to loan
                    query = "DELETE FROM BOOKRESERVATION WHERE bookID = :x"
                    query_data = {'x': bookid}
                    sqlsession.execute(query, query_data)
                    sqlsession.commit()
                flash("Loan Successful")
                return redirect(url_for("booksearch"))
            else:
                flash("Book is reserved")
                return redirect(url_for("booksearch"))
        else:
            if loancount >= 4:
                message += " Exceed loan limit!"
            if onloan == 1:
                message += " Book on loan!"
            if finecount > 0:
                message += " You have outstanding fines!"
            flash(message)
            return redirect(url_for("booksearch"))
    else:
        return redirect(url_for("login"))

@app.route("/loan2/<bookid>/<action>")
def loan2(bookid, action):
    session.pop('_flashes', None)
    if "user" in session and session["usertype"] != "ADMIN":
        message = ""
        connection = engine.connect()
        user = session["user"]
        #check if loancount <= 4
        query = text("SELECT * FROM LOAN WHERE userID = :x and dateTimeReturned is NULL")
        result = connection.execute(query, x=user)
        loancount = result.rowcount
        #check if user has outstanding loan
        query = text("SELECT FINE.userID FROM FINE INNER JOIN PAYMENT ON FINE.userID = PAYMENT.userID WHERE FINE.userID = :x AND paymentDate IS NULL")
        result = connection.execute(query, x=user)
        finecount = result.rowcount
        #check if book is on loan
        query = text("SELECT * FROM LOAN WHERE bookID = :x and dateTimeReturned is NULL")
        result = connection.execute(query, x=bookid)
        onloan = result.rowcount
        #check if book is reserved
        query = text("SELECT * FROM BOOKRESERVATION WHERE bookID =:x AND userID NOT IN (:y)")
        result = connection.execute(query, x=bookid, y=user)
        reserved = result.rowcount
        #check if user has bookreservation
        query = text("SELECT * FROM BOOKRESERVATION WHERE userID =:x ")
        result = connection.execute(query, x=user)
        bookreservation = result.rowcount
        if loancount < 4 and finecount == 0 and onloan == 0:
            #only allow loan if reserved == 0 or user converts reservation to loan
            if action == "reserve" or reserved == 0:
                query = "INSERT INTO LOAN (dateTimeDue, userID, bookID) VALUES (DATE_ADD(CURDATE(), INTERVAL 28 DAY), :x, :y)"
                query_data = {'x': user, 'y': bookid}
                sqlsession.execute(query, query_data)
                sqlsession.commit()
                if bookreservation > 0:
                    query = "DELETE FROM BOOKRESERVATION WHERE bookID = :x"
                    query_data = {'x': bookid}
                    sqlsession.execute(query, query_data)
                    sqlsession.commit()
                if action == "reserve":
                    #delete reservation record when user converts reservation to loan
                    query = "DELETE FROM BOOKRESERVATION WHERE bookID = :x"
                    query_data = {'x': bookid}
                    sqlsession.execute(query, query_data)
                    sqlsession.commit()
                flash("Loan Successful")
                return redirect(url_for("booksearch"))
            else:
                flash("Book is reserved")
                return redirect(url_for("booksearch"))
        else:
            if loancount >= 4:
                message += " Exceed loan limit!"
            if onloan == 1:
                message += " Book on loan!"
            if finecount > 0:
                message += " You unpaid fines!"
            flash(message)
            return redirect(url_for("booksearch"))
    else:
        return redirect(url_for("login"))

@app.route("/reserve/<bookid>")
def makereservation(bookid):
    session.pop('_flashes',None)
    if "user" in session and session["usertype"] != "ADMIN":
        user = session["user"]
        connection = engine.connect()
        #check if book is being reserved
        query = text("SELECT * FROM BOOKRESERVATION WHERE bookID = :x")
        result = connection.execute(query, x = bookid)
        reservecount = result.rowcount
        #check if user is currently loaning the book
        query = text("SELECT * FROM LOAN WHERE bookID = :x AND userID = :y AND dateTimeReturned IS NULL")
        result = connection.execute(query, x = bookid, y = user)
        loan = result.rowcount
        if reservecount == 0 and loan == 0:
            query = text("SELECT * FROM payment WHERE userID =:x and paymentDate IS NULL")
            result = connection.execute(query, x=user)
            finecount = result.rowcount
            if finecount != 0:
                flash("You have outstanding fines!")
                return redirect(url_for("booksearch"))
            query = text("INSERT INTO BOOKRESERVATION (bookID, userID) VALUES (:y, :z)")
            query_data = { 'y':bookid, 'z': user}
            sqlsession.execute(query, query_data)
            sqlsession.commit()
            flash("Reservation Successful")
        else:
            if reservecount == 1:
                flash("Book already reserved.")
            else:
                flash("You are already loaning the book.")
        return redirect(url_for("booksearch"))
    else:
        return redirect(url_for("login"))

@app.route("/cancelreservation/<bookid>")
def cancelreservation(bookid):
    if "user" in session and session["usertype"] != "ADMIN":
        connection = engine.connect()
        user = session["user"]
        query = "DELETE FROM BOOKRESERVATION WHERE bookID = :x"
        query_data = {'x':bookid}
        sqlsession.execute(query, query_data)
        sqlsession.commit()
        flash("Reservation Cancelled!")
        return redirect(url_for("reserve"))
    else:
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
        flash("You have been logged out", "info")
        session.pop("user", None)
        session.pop("email", None)
        session.pop('_flashes', None)
        return redirect(url_for("login"))

@app.route("/returnBook/<bookid>/<dateTime>")
def returnBook(bookid, dateTime):
    query = "UPDATE LOAN SET dateTimeReturned=CURDATE() where bookID = :y and userID = :x and dateTimeBorrowed = :z"
    query_dataloan = {'y': bookid, 'x':session["user"], 'z' : dateTime}
    sqlsession.execute(query, query_dataloan)
    sqlsession.commit()
    flash("Return Successful")
    return redirect(url_for('user'))

@app.route("/extendBook/<bookid>/<dateTime>")
def extendBook(bookid, dateTime):
    reservationchecker = "SELECT Loan.bookID, Loan.userID FROM LOAN INNER JOIN bookreservation as br on LOAN.bookID = br.bookID INNER JOIN bookreservation br2 on Loan.userId = br2.userID where Loan.dateTimeReturned is NULL"
    result = sqlsession.execute(reservationchecker)
    
    query_datauser = {'x':session["user"], 'y': bookid, 'z' : dateTime}
    finechecker = "SELECT * FROM PAYMENT where userID = :x and paymentDate is NULL"
    fresult = sqlsession.execute(finechecker, query_datauser)
                
    datechecker = "SELECT IF(curDate() <=dateTimeDue, 0,1) from LOAN where userID = :x and bookID = :y and dateTimeBorrowed = :z"
    dresult = sqlsession.execute(datechecker,query_datauser)
    date = dresult.first()[0]
    if fresult.rowcount > 0:
        message ="Extension Failed! You have outstanding fines! Please pay before you proceed to extend."
    elif date == 1:
        message = "Extension Failed! Please return the book and borrow again, book is already past due date."
    elif result.rowcount > 0:
        message ="Extension Failed! This book is reserved by someone."
    else:
        query = "UPDATE LOAN as l \
        INNER JOIN BOOK as b ON l.bookID = b.bookID \
        SET dateTimeDue = DATE_ADD(dateTimeDue, INTERVAL 4 WEEK) WHERE curDate() <= l.dateTimeDue and l.userID = :x and l.bookID = :y and dateTimeBorrowed = :z"
        sqlsession.execute(query, query_datauser)
        sqlsession.commit()
        message = "Extension Successful!"
    flash(message)
    return redirect(url_for('user'))


@app.route("/home", methods=["POST", "GET"])
def user():
    if "user" in session and session["usertype"] != "ADMIN":
        user = session["user"]
        connect = engine.connect()
        query_datauser = {'x':user}
        global loanID
        query = text("SELECT Book.title, LOAN.dateTimeBorrowed, LOAN.dateTimeDue, loan.bookID FROM LOAN INNER JOIN BOOK ON LOAN.bookID = Book.bookID WHERE userID =:x AND LOAN.dateTimeReturned is NULL")
        loans = connect.execute(query, x=user)
        books = sqlsession.execute("SELECT * from BOOK ORDER BY BookID DESC limit 1")
        numberOfLoans = loans.rowcount
        return render_template('home.html', count=numberOfLoans, currentLoans=loans, title = books)
    else:
        session.pop('_flashes', None)
        flash("You are not logged in")
        return redirect(url_for("login"))

@app.route("/showfine", methods=["POST", "GET"])
def showfine():
    if "user" in session and session["usertype"] != "ADMIN":
        query =  "SELECT fine.paymentID, amount FROM FINE INNER JOIN PAYMENT ON FINE.paymentID=PAYMENT.PAYMENTID WHERE FINE.USERID = :x and Payment.paymentDate IS NULL"
        query_data = {'x': session["user"]}
        result = sqlsession.execute(query, query_data)
        sqlsession.commit()
        numberOfFines = result.rowcount
        return render_template("showfine.html", data=result, count=numberOfFines)
    else:
        return redirect(url_for("login"))

@app.route("/payFine/<paymentid>")
def payFine(paymentid):
    global payID
    payID = paymentid
    return redirect(url_for('makepayment'))

@app.route("/makepayment", methods=["POST", "GET"])
def makepayment():
    if request.method == 'POST':
        cardName = request.form["cardname"]
        cardNumber = request.form["cardnumber"]
        cvv = request.form["cvv"]
        expmonth = request.form["expmonth"]
        expyear = request.form["expyear"]
        if cardName != "" and cardNumber.isdigit() and len(cardNumber) == 16 and cvv.isdigit() and len(cvv) == 3 and expmonth.isdigit() and len(expmonth) == 2  and expyear.isdigit() and len(expyear) == 2 :
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            query = "UPDATE payment SET cardNumber = :x, cvv = :z, expMonth = :a, expYear = :b, paymentDate = :c where paymentID = :y "
            query_data = {'y': payID, 'x': cardNumber, 'z': cvv, 'a': expmonth, 'b': expyear, 'c': timestamp  }
            sqlsession.execute(query, query_data)
            sqlsession.commit()
            flash("Fines Paid")
            return redirect(url_for("showfine"))
        flash("Please enter the correct card information")
        return render_template("makepayment.html")
    else:
        return render_template("makepayment.html")
    
@app.route("/reserve", methods=["POST", "GET"])
def reserve():
    if "user" in session and session["usertype"] != "ADMIN":
        connection = engine.connect()
        user = session["user"]
        #display reservation made by user
        query = text("SELECT r.dateTimeReserved, r.bookID, b.title FROM BOOKRESERVATION r \
                INNER JOIN BOOK b ON r.bookID = b.bookID \
                WHERE r.userID = :x")
        results = connection.execute(query, x=user)
        numberOfRes = results.rowcount
        connection.close()
        return render_template('reservation.html', results=results, count = numberOfRes)
    else:
        return redirect(url_for("login"))

@app.route("/admin", methods=["POST", "GET"])
def admin():
    if "user" in session:
        if session["usertype"] == "ADMIN":
            data = ""
            param =  ""
            if request.method == "POST":
                userDetails = request.form
                requesttype = userDetails['RequestType']
                cur = mysql.connection.cursor()
                if requesttype == "loan": 
                    query = "SELECT * FROM LOAN"
                    cur.execute(query)
                    data = cur.fetchall()
                    cur.close()
                    param = ["Date Borrowed", "Book ID", "User ID","Date Due", "Date Returned"]
                elif requesttype == "reservation":
                    query = "SELECT  * FROM bookReservation"
                    cur.execute(query)
                    data = cur.fetchall()
                    cur.close()
                    param = ["Date Reserved", "Book ID","User ID"]
                else:
                    query = "SELECT  fineDateTime, amount, userID  FROM fine WHERE userID = (SELECT userID FROM Payment where paymentDate IS NULL)"
                    cur.execute(query)
                    data = cur.fetchall()
                    cur.close()
                    param = ["Date of Fine", "Amount", "User ID"]
            return render_template('admin.html', data = data, param = param)
        else:
            return redirect(url_for("user"))
    else:
        return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)


