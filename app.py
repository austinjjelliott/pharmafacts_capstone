from flask import Flask, render_template, redirect, session, flash, url_for
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User
from forms import UserForm, LoginForm, EditUserForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///pharmafacts'
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route('/')
def home_page():
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template ('homepage.html', user = user)

@app.route('/register', methods = ["GET", "POST"])
def register_user():
    form = UserForm()
    if form.validate_on_submit():
        # Grab info from form 
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        # Create new user
        new_user = User.register(username, password, email, first_name, last_name)
        # Add user to db.session
        db.session.add(new_user)
        # Check if its valid. If so, add user to DB. If not, show error msg
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username Taken - Please Try Another')
            return render_template('register.html', form = form)
        
        session['user_id'] = new_user.id
        flash('Welcome! Successfully created your account', 'success')
        return redirect(f'/users/{username}')
    
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        flash('You are already logged in. Log out to register new account', 'danger')
        return redirect(f'/users/{user.username}')

    return(render_template('register.html', form = form ))

@app.route('/login', methods = ["GET", "POST"])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f'Welcome Back {user.username}', 'info')
            session['user_id'] = user.id
            return redirect(f'/users/{username}')
        else:
            form.username.errors = ['Invalid Username/Password']
    
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        flash('You are already logged in', 'danger')
        return redirect(f'/users/{user.username}')
    
    return render_template('/login.html', form = form)

@app.route('/users/<username>')
def show_user(username):
    user = User.query.get_or_404(session['user_id'])

    if 'user_id' not in session:
        flash('Please Login To View')
        return redirect('/')
    if session['user_id'] != user.id:
        return('Access Denied')    

    return render_template('user_homepage.html', user = user)

@app.route('/logout')
def logout_user():
    session.pop('user_id')
    flash('You Are Now Logged Out', 'danger')
    return redirect('/')

@app.route('/users/<username>/delete', methods = ["POST"])
def delete_user(username):
    user = User.query.filter_by(username = username).first_or_404()
    
    if 'user_id' not in session:
        flash('You need to login first!')
        return redirect('/login')

    if session['user_id'] != user.id:
        flash('You need to login first!')
        return redirect('/login')
    if user.id == session['user_id']:
        db.session.delete(user)
        db.session.commit()
        session.clear()  # Clear session to log the user out
        flash('Account deleted', 'danger')
        return redirect('/register')
    return render_template('user_homepage.html', user = user)

@app.route('/users/<username>/edit', methods = ["GET", "POST"])
def edit_user(username):
    
    user = User.query.filter_by(username = username).first_or_404()
    form = EditUserForm(obj = user)

    if 'user_id' not in session:
        flash('You need to login first!')
        return redirect('/login')

    if session['user_id'] != user.id:
        flash('You need to login first!')
        return redirect('/login')

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data 
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        if form.password.data:
            user.update_password(form.password.data)

        db.session.commit()
        flash('User has been updated!', 'success')
        return redirect(f'/users/{user.username}')
    return render_template('user_edit.html', user=user, form=form)