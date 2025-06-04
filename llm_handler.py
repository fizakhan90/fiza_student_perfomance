# llm_handler.py
import google.generativeai as genai
import config  # To get the API key (from config.py)
import json    # For example usage, not strictly needed by functions
from data_processor import load_data as dp_load_data, process_student_data as dp_process_student_data
import os 

# --- Configure the Gemini API client ---
# Why: We need to tell the 'google-generativeai' library our API key
#      and choose which Gemini model we want to use.
try:
    if not config.GOOGLE_API_KEY or config.GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY":
        # This check helps catch if the API key placeholder wasn't replaced.
        raise ValueError("GOOGLE_API_KEY not configured in config.py or is a placeholder.")
    
    genai.configure(api_key=config.GOOGLE_API_KEY)
    
    # Choose the Gemini model. 'gemini-pro' is a good general-purpose text model.
    # Other options like 'gemini-1.5-pro-latest' might be available depending on your access.
    model = genai.GenerativeModel('gemini-2.0-flash') 
    print("Gemini API configured successfully with 'gemini-pro' model.")

except AttributeError:
    print("Fatal Error: GOOGLE_API_KEY not found attribute in config.py. Please ensure config.py exists and the variable is defined.")
    model = None # Ensure model is None if configuration fails
except ValueError as ve:
    print(f"Fatal Configuration Error: {ve}")
    model = None
except Exception as e:
    # Catch any other unexpected errors during configuration
    print(f"An unexpected error occurred during Gemini API configuration: {e}")
    model = None

def format_time_for_llm(seconds):
    """Converts seconds to a human-readable 'X min Y sec' or 'Y sec' string."""
    if seconds is None or not isinstance(seconds, (int, float)) or seconds < 0:
        return "N/A"
    
    seconds = int(seconds) # Ensure integer seconds for calculation
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes > 0:
        return f"{minutes} min {remaining_seconds} sec"
    elif remaining_seconds >= 0: # Show even if 0 seconds, or just minutes if seconds is 0
        return f"{remaining_seconds} sec"
    return "N/A"

