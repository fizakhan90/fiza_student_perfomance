# AI-Powered Student Performance Feedback System (MathonGo)

This project analyzes student test data from JSON files and uses Google's Gemini API to generate personalized feedback, producing a professionally styled PDF report with data visualizations.

---

####  Public Link to PDF hosted report [https://drive.google.com/file/d/1WpcnDExOn52cNIt2RLKOtr7lnTwkIP3J/view?usp=sharing]

## Objective

- Parse and interpret complex student test performance data (JSON).
- Generate high-quality, personalized, actionable feedback using Google Gemini.
- Produce a styled PDF report with charts and tables.
- Demonstrate prompt engineering, data interpretation, API integration, and automation skills.

---

## Tech Stack

- **Language:** Python (3.8+)
- **Core Libraries:**
  - `google-generativeai` (Gemini API)
  - `pandas`
  - `reportlab`
  - `matplotlib`
- **Supporting Libraries:**
  - `python-dotenv` 
  - `numpy` 

---

## Project Structure


---

## Setup and Installation

1. **Clone the Repository:**
    ```
    git clone https://github.com/fizakhan90/fiza-student-performance.git
    cd fiza-student-performance
    ```

2. **Create and Activate a Virtual Environment:**
    ```
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```

3. **Install Dependencies:**
    ```
    pip install -r requirements.txt
    ```

4. **Set Up Google Gemini API Key:**
    - Obtain your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    - Edit `config.py`:
      ```
      # config.py
      GOOGLE_API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY_HERE"
      ```
    - **Security:** For public repos, use a `.env` file and add `config.py` to `.gitignore`.

5. **Place Input Data Files:**
    - Ensure the `sample_data` folder exists.
    - Place/rename your JSON files as `sample_submission_analysis_1.json`, etc.
    - Update the `example_submission_files` list in `main.py` to match your files.

---

## How to Run the System

1. Navigate to the root directory.
2. Activate your virtual environment.
3. Run:
    ```
    python main.py
    ```
- The script will process each JSON, generate feedback, and create a PDF report in `generated_reports/`.

---

## API(s) Used

- **Google Gemini API (gemini-pro):** Used for generating personalized feedback. All logic is encapsulated in `llm_handler.py`.

---

## Prompt Logic (`llm_handler.py`)

- **Role Assignment:** LLM acts as an "expert AI academic advisor for MathonGo."
- **Structured Context:** Pre-processed summaries (overall, subject, chapter, difficulty, concepts, time vs accuracy).
- **Output Structure:** Markdown headings for sections:
  - Personalized Introduction
  - Detailed Performance Breakdown
  - Time Management vs Accuracy Insights
  - Actionable Suggestions (2-3 points)
- **Tone/Style:** Encouraging, constructive, empathetic, data-driven, concise.
- **Formatting:** Markdown for easy PDF parsing; double asterisks are removed during PDF generation.
- **Safety:** Generation parameters and safety settings are configured for Gemini.

---

## PDF Report Structure (`pdf_generator.py`)

- **Header/Footer:** Colored banner, report title, logo placeholder, date, page numbers.
- **Main Title/Subtitles:** "Student Performance Report" and "Detailed Analysis & Actionable Insights."
- **Candidate Overview:** Name, test name, overall score, accuracy (dynamic color).
- **Personalized Analysis:** Incorporates Gemini's Markdown output (headings, lists, etc.).
- **Visualizations:** 
  - Bar charts (subject-wise, difficulty-level accuracy)
  - Styled tables (accuracy, correct/total, average time)
  - Chapter highlights

---

## Accuracy Metrics Note

- System reports accuracy as **Total Correct Answers Parsed / Total Questions Parsed** for each category, ensuring consistency across all breakdowns, independent of "attempted" metrics in the source JSON.

---


**Refinements Made:**
- Improved section clarity and formatting.
- Used concise bullet points for readability.
- Added explicit code blocks and plaintext for structure.
- Clarified security and setup steps.
- Summarized prompt and PDF logic for quick understanding.
