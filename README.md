# Research Paper Annotation with LLMs

## Overview

This project automates the annotation of NeurIPS research papers by classifying them into predefined categories using LLMs. It leverages:

- **DeepSeek-R1** via Ollama for local classification.
- **Google Gemini API** for generating labels from extracted text.
- **MySQL database** for storing metadata and assigned labels.

## Features

- ✅ Scrapes research paper PDFs and metadata
- ✅ Classifies papers into six categories (Deep Learning, Optimization, Reinforcement Learning, Probabilistic Models, Neural Networks, Machine Learning)
- ✅ Handles API rate limits and safety restrictions
- ✅ Extracts text from PDFs and sends them for classification
- ✅ Stores categories and labels in a MySQL database

## Setup

### 1. Install Dependencies

Ensure you have the required Python libraries:

```bash
pip install mysql-connector-python ollama pymupdf google-generativeai
```

### 2. Database Configuration

Create a MySQL database named `neurips_papers` and a `papers` table:

```sql
CREATE TABLE papers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    pdf_path TEXT,
    category VARCHAR(255),
    labels JSON
);
```

Update `DB_CONFIG` in the scripts with your MySQL credentials.

### 3. Setup Ollama for Local Classification

Download the DeepSeek-R1 model:

```bash
ollama pull deepseek-r1:8b
```

### 4. Configure Google Gemini API

Replace `GENAI_API_KEY` in the script with your API key.

## Running the Scripts

### Classify Papers Using DeepSeek-R1

```bash
python classify_with_deepseek.py
```

### Annotate Papers Using Google Gemini

```bash
python annotate_with_gemini.py
```

## Challenges & Solutions

- ✅ **Handling API Rate Limits**
  - Implemented retries and delays for Gemini API.
  - Switched to local LLM inference (DeepSeek-R1) to bypass rate limits.

- ✅ **Dealing with Unexpected Responses**
  - Implemented error handling for empty or malformed responses.
  - Extracted only the last meaningful line from DeepSeek-R1 outputs.

- ✅ **Improving Performance**
  - Instead of processing full PDFs, classification is based on title + abstract.

## Future Improvements

- 🔹 **Hybrid approach**: Using both Gemini API and DeepSeek-R1 based on confidence scores.
- 🔹 **Enhance text extraction**: Preprocessing noisy PDF content for better classification.
- 🔹 **Optimize storage**: Improving database schema for faster queries.

## Contributing

Feel free to fork this repo, improve the scripts, and open a pull request!

Happy Annotation! 🚀
