# pdf_generator.py
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak,
    KeepInFrame, HRFlowable, Frame, PageTemplate, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.units import inch, cm, mm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from data_processor import load_data as dp_load_data, process_student_data as dp_process_student_data
from llm_handler import format_data_for_llm as llm_format_data, generate_feedback as llm_generate_feedback
import os
import re 
import matplotlib.pyplot as plt
import io
import pandas as pd
import numpy as np

# --- Enhanced Color Palette (Modern Design System) ---
COLOR_PRIMARY = colors.HexColor('#2563EB')      # Modern Blue
COLOR_PRIMARY_LIGHT = colors.HexColor('#60A5FA') # Light Blue
COLOR_PRIMARY_DARK = colors.HexColor('#1D4ED8')  # Dark Blue
COLOR_SECONDARY = colors.HexColor('#64748B')     # Slate Gray
COLOR_ACCENT = colors.HexColor('#10B981')        # Emerald Green
COLOR_ACCENT_LIGHT = colors.HexColor('#34D399')  # Light Green
COLOR_WARNING = colors.HexColor('#F59E0B')       # Amber
COLOR_DANGER = colors.HexColor('#EF4444')        # Red
COLOR_TEXT = colors.HexColor('#1E293B')          # Dark Slate
COLOR_TEXT_LIGHT = colors.HexColor('#475569')    # Light Slate
COLOR_BACKGROUND = colors.HexColor('#F8FAFC')    # Very Light Gray (Page Background - not directly used by SimpleDocTemplate)
COLOR_CARD_BG = colors.HexColor('#FFFFFF')       # White (for card-like elements)
COLOR_BORDER = colors.HexColor('#E2E8F0')        # Light Border
COLOR_TABLE_HEADER_BG = colors.HexColor('#334155')  # Dark Slate for table headers
COLOR_TABLE_ALT_ROW = colors.HexColor('#F1F5F9')     # Alternating row color for tables

# --- Helper to convert ReportLab color to Matplotlib/Hex string compatible format ---
def to_matplotlib_color(rl_color):
    """Converts a ReportLab color object to a Matplotlib-compatible format (hex string or RGB tuple)."""
    if hasattr(rl_color, 'toHex'): 
        return rl_color.toHex()
    elif hasattr(rl_color, 'red') and hasattr(rl_color, 'green') and hasattr(rl_color, 'blue'):
        alpha = getattr(rl_color, 'alpha', 1.0) 
        return (rl_color.red, rl_color.green, rl_color.blue, alpha)
    elif isinstance(rl_color, str):
        return rl_color
    print(f"Warning: Unknown color type for Matplotlib: {type(rl_color)}. Attempting to pass as is.")
    return rl_color 

def color_to_hex_string(rl_color):
    """Converts a ReportLab color to a hex string for HTML-like font tags."""
    if hasattr(rl_color, 'toHex'):
        return rl_color.toHex()
    elif hasattr(rl_color, 'red') and hasattr(rl_color, 'green') and hasattr(rl_color, 'blue'):
        r = int(rl_color.red * 255)
        g = int(rl_color.green * 255)
        b = int(rl_color.blue * 255)
        return f'#{r:02x}{g:02x}{b:02x}'
    elif isinstance(rl_color, str) and rl_color.startswith('#'):
        return rl_color
    return '#000000' 

