from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import re
import os
from difflib import get_close_matches

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load movie links from file
def load_movie_links():
    movies = {}
    file_path = "final_cleaned_links.txt"  # Ensure this file is in the same directory

    if not os.path.exists(file_path):
        print("❌ ERROR: final_cleaned_links.txt NOT FOUND!")
        return {}

    print("📂 File exists. Reading file now...")

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            match = re.match(r"(.+?)\((\d{4})\) - (http.+)", line)
            if match:
                title, year, url = match.groups()
                title = title.lower().strip()  # Normalize title
                movies[(title, year.strip())] = url

    print(f"✅ Loaded {len(movies)} movies!")
    return movies

movies_db = load_movie_links()

def clean_movie_name(name):
    """Removes unnecessary details from user input for better search."""
    name = re.sub(r"(\d{3,4}p.*|webrip.*|x264.*|aac.*|yts.*)", "", name, flags=re.IGNORECASE)  # Remove quality tags
    name = re.sub(r"[^a-zA-Z0-9]", "", name)  # Remove special characters
    return name.lower().strip()

def find_best_match(user_input, movie_list):
    """Finds the best matching movie title from the list."""
    cleaned_input = clean_movie_name(user_input)
    matches = get_close_matches(cleaned_input, [title for title, _ in movie_list], n=1, cutoff=0.5)
    return matches[0] if matches else None

@app.get("/get_movie_link")
async def get_movie_link(name: str = Query(...), year: str = Query(...)):
    name = clean_movie_name(name)  # Clean user input
    year = year.strip()

    print(f"🔍 Searching for: ({name}, {year})")  # Debugging info

    # Try exact match first
    if (name, year) in movies_db:
        print("✅ Found exact match!")
        return {"title": name, "year": year, "link": movies_db[(name, year)]}

    # Try fuzzy matching
    best_match = find_best_match(name, movies_db.keys())
    print(f"🤖 Closest match found: {best_match}")

    if best_match and (best_match, year) in movies_db:
        return {"title": best_match, "year": year, "link": movies_db[(best_match, year)]}

    print("❌ Movie not found!")
    return {"error": "Movie not found"}
