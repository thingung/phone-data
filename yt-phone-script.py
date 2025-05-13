import csv
import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import timedelta
import isodate  # To parse ISO 8601 durations

# Load API key from .env
load_dotenv()
api_key = os.getenv("yt_api_key")

MAX_RESULTS = 150

# Initialize YouTube API client
youtube = build('youtube', 'v3', developerKey=api_key)

# Function to get top 10 review video URLs for a phone
def get_top_reviews(phone_name):
    search_response = youtube.search().list(
        q=f"{phone_name} review",
        part="snippet",
        maxResults=MAX_RESULTS,  # slightly more to allow for filtering
        order="viewCount",
        type="video",
        relevanceLanguage="en"
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response["items"]]

    videos_response = youtube.videos().list(
        part="contentDetails",
        id=",".join(video_ids)
    ).execute()

    long_video_ids = []
    for item in videos_response["items"]:
        duration = isodate.parse_duration(item["contentDetails"]["duration"])
        if duration >= timedelta(seconds=90):  # not a Short
            long_video_ids.append(item["id"])

    return [f"https://www.youtube.com/watch?v={vid}" for vid in long_video_ids]

# List of phone names
phones = [
    "'iPhone 16 Pro Max'",
    "'Samsung Galaxy S25 Ultra'",
    "'Google Pixel 9 Pro'",
    "'OnePlus 12'",
    "'Google Pixel 9 Pro Fold'",
    "'Samsung Galaxy S24 Ultra'",
    "'Apple iPhone 16'",
    "'Moto Edge 2024'",
    "'Samsung Galaxy S25'",
    "'Nothing Phone 3a Pro'"
]

# Create and write to a CSV file
with open("top_youtube_reviews.csv", mode="w", newline='', encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Phone", "YouTube Review URL"])

    for phone in phones:
        print(f"Fetching reviews for: {phone}")
        urls = get_top_reviews(phone)
        for url in urls:
            writer.writerow([phone, url])

