import os
import json
import mysql.connector

# MySQL Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Change if needed
    "password": "",  # Change if needed
    "database": "neurips_papers"
}

# Folder where metadata files are stored
METADATA_FOLDER = "D:/scraped-pdfs/"

def get_pdf_filename(title):
    """Use the title as the filename without modification"""
    return title + ".pdf"

def insert_paper(cursor, paper):
    """Insert paper data into the database"""
    query = """
    INSERT INTO papers (year, title, authors, abstract, pdf_url, pdf_path, labels)
    VALUES (%s, %s, %s, %s, %s, %s, NULL)
    """
    cursor.execute(query, (
        paper["year"],
        paper["title"],
        paper["authors"],
        paper["abstract"],
        paper["pdf_url"],
        paper["pdf_path"]
    ))

def process_metadata_files():
    """Process all metadata_{year}.json files and insert into the database"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Loop through all metadata files in the folder
    for filename in os.listdir(METADATA_FOLDER):
        if filename.startswith("metadata_") and filename.endswith(".json"):
            year = filename.split("_")[1].split(".")[0]
            metadata_path = os.path.join(METADATA_FOLDER, filename)

            # Load metadata JSON
            with open(metadata_path, "r", encoding="utf-8") as file:
                papers = json.load(file)

                for paper in papers:
                    # Generate the local PDF path
                    pdf_filename = get_pdf_filename(paper["title"])
                    paper["pdf_path"] = f"{year}/{pdf_filename}"

                    # Insert paper into DB
                    insert_paper(cursor, paper)

                print(f"Inserted {len(papers)} papers from {filename}")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ All metadata files processed successfully.")

if __name__ == "__main__":
    process_metadata_files()
