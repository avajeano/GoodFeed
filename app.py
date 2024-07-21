from flask import Flask, render_template, session, g, redirect, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from models import db, connect_db, Restaurant, User, Bookmark, Review, Follows
from forms import UserForm, LoginForm, SearchForm, ReviewForm

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///restaurants_app_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = "123"

app.app_context().push()
connect_db(app)

migrate = Migrate(app, db)

#################### USER LOGIN/LOGOUT ####################

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Login user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]    

#################### HOME PAGE ####################

@app.route('/')
def home_page():
    """Home page renders 20 random restaurants from the API."""
    restaurants = Restaurant.get_restaurants()[:20]

    if g.user:
        user_bookmarks = Bookmark.query.filter_by(user_id=g.user.id).all()
        bookmarked_restaurants = [bookmark.restaurant_id for bookmark in user_bookmarks]
    else:
        bookmarked_restaurants=[]

    print("bookmarked Restaurants:", bookmarked_restaurants)
    for restaurant in restaurants:
        print(f"restaurant id: {restaurant.id}, name: {restaurant.name}")

    return render_template('home.html', restaurants=restaurants, bookmarked_restaurants=bookmarked_restaurants)

#################### EXPLORE ####################

@app.route('/explore')
def explore_page():
    """Retrieves all unique cuisines from the database."""
    
    cuisines = db.session.query(Restaurant.cuisine).distinct().order_by(Restaurant.cuisine.asc()).all()
    # removes string from cuisine tuple
    cuisine_string = [cuisine[0] for cuisine in cuisines]

    if g.user:
        user_bookmarks = Bookmark.query.filter_by(user_id=g.user.id).all()
        bookmarked_restaurants = [bookmark.restaurant_id for bookmark in user_bookmarks]
    else:
        bookmarked_restaurants=[]

    return render_template('explore.html', cuisines=cuisine_string, bookmarked_restaurants=bookmarked_restaurants)

@app.route('/cuisine/<restaurant_cuisine>')
def explore_cuisine(restaurant_cuisine):
    """Lists all restaurants from the database that have the selected cuisine."""

    restaurants = Restaurant.query.filter_by(cuisine=restaurant_cuisine).all()

    if g.user:
        user_bookmarks = Bookmark.query.filter_by(user_id=g.user.id).all()
        bookmarked_restaurants = [bookmark.restaurant_id for bookmark in user_bookmarks]
    else:
        bookmarked_restaurants=[]

    return render_template('cuisine.html', cuisine=restaurant_cuisine, restaurants=restaurants, bookmarked_restaurants=bookmarked_restaurants)

#################### SEARCH ####################
@app.route('/search', methods=['GET', 'POST'])
def search_restaurant():
    """Functionality to search for a restaurant by name."""

    form = SearchForm() 
    restaurants = []

    if g.user:
        user_bookmarks = Bookmark.query.filter_by(user_id=g.user.id).all()
        bookmarked_restaurants = [bookmark.restaurant_id for bookmark in user_bookmarks]
    else:
        bookmarked_restaurants = []

    if form.validate_on_submit():
        name = form.name.data.upper()
        restaurants = Restaurant.get_unique_restaurants(name)

    elif request.method == 'GET':
        search = request.args.get('q')
        if search:
            restaurants = Restaurant.get_unique_restaurants(search.upper())
        
    return render_template('search.html', form=form, restaurants=restaurants, bookmarked_restaurants=bookmarked_restaurants)

#################### REGISTER ####################

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """Registers a new user."""

    form = UserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        db.session.commit()
        # adding the username to the session
        session['user_username'] = new_user.username
        return redirect('/')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """User login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
    
        if user:
            do_login(user)
            return redirect('/')
        flash("Invalid credentials.", "danger")
    return render_template('login.html', form=form)

@app.route('/logout')
def logout_user():
     """User logout."""

     do_logout()
     return redirect('/login')

#################### GENERAL USER ROUTES ####################
@app.route('/users')
def list_users():
    """Page with listing of users."""

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/search.html', users=users)

@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of users that logged in user follows."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)

@app.route('/users/<int:user_id>/followers')
def show_followers(user_id):
    """Show list of users followers."""

    if not g.user:
        flash("Access unathorized", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=["POST"])
def add_follow(follow_id):
    """Logged in user adds a follow."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")