def format_data_for_llm(processed_data):
    """
    Formats the processed data into a string that the LLM can easily understand.
    Why: LLMs work best with clear, well-structured text. We're creating a
         "briefing document" for the AI based on our processed numbers.
    """
    if not processed_data:
        return "No data available to format for LLM."

    # We'll build a string. Using an f-string for easy variable insertion.
    # The goal is to make it readable for a human too, which helps the LLM.
    
    # Create a copy to avoid modifying the original dict, and remove DataFrame
    data_for_llm_context = processed_data.copy()
    if "raw_questions_df" in data_for_llm_context:
        del data_for_llm_context["raw_questions_df"] # Don't send the raw DataFrame to LLM

    context_str = f"Student Performance Analysis:\n"
    context_str += f"Student Name: {data_for_llm_context.get('student_name', 'N/A')}\n"
    context_str += f"Test Name: {data_for_llm_context.get('test_name', 'N/A')}\n\n"

    context_str += "Overall Summary:\n"
    overall = data_for_llm_context.get('overall_summary', {})
    context_str += f"  Score: {overall.get('score', 'N/A')}\n"
    context_str += f"  Accuracy: {overall.get('accuracy_percent', 'N/A')}%\n"
    context_str += f"  Correct Answers: {overall.get('correct_answers', 'N/A')} / {overall.get('total_questions_in_test', 'N/A')}\n"
    # Add more details from 'overall_summary' if they are consistently available and useful
    context_str += f"  Total Time Taken: {format_time_for_llm(overall.get('time_taken_seconds'))}\n\n"

    context_str += "Subject-wise Performance:\n"
    subject_perf = data_for_llm_context.get('subject_performance', {})
    if subject_perf:
        for subject, perf in subject_perf.items():
            context_str += f"  - {subject}:\n"
            context_str += f"    Accuracy: {perf.get('accuracy_percent', 'N/A')}% ({perf.get('correct_answers', 'N/A')}/{perf.get('total_questions', 'N/A')} questions)\n"
            context_str += f"    Average Time per Question: {format_time_for_llm(perf.get('average_time_seconds'))}\n"
    else:
        context_str += "  No subject-wise data available.\n"
    context_str += "\n"
    
    # Chapter-wise: Show a few weakest or most notable. Sorting helps.
    context_str += "Chapter-wise Performance Highlights (e.g., weakest or notable chapters):\n"
    chapter_perf_data = data_for_llm_context.get('chapter_performance', {})
    if chapter_perf_data:
        # Sort chapters by accuracy (ascending) to find weakest, or by number of questions
        # For this example, let's sort by accuracy (lowest first) and show top 5 or any below 60%
        sorted_chapters = sorted(chapter_perf_data.items(), key=lambda item: item[1].get('accuracy_percent', 100))
        chapters_shown = 0
        for chapter, perf in sorted_chapters:
            if chapters_shown < 5 or perf.get('accuracy_percent', 100) < 60:
                 context_str += f"  - {chapter}:\n"
                 context_str += f"    Accuracy: {perf.get('accuracy_percent', 'N/A')}% ({perf.get('correct_answers', 'N/A')}/{perf.get('total_questions', 'N/A')} questions)\n"
                 context_str += f"    Average Time per Question: {format_time_for_llm(perf.get('average_time_seconds'))}\n"
                 chapters_shown += 1
            if chapters_shown >= 5 and perf.get('accuracy_percent', 100) >= 60: # Stop if we've shown 5 and accuracy is decent
                break
        if chapters_shown == 0:
            context_str += "  No specific chapters highlighted based on current criteria (e.g. all above 60% accuracy and few chapters overall).\n"
    else:
        context_str += "  No chapter-wise data available.\n"
    context_str += "\n"

    context_str += "Difficulty-wise Performance:\n"
    difficulty_perf_data = data_for_llm_context.get('difficulty_performance', {})
    if difficulty_perf_data:
        for diff_level, perf in difficulty_perf_data.items():
            context_str += f"  - {str(diff_level).capitalize()}:\n" # Ensure diff_level is string
            context_str += f"    Accuracy: {perf.get('accuracy_percent', 'N/A')}% ({perf.get('correct_answers', 'N/A')}/{perf.get('total_questions', 'N/A')} questions)\n"
            context_str += f"    Average Time per Question: {format_time_for_llm(perf.get('average_time_seconds'))}\n"

    else:
        context_str += "  No difficulty-wise data available.\n"
    context_str += "\n"

    context_str += "Concept Performance Highlights (e.g., weakest concepts):\n"
    concept_perf_data = data_for_llm_context.get('concept_performance', {})
    if concept_perf_data:
        # Sort concepts by accuracy (lowest first) and show top 5 or any below 60%
        sorted_concepts = sorted(concept_perf_data.items(), key=lambda item: item[1].get('accuracy_percent', 100))
        concepts_shown = 0
        for concept_name, perf in sorted_concepts:
            if concepts_shown < 5 or perf.get('accuracy_percent', 100) < 60:
                context_str += f"  - {concept_name}:\n"
                context_str += f"    Accuracy: {perf.get('accuracy_percent', 'N/A')}% ({perf.get('correct_answers', 'N/A')}/{perf.get('total_questions', 'N/A')} questions)\n"
                context_str += f"    Average Time per Question: {format_time_for_llm(perf.get('average_time_seconds'))}\n"
                concepts_shown += 1
            if concepts_shown >= 5 and perf.get('accuracy_percent', 100) >= 60:
                break
        if concepts_shown == 0:
            context_str += "  No specific concepts highlighted as weak based on current criteria.\n"
    else:
        context_str += "  No concept-wise data available.\n"
    context_str += "\n"

    context_str += "Time Management Insights:\n"
    time_acc = data_for_llm_context.get('time_accuracy_summary', {})
    if time_acc:
        context_str += f"  Average time per correct question: {format_time_for_llm(time_acc.get('avg_time_per_correct_q_seconds'))}\n"
        context_str += f"  Average time per incorrect question: {format_time_for_llm(time_acc.get('avg_time_per_incorrect_q_seconds'))}\n"
    else:
        context_str += "  Time management summary data not available.\n"
    context_str += "\n"
    
    return context_str