# --- Enhanced Chart Creation with Modern Styling ---
def create_modern_bar_chart(labels, values, title, xlabel, ylabel, value_format_string='{:.1f}', chart_type='performance'):
    if not labels or not isinstance(labels, list) or \
       not values or not isinstance(values, list) or \
       len(labels) != len(values):
        print(f"Warning: Invalid data for chart '{title}'. Labels/values empty, not lists, or lengths differ. Skipping chart.")
        return None
    
    try:
        numeric_values_for_plot = []
        for v in values:
            if v is None:
                print(f"Warning: Found None in values for chart '{title}'. Treating as 0.")
                numeric_values_for_plot.append(0.0)
            else:
                numeric_values_for_plot.append(float(v))
    except (ValueError, TypeError) as e:
        print(f"Warning: Non-numeric data found in values for chart '{title}'. Error: {e}. Skipping chart.")
        return None

    if not numeric_values_for_plot:
        print(f"Warning: No valid numeric values to plot for chart '{title}' after conversion. Skipping chart.")
        return None

    # Modern color schemes based on chart type
    chart_bar_colors = []
    if chart_type == 'performance': 
        for val in numeric_values_for_plot:
            if val >= 75: chart_bar_colors.append(to_matplotlib_color(COLOR_ACCENT))      
            elif val >= 50: chart_bar_colors.append(to_matplotlib_color(COLOR_WARNING))
            else: chart_bar_colors.append(to_matplotlib_color(COLOR_DANGER))      
    else: 
        default_palette = [COLOR_PRIMARY, COLOR_PRIMARY_LIGHT, colors.HexColor('#93C5FD'), colors.HexColor('#DBEAFE')]
        chart_bar_colors = [to_matplotlib_color(default_palette[i % len(default_palette)]) for i in range(len(labels))]
    
    plt.style.use('default') 
    fig, ax = plt.subplots(figsize=(7.8, 4.2), facecolor=to_matplotlib_color(COLOR_CARD_BG))
    
    bars = ax.bar(labels, numeric_values_for_plot, 
                  color=chart_bar_colors, 
                  alpha=0.9,
                  edgecolor=to_matplotlib_color(COLOR_BORDER),
                  linewidth=0.5)
    
    ax.set_title(title, fontsize=15, fontweight='600', color=to_matplotlib_color(COLOR_TEXT), pad=18)
    ax.set_xlabel(xlabel, fontsize=10, color=to_matplotlib_color(COLOR_TEXT_LIGHT), fontweight='500', labelpad=10)
    ax.set_ylabel(ylabel, fontsize=10, color=to_matplotlib_color(COLOR_TEXT_LIGHT), fontweight='500', labelpad=10)
    
    ax.tick_params(axis='x', rotation=25, labelsize=8.5, colors=to_matplotlib_color(COLOR_TEXT_LIGHT), pad=5)
    ax.tick_params(axis='y', labelsize=8.5, colors=to_matplotlib_color(COLOR_TEXT_LIGHT), pad=5)
    
    ax.grid(True, axis='y', alpha=0.4, linestyle=':', linewidth=0.6, color=to_matplotlib_color(COLOR_BORDER))
    ax.set_axisbelow(True)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(to_matplotlib_color(COLOR_BORDER))
    ax.spines['bottom'].set_color(to_matplotlib_color(COLOR_BORDER))
    
    max_val = max(numeric_values_for_plot, default=0) if numeric_values_for_plot else 0
    for bar_obj in bars: 
        height = bar_obj.get_height()
        ax.text(bar_obj.get_x() + bar_obj.get_width()/2., height + 0.015 * max_val, 
                value_format_string.format(height), 
                ha='center', va='bottom', fontsize=8, 
                color=to_matplotlib_color(COLOR_TEXT), fontweight='500')
    
    plt.tight_layout(pad=1.8) 
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=250, bbox_inches='tight', facecolor=fig.get_facecolor())
    img_buffer.seek(0)
    plt.close(fig) 
    return img_buffer

# --- Helper Function for Time Formatting ---
def format_seconds_for_pdf(seconds):
    """Converts seconds to a human-readable 'Xm Ys' or 'Ys' string for PDF."""
    if seconds is None or not isinstance(seconds, (int, float)) or seconds < 0:
        return "N/A"
    seconds = int(seconds)
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    if minutes > 0:
        return f"{minutes}m {remaining_seconds}s"
    elif remaining_seconds >= 0:
        return f"{remaining_seconds}s"
    return "N/A"

