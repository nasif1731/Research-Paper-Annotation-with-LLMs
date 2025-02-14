import fitz  # PyMuPDF for reading PDFs
import mysql.connector
import ollama
import json
import os
import time

# MySQL Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Change if needed
    "password": "",  # Change if needed
    "database": "neurips_papers"
}

# Folder where PDFs are stored
PDF_BASE_PATH = "D:/scraped-pdfs/"

# Categories for classification
CATEGORIES = [
    "Deep Learning",
    "Optimization",
    "Reinforcement Learning",
    "Probabilistic Models",
    "Neural Networks",
    "Machine Learning"
]

def fetch_papers_without_category():
    """Fetch papers from the database that do not have a category assigned yet"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    query = "SELECT id, title, pdf_path FROM papers WHERE category IS NULL LIMIT 10"
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

def classify_with_deepseek(text):
    """Send extracted text to DeepSeek-R1-Distill-Llama-8B via Ollama and get a category."""
    prompt = f"""
    Read the following research paper text and classify it into one of the following categories:
    {CATEGORIES}
    -----
    {text[:4000]}
    -----
    Respond with only one category name.
    """
    
    for attempt in range(5):  # Retry up to 5 times
        try:
            response = ollama.chat(model="deepseek", messages=[{"role": "user", "content": prompt}])
            if response and "message" in response and "content" in response["message"]:
                category = response["message"]["content"].strip()
                if category in CATEGORIES:
                    return category
                else:
                    print(f"⚠️ Unexpected category: {category}")
        except Exception as e:
            print(f"❌ API Error: {e}")
            time.sleep(10)
    
    return None

def update_category_in_db(paper_id, category):
    """Update the category for a paper in the database"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    query = "UPDATE papers SET category = %s WHERE id = %s"
    cursor.execute(query, (category, paper_id))

    conn.commit()
    cursor.close()
    conn.close()

def process_papers():
    """Continuously process unclassified papers until all are categorized"""
    while True:
        papers = fetch_papers_without_category()

        if not papers:
            print("✅ All papers are categorized!")
            break

        for paper in papers:
            print(f"🔍 Processing: {paper['title']}")

            pdf_text = extract_text_from_pdf(paper["pdf_path"])
            if not pdf_text:
                print("⚠️ Skipping due to empty PDF content.")
                continue

            category = classify_with_deepseek(pdf_text)
            if category:
                print(f"✅ Category Assigned: {category}")
                update_category_in_db(paper["id"], category)
            else:
                print("❌ Failed to classify paper.")

            time.sleep(2)  # Delay to avoid API rate limits

    print("🎉 Classification process fully completed.")

if __name__ == "__main__":
    process_papers()
