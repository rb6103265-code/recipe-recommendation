# app.py
import os, json
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, verify_jwt_in_request
)

from models import db, User, Recipe, Rating
from recommender import get_recommendations
from weather import fetch_weather

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///recipes.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

    db.init_app(app)
    JWTManager(app)
    CORS(app)

    return app

app = create_app()

# ✅ Allow CORS preflight but enforce JWT on protected endpoints
@app.before_request
def check_jwt_if_needed():
    if request.endpoint in ("recommend", "feedback"):
        if request.method != "OPTIONS":  # skip CORS preflight
            verify_jwt_in_request()

# ------------------------
# Helpers
# ------------------------
def recipe_to_dict(r: Recipe):
    try:
        ingredients = json.loads(r.ingredients)
    except Exception:
        ingredients = r.ingredients.split(',') if r.ingredients else []
    try:
        nutrition = json.loads(r.nutrition) if r.nutrition else {}
    except Exception:
        nutrition = {}
    return {
        'id': r.id,
        'title': r.title,
        'ingredients': ingredients,
        'instructions': r.instructions,
        'prep_time_minutes': r.prep_time_minutes,
        'tags': [t.strip() for t in (r.tags or '').split(',') if t.strip()],
        'nutrition': nutrition,
        'servings': r.servings
    }

# ------------------------
# Routes
# ------------------------
@app.route('/')
def home():
    return jsonify({"msg": "Recipe Recommender API running"})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    if not all(k in data for k in ('name','email','password')):
        return jsonify({'msg':'name, email and password required'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'msg':'Email already registered'}), 400
    user = User(
        name=data.get('name'),
        email=data.get('email'),
        password_hash=generate_password_hash(data.get('password')),
        age=data.get('age'),
        gender=data.get('gender'),
        dietary_pref=data.get('dietary_pref'),
        allergies=','.join(data.get('allergies', [])) if isinstance(data.get('allergies'), list) else data.get('allergies'),
        health_goals=data.get('health_goals')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'msg':'registered'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    if 'email' not in data or 'password' not in data:
        return jsonify({'msg':'email & password required'}), 400
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'msg':'bad credentials'}), 401
    
    # ✅ identity must be string
    token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': token, 'user_id': user.id})

@app.route('/recipes/recommend', methods=['GET'])
@jwt_required()
def recommend():
    # ✅ cast identity back to int
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    location = request.args.get('location') or data.get('location') or 'Delhi'
    weather = fetch_weather(location)
    recs = get_recommendations(user_id, weather, top_k=10)
    return jsonify({'weather': weather, 'recommendations': recs})

@app.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    return jsonify(recipe_to_dict(r))

@app.route('/feedback', methods=['POST'])
@jwt_required()
def feedback():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    if 'recipe_id' not in data or 'rating' not in data:
        return jsonify({'msg':'recipe_id and rating required'}), 400
    rating = Rating(
        user_id=user_id,
        recipe_id=int(data['recipe_id']),
        rating=int(data['rating']),
        comment=data.get('comment')
    )
    db.session.add(rating)
    db.session.commit()
    return jsonify({'msg':'thanks for feedback'})

# ------------------------
# Run
# ------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("✅ Starting Flask server at http://127.0.0.1:5000 ...")
    app.run(debug=True, host='0.0.0.0', port=5000)
