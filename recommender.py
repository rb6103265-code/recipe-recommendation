# recommender.py
import random
import logging
from models import Recipe

# Configure simple logging for debugging (shows in Flask console)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# region detection keywords -> normalized region token used in tags
REGION_KEYWORDS = {
    "south": ["kerala", "kottayam", "palakkad", "trivandrum", "thiruvananthapuram", "kochi",
              "tamil", "chennai", "madurai", "karnataka", "bangalore", "andhra", "vizag", "telangana"],
    "north": ["delhi", "punjab", "chandigarh", "uttar", "lucknow", "varanasi", "shimla", "himachal"],
    "west":  ["mumbai", "maharashtra", "gujarat", "rajasthan", "goa"],
    "east":  ["kolkata", "bengal", "west bengal", "assam", "odisha", "manipur", "nagaland"]
}

# high-level keyword groups for matching and type detection
CATEGORY_KEYWORDS = {
    "food":    ["main course", "curry", "rice", "biryani", "paratha", "dosa", "idli", "pulao", "thali", "sabzi", "dal"],
    "drinks":  ["drink", "juice", "lassi", "chai", "coffee", "buttermilk", "sharbat"],
    "soups":   ["soup", "rasam", "stew", "broth", "clear soup"],
    "desserts":["dessert", "sweet", "halwa", "kheer", "kulfi", "ice cream", "gulab", "jalebi", "barfi"],
    "snacks":  ["snack", "chaat", "pakora", "samosa", "vada", "cutlet", "pani puri", "bhel"]
}

# weather-based keyword hints (used to boost matches)
WEATHER_HINTS = {
    "rainy": ["pakora", "chai", "rasam", "soup", "vada"],
    "hot": ["lassi", "juice", "salad", "raita", "ice", "kulfi", "cool"],
    "cold": ["paratha", "hot", "halwa", "gajar", "pudding"]
}

# how many items we want per category
TARGET_COUNTS = {"food": 10, "drinks": 5, "soups": 5, "desserts": 5, "snacks": 5}


def normalize_text(s):
    if not s:
        return ""
    return str(s).strip().lower()


def tags_list(recipe):
    """Return normalized list of tags for a recipe (from tags string)."""
    t = recipe.tags or ""
    return [x.strip().lower() for x in t.split(",") if x.strip()]


def detect_region_from_location(location):
    loc = normalize_text(location)
    if not loc:
        return None
    for region, keys in REGION_KEYWORDS.items():
        for k in keys:
            if k in loc:
                return region
    # fallback: check words that mention north/south/east/west/country
    if "south" in loc or "sindh" in loc:
        return "south"
    if "north" in loc:
        return "north"
    if "west" in loc:
        return "west"
    if "east" in loc:
        return "east"
    return None


def detect_weather_tag(weather):
    if not weather:
        return "all"
    cond = normalize_text(weather.get("condition", ""))
    temp = weather.get("temp")
    if "rain" in cond or "drizzle" in cond or "shower" in cond:
        return "rainy"
    if temp is not None:
        try:
            t = float(temp)
            if t > 30:
                return "hot"
            if t < 15:
                return "cold"
        except Exception:
            pass
    return "all"


def detect_type_from_recipe(recipe):
    """Return one of 'food','drinks','soups','desserts','snacks' by scanning tags and title."""
    tlist = tags_list(recipe)
    title = normalize_text(recipe.title)
    # check tags first
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            # check tags or title name
            if any(kw in tag for tag in tlist) or kw in title:
                return cat
    # fallback heuristics
    if any(x in title for x in ["juice", "lassi", "tea", "coffee", "sharbat"]):
        return "drinks"
    if any(x in title for x in ["soup", "rasam", "stew"]):
        return "soups"
    if any(x in title for x in ["ice", "kulfi", "halwa", "kheer", "gulab", "jalebi"]):
        return "desserts"
    # default
    return "food"


def compute_score(recipe, region, weather_tag, filters):
    """
    Score a recipe based on:
      - region match (strong)
      - weather_tag match (strong)
      - category match (medium)
      - keyword hits (small)
    """
    score = 0
    tlist = tags_list(recipe)
    title = normalize_text(recipe.title)

    # region match
    if region:
        if region in tlist or region in title:
            score += 40

    # weather match
    if weather_tag and weather_tag != "all":
        if weather_tag in tlist or weather_tag in title:
            score += 30

    # category boosting: if recipe type matches any desired category keywords present in filters
    for cat, kws in filters.items():
        # count keyword matches in tags/title
        for kw in kws:
            if any(kw in tag for tag in tlist) or kw in title:
                score += 6

    # add small bonus for recipe tags length (prefer tagged recipes)
    if tlist:
        score += min(len(tlist), 5)

    # slight random tie breaker
    score += random.random() * 2.0

    return score