def generate_feedback(processed_data_str, student_name="Student"):
    """
    Generates feedback using the configured Gemini model.
    Why: This is where the "AI magic" happens. We send our data summary and
         instructions (the prompt) to Gemini and get back its textual feedback.
    """
    if not model: # Check if the model was initialized successfully
        print("Error: Gemini model not initialized. Cannot generate feedback. Check API key and configuration in config.py.")
        return "Error: AI Feedback generation service is unavailable due to configuration issues."
    
    if not processed_data_str or processed_data_str == "No data available to format for LLM.":
         return "Error: No processed data was provided to generate feedback."

    # --- This is the core of Prompt Engineering ---
    # We tell the AI:
    # 1. Its role (expert academic advisor).
    # 2. Who the student is.
    # 3. The data to analyze (the `processed_data_str`).
    # 4. The desired output structure and tone.
    # Using Markdown for headings (##) helps us parse it later for the PDF.

    prompt = f"""
You are an expert AI academic advisor for MathonGo. Your goal is to provide highly personalized, encouraging, and constructive feedback to a student based on their recent test performance.
The student's name is {student_name}.

Please analyze the following performance data carefully:
--- START OF PERFORMANCE DATA ---
{processed_data_str}
--- END OF PERFORMANCE DATA ---

Based on this data, please generate a feedback report with the following sections. Use Markdown for headings (e.g., ## Section Title for main sections, ### Sub-section Title for sub-sections if needed).

## 1. Personalized Motivating Introduction
   - Address the student by name ({student_name}).
   - Craft an opening message that is genuinely motivating and human-like. Avoid generic phrases.
   - Briefly acknowledge their effort and the test they took. You can pick one positive aspect or area of focus from the data to make it specific.

## 2. Detailed Performance Breakdown
   - **Overall Performance:** Briefly summarize their overall score, accuracy, and how they managed their time.
   - **Subject-wise Analysis:**
     - Identify subjects where {student_name} performed well (e.g., high accuracy, efficient time use).
     - Point out subjects that need more attention (e.g., lower accuracy, spending too much/too little time). Be specific, referencing the data.
   - **Chapter-wise Hotspots (if data available):**
     - Highlight 1-2 chapters where {student_name} excelled, if clearly indicated by high accuracy.
     - Pinpoint 1-2 chapters that were particularly challenging, based on low accuracy. Suggest these as areas for focused revision.
   - **Difficulty Level Insights (if data available):**
     - Analyze performance across Easy, Medium, and Hard questions.
     - Did {student_name} make unexpected errors on Easy questions? How was the performance on Hard questions?
   - **Key Conceptual Strengths and Weaknesses (if data available):**
     - Based on the 'Concept Performance' data, mention 1-2 concepts {student_name} seems to grasp well.
     - Identify 1-2 key concepts where improvement is needed, as shown by lower accuracy.

## 3. Time Management vs. Accuracy Insights
   - Discuss the relationship between the time {student_name} spent on questions and their accuracy.
   - For example: "I noticed you spent an average of X seconds on incorrect questions in [Subject], which is [higher/lower] than the Y seconds on correct ones. This might suggest [rushing/getting bogged down]."
   - Were there specific subjects or question types where time management seemed to be a factor (either positively or negatively)?

## 4. Actionable Suggestions for Improvement (2-3 Key Points)
   - Provide 2-3 concrete, actionable suggestions tailored to {student_name}'s specific performance.
   - Link these suggestions directly to the weaknesses identified in the breakdown.
   - Examples:
     - "To improve in [Specific Chapter/Concept], I recommend [Specific Action, e.g., 'reviewing NCERT theory thoroughly, then solving 15-20 targeted MCQs']."
     - "For [Subject where time was an issue], try practicing with a timer. Aim to solve [Type of] questions within [Time limit] minutes each."
     - "Consider a strategy for Hard questions: if you're stuck for more than [e.g., 3] minutes on a Hard question in [Subject], mark it for review and move on. You can return to it if time permits."

**Important Tones and Styles:**
- **Encouraging and Constructive:** The main goal is to motivate, not discourage. Frame weaknesses as opportunities for growth.
- **Empathetic and Human-like:** Use phrases like "I noticed...", "It seems like...", "You might find it helpful to...".
- **Specific and Data-Driven:** Refer to aspects of the provided data to support your points, but interpret the data, don't just repeat numbers.
- **Clear and Concise:** Use simple language. Bullet points for lists or suggestions are good.

Please ensure the entire response is a single block of text, formatted with Markdown as requested. Do not include the "--- START/END OF PERFORMANCE DATA ---" markers in your final output.
"""

    # Generation Configuration (optional, but good for controlling output)
    # Refer to Gemini API documentation for all available parameters.
    generation_config = genai.types.GenerationConfig(
        temperature=0.6,      # Controls randomness. Lower is more deterministic. 0.5-0.8 is often good.
        # max_output_tokens=2048, # Max length of the generated response. Default is usually fine for gemini-pro.
        # top_p=0.9,            # Nucleus sampling: considers tokens with cumulative probability >= top_p.
        # top_k=40              # Considers the top_k most probable tokens.
    )

    # Safety Settings (optional, adjust as needed)
    # Define what content to block.
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Check for safety blocks or empty response
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason_msg = response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason
            print(f"Warning: Prompt was blocked by Gemini. Reason: {block_reason_msg}")
            return f"Error: The AI could not generate feedback because the request was blocked by safety filters. Reason: {block_reason_msg}"

        if not response.candidates or not response.candidates[0].content.parts:
            print("Warning: No content generated by Gemini or unexpected response structure.")
            return "Error: The AI did not generate any feedback content, or the response was empty."
            
        # The response text is typically in response.text or within parts
        generated_text = "".join(part.text for part in response.candidates[0].content.parts if part.text)
        if not generated_text.strip(): # Check if the text is empty after joining
            return "Error: The AI generated an empty feedback string."

        return generated_text

    except Exception as e:
        print(f"An error occurred while calling the Gemini API: {e}")
        # Provide more specific error messages if possible
        if "API_KEY_INVALID" in str(e) or "PERMISSION_DENIED" in str(e):
             return "Error generating feedback: The Google Gemini API Key is invalid or permissions are denied. Please check `config.py`."
        elif "deadline exceeded" in str(e).lower() or "timeout" in str(e).lower():
            return "Error generating feedback: The request to the AI service timed out. Please try again later."
        return f"Error generating feedback: An unexpected error occurred with the AI service. Details: {str(e)[:200]}" # Show part of error