# --- Enhanced PDF Generation Function ---
def generate_pdf_report(processed_data, ai_feedback_text, output_filename="student_report.pdf", logo_path=None):
    if not processed_data:
        print("Error: No processed data for PDF.")
        return

    doc = SimpleDocTemplate(output_filename, pagesize=A4,
                            rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=22*mm, bottomMargin=18*mm) 
    
    styles = getSampleStyleSheet()
    story = []

    FONT_NORMAL = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
    
    title_style = ParagraphStyle('ModernTitle', parent=styles['h1'], alignment=TA_CENTER, 
                                 fontSize=26, fontName=FONT_BOLD, spaceAfter=6*mm, 
                                 textColor=COLOR_PRIMARY_DARK, leading=30)
    
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, 
                                    fontSize=13, fontName=FONT_NORMAL, spaceAfter=5*mm, 
                                    textColor=COLOR_TEXT_LIGHT, leading=16)
    
    section_heading_style = ParagraphStyle('ModernSectionHeading', parent=styles['h2'], fontSize=17, 
                                           fontName=FONT_BOLD, textColor=COLOR_PRIMARY, 
                                           spaceBefore=7*mm, spaceAfter=3.5*mm, keepWithNext=1, leading=20)

    subsection_heading_style = ParagraphStyle('ModernSubsectionHeading', parent=styles['h3'], fontSize=13, 
                                              fontName=FONT_BOLD, textColor=COLOR_TEXT, 
                                              spaceBefore=5*mm, spaceAfter=2.5*mm, keepWithNext=1, leading=16)

    body_text_style = ParagraphStyle('ModernBodyText', parent=styles['Normal'], fontSize=10.5, 
                                     fontName=FONT_NORMAL, leading=15, alignment=TA_JUSTIFY, 
                                     spaceAfter=2.5*mm, textColor=COLOR_TEXT)

    bullet_style = ParagraphStyle('ModernBulletList', parent=body_text_style, leftIndent=7*mm, 
                                  bulletIndent=3*mm, spaceBefore=1*mm, spaceAfter=1*mm, firstLineIndent=-2*mm) 

    
    main_frame = Frame(doc.leftMargin, doc.bottomMargin, 
                       doc.width, doc.height - 10*mm, 
                       id='main_frame', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    def modern_page_template(canvas, doc):
        canvas.saveState()
        page_width = doc.width + doc.leftMargin + doc.rightMargin
        
    
        header_rect_height = 12*mm
        canvas.setFillColor(COLOR_PRIMARY)
        canvas.rect(0, A4[1] - header_rect_height, A4[0], header_rect_height, fill=1, stroke=0)
        
        if logo_path and os.path.exists(logo_path):
            try: 
                logo_img = Image(logo_path, width=1.5*inch, height=0.4*inch) 
                logo_img.hAlign = 'LEFT'
                logo_img.drawOn(canvas, doc.leftMargin, A4[1] - header_rect_height + 1.5*mm) 
            except Exception as e: print(f"Warning: Could not draw logo: {e}")
        
        canvas.setFont(FONT_BOLD, 11)
        canvas.setFillColor(colors.white)
        canvas.drawCentredString(page_width / 2.0, A4[1] - header_rect_height + 4*mm, 
                                "MathonGo - Student Performance Analysis")
        
        # Modern Footer
        footer_line_y = doc.bottomMargin - 6*mm
        canvas.setStrokeColor(COLOR_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, footer_line_y + 2*mm, 
                    doc.width + doc.leftMargin, footer_line_y + 2*mm)
        
        canvas.setFont(FONT_NORMAL, 8)
        canvas.setFillColor(COLOR_TEXT_LIGHT)
        canvas.drawString(doc.leftMargin, footer_line_y - 1*mm, 
                         f"Report Generated: {pd.Timestamp('now').strftime('%B %d, %Y')}")
        canvas.drawRightString(doc.width + doc.leftMargin, footer_line_y - 1*mm, 
                              f"Page {doc.page}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id='modern_template', frames=[main_frame], onPage=modern_page_template)])

    # --- Report Header ---
    story.append(Paragraph("Student Performance Report", title_style))
    story.append(Paragraph("Detailed Analysis & Actionable Insights", subtitle_style))
    story.append(HRFlowable(width="50%", thickness=1.5, color=COLOR_PRIMARY_LIGHT, 
                           spaceBefore=1*mm, spaceAfter=5*mm, hAlign='CENTER'))

    # --- Student Information Section ---
    story.append(Paragraph("Candidate Overview", section_heading_style))
    
    student_info_table_data = [
        [Paragraph("<b>Student Name:</b>", body_text_style), Paragraph(f"{processed_data.get('student_name', 'N/A')}", body_text_style)],
        [Paragraph("<b>Assessment:</b>", body_text_style), Paragraph(f"{processed_data.get('test_name', 'N/A')}", body_text_style)],
    ]
    overall_sum = processed_data.get('overall_summary', {})
    score_display = f"{overall_sum.get('score', 'N/A')}"
    total_marks_val = overall_sum.get('total_marks_in_test')
    if total_marks_val and total_marks_val != 'N/A': score_display += f" / {total_marks_val}"
    
    accuracy_val = overall_sum.get('accuracy_percent', 0)
    accuracy_color_hex = color_to_hex_string(COLOR_ACCENT if accuracy_val >= 75 else (COLOR_WARNING if accuracy_val >= 50 else COLOR_DANGER))
    accuracy_display_text = f'<font color="{accuracy_color_hex}"><b>{accuracy_val:.1f}%</b></font>' if isinstance(accuracy_val, (int, float)) else str(accuracy_val)

    student_info_table_data.extend([
        [Paragraph("<b>Overall Score:</b>", body_text_style), Paragraph(score_display, body_text_style)],
        [Paragraph("<b>Overall Accuracy:</b>", body_text_style), Paragraph(accuracy_display_text, body_text_style)]
    ])
    
    info_table = Table(student_info_table_data, colWidths=[4.5*cm, None]) 
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 1.5*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5*mm),

    ]))
    story.append(info_table)
    story.append(Spacer(1, 7*mm))

    # --- AI Feedback Section ---
    story.append(Paragraph("Analysis & Personalized Recommendations", section_heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceAfter=3*mm))
    
    if ai_feedback_text and not ai_feedback_text.startswith("Error:"):
        feedback_lines = ai_feedback_text.split('\n')
        for line in feedback_lines:
            line_stripped = line.strip()
            line_processed = line_stripped.replace("**", "") 

            if line_processed.startswith("### "): story.append(Paragraph(line_processed.replace("###", "").strip(), subsection_heading_style))
            elif line_processed.startswith("## "): story.append(Paragraph(line_processed.replace("##", "").strip(), section_heading_style)) # Re-using section for AI's H2
            elif line_stripped.startswith("* ") or line_stripped.startswith("- "):
                content_part = line_stripped[2:].strip().replace("**", "")
                story.append(Paragraph(f"<bullet color='{color_to_hex_string(COLOR_PRIMARY)}'>•</bullet> {content_part}", bullet_style))
            elif re.match(r"^\d+\.\s+", line_stripped):
                content_part = re.sub(r"^\d+\.\s*", "", line_stripped).replace("**", "")
                num_prefix = re.match(r"^(\d+\.)\s*", line_stripped).group(1)
                story.append(Paragraph(f"<b>{num_prefix}</b> {content_part}", bullet_style)) 
            elif line_processed: story.append(Paragraph(line_processed, body_text_style))
    else:
        story.append(Paragraph(f"⚠️ AI feedback could not be generated. Details: {ai_feedback_text}", body_text_style))
    
    story.append(PageBreak())
    story.append(Paragraph("Detailed Performance Visualizations", section_heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceAfter=5*mm))

    # Enhanced table styling function
    def create_styled_data_table(data_rows, colWidths, header_row, col_alignments=None):
        if not data_rows: return None
        table_content = [header_row] + data_rows
        table = Table(table_content, colWidths=colWidths, repeatRows=1)
        
        style_cmds = [
            ('BACKGROUND', (0,0), (-1,0), COLOR_TABLE_HEADER_BG), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD), ('FONTSIZE', (0,0), (-1,0), 9.5),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2.5*mm), ('BOTTOMPADDING', (0,0), (-1,-1), 2.5*mm),
            ('LEFTPADDING', (0,0), (-1,-1), 2*mm), ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
            ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
            ('FONTNAME', (0,1), (-1,-1), FONT_NORMAL), ('FONTSIZE', (0,1), (-1,-1), 9),
            ('TEXTCOLOR', (0,1), (-1,-1), COLOR_TEXT),
        ]
        if col_alignments:
            for i, align in enumerate(col_alignments):
                style_cmds.append(('ALIGN', (i,1), (i,-1), align))
        for i in range(1, len(table_content)):
            if i % 2 == 0: style_cmds.append(('BACKGROUND', (0,i), (-1,i), COLOR_TABLE_ALT_ROW))
        
        table.setStyle(TableStyle(style_cmds))
        return table

    # --- Subject Performance ---
    subject_perf = processed_data.get("subject_performance", {})
    if subject_perf:
        story.append(Paragraph("Subject-wise Performance", subsection_heading_style))
        subjects = list(subject_perf.keys())
        accuracies = [p.get('accuracy_percent', 0) for p in subject_perf.values()]
        
        chart_buf = create_modern_bar_chart(subjects, accuracies, "Subject Accuracy Breakdown", 
                                            "Subject", "Accuracy (%)", chart_type='performance')
        if chart_buf: story.append(Image(chart_buf, width=16.5*cm, height=9*cm)); story.append(Spacer(1, 3*mm))

        header = [Paragraph(h, body_text_style) for h in ["<b>Subject</b>", "<b>Accuracy</b>", "<b>Correct/Total</b>", "<b>Avg. Time</b>"]]
        data_rows = []
        for subj, p_data in subject_perf.items():
            acc_val = p_data.get('accuracy_percent', 0)
            acc_color_hex = color_to_hex_string(COLOR_ACCENT if acc_val >= 75 else (COLOR_WARNING if acc_val >= 50 else COLOR_DANGER))
            acc_text = f'<font color="{acc_color_hex}">{acc_val:.1f}%</font>' if isinstance(acc_val, (int, float)) else str(acc_val)
            data_rows.append([
                Paragraph(subj, body_text_style), Paragraph(acc_text, body_text_style),
                Paragraph(f"{p_data.get('correct_answers',0)}/{p_data.get('total_questions',0)}", body_text_style),
                Paragraph(format_seconds_for_pdf(p_data.get('average_time_seconds')), body_text_style)
            ])
        subj_table = create_styled_data_table(data_rows, [5.5*cm, 3*cm, 3.5*cm, 3*cm], header, ['LEFT', 'CENTER', 'CENTER', 'CENTER'])
        if subj_table: story.append(subj_table)
        story.append(Spacer(1, 6*mm))

    # --- Difficulty Performance ---
    difficulty_perf = processed_data.get("difficulty_performance", {})
    if difficulty_perf:
        story.append(Paragraph("Performance by Difficulty Level", subsection_heading_style))
        ordered_levels = [] 
        for level_key_main in ["Easy", "Medium", "Hard", "Tough"]: 
             if level_key_main in difficulty_perf: ordered_levels.append(level_key_main)
             elif level_key_main.lower() in difficulty_perf: ordered_levels.append(level_key_main.lower())
        for level_key_other in difficulty_perf.keys(): 
            if level_key_other not in ordered_levels and level_key_other.capitalize() not in ordered_levels:
                 ordered_levels.append(level_key_other)

        if ordered_levels:
            accuracies_diff = [difficulty_perf[lvl].get('accuracy_percent', 0) for lvl in ordered_levels]
            level_labels_diff = [lvl.capitalize() for lvl in ordered_levels]
            chart_buf_diff = create_modern_bar_chart(level_labels_diff, accuracies_diff, "Difficulty Level Accuracy",
                                                "Difficulty", "Accuracy (%)", chart_type='performance')
            if chart_buf_diff: story.append(Image(chart_buf_diff, width=15*cm, height=8*cm)); story.append(Spacer(1, 3*mm))
        
        header_diff = [Paragraph(h, body_text_style) for h in ["<b>Difficulty</b>", "<b>Accuracy</b>", "<b>Correct/Total</b>", "<b>Avg. Time</b>"]]
        data_rows_diff = []
        for lvl in ordered_levels:
            p_data = difficulty_perf[lvl]
            acc_val = p_data.get('accuracy_percent', 0)
            acc_color_hex = color_to_hex_string(COLOR_ACCENT if acc_val >= 75 else (COLOR_WARNING if acc_val >= 50 else COLOR_DANGER))
            acc_text = f'<font color="{acc_color_hex}">{acc_val:.1f}%</font>' if isinstance(acc_val, (int, float)) else str(acc_val)
            data_rows_diff.append([
                Paragraph(lvl.capitalize(), body_text_style), Paragraph(acc_text, body_text_style),
                Paragraph(f"{p_data.get('correct_answers',0)}/{p_data.get('total_questions',0)}", body_text_style),
                Paragraph(format_seconds_for_pdf(p_data.get('average_time_seconds')), body_text_style)
            ])
        diff_table = create_styled_data_table(data_rows_diff, [4*cm, 3*cm, 4*cm, 4*cm], header_diff, ['LEFT', 'CENTER', 'CENTER', 'CENTER'])
        if diff_table: story.append(diff_table)
        story.append(Spacer(1, 6*mm))


    # --- Chapter Performance Table ---
    chapter_perf = processed_data.get("chapter_performance", {})
    if chapter_perf:
        story.append(Paragraph("Chapter Performance Highlights", subsection_heading_style))
        sorted_chapters = sorted(chapter_perf.items(), key=lambda item: item[1].get('accuracy_percent', 100))
        
        header_chap = [Paragraph(h, body_text_style) for h in ["<b>Chapter</b>", "<b>Accuracy</b>", "<b>Correct/Total</b>", "<b>Avg. Time</b>"]]
        data_rows_chap = []
        chapters_shown = 0
        for chapter, p_data in sorted_chapters:
            if chapters_shown < 7 or p_data.get('accuracy_percent', 100) < 65: 
                acc_val = p_data.get('accuracy_percent', 0)
                acc_color_hex = color_to_hex_string(COLOR_ACCENT if acc_val >= 75 else (COLOR_WARNING if acc_val >= 50 else COLOR_DANGER))
                acc_text = f'<font color="{acc_color_hex}">{acc_val:.1f}%</font>' if isinstance(acc_val, (int, float)) else str(acc_val)
                data_rows_chap.append([
                    Paragraph(chapter[:35] + '...' if len(chapter) > 35 else chapter, body_text_style),
                    Paragraph(acc_text, body_text_style),
                    Paragraph(f"{p_data.get('correct_answers',0)}/{p_data.get('total_questions',0)}", body_text_style),
                    Paragraph(format_seconds_for_pdf(p_data.get('average_time_seconds')), body_text_style)
                ])
                chapters_shown +=1
            if chapters_shown >= 10: break 
        
        if data_rows_chap:
            chap_table = create_styled_data_table(data_rows_chap, [6*cm, 3*cm, 3.5*cm, 2.5*cm], header_chap, ['LEFT', 'CENTER', 'CENTER', 'CENTER'])
            if chap_table: story.append(chap_table)
        story.append(Spacer(1, 6*mm))


    # --- Build the PDF ---
    try:
        doc.build(story)
        print(f"✅ Modern PDF report generated successfully: {output_filename}")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        try:
            print("🔄 Attempting simplified PDF generation...")
            simple_story_content = [Paragraph("Student Performance Report (Simplified)", title_style)]
            simple_doc_filename = output_filename.replace(".pdf", "_simplified.pdf")
            simple_doc = SimpleDocTemplate(simple_doc_filename, pagesize=A4)
            simple_doc.build(simple_story_content)
            print(f"✅ Simplified PDF generated: {simple_doc_filename}")
        except Exception as e_simple:
            print(f"❌ Failed to generate even simplified PDF: {e_simple}")