def get_recommendations(user_id, weather, top_k=30):
    """
    Returns a balanced list of recommended recipes:
      - Attempts to return TARGET_COUNTS per category
      - If not enough found, fills with best remaining recipes
    """
    # safety
    top_k = int(top_k or 30)

    location = normalize_text(weather.get("location", "")) if weather else ""
    region = detect_region_from_location(location)
    weather_tag = detect_weather_tag(weather)

    log.info(f"Recommender: location='{location}', region='{region}', weather_tag='{weather_tag}'")

    # choose filters for keyword boosts based on weather
    if weather_tag == "rainy":
        boosts = {
            "food": ["curry", "biryani", "masala", "dosa", "idli"],
            "drinks": ["chai", "tea", "coffee"],
            "soups": ["soup", "rasam"],
            "desserts": ["halwa", "kheer", "payasam"],
            "snacks": ["pakora", "samosa", "vada"]
        }
    elif weather_tag == "hot":
        boosts = {
            "food": ["salad", "pulao", "rice", "light", "thali"],
            "drinks": ["lassi", "juice", "sharbat", "buttermilk"],
            "soups": ["raita", "cold soup"],
            "desserts": ["ice cream", "kulfi", "falooda"],
            "snacks": ["chaat", "fruit"]
        }
    elif weather_tag == "cold":
        boosts = {
            "food": ["paratha", "curry", "biryani", "masala"],
            "drinks": ["chai", "coffee", "hot"],
            "soups": ["soup", "stew", "rasam"],
            "desserts": ["halwa", "pudding", "gajar"],
            "snacks": ["pakora", "samosa"]
        }
    else:
        boosts = {
            "food": ["indian", "main course", "dal", "sabzi"],
            "drinks": ["juice", "lassi", "chai"],
            "soups": ["soup", "rasam"],
            "desserts": ["dessert", "sweet"],
            "snacks": ["snack", "chaat"]
        }

    # Load candidate pool (limit to avoid huge memory if DB is large)
    try:
        candidates = Recipe.query.limit(5000).all()
    except Exception as e:
        log.exception("DB query failed in recommender")
        candidates = []

    # Score each candidate
    scored = []
    for r in candidates:
        try:
            score = compute_score(r, region, weather_tag, boosts)
            r_type = detect_type_from_recipe(r)
            scored.append((score, r, r_type))
        except Exception:
            # keep going even if one recipe causes an error
            continue

    # sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)

    # pick top recipes per category, avoiding duplicates
    selected = []
    selected_ids = set()

    # helper to pick from scored list that match a category
    def pick_for_category(cat, count):
        picked = 0
        for score, recipe, rtype in scored:
            if picked >= count:
                break
            if recipe.id in selected_ids:
                continue
            # prefer recipes detected as this category OR having keywords in tags/title
            if rtype == cat:
                selected.append((score, recipe, rtype))
                selected_ids.add(recipe.id)
                picked += 1
        # second pass: broader match (title/tags contain category keywords)
        if picked < count:
            for score, recipe, rtype in scored:
                if picked >= count:
                    break
                if recipe.id in selected_ids:
                    continue
                tags = tags_list(recipe)
                title = normalize_text(recipe.title)
                # if any keyword for this cat appears:
                if any(kw in title or any(kw in t for t in tags) for kw in CATEGORY_KEYWORDS.get(cat, [])):
                    selected.append((score, recipe, cat))
                    selected_ids.add(recipe.id)
                    picked += 1
        return picked

    # pick per category using TARGET_COUNTS
    for cat, need in TARGET_COUNTS.items():
        pick_for_category(cat, need)

    # If we still don't have top_k, backfill with highest scoring remaining
    if len(selected) < top_k:
        for score, recipe, rtype in scored:
            if len(selected) >= top_k:
                break
            if recipe.id in selected_ids:
                continue
            selected.append((score, recipe, rtype))
            selected_ids.add(recipe.id)

    # final formatting
    output = []
    for score, r, rtype in selected[:top_k]:
        output.append({
            "id": r.id,
            "title": r.title,
            "prep_time_minutes": getattr(r, "prep_time_minutes", None),
            "tags": tags_list(r),
            "type": rtype,
            # include score for debug (optional - remove if you don't want it)
            "score": round(float(score), 2)
        })

    log.info(f"Returning {len(output)} recommendations (region={region}, weather={weather_tag})")
    return output
