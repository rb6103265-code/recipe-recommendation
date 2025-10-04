# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    dietary_pref = db.Column(db.String(120))
    allergies = db.Column(db.String(255))
    health_goals = db.Column(db.String(255))

    ratings = db.relationship('Rating', backref='user', lazy=True)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    ingredients = db.Column(db.Text)  # JSON string or comma-separated
    instructions = db.Column(db.Text)
    prep_time_minutes = db.Column(db.Integer)
    tags = db.Column(db.String(255))
    nutrition = db.Column(db.Text)  # JSON string
    servings = db.Column(db.Integer)

    ratings = db.relationship('Rating', backref='recipe', lazy=True)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
