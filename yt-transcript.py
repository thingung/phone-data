import os
import csv
from pathlib import Path
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    CouldNotRetrieveTranscript
)
from xml.etree.ElementTree import ParseError

# Load environment variables (if needed for future expansion)
load_dotenv()

FILE_PATH = "top_youtube_reviews.csv"

# Ensure transcripts directory exists
Path("transcripts").mkdir(exist_ok=True)

def get_translated_transcript(video_id):
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try English first
        try:
            return transcripts.find_transcript(["en"]).fetch()
        except NoTranscriptFound:
            pass

        # Try translatable ones
        for transcript in transcripts:
            if transcript.is_translatable:
                return transcript.translate("en").fetch()

    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable, CouldNotRetrieveTranscript, ParseError) as e:
        print(f"❌ Transcript not available or could not be retrieved for {video_id}: {e}")
    except Exception as e:
        print(f"❌ Unexpected error for {video_id}: {e}")
    
    return None

def save_transcript_to_file(transcript_data, filepath):
    try:
        formatter = TextFormatter()
        formatted_text = formatter.format_transcript(transcript_data)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(formatted_text)
    except Exception as e:
        print(f"❌ Error writing transcript to {filepath}: {e}")

def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    return None

# Read from the CSV and process each video
with open(FILE_PATH, newline="", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip header

    for row in reader:
        phone_name, url = row
        video_id = extract_video_id(url)

        if not video_id:
            print(f"⚠️ Invalid video URL: {url}")
            continue

        print(f"📥 Downloading transcript for {phone_name.strip()}: {video_id}")

        transcript_data = get_translated_transcript(video_id)

        if transcript_data:
            safe_name = phone_name.strip().replace(" ", "_").replace("'", "")
            output_path = f"transcripts/{safe_name}-{video_id}.txt"
            save_transcript_to_file(transcript_data, output_path)
            print(f"✅ Saved transcript to {output_path}")
        else:
            print(f"⚠️ No usable transcript found or saved for: {url}")
