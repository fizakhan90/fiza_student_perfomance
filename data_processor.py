# data_processor.py
import json
from collections import defaultdict
import pandas as pd
import re

def load_data(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) > 0:
            print(f"Successfully loaded data from {json_file_path} (extracted first element of array)")
            return data[0]
        elif isinstance(data, dict):
            print(f"Successfully loaded data from {json_file_path} (as dictionary)")
            return data
        else:
            print(f"Warning: Data in {json_file_path} is not in the expected array or dict format, or is empty.")
            return None
    except FileNotFoundError:
        print(f"Error: File not found at {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from {json_file_path}. Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading {json_file_path}: {e}")
        return None

def extract_subject_from_title(section_title):
    if not section_title or not isinstance(section_title, str):
        return "Unknown Subject"
    title_lower = section_title.lower()
    if re.search(r'\bphysics\b', title_lower):
        return "Physics"
    elif re.search(r'\bchemistry\b', title_lower):
        return "Chemistry"
    elif re.search(r'\bmath(s|ematics)?\b', title_lower):
        return "Maths"
    return "Other Subjects"

def process_student_data(data):
    if not data:
        print("Error: No data provided to process.")
        return None

    test_info = data.get("test", {})
    test_name = f"QPT Analysis (Total Marks: {test_info.get('totalMarks', 'N/A')})"
    student_name = data.get("student_name", "Valued Student")

    all_questions_list = []
    if "sections" not in data or not isinstance(data["sections"], list):
        print("Error: 'sections' field is missing or not a list. Cannot process questions deeply.")
        return {
            "student_name": student_name,
            "test_name": test_name,
            "overall_summary": {},
            "subject_performance": {}, "chapter_performance": {}, "difficulty_performance": {},
            "concept_performance": {}, "time_accuracy_summary": {}, "raw_questions_df": pd.DataFrame()
        }

    for section in data.get("sections", []):
        section_id_info = section.get("sectionId", {})
        section_title = section_id_info.get("title", "Unknown Section")
        subject_name_for_section = extract_subject_from_title(section_title)

        for q_data in section.get("questions", []):
            question_detail = q_data.get("questionId", {})
            chapters = [chap.get("title") for chap in question_detail.get("chapters", []) if chap.get("title")]
            primary_chapter = chapters[0] if chapters else "Unknown Chapter"
            concepts = [concept.get("title") for concept in question_detail.get("concepts", []) if concept.get("title")]
            difficulty = question_detail.get("level", "Unknown Difficulty").capitalize()

            is_marked_correct_by_system = False
            if q_data.get("markedOptions") and isinstance(q_data.get("markedOptions"), list):
                for opt in q_data.get("markedOptions"):
                    if opt.get("isCorrect"):
                        is_marked_correct_by_system = True
                        break
            if q_data.get("inputValue", {}).get("isCorrect"):
                is_marked_correct_by_system = True

            q_status_from_json = q_data.get("status", "notAnswered").lower()
            final_q_status_for_df = "Unattempted"
            if q_status_from_json == "answered":
                final_q_status_for_df = "Correct" if is_marked_correct_by_system else "Incorrect"

            all_questions_list.append({
                "subject": subject_name_for_section,
                "chapter": primary_chapter,
                "difficulty": difficulty,
                "concepts": concepts,
                "status": final_q_status_for_df,
                "time_taken_seconds": q_data.get("timeTaken", 0)
            })

    questions_df = pd.DataFrame(all_questions_list)

    total_questions_in_df = len(questions_df)
    total_correct_in_df = sum(questions_df["status"] == "Correct")
    total_incorrect_in_df = sum(questions_df["status"] == "Incorrect")
    total_unattempted_in_df = sum(questions_df["status"] == "Unattempted")
    total_attempted_in_df = total_correct_in_df + total_incorrect_in_df
    overall_accuracy_calculated = (total_correct_in_df / total_questions_in_df) * 100 if total_questions_in_df > 0 else 0

    official_total_questions = test_info.get("totalQuestions", total_questions_in_df)

    overall_summary = {
        "score": data.get("totalMarkScored"),
        "accuracy_percent": round(overall_accuracy_calculated, 2),
        "correct_answers": total_correct_in_df,
        "incorrect_answers": total_incorrect_in_df,
        "unattempted_answers": total_unattempted_in_df,
        "attempted_answers": total_attempted_in_df,
        "total_questions_in_test": total_questions_in_df,
        "official_total_questions_header": official_total_questions,
        "total_marks_in_test": test_info.get("totalMarks"),
        "time_taken_seconds": data.get("totalTimeTaken")
    }

    # SUBJECT-WISE PERFORMANCE (with normalization)
    EXPECTED_QUESTIONS_PER_SUBJECT = {"Physics": 25, "Chemistry": 25, "Maths": 25}
    subject_performance = {}
    if 'subject' in questions_df.columns and not questions_df.empty:
        grouped = questions_df.groupby("subject")
        for subject in ["Physics", "Chemistry", "Maths"]:
            group_df = grouped.get_group(subject) if subject in grouped.groups else pd.DataFrame()
            total_expected = EXPECTED_QUESTIONS_PER_SUBJECT.get(subject, len(group_df))
            count_correct = sum(group_df["status"] == "Correct")
            avg_time = group_df["time_taken_seconds"].mean() if not group_df.empty else 0

            subject_performance[subject] = {
                "total_questions": total_expected,
                "correct_answers": count_correct,
                "accuracy_percent": round((count_correct / total_expected) * 100 if total_expected else 0, 2),
                "average_time_seconds": round(avg_time, 2)
            }

    chapter_performance = {}
    if 'chapter' in questions_df.columns and not questions_df.empty:
        for chapter_name, group_df in questions_df.groupby("chapter"):
            if chapter_name == "Unknown Chapter": continue
            count_total_chap_q = len(group_df)
            count_correct_chap_q = sum(group_df["status"] == "Correct")
            accuracy_chap = (count_correct_chap_q / count_total_chap_q) * 100 if count_total_chap_q > 0 else 0
            avg_time_chap = group_df["time_taken_seconds"].mean() if count_total_chap_q > 0 else 0
            chapter_performance[chapter_name] = {
                "total_questions": count_total_chap_q, "correct_answers": count_correct_chap_q,
                "accuracy_percent": round(accuracy_chap, 2), "average_time_seconds": round(avg_time_chap, 2)
            }

    difficulty_performance = {}
    if 'difficulty' in questions_df.columns and not questions_df.empty:
        for diff_level, group_df in questions_df.groupby("difficulty"):
            if diff_level == "Unknown Difficulty": continue
            count_total_diff_q = len(group_df)
            count_correct_diff_q = sum(group_df["status"] == "Correct")
            accuracy_diff = (count_correct_diff_q / count_total_diff_q) * 100 if count_total_diff_q > 0 else 0
            avg_time_diff = group_df["time_taken_seconds"].mean() if count_total_diff_q > 0 else 0
            difficulty_performance[diff_level] = {
                "total_questions": count_total_diff_q, "correct_answers": count_correct_diff_q,
                "accuracy_percent": round(accuracy_diff, 2), "average_time_seconds": round(avg_time_diff, 2)
            }

    concept_performance_agg = defaultdict(lambda: {"correct": 0, "total": 0, "time_taken_list": []})
    concept_performance = {}
    if 'concepts' in questions_df.columns and not questions_df.empty:
        for _, row_series in questions_df.iterrows():
            for concept in row_series.get("concepts", []):
                if not concept: continue
                concept_performance_agg[concept]["total"] += 1
                if row_series["status"] == "Correct":
                    concept_performance_agg[concept]["correct"] += 1
                concept_performance_agg[concept]["time_taken_list"].append(row_series["time_taken_seconds"])

        for concept, values in concept_performance_agg.items():
            total = values["total"]
            correct = values["correct"]
            avg_time = sum(values["time_taken_list"]) / len(values["time_taken_list"])
            concept_performance[concept] = {
                "total_questions": total, "correct_answers": correct,
                "accuracy_percent": round((correct / total) * 100 if total else 0, 2),
                "average_time_seconds": round(avg_time, 2)
            }

    time_accuracy_summary = {}
    if not questions_df.empty:
        avg_time_correct_q = questions_df[questions_df["status"] == "Correct"]["time_taken_seconds"].mean()
        avg_time_incorrect_q = questions_df[questions_df["status"] == "Incorrect"]["time_taken_seconds"].mean()
        time_accuracy_summary = {
            "avg_time_per_correct_q_seconds": round(avg_time_correct_q, 2) if pd.notna(avg_time_correct_q) else 0,
            "avg_time_per_incorrect_q_seconds": round(avg_time_incorrect_q, 2) if pd.notna(avg_time_incorrect_q) else 0,
        }

    return {
        "student_name": student_name,
        "test_name": test_name,
        "overall_summary": overall_summary,
        "subject_performance": subject_performance,
        "chapter_performance": chapter_performance,
        "difficulty_performance": difficulty_performance,
        "concept_performance": dict(concept_performance),
        "time_accuracy_summary": time_accuracy_summary,
        "raw_questions_df": questions_df
    }

if __name__ == '__main__':
    import os
    sample_data_dir = "sample_data"
    actual_sample_file_name = 'sample_submission_analysis_1.json'
    actual_json_file_path = os.path.join(sample_data_dir, actual_sample_file_name)

    if not os.path.exists(actual_json_file_path):
        print(f"ERROR: The primary test file '{actual_json_file_path}' was not found.")
    else:
        raw_data = load_data(actual_json_file_path)
        if raw_data:
            processed_data = process_student_data(raw_data)
            if processed_data:
                print(json.dumps({k: v for k, v in processed_data.items() if k != 'raw_questions_df'}, indent=2))
                print("\n--- Accuracy Check ---")
                for subj, perf in processed_data.get("subject_performance", {}).items():
                    print(f"{subj}: {perf['accuracy_percent']}%")
