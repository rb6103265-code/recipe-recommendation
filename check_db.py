# check_db.py
from models import Recipe
from app import app, db

with app.app_context():
    recs = Recipe.query.limit(20).all()  # fetch first 20 recipes
    for r in recs:
        print("Title:", r.title)
        print("Tags:", r.tags)
        print("-" * 40)
