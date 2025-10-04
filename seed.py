import pandas as pd
from models import db, Recipe
from app import app

# Map cuisine → region
def map_region(cuisine):
    if not cuisine:
        return "all"
    cuisine = cuisine.lower()
    if "north" in cuisine:
        return "north"
    if "south" in cuisine:
        return "south"
    if any(x in cuisine for x in ["gujarat", "rajasth", "maharashtra", "punjab"]):
        return "west"
    if any(x in cuisine for x in ["bengal", "assam", "oriya"]):
        return "east"
    return "all"

# Map dish/course → weather suitability
def map_weather(course, name):
    name = (name or "").lower()
    if course and "soup" in course.lower():
        return "rainy"
    if any(x in name for x in ["ice cream", "kulfi", "falooda", "sharbat"]):
        return "hot"
    if any(x in name for x in ["halwa", "gajar", "paratha"]):
        return "cold"
    return "all"

with app.app_context():
    # Load dataset
    df = pd.read_csv("indianFoodDatasetCSV.csv")

    # Reset DB
    db.drop_all()
    db.create_all()

    for _, row in df.iterrows():
        recipe = Recipe(
            title=row.get("TranslatedRecipeName"),
            ingredients=row.get("TranslatedIngredients"),
            instructions=row.get("TranslatedInstructions"),
            prep_time_minutes=row.get("PrepTimeInMins"),
            servings=row.get("Servings"),
            tags=",".join(
                filter(None, [
                    map_region(row.get("Cuisine")),
                    map_weather(row.get("Course"), row.get("TranslatedRecipeName")),
                    str(row.get("Course") or "").lower(),
                    str(row.get("Diet") or "").lower()
                ])
            )
        )
        db.session.add(recipe)

    db.session.commit()
    print("✅ Database seeded with 6000+ recipes from indianFoodDatasetCSV.csv")