# Test this module
if __name__ == '__main__':
    if not model: # Check if model initialization failed earlier
        print("LLM Handler Test: Gemini model not initialized. Aborting test.")
    else:
        print("\n--- LLM Handler Test ---")
        
        # --- Load and process actual sample data for a more realistic test ---
        sample_data_dir_for_llm = "sample_data"
        # Use one of your actual files for this test
        actual_sample_file_for_llm = 'sample_submission_analysis_1.json' 
        llm_test_json_path = os.path.join(sample_data_dir_for_llm, actual_sample_file_for_llm)

        processed_data_for_llm = None
        if os.path.exists(llm_test_json_path):
            print(f"Loading data from: {llm_test_json_path} for LLM handler test...")
            raw_data_for_llm = dp_load_data(llm_test_json_path)
            if raw_data_for_llm:
                processed_data_for_llm = dp_process_student_data(raw_data_for_llm)
                if not processed_data_for_llm:
                    print("LLM Handler Test: Failed to process data.")
            else:
                print("LLM Handler Test: Failed to load data.")
        else:
            print(f"LLM Handler Test: Test data file not found: {llm_test_json_path}")
            print("Using minimal dummy data instead for LLM context formatting.")
            # Fallback to minimal dummy data if actual file not found
            processed_data_for_llm = { 
                "student_name": "Dummy LLM Student", "test_name": "Dummy LLM Test",
                "overall_summary": {"score": 50, "accuracy_percent": 50.0},
                "subject_performance": {"Math": {"accuracy_percent": 60.0}}
                # Add more minimal fields if format_data_for_llm requires them
            }

        if processed_data_for_llm:
            student_name_for_llm = processed_data_for_llm.get("student_name", "Test Student")
            llm_context_string = format_data_for_llm(processed_data_for_llm)
            
            print("\n--- Context String for LLM (from llm_handler.py test) ---")
            print(llm_context_string[:1000] + "..." if len(llm_context_string) > 1000 else llm_context_string) # Print snippet

            print("\n--- Generating Feedback with Gemini (this may take a moment) ---")
            # Ensure your GOOGLE_API_KEY is correctly set in config.py
            feedback = generate_feedback(llm_context_string, student_name=student_name_for_llm)
            
            print("\n--- AI Generated Feedback (from Gemini - llm_handler.py test) ---")
            print(feedback)
        else:
            print("LLM Handler Test: No processed data available to generate context or feedback.")