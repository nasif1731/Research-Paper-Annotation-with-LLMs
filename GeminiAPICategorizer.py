import mysql.connector
import google.generativeai as genai
import time

# MySQL Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Change if needed
    "password": "",  # Change if needed
    "database": "neurips_papers"
}

# Google Gemini API Configuration
GENAI_API_KEY = "AIzaSyAa5UaPTswpZd50GJ5vDDNAgFnO8WLRu_A"  # Replace with your actual API key
genai.configure(api_key=GENAI_API_KEY)

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

    query = "SELECT id, title, abstract FROM papers WHERE category IS NULL LIMIT 10"
    cursor.execute(query)
    papers = cursor.fetchall()

    cursor.close()
    conn.close()
    return papers

def classify_with_gemini(title, abstract):
    """Send title and abstract to Gemini API and get a category."""
    prompt = f"""
    Classify the following research paper strictly into one of these categories:
    {CATEGORIES}

    Title: {title}
    Abstract: {abstract}

    Respond with  only the category name on the last line.
    """

    model = genai.GenerativeModel("gemini-pro")
    
    for attempt in range(5):  # Retry up to 5 times
        try:
            response = model.generate_content(prompt)
            if response and hasattr(response, "text") and response.text.strip():
                category = response.text.strip().split("\n")[-1]  # Extract last line
                if category in CATEGORIES:
                    return category
                print(f"⚠️ Unexpected category: {category}")
        except Exception as e:
            print(f"❌ API Error: {e}")
            time.sleep(30)
    
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

            if not paper["abstract"]:  # Skip if abstract is missing
                print("⚠️ Skipping due to missing abstract.")
                continue

            category = classify_with_gemini(paper["title"], paper["abstract"])
            if category:
                print(f"✅ Category Assigned: {category}")
                update_category_in_db(paper["id"], category)
            else:
                print("❌ Failed to classify paper.")

            time.sleep(2)  # Delay to avoid API rate limits

    print("🎉 Classification process fully completed.")

if __name__ == "__main__":
    process_papers()
