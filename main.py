from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
import json
import os
import math
from werkzeug.utils import secure_filename
from datetime import datetime
# from flask_mail import Mail

with open("config.json", "r") as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

# app.config.update(
#     MAIL_SERVER = 'smtp.gmail.com',
#     MAIL_PORT = '465',
#     MAIL_USE_SSL = True,
#     MAIL_USERNAME = params['gmail_user'],
#     MAIL_PASSWORD = params['gmail_password']
# )
# mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)


# sno	name	email	phone_num	msg	date
class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    sub_title = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(21), nullable=False)
    img_file = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    i = (page-1)*int(params['no_of_posts'])
    posts = posts[i : i + int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>")
def delete(sno):
    if "user" in session and session['user']==params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')

@app.route("/uploader" , methods=['GET', 'POST'])
def uploader():
    if "user" in session and session['user']==params['admin_user']:
        if request.method=='POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return redirect('/dashboard')


@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    if "user" in session and session['user']==params['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method=="POST":
        username = request.form.get("uname")
        userpass = request.form.get("upass")
        if username==params['admin_user'] and userpass==params['admin_password']:
            # set the session variable
            session['user']=username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)
    else:
        return render_template("login.html", params=params)

@app.route("/edit/<string:sno>" , methods=['GET', 'POST'])
def edit(sno):
    if "user" in session and session['user']==params['admin_user']:
        if request.method=="POST":
            title = request.form.get('title')
            sub_title = request.form.get('sub_title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            author = request.form.get('author')
            img_file = request.form.get('img_file')
        
            if sno=='0':
                post = Posts(title=title, slug=slug, content=content, sub_title=sub_title, author=author, img_file=img_file, date=datetime.now())
                db.session.add(post)
                db.session.commit()
                # return redirect('/edit/0')
                posts = Posts.query.all()
                return render_template("dashboard.html", params=params, posts=posts)
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.sub_title = sub_title
                post.slug = slug
                post.content = content
                post.author = author
                post.img_file = img_file
                db.session.commit()
                return redirect('/edit/'+sno)
    post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post, sno=sno)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, email=email, phone_num=phone, msg=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New message from ' + name, sender = email, recipients = [params['gmail_user']], body = message + "\n" + phone)
    return render_template('contact.html', params=params)


app.run(debug=True)