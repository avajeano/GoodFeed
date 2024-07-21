"""SQLAlchemy models for Restaurants App."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import requests 
from datetime import datetime 

bcrypt = Bcrypt()
db = SQLAlchemy()

class Restaurant(db.Model):
    """A restaurant."""

    __tablename__ = 'restaurants'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.Text, nullable = False)
    cuisine = db.Column(db.Text, nullable = False)
    boro = db.Column(db.Text, nullable = False)
    building_number = db.Column(db.Text, nullable = False)
    street = db.Column(db.Text, nullable = False)
    zipcode = db.Column(db.Text, nullable = False)

    bookmarks = db.relationship('Bookmark', backref='restaurant')
    reviews = db.relationship('Review', backref='restaurant')
 
    @classmethod
    def get_restaurants(cls):
        """Retrieve a restaurants from the API only if the restaurant object has all required fields."""

        url = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            restaurants = []
            for item in data:
                # check if all required fields are present and not empty
                if (item.get('dba') and item.get('cuisine_description') and
                        item.get('boro') and item.get('building') and
                        item.get('street') and item.get('zipcode')):
                    
                    # check if the restaurant already exists in the database
                    restaurant = cls.query.filter_by(
                        name=item.get('dba'),
                        cuisine=item.get('cuisine_description'),
                        boro=item.get('boro'),
                        building_number=item.get('building'),
                        street=item.get('street'),
                        zipcode=item.get('zipcode')
                    ).first()

                    if not restaurant:
                        # create a new restaurant object and commit
                        restaurant = cls(
                            name=item.get('dba'),
                            cuisine=item.get('cuisine_description'),
                            boro=item.get('boro'),
                            building_number=item.get('building'),
                            street=item.get('street'),
                            zipcode=item.get('zipcode')
                        )
                        db.session.add(restaurant)
                        db.session.commit()
                    
                    # append the restaurant retrieved from the database 
                    restaurants.append(restaurant)
            return restaurants
        else:
            return []

    @classmethod
    def get_unique_restaurants(cls, name=None):
        """Ignore duplicate restaurants in the API."""
        url = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
        params = {"dba": name} if name else {}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            unique_restaurants = {}
            for item in data:
                if(item.get('dba') and 
                   item.get('cuisine_description') and
                   item.get('boro') and 
                   item.get('building') and
                   item.get('street') and 
                   item.get('zipcode')):
                    
                   address = f"{item.get('building')} {item.get('street')} {item.get('boro')} {item.get('zipcode')}"

                   if address not in unique_restaurants:
                        # check if the restaurant already exists in the db
                        restaurant = cls.query.filter_by(
                            name=item.get('dba'),
                            cuisine=item.get('cuisine_description'),
                            boro=item.get('boro'),
                            building_number=item.get('building'),
                            street=item.get('street'),
                            zipcode=item.get('zipcode')
                        ).first()

                        if restaurant:
                            unique_restaurants[address] = restaurant
                        else:
                            new_restaurant = cls(
                                name=item.get('dba'),
                                cuisine=item.get('cuisine_description'),
                                boro=item.get('boro'),
                                building_number=item.get('building'),
                                street=item.get('street'),
                                zipcode=item.get('zipcode')
                            )
                            db.session.add(new_restaurant)
                            db.session.commit()
                            unique_restaurants[address] = new_restaurant

            for rest in unique_restaurants.values():
                print(rest.id)
            
            return list(unique_restaurants.values())
        else:
            return []
        
class Follows(db.Model):
    """Connection of a follwer."""

    __tablename__ = 'follows'

    user_being_followed_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="cascade"), primary_key=True)
    user_following_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="cascade"), primary_key=True)


class User(db.Model):
    """A user."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    
    bookmarks = db.relationship('Bookmark', backref='user')
    reviews = db.relationship('Review', backref='user')

    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_being_followed_id == id),
        secondaryjoin=(Follows.user_following_id == id)
    )

    following = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_following_id == id),
        secondaryjoin=(Follows.user_being_followed_id == id)
    )

    @classmethod
    def register(cls, username, pwd, email, first_name, last_name):
         """Register user with hashed password & return user."""

         hashed = bcrypt.generate_password_hash(pwd)
         # turn bytestring into normal (unicode utf8) string
         hashed_utf8 = hashed.decode("utf8")

         # return instance of user with username and hashed pwd
         return cls(username=username, password=hashed_utf8, email=email, first_name=first_name, last_name=last_name)
    
    @classmethod
    def authenticate(cls, username, pwd):
         """Validate that user exists & password is correct.
         Return user if valid; else return False.
         """

         u = User.query.filter_by(username=username).first()

         if u and bcrypt.check_password_hash(u.password, pwd):
              # return user instance 
              return u
         else:
              return False 
         
class Bookmark(db.Model):
    """Mapping user bookmarks to a restaurant."""

    __tablename__ = "bookmarks"

    id = id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id', ondelete='CASCADE'))

class Review(db.Model):
    """Mapping user reviews to a restaurant."""

    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.String(150), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id', ondelete='CASCADE'))

def connect_db(app):
    """Database connects to the Flask app."""
    
    app.app_context().push
    db.app = app
    db.init_app(app)