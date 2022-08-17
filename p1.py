from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
from datetime import datetime
import os
import math
import json

with open("templates/config.json", "r") as c:
    params = json.load(c)["params"]
local_server = "True"
app = Flask(__name__)
app.secret_key = 'my_secretkey'
app.config['UPLOAD_FOLDER'] = params['upload_location']
# app.config.update(
#     MAIL_SERVER="smtp.gmail.com",
#     MAIL_PORT="465",
#     MAIL_USE_SSL=True,
#     MAIL_USERNAME=params['mail_user'],
#     MAIL_PASSWORD=params['mail_pass']
# )
# mail = Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]
db = SQLAlchemy(app)


class Contact(db.Model):
    """sno,name,email phone_num message date-time"""

    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=True)
    date_time = db.Column(db.String(12))


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    author = db.Column(db.String(12), nullable=False)
    img_file = db.Column(db.String(12), nullable=False)
    content = db.Column(db.String(12), nullable=False)
    date_time = db.Column(db.String(12))


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    #PAGINATION STARTS HERE>>>>
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']):(page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/blog/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('blog.html', params=params, post=post)


# @app.route('/blog')
# def blog():
#     return render_template('blog.html', params=params)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        msg = request.form.get('message')
        entry = Contact(name=name, email=email, phone_num=phone, message=msg, date_time=datetime.now())
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New message from ' + name,
        #                   sender=email,
        #                   recipients=[params['mail_user']],
        #                   body=msg + "\n" + phone
        #                   )
    return render_template('contact.html', params=params)


@app.route('/search')
def search():
    return render_template('search.html', params=params)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_email']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if (request.method == 'POST'):
        username = request.form.get('email')
        password = request.form.get('pass')
        if (username == params['admin_email'] and password == params['admin_pass']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('signin.html', params=params)


@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_email']):
        if (request.method == "POST"):
            edit_title = request.form.get('title')
            slug = request.form.get('slug')
            author_name = request.form.get('author')
            image = request.form.get('img')
            content = request.form.get('content')
            date = datetime.now()
            if sno == '0':
                post = Posts(title=edit_title, slug=slug, author=author_name, img_file=image, content=content,
                             date_time=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = edit_title
                post.slug = slug
                post.author = author_name
                post.img_file = image
                post.content = content
                post.date_time = date
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post)
@app.route("/uploader" , methods=['GET', 'POST'])
def uploader():
    if ("user" in session and session['user']==params['admin_email']):
        if request.method=='POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully!"
@app.route('/delete/<string:sno>', methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_email']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')
@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')
app.run(debug=True)
