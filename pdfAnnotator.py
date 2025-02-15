import fitz  # PyMuPDF for reading PDFs
import mysql.connector
import google.generativeai as genai
import json
import os
import time
import re

# MySQL Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Change if needed
    "password": "",  # Change if needed
    "database": "neurips_papers"
}

# Google Gemini API Configuration
GENAI_API_KEY = "GENAI_API_KEY"  # Replace with your actual API key

# Set up Google Gemini API
genai.configure(api_key=GENAI_API_KEY)

# Folder where PDFs are stored
PDF_BASE_PATH = "D:/scraped-pdfs/"

def fetch_papers_without_labels():
    """Fetch papers from the database that do not have labels yet"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    query = "SELECT id, title, pdf_path FROM papers WHERE labels IS NULL LIMIT 10"
    cursor.execute(query)
    papers = cursor.fetchall()

    cursor.close()
    conn.close()
    return papers

def extract_text_from_pdf(pdf_path):
    """Extract text content from a given PDF"""
    full_path = os.path.join(PDF_BASE_PATH, pdf_path)

    if not os.path.exists(full_path):
        print(f"❌ PDF not found: {full_path}")
        return None

    doc = fitz.open(full_path)
    text = ""

    for page in doc:
        text += page.get_text("text") + "\n"

    return text if text.strip() else None

def call_gemini_api(text):
    """Send extracted text to Google Gemini API and get three labels."""
    prompt = f"""
    Read the following research paper text and generate exactly three relevant category labels:
    -----
    {text[:4000]}  # Limit to 4000 characters to avoid API token issues
    -----
    Return only a JSON list of three labels. Example:
    ["Deep Learning", "Computer Vision", "Interpretability"]
    """

    model = genai.GenerativeModel("gemini-pro")

    for attempt in range(5):  # Retry up to 5 times
        try:
            response = model.generate_content(prompt)

            # Check if response exists and contains valid text
            if not response or not hasattr(response, "text") or not response.text.strip():
                print("⚠️ Empty API response. Retrying...")
                time.sleep(10)
                continue

            # Clean response text (remove ```json and any extra code formatting)
            cleaned_text = re.sub(r"```json|```", "", response.text).strip()

            # Parse JSON safely
            try:
                labels = json.loads(cleaned_text)
                if isinstance(labels, list) and len(labels) == 3:
                    return labels
                else:
                    print(f"⚠️ Invalid label format: {labels}")
            except json.JSONDecodeError:
                print(f"⚠️ JSON decoding failed: {cleaned_text}")

        except Exception as e:
            error_message = str(e)
            if "429" in error_message:
                print("⚠️ API quota exceeded! Retrying after 60 seconds...")
                time.sleep(60)  # Wait before retrying
                continue
            elif "finish_reason is 3" in error_message or "safety_ratings" in error_message:
                print("⚠️ Gemini API blocked this paper due to safety concerns.")
                return None
            else:
                print(f"❌ API Error: {e}")
                break  # Exit loop on non-retryable errors

    print(f"⚠️ Unexpected API Response: {response.text if response else 'No Response'}")
    return None

def update_labels_in_db(paper_id, labels):
    """Update the labels for a paper in the database"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    labels_str = json.dumps(labels)  # Convert list to JSON string

    query = "UPDATE papers SET labels = %s WHERE id = %s"
    cursor.execute(query, (labels_str, paper_id))

    conn.commit()
    cursor.close()
    conn.close()

def process_papers():
    """Continuously process unannotated papers until all are labeled"""
    while True:
        papers = fetch_papers_without_labels()

        if not papers:
            print("✅ All papers are annotated!")
            break  # Exit the loop when no more papers are left

        for paper in papers:
            print(f"🔍 Processing: {paper['title']}")

            pdf_text = extract_text_from_pdf(paper["pdf_path"])
            if not pdf_text:
                print("⚠️ Skipping due to empty PDF content.")
                continue

            labels = call_gemini_api(pdf_text)
            if labels:
                print(f"✅ Labels Generated: {labels}")
                update_labels_in_db(paper["id"], labels)
            else:
                print("❌ Failed to generate labels.")

            # Delay to avoid hitting API rate limits
            time.sleep(2)  

    print("🎉 Annotation process fully completed.")


if __name__ == "__main__":
    process_papers()