@app.route('/users/unfollow/<int:follow_id>', methods=["POST"])
def unfollow(follow_id):
    """Logged in user removes a follow."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")

@app.route('/users/<int:user_id>')
def show_profile(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)
    bookmarks = (Bookmark.query.filter(Bookmark.user_id == user_id).all())
    reviews = (Review
               .query
               .filter(Review.user_id == user_id)
               .order_by(Review.timestamp.desc())
               .all())

    return render_template('profile.html', user=user, bookmarks=bookmarks, reviews=reviews)

#################### BOOKMARK ROUTES ####################
@app.route('/users/bookmarks/<int:user_id>')
def users_bookmarks(user_id):
    """Show restaurants that the user has liked."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)

    # query the bookmarked restaurants for the user
    bookmarked_restaurants = (db.session.query(Restaurant)
                              .join(Bookmark)
                              .filter(Bookmark.user_id == user.id)
                              .all())
    
    return render_template("bookmarks.html", user=user, bookmarked_restaurants=bookmarked_restaurants)

@app.route('/users/add_bookmark', methods=["POST"])
def bookmark_restaurnt():
    """Bookmark or unbookmark a restaurant."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    print("route hit successfully")

    # extract the restaurant data from the html form
    name = request.form.get('name')
    cuisine = request.form.get('cuisine')
    boro = request.form.get('boro')
    building_number = request.form.get('building_number')
    street = request.form.get('street')
    zipcode = request.form.get('zipcode')

    # debugging output
    print(f"received data: {name}, {cuisine}, {boro}, {building_number}, {street}, {zipcode}")

    # check if the restaurant is already in the db
    restaurant = Restaurant.query.filter_by(
        name = name,
        cuisine = cuisine,
        boro = boro,
        building_number = building_number,
        street = street,
        zipcode = zipcode
    ).first()

    if not restaurant:
        # create a new restaurant object
        restaurant = Restaurant(
            name = name,
            cuisine = cuisine,
            boro = boro,
            building_number = building_number,
            street = street,
            zipcode = zipcode
        )

        # save the restaurant to the db
        db.session.add(restaurant)
        db.session.commit()

    # checks if the user has already bookmarked the restaurant
    bookmark = Bookmark.query.filter_by(user_id=g.user.id, restaurant_id=restaurant.id).first()    

    if bookmark:
        # if the user has already bookmarked the restaurant, delete the bookmark
        db.session.delete(bookmark)
        db.session.commit()

        # debugging output to confirm bookmark deletion
        print(f"deleted bookmark for restaurant id: {restaurant.id} by user id: {g.user.id}")
    else: 
        # if the user has not liked the restaurant, create a new bookmark
        new_bookmark = Bookmark(user_id=g.user.id, restaurant_id=restaurant.id)
        db.session.add(new_bookmark)
        db.session.commit()
    return redirect('/')

#################### REVIEW RESTAURANT ROUTES ####################
@app.route('/restaurant/review', methods=["POST"])
def review_id_restaurant():
    """Make sure a restaurant has an id before it's reviewed."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    # extract the restaurant data from the html form
    name = request.form.get('name')
    cuisine = request.form.get('cuisine')
    boro = request.form.get('boro')
    building_number = request.form.get('building_number')
    street = request.form.get('street')
    zipcode = request.form.get('zipcode')

    # check if the restaurant is already in the db
    restaurant = Restaurant.query.filter_by(
        name = name,
        cuisine = cuisine,
        boro = boro,
        building_number = building_number,
        street = street,
        zipcode = zipcode
    ).first()

    if not restaurant:
        # create a new restaurant object
        restaurant = Restaurant(
            name = name,
            cuisine = cuisine,
            boro = boro,
            building_number = building_number,
            street = street,
            zipcode = zipcode
        )

        # save the restaurant to the db
        db.session.add(restaurant)
        db.session.commit()
    
    return redirect(f"/restaurant/review/{restaurant.id}")

@app.route('/restaurant/review/<int:restaurant_id>', methods=["GET", "POST"])
def review_restaurant(restaurant_id):
    """Review a restaurant."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    restaurant = Restaurant.query.get_or_404(restaurant_id)
    form = ReviewForm()

    if form.validate_on_submit():
        review = Review(text=form.review.data, user_id=g.user.id, restaurant_id=restaurant.id)
        db.session.add(review)
        db.session.commit()

        return redirect(f"/restaurant/{restaurant.id}")
    
    return render_template('restaurants/review.html', restaurant=restaurant, form=form)

@app.route('/restaurant/<int:restaurant_id>', methods=["GET", "POST"])
def show_restaurant(restaurant_id):
    """Show reviews and additional information about a restaurant."""

    restaurant = Restaurant.query.get_or_404(restaurant_id)

    # getting reviews in order from the database
    reviews = (Review
               .query
               .filter(Review.restaurant_id == restaurant_id)
               .order_by(Review.timestamp.desc())
               .all())

    return render_template('/restaurants/restaurant.html', restaurant=restaurant, reviews=reviews)

@app.route('/review/<int:review_id>/delete', methods=["POST"])
def delete_review(review_id):
    """Delete a review."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    review = Review.query.get(review_id)

    if review.user_id != g.user.id:
        flash("Access unauthoroized.", "danger")
        return redirect("/")

    db.session.delete(review)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")