import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, session, flash, url_for, request
import requests
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Bookmark
from forms import UserForm, LoginForm, EditUserForm
from sqlalchemy.exc import IntegrityError

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route('/')
def home_page():
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template ('homepage.html', user = user)

@app.route('/about')
def about():
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template('about.html', user=user)

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
    bookmarks = Bookmark.query.filter_by(user_id = session['user_id']).all()

    if 'user_id' not in session:
        flash('Please Login To View')
        return redirect('/')
    if session['user_id'] != user.id:
        return('Access Denied')    

    return render_template('user_homepage.html', user = user, bookmarks=bookmarks)

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


#############################
# Getting the info from the API 
API_BASE_URL = 'https://api.fda.gov/drug/label.json'
API_KEY = os.getenv("API_KEY")


@app.route('/drug_info', methods = ["GET"])
def get_drug_info():
   user = User.query.get(session['user_id']) if 'user_id' in session else None
   drug = request.args.get('drug', '')
   page = request.args.get('page', 1, type = int)
   results_per_page = 5

   if not drug:
       flash('Please enter a valid drug name to search', 'warning')
       return redirect('/')
  
   params = {'api_key': API_KEY,
             'search': f'openfda.brand_name:"{drug}" OR openfda.generic_name:"{drug}"',
             "limit": 20}
   res = requests.get(API_BASE_URL, params = params)
   if res.status_code != 200:
       flash('Drug Not Found', 'danger')
       return redirect('/')
  
   # Extract first drugs info to decide what to display:
   try:
       results = res.json()['results']
   except(KeyError, IndexError):
       flash('No Results Found', 'warning')
       return redirect('/')
   
# Filter the results for brand or generic name matches 
   filtered_results = [
        item for item in results
        if drug.lower() in (item.get('openfda', {}).get('brand_name', [''])[0].lower() or '')
        or drug.lower() in (item.get('openfda', {}).get('generic_name', [''])[0].lower() or '')
    ]
   if not filtered_results:
        flash('No Results Found With Brand or Generic Name', 'warning')
        return redirect('/')
#Sort the results so exact matches show first 
   def match_score(result):
       brand_name = result.get('openfda',{}).get('brand_name', [''])[0].lower()
       generic_name = result.get('openfda',{}).get('generic_name',[''])[0].lower()
       
       if drug.lower() == brand_name:
           return 2
       elif drug.lower() == generic_name:
           return 1
       return 0
   filtered_results.sort(key=match_score, reverse = True)

   #Paginate the results:
   total_results = len(filtered_results)
   total_pages = (total_results + results_per_page -1 ) // results_per_page 
   start = (page-1) * results_per_page
   end = start + results_per_page
   paginated_results = filtered_results[start:end]
   
   
   return render_template('homepage.html', user = user, results=paginated_results, page=page, total_pages=total_pages)

@app.route('/bookmark', methods=['POST'])
def bookmark_drug():
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    brand_name = request.form.get('brand_name')
    generic_name = request.form.get('generic_name')
    active_ingredient = request.form.get('active_ingredient')
    purpose = request.form.get('purpose')
    warnings = request.form.get('warnings')
    indications = request.form.get('indications_and_usage')
    dosage = request.form.get('dosage_and_administration')
    adverse_reactions = request.form.get('adverse_reactions')
    storage = request.form.get('storage')
    
    if 'user_id' not in session:
        flash('Please Sign Up To Bookmark A Medication', 'warning')
        return redirect('/register')
    if session['user_id'] != user.id:
        return('Access Denied')
    
    existing_bookmark = Bookmark.query.filter_by(user_id=user.id, brand_name = brand_name).first()
    if existing_bookmark:
        flash('Already Bookmarked!', 'info')
    else:
        new_bookmark = Bookmark(user_id = session['user_id'], brand_name=brand_name, generic_name=generic_name, active_ingredient=active_ingredient, purpose=purpose, warnings=warnings, indications=indications, dosage=dosage, adverse_reactions=adverse_reactions, storage=storage)
        db.session.add(new_bookmark)
        db.session.commit()
        flash('Bookmarked Successfully', 'info')
    return redirect(request.referrer)
    
@app.route('/bookmark/<int:id>/remove', methods = ["POST"])
def remove_bookmark(id):
    if 'user_id' not in session:
        flash('Please login first!', 'danger')
        return redirect('/login')
    user = User.query.get_or_404(session['user_id'])
    bookmark = Bookmark.query.get_or_404(id)
    if bookmark.user_id == session['user_id']:
        db.session.delete(bookmark)
        db.session.commit()
        flash('Bookmark Removed!', 'success')
        return redirect(url_for('show_user', username = user.username))
