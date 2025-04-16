from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
import math
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load parameters from config.json
local_server = os.getenv("local_server", "true").lower() == "true"

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Mail Config
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv("GMAIL_USER"),
    MAIL_PASSWORD=os.getenv("GMAIL_PASSWORD")
)
mail = Mail(app)

# Upload folder config
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")

# Database URI config
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("LOCAL_URI")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("PROD_URI")

db = SQLAlchemy(app)

# Define your models
class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(12), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

class Files(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    upload_files = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(12), nullable=True)

# Routes
@app.route("/")
def home():
    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts) / int(params['no_of_post']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_post']):(page - 1) * int(params['no_of_post']) + int(params['no_of_post'])]
    prev = "#" if page == 1 else f"/?page={page - 1}"
    next = "#" if page == last else f"/?page={page + 1}"
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/upload_files", methods=['GET', 'POST'])
def upload_file():
    myfiles = Files.query.all()
    return render_template('upload_files.html', myfiles=myfiles, params=params)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/uploder", methods=['GET', 'POST'])
def uploder():
    if 'user' in session and session['user'] == os.getenv("USER_NAME"):
        if request.method == "POST":
            f = request.files['file1']
            filename = secure_filename(f.filename)
            date = datetime.now()
            f.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            addfile = Files(upload_files=filename, date=date)
            db.session.add(addfile)
            db.session.commit()
            return render_template("successful.html")

@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/dashbord")

@app.route("/dashbord", methods=['GET', 'POST'])
def dashbord():
    if 'user' in session and session['user'] == os.getenv("USER_NAME"):
        posts = Post.query.all()
        myfiles = Files.query.all()
        return render_template('dashbord.html', params=params, posts=posts, myfiles=myfiles)

    if request.method == "POST":
        username = request.form.get('uname')
        userpassword = request.form.get('pass')
        if username == os.getenv("USER_NAME") and userpassword == os.getenv("USER_PASSWORD"):
            session["user"] = username
            posts = Post.query.all()
            myfiles = Files.query.all()
            return render_template('dashbord.html', params=params, posts=posts, myfiles=myfiles)

    return render_template('login.html', params=params)

@app.route("/delete_post/<string:sno>", methods=['GET', 'POST'])
def delete_post(sno):
    if 'user' in session and session['user'] == os.getenv("USER_NAME"):
        post = Post.query.filter_by(sno=sno).first()
        if post:
            db.session.delete(post)
            db.session.commit()
            return redirect(url_for('dashbord'))
        return "Error"

@app.route("/delete_file/<string:sno>", methods=['GET', 'POST'])
def delete_file(sno):
    if 'user' in session and session['user'] == os.getenv("USER_NAME"):
        myfiles = Files.query.filter_by(sno=sno).first()
        if myfiles:
            db.session.delete(myfiles)
            db.session.commit()
            return redirect(url_for('dashbord'))
        return "Error"

@app.route("/edit/<int:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == os.getenv("USER_NAME"):
        if request.method == 'POST':
            box_title = request.form.get('title')
            box_tagline = request.form.get('tline')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == 0:
                add_post = Post(title=box_title, slug=box_slug, content=box_content,
                                tagline=box_tagline, date=date, img_file=box_img_file)
                db.session.add(add_post)
                db.session.commit()
                return redirect(url_for('edit', sno=add_post.sno))
            else:
                post = Post.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = box_slug
                post.content = box_content
                post.tagline = box_tagline
                post.date = date
                post.img_file = box_img_file
                db.session.commit()
                return redirect(url_for('edit', sno=sno))

        post = Post.query.filter_by(sno=sno).first() if sno != 0 else None
        return render_template('edit.html', params=params, sno=sno, post=post)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    posts = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, posts=posts)

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        variable_name = request.form.get('name')
        variable_phone = request.form.get('phone')
        variable_email = request.form.get('email')
        variable_message = request.form.get('message')
        entry_variable = Contact(name=variable_name, phone_num=variable_phone,
                                 message=variable_message, date=datetime.now(),
                                 email=variable_email)
        db.session.add(entry_variable)
        db.session.commit()
        mail.send_message('New message from ' + variable_name,
                          sender=variable_email,
                          recipients=[os.getenv("GMAIL_USER")],
                          body=variable_message + "\n" + variable_phone)
    return render_template('contact.html', params=params)

# Run app
if __name__ == "__main__":
    app.run(debug=True)

