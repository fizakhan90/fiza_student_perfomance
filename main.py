import os
import json 
from data_processor import load_data, process_student_data
from llm_handler import format_data_for_llm, generate_feedback
from pdf_generator import generate_pdf_report

def run_full_analysis_and_report_generation(json_file_path, output_pdf_dir="generated_reports"):
    """
    Main function to orchestrate the entire process for a single JSON file.
    1. Loads data from the JSON file.
    2. Processes the data to extract insights.
    3. Formats data and sends it to the LLM for feedback.
    4. Generates a PDF report with the insights and AI feedback.
    Why: This function defines the main workflow of our application.
    """
    print(f"\nStarting analysis for: {json_file_path}")

    # --- 1. Load Raw Data ---
    raw_data = load_data(json_file_path)
    if not raw_data:
        print(f"Failed to load data from {json_file_path}. Aborting for this file.")
        return False 
    
    # --- 2. Process Data ---
    print("Processing student data...")
    processed_data = process_student_data(raw_data)
    if not processed_data:
        print(f"Failed to process data for {json_file_path}. Aborting for this file.")
        return False

    student_name = processed_data.get("student_name", "Student")
    test_name = processed_data.get("test_name", "Test")
    print(f"Data processed successfully for {student_name} - {test_name}.")

    # --- 3. Get AI Feedback ---
    print("Formatting data for AI...")
    llm_context_str = format_data_for_llm(processed_data)
    if llm_context_str == "No data available to format for LLM.":
        print(f"No data to format for LLM for {json_file_path}. Aborting AI feedback for this file.")
        ai_feedback = "Error: Could not format data for AI processing." 
    else:
        print("Requesting AI feedback from Gemini (this may take a few moments)...")
        ai_feedback = generate_feedback(llm_context_str, student_name)
        if ai_feedback.startswith("Error:"):
            print(f"AI feedback generation failed for {student_name}: {ai_feedback}")
        else:
            print(f"AI feedback received successfully for {student_name}.")
            


    # --- 4. Generate PDF Report ---
    if not os.path.exists(output_pdf_dir):
        try:
            os.makedirs(output_pdf_dir)
            print(f"Created output directory: {output_pdf_dir}")
        except OSError as e:
            print(f"Error creating output directory {output_pdf_dir}: {e}. PDF will be saved in current directory.")
            output_pdf_dir = "." 

    # Construct a unique output PDF name
    base_name = os.path.splitext(os.path.basename(json_file_path))[0]
    safe_base_name = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in base_name)
    output_pdf_filename = os.path.join(output_pdf_dir, f"{safe_base_name}_report.pdf")
    
    print(f"Generating PDF report: {output_pdf_filename}...")
    generate_pdf_report(processed_data, ai_feedback, output_pdf_filename)
    
    return True 

# --- Entry point of the script ---
if __name__ == "__main__":
    print("--- Student Performance Feedback System ---")

    sample_data_dir = "sample_data"
    example_submission_files = [
        "sample_submission_analysis_1.json", 
        "sample_submission_analysis_2.json",
        "sample_submission_analysis_3.json"
    ]
    
    json_files_to_process = []
    if not os.path.exists(sample_data_dir):
        print(f"Warning: The '{sample_data_dir}' directory does not exist. Please create it and add your JSON files.")
    else:
        for fname in example_submission_files:
            fpath = os.path.join(sample_data_dir, fname)
            if os.path.exists(fpath):
                json_files_to_process.append(fpath)
            else:
                print(f"Warning: Specified data file not found: {fpath}. It will be skipped.")

    if not json_files_to_process:
        print(f"No valid JSON files found for processing in '{sample_data_dir}' based on 'example_submission_files' list.")
        print("Please check filenames and ensure files are present.")
    else:
        print(f"\nFound {len(json_files_to_process)} JSON file(s) to process:")
        for f_path in json_files_to_process:
            print(f"  - {f_path}")

         
        main_logo_path = None 

        successful_reports = 0
        failed_reports = 0
        output_reports_dir = "generated_reports" 

        for json_file in json_files_to_process:
            if run_full_analysis_and_report_generation(json_file, output_pdf_dir=output_reports_dir): 
                successful_reports += 1
            else:
                failed_reports +=1
            print("-" * 50) 

        print("\n--- Processing Summary ---")
        print(f"Total files attempted: {len(json_files_to_process)}")
        print(f"Successfully generated reports: {successful_reports}")
        print(f"Failed reports: {failed_reports}")
        if successful_reports > 0:
             print(f"PDF reports are located in the '{os.path.abspath(output_reports_dir)}' directory.")

    print("\n--- System run complete. ---")