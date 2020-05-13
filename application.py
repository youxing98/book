from flask import Flask, render_template, request, session
from flask_session import Session
from sqlalchemy.sql.elements import and_
from sqlalchemy.sql.elements import or_
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import redirect
from models import *
from helper import login_required
import requests

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
#app.config["SQLALCHEMY_DATABASE_URI"] = "mssql+pymssql://youxing:8601015@hp/C50W"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#Session(app)
db.init_app(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    else:
        usr = request.form.get("username")
        psd = request.form.get("password")

        user = User.query.filter(User.username == usr).first()
        if user is None:
            return render_template("error.html", message="user does not exist.")
        elif not check_password_hash(user.password, psd):
            return render_template("error.html", message="wrong password.")
        session["user_id"] = user.id
        session["user_name"] = user.username
        return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("error.html", message="password mismatch.")
        usr = request.form.get("username")
        psd = generate_password_hash(request.form.get("password"))
        #user = User.query.filter(and_(User.username==usr, User.password==psd)).first()
        user = User.query.filter(User.username == usr).first()
        if user is None:
            user = User(username=usr, password=psd)
            db.session.add(user)
            db.session.commit()
        else:
            return render_template("error.html", message="user already exists.")
        return redirect("/login")

@app.route("/search", methods=["GET"])
@login_required
def search():
    q = "%" + request.args.get("book") + "%"
    books = Books.query.filter(or_(Books.isbn.like(q), Books.author.like(q), Books.title.like(q))).order_by(Books.title).all()
    return render_template("results.html", books=books)

@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    if request.method == "GET":
        book = Books.query.filter(Books.isbn == isbn).all()

        #API call
        goodreads = requests.get("https://www.goodreads.com/book/review_counts.json", \
                                 params={"key": "ggFNlxAAZcrXp1Ipv1LSLw", "isbns": isbn})
        response = goodreads.json()
        response = response["books"][0]
        book.append(response)

        reviews = Review.query.filter(Review.book_id == book[0].id).all()

        return render_template("book.html", bookInfo=book, reviews=reviews)
    #make user revie
    else:
        book = Books.query.filter(Books.isbn == isbn).first()

        user_id = session["user_id"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        book_id = book.id
        review = Review(user_id=user_id, book_id=book_id, comment=comment, rating=rating)
        db.session.add(review)
        db.session.commit()
        return redirect("/book/" + isbn)