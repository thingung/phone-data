import os
import json
import csv
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

INPUT_FOLDER = "transcripts"

def extract_json(text):
    # Remove Markdown code block markers like ```json ... ```
    cleaned = re.sub(r"```json\s*", "", text)
    cleaned = re.sub(r"```", "", cleaned)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # fallback: try to extract JSON inside braces if still fails
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except Exception:
                pass
    return None

def analyze_text(text):
    prompt = f"""
You are a helpful assistant that analyzes the sentiment of a YouTube video transcript focused on a specific phone model.

Analyze the following transcript and return a JSON object including these keys:

- sentiment: {{
    overall: "positive"|"neutral"|"negative",
    polarity: float (range -1 to 1),
    subjectivity: float (range 0 to 1),
    explanation: string,
    highlighted_phrases: list of key phrases illustrating sentiment
  }}

- advertisement: {{
    is_ad: "Yes"|"No",
    explanation: string
  }}

IMPORTANT: When determining if the video is an advertisement, specifically check if the transcript contains explicit statements that the video is sponsored or paid to review or promote the phone being discussed. Ignore any mentions of sponsorships by other companies or general positive language about the phone. Only consider it an advertisement if it clearly states or implies sponsorship or paid promotion for that specific phone.

Return only valid JSON in your response, no additional text.

Transcript:
\"\"\"
{text}
\"\"\"
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    raw_output = response.choices[0].message.content
    return extract_json(raw_output)

def process_files(folder_in=INPUT_FOLDER, folder_out="sentiment_results"):
    os.makedirs(folder_out, exist_ok=True)

    csv_file_path = os.path.join(folder_out, "sentiment_summary.csv")
    csv_headers = [
        "filename", "overall_sentiment", "polarity", "subjectivity", "highlighted_phrases",
        "is_advertisement", "advertisement_explanation", "sentiment_explanation"
    ]

    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()

        for filename in os.listdir(folder_in):
            if filename.endswith(".txt"):
                file_path = os.path.join(folder_in, filename)
                print(f"Analyzing {filename}...")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()

                    analysis = analyze_text(text)
                    if not analysis:
                        raise ValueError("Failed to parse JSON from API response")

                    # Save JSON file
                    json_file_path = os.path.join(folder_out, filename.replace(".txt", ".json"))
                    with open(json_file_path, "w", encoding="utf-8") as jf:
                        json.dump(analysis, jf, indent=2)

                    sentiment = analysis.get("sentiment", {})
                    advertisement = analysis.get("advertisement", {})

                    writer.writerow({
                        "filename": filename,
                        "overall_sentiment": sentiment.get("overall", ""),
                        "polarity": sentiment.get("polarity", ""),
                        "subjectivity": sentiment.get("subjectivity", ""),
                        "highlighted_phrases": "; ".join(sentiment.get("highlighted_phrases", [])),
                        "is_advertisement": advertisement.get("is_ad", ""),
                        "advertisement_explanation": advertisement.get("explanation", ""),
                        "sentiment_explanation": sentiment.get("explanation", "")
                    })

                except Exception as e:
                    print(f"Error analyzing {filename}: {e}")

if __name__ == "__main__":
    process_files()
