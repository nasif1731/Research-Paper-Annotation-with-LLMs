import mysql.connector
import ollama
import time

# MySQL Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Change if needed
    "password": "",  # Change if needed
    "database": "neurips_papers"
}

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

def extract_category(response_text):
    """Extract the last meaningful line from DeepSeek-R1 response"""
    # Remove <think>...</think> if present
    if "<think>" in response_text and "</think>" in response_text:
        response_text = response_text.split("</think>")[-1].strip()
    
    # Get the last non-empty line
    lines = response_text.strip().split("\n")
    category = lines[-1].strip()

    # Ensure it's a valid category
    if category in CATEGORIES:
        return category
    
    print(f"⚠️ Unexpected category: {category}")
    return None

def classify_with_deepseek(title, abstract):
    """Send title and abstract to DeepSeek-R1-Distill-Llama-8B via Ollama and get a category."""
    prompt = f"""
    Classify the following research paper into one of these categories:
    {CATEGORIES}

    Title: {title}
    Abstract: {abstract}

    Respond with only the category name on the last line.
    """
    
    for attempt in range(5):  # Retry up to 5 times
        try:
            response = ollama.chat(model="deepseek-r1:8b", messages=[{"role": "user", "content": prompt}])
            if response and "message" in response and "content" in response["message"]:
                category = extract_category(response["message"]["content"])
                if category:
                    return category
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

            if not paper["abstract"]:  # Skip if abstract is missing
                print("⚠️ Skipping due to missing abstract.")
                continue

            category = classify_with_deepseek(paper["title"], paper["abstract"])
            if category:
                print(f"✅ Category Assigned: {category}")
                update_category_in_db(paper["id"], category)
            else:
                print("❌ Failed to classify paper.")

            time.sleep(2)  # Delay to avoid API rate limits

    print("🎉 Classification process fully completed.")

if __name__ == "__main__":
    process_papers()