# --- Test module execution ---
if __name__ == '__main__':
    print("🧪 Testing Enhanced PDF Generator...")
    
    sample_data_dir = "sample_data"
    sample_file = 'sample_submission_analysis_1.json' 
    test_json_path = os.path.join(sample_data_dir, sample_file)

    processed_data_for_pdf_test = None
    if os.path.exists(test_json_path):
        print(f"📂 Loading test data from: {test_json_path}")
        raw_data_test = dp_load_data(test_json_path)
        if raw_data_test:
            processed_data_for_pdf_test = dp_process_student_data(raw_data_test)
            if not processed_data_for_pdf_test:
                 print("❌ Failed to process data for PDF test.")
        else:
            print("❌ Failed to load data for PDF test.")
    else:
        print(f"❌ Test data file not found: {test_json_path}. PDF generator test cannot run with real data.")

    if processed_data_for_pdf_test:
        student_name_test = processed_data_for_pdf_test.get("student_name", "Test Student")
        print(f"🧠 Formatting data for LLM for student: {student_name_test}")
        llm_context_test = llm_format_data(processed_data_for_pdf_test)
        
        ai_feedback_for_pdf_test = "Test AI Feedback: Student showed good effort. Focus on weak areas." # Default
        if not llm_context_test.startswith("Error") and llm_context_test != "No data available to format for LLM.":
            print("📞 Requesting AI feedback for PDF test (this may take a moment)...")
            ai_feedback_for_pdf_test = llm_generate_feedback(llm_context_test, student_name_test)
            if ai_feedback_for_pdf_test.startswith("Error:"):
                 print(f"⚠️ AI feedback generation failed for PDF test: {ai_feedback_for_pdf_test}")
            else:
                 print("👍 AI feedback generated successfully for PDF test.")
        else:
            print(f"⚠️ Could not format data for LLM: {llm_context_test}")
            ai_feedback_for_pdf_test = f"Error: Could not format data for AI. Details: {llm_context_test}"
        
        output_dir_test = "generated_reports_enhanced_test"
        os.makedirs(output_dir_test, exist_ok=True)
        
        pdf_output_path_test = os.path.join(output_dir_test, "enhanced_module_test_report.pdf")
        test_logo_path = None 
        
        print(f"📄 Generating PDF: {pdf_output_path_test}")
        generate_pdf_report(processed_data_for_pdf_test, ai_feedback_for_pdf_test, 
                            output_filename=pdf_output_path_test, logo_path=test_logo_path)
    else:
        print("❌ No processed data available. PDF generator test cannot proceed with full features.")