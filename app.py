import sqlite3
import json
import datetime as dt
from bs4 import BeautifulSoup
from helpers import login_required,set_quote,QUOTES,QUOTE
from urllib.request import urlopen
from flask import Flask,render_template,redirect,request,session,jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


# Configure application
app = Flask(__name__)

# Configure GOOGLE BOOKS API
url='https://www.googleapis.com/books/v1/volumes?q='

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Load db
con = sqlite3.connect("project.db",check_same_thread=False)
con.row_factory= lambda cursor, row: row[0]
cur = con.cursor()

# Get this year and list of years before
today = dt.date.today()
THIS_YEAR = today.year
YEARS = [(THIS_YEAR-i) for i in range(80)]

# Set quote of the day
if today != QUOTE[0]:
    QUOTE = set_quote(QUOTES)
else:
    QUOTE_OF_DAY = QUOTE[1]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html",message="")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check if username already exists
        usernames = cur.execute("SELECT username FROM users").fetchall()
        if username in usernames:
            message = f"Registration failed. Username {username} already exists."
            return render_template("register.html",message= message)

        # Check if passwords match
        if password != confirmation:
            return render_template("register.html",message="Registration failed. Passwords need to match.")

        # Load user into db
        params = (username,generate_password_hash(password))
        cur.execute("INSERT INTO users ('username','password') VALUES (?,?)",params)
        con.commit()

        # Remember session
        session["user_id"] = cur.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone()
        return redirect("/home")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html",message="")
    else:
        # Check if user exists
        username = request.form.get("username")
        if username not in cur.execute("SELECT username FROM users").fetchall():
            return render_template("login.html",message="Log in failed. Username does not exists.")

        # Check if password is correct
        passw = cur.execute("SELECT password FROM users WHERE username=?",(username,)).fetchone()
        if not check_password_hash(passw,request.form.get("password")):
            return render_template("login.html",message="Log in failed. Password not correct.")

        # Remember session
        session["user_id"] = cur.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone()
        return redirect("/home")

@app.route("/logout")
def logout():
    # Forget user session
    session.clear()
    return redirect("/")

@app.route("/home")
@login_required
def home():
    return render_template("home.html",quote=QUOTE_OF_DAY)

@app.route("/add", methods=["POST","GET"])
@login_required
def add():
    if request.method == "GET":
        return render_template("add.html")
    else:
        return render_template("manually.html",title=request.form.get("livebox"),author="",published="",category="",image="static/book_cover.jpg",this_year=THIS_YEAR,years=YEARS)

@app.route("/livesearch",methods=["POST","GET"])
@login_required
def livesearch():
    if request.method == "POST":
        # Get user's input dynamically
        query = request.form.get("text")
        query = query.replace(" ","+")

        # Get books data from GOOGLE BOOKS
        response = urlopen(f"https://www.googleapis.com/books/v1/volumes?q={query}&printType=books&maxResults=10&langRestrict=en")
        data = json.load(response)["items"]
        book_ids = [book["id"] for book in data][:3]
        books = []
        for id in book_ids:
            response = urlopen(f"https://www.googleapis.com/books/v1/volumes?q={id}")
            data = json.load(response)["items"][0]["volumeInfo"]
            book = {}
            book["title"] = data["title"]
            book["authors"] = data["authors"][0]
            book["published"] = data["publishedDate"]
            book["category"] = data["categories"][0]
            book["image"] = data["imageLinks"]["smallThumbnail"]
            books.append(book)

        # Load temp search data
        user_id = session["user_id"]
        with open(f"temp/user{user_id}_search.json","w") as file:
            json.dump(books,file)

        # Send data back to web page
        return jsonify(books)

@app.route("/suggestion1",methods=["POST"])
@login_required
def suggestion1():
    if request.method == "POST":
        # Create individual temp file for user
        user_id = session["user_id"]
        with open(f"temp/user{user_id}_search.json","r") as file:
            book = json.load(file)[0]
        return render_template("manually.html",title=book["title"],author=book["authors"],published=book["published"],category=book["category"],image=book["image"],this_year=THIS_YEAR,years=YEARS)

@app.route("/suggestion2",methods=["POST"])
@login_required
def suggestion2():
    if request.method == "POST":
        user_id = session["user_id"]
        with open(f"temp/user{user_id}_search.json","r") as file:
            book = json.load(file)[1]
        return render_template("manually.html",title=book["title"],author=book["authors"],published=book["published"],category=book["category"],image=book["image"],this_year=THIS_YEAR,years=YEARS)

@app.route("/suggestion3",methods=["POST"])
@login_required
def suggestion3():
    if request.method == "POST":
        user_id = session["user_id"]
        with open(f"temp/user{user_id}_search.json","r") as file:
            book = json.load(file)[2]
        return render_template("manually.html",title=book["title"],author=book["authors"],published=book["published"],category=book["category"],image=book["image"],this_year=THIS_YEAR,years=YEARS)

@app.route("/manually",methods=["POST"])
@login_required
def manually():
    if request.method == "POST":

        # Check if book in db, load into db if it isn't
        title,author,category,published,image = request.form.get("title"),request.form.get("author"),request.form.get("category"),request.form.get("published"),request.form.get("coverImageHidden")
        params = (title,author,category,published,image)
        book_id = cur.execute("SELECT book_id FROM books WHERE title=? AND author=? AND category=? AND published=? AND cover_image=?",params).fetchone()
        if not book_id:
            cur.execute("INSERT INTO books ('title','author','category','published','cover_image') VALUES (?,?,?,?,?)",params)
            con.commit()

        # Load comments into db
        book_id = cur.execute("SELECT book_id FROM books WHERE title=? AND author=? AND category=? AND published=? AND cover_image=?",params).fetchone()
        user_id = session["user_id"]
        comment_params = (user_id,book_id,request.form.get(f"comment1"),request.form.get(f"comment2"),request.form.get(f"comment3"))
        cur.execute("INSERT INTO comments ('user_id','book_id','text1','text2','text3') VALUES (?,?,?,?,?)",comment_params)
        con.commit()

        # Load book into user's books
        date_params = (user_id,book_id,request.form.get("finished"))
        cur.execute("INSERT INTO user_books ('user_id','book_id','finished_reading') VALUES (?,?,?)",date_params)
        con.commit()
        return redirect("/list")

@app.route("/list",methods=["GET","POST"])
@login_required
def list():
    if request.method == "GET":
        # Load books list from db
        user_id = session["user_id"]
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        params = (user_id,)
        books = cur.execute("SELECT books.book_id,title,author,category,published,cover_image,text1,text2,text3,finished_reading FROM books INNER JOIN user_books ON books.book_id = user_books.book_id INNER JOIN comments ON user_books.user_id = comments.user_id AND user_books.book_id = comments.book_id WHERE comments.user_id = ? GROUP BY title ORDER BY finished_reading DESC",params).fetchall()
        return render_template("list.html",books=books)
