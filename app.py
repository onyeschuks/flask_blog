from crypt import methods
import os
from bson import ObjectId
from flask import Flask, url_for, request, redirect, render_template, flash, session
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRETE_KEY')
client = MongoClient(os.getenv('MONGO_URL'))
flask_blog = client['flask_blog']
users_collection = flask_blog['users']
posts_collection = flask_blog['posts']
comments_collection = flask_blog['comments']


@app.route('/')
@app.route('/')
def home():
    if 'user' not in session:
        flash('please log in to access the home page', 'danger')
        return redirect(url_for('login'))

    posts = list(posts_collection.find())  # Convert to list to prevent cursor issues
    print(posts)  # Debugging: check if posts are being retrieved
    return render_template('home.html', user=session['user'], posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # check if the user already exists
        user = users_collection.find_one({'email': email})
        if user is not None:
            flash('email already exists', 'warning')
            return redirect(url_for('login'))

        # hash the password
        hashed_password = generate_password_hash(password)
        users_collection.insert_one({
            'email': email,
            'username': username,
            'password': hashed_password
        })
        flash('registration successful', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # find user from the database
        user = users_collection.find_one({'email': email})
        if user:
            if check_password_hash(user['password'], password):
                session['user'] = user['username']
                flash('login successful', 'success')
                return redirect(url_for('home'))
            flash('invalid credential', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('logout succesful', 'info')
    return redirect(url_for('login'))

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user' not in session:
        flash('please login to create a post', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files['image']
        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join('static/uploads', image_filename))
        else:
            image_filename = None
        post = {
            'title': title,
            'content': content,
            'image': image_filename,
            'author': session['user']
        }

        posts_collection.insert_one(post)
        flash('new post create', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html')

@app.route('/posts/<post_id>')
def post_detail(post_id):
    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    comments = comments_collection.find({"post_id": ObjectId(post_id) })

    return render_template('post_detail.html', post=post, comments=comments)

@app.route('/post/<post_id>/add_comment', methods=['POST'])
def add_comment(post_id):
    if 'user' not in session:
        flash('Please log in to add a comment.', 'danger')
        return redirect(url_for('login'))

    comment_text = request.form['comment']
    comment = {
        'post_id': ObjectId(post_id),
        'author': session['user'],
        'text': comment_text
    }
    comments_collection.insert_one(comment)
    flash('Comment added!', 'success')
    return redirect(url_for('post_detail', post_id=post_id))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
