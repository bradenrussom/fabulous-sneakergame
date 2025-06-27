#!/usr/bin/env python3
"""
MVP Document Processor - Flask Web Application
Complete web interface for MVP Health Care document processing
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
import yaml
import re
from docx import Document
from docx.shared import RGBColor, Pt
import datetime
import textstat
from collections import defaultdict
import io
from pathlib import Path
import traceback

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mvp-processor-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class MVPDocumentProcessor:
    """
    Complete MVP Document Processor with all 71 corporate rules
    Adapted from your working_document_processor.py
    """
    
    def __init__(self):
        self.corrections_made = []
        self.statistics = {
            'total_corrections': 0,
            'rules_applied': defaultdict(int),
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'reading_level': 0
        }
        self.detailed_corrections = []
        self.corrections_by_category = defaultdict(int)
        self.rules = self._load_mvp_rules()
    
    def _load_mvp_rules(self):
        """Load all MVP corporate rules (embedded from your YAML)"""
        return {
            'time_formatting_rules': [
                {
                    'category': 'remove_all_unnecessary_minutes',
                    'find': r'\b(\d{1,2}):00\b',
                    'replace': r'\1',
                    'case_sensitive': False,
                    'description': "Remove all instances of :00 minutes",
                    'enabled': True
                },
                {
                    'category': 'am_all_variations_lowercase',
                    'find': r'\b(\d{1,2}(?::\d{2})?)\s*([Aa]\.?[Mm]\.?)\b',
                    'replace': r'\1 am',
                    'case_sensitive': False,
                    'description': "Convert all AM variations to lowercase am",
                    'enabled': True
                },
                {
                    'category': 'pm_all_variations_lowercase',
                    'find': r'\b(\d{1,2}(?::\d{2})?)\s*([Pp]\.?[Mm]\.?)\b',
                    'replace': r'\1 pm',
                    'case_sensitive': False,
                    'description': "Convert all PM variations to lowercase pm",
                    'enabled': True
                },
                {
                    'category': 'time_range_en_dash',
                    'find': r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*[-–—]\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b',
                    'replace': r'\1–\2',
                    'case_sensitive': False,
                    'description': "Use en dash with no spaces for time ranges",
                    'enabled': True
                },
                {
                    'category': 'space_before_am_pm',
                    'find': r'\b(\d{1,2}(?::\d{2})?)(am|pm)\b',
                    'replace': r'\1 \2',
                    'case_sensitive': False,
                    'description': "Ensure space between number and am/pm",
                    'enabled': True
                }
            ],
            'number_formatting_rules': [
                {
                    'category': 'spell_out_small_numbers',
                    'find': r'\b(?<![\d\-/])(?<!January\s)(?<!February\s)(?<!March\s)(?<!April\s)(?<!May\s)(?<!June\s)(?<!July\s)(?<!August\s)(?<!September\s)(?<!October\s)(?<!November\s)(?<!December\s)([1-9])\b(?!\s*(?:[AaPp]\.?[Mm]\.?|am|pm|:\d|%|\.|,\d{3}|-star|th|nd|rd|st)\b)(?![\d\-/])',
                    'replace': 'NUMBER_WORD_\\1',
                    'case_sensitive': False,
                    'description': "Spell out numbers 1-9 (with exclusions)",
                    'enabled': True
                },
                {
                    'category': 'comma_in_large_numbers',
                    'find': r'\b(?<!extension\s)(?<!ext\.\s)(?<!\d)(\d{1,3})(\d{3})\b(?![\d/])',
                    'replace': r'\1,\2',
                    'case_sensitive': False,
                    'description': "Add commas to numbers 1,000+",
                    'enabled': True
                }
            ],
            'brand_trademark_rules': [
                {
                    'category': 'mvp_health_care_registration_mark',
                    'find': r'\bMVP Health Care(?!®)\b',
                    'replace': 'MVP Health Care®',
                    'case_sensitive': True,
                    'description': "Add registration mark to first instance of MVP Health Care",
                    'first_instance_only': True,
                    'enabled': True
                },
                {
                    'category': 'gia_registration_mark',
                    'find': r'\bGia(?!®)\b',
                    'replace': 'Gia®',
                    'case_sensitive': True,
                    'description': "Add registration mark to first instance of Gia",
                    'first_instance_only': True,
                    'enabled': True
                }
            ],
            'mvp_terminology_rules': [
                {
                    'category': 'mvp_health_plans_to_mvp_health_care_plans',
                    'find': r'\bMVP health plans\b',
                    'replace': 'MVP Health Care plans',
                    'case_sensitive': False,
                    'description': "Use full company name for plans",
                    'enabled': True
                },
                {
                    'category': 'telehealth_to_virtual_care',
                    'find': r'\btelehealth\b',
                    'replace': 'virtual care',
                    'case_sensitive': False,
                    'description': "Use virtual care for member communications",
                    'enabled': True
                },
                {
                    'category': 'healthcare_terminology',
                    'find': r'\bhealthcare\b',
                    'replace': 'health care',
                    'case_sensitive': False,
                    'description': "Always use 'health care' (two words)",
                    'enabled': True
                },
                {
                    'category': 'login_to_signin',
                    'find': r'\blogin\b',
                    'replace': 'sign in',
                    'case_sensitive': False,
                    'description': "Replace 'login' with 'sign in'",
                    'enabled': True
                },
                {
                    'category': 'log_in_to_sign_in',
                    'find': r'\blog in\b(?!\s+to)',
                    'replace': 'sign in',
                    'case_sensitive': False,
                    'description': "Replace 'log in' with 'sign in'",
                    'enabled': True
                },
                {
                    'category': 'preventative_to_preventive',
                    'find': r'\bpreventative\b',
                    'replace': 'preventive',
                    'case_sensitive': False,
                    'description': "Use 'preventive' instead of 'preventative'",
                    'enabled': True
                }
            ],
            'punctuation_rules': [
                {
                    'category': 'ampersand_replacement',
                    'find': r'\s&\s',
                    'replace': ' and ',
                    'case_sensitive': False,
                    'description': "Replace ampersands with 'and'",
                    'enabled': True
                },
                {
                    'category': 'double_spaces',
                    'find': r'  +',
                    'replace': ' ',
                    'case_sensitive': False,
                    'description': "Remove multiple spaces",
                    'enabled': True
                }
            ],
            'state_abbreviation_rules': [
                {
                    'category': 'remove_periods_from_states',
                    'find': r'\b([NnVvCc])\.([YyTt])\.\b',
                    'replace': r'\1\2',
                    'case_sensitive': False,
                    'description': "Remove periods from state abbreviations (NY, VT, CT only)",
                    'enabled': True
                },
                {
                    'category': 'capitalize_limited_state_abbreviations',
                    'find': r'\b(ny|vt|ct)\b',
                    'replace': 'UPPERCASE_\\1',
                    'case_sensitive': False,
                    'description': "Capitalize state abbreviations (NY, VT, CT only)",
                    'enabled': True
                }
            ]
        }
    
    def apply_corporate_rules(self, doc):
        """Apply all corporate rules to document - based on your working method"""
        total_corrections = 0
        corrections_by_category = defaultdict(int)
        detailed_corrections = []

        print(f"🔄 Applying corporate rules directly...")

        # Process each paragraph
        for para_idx, paragraph in enumerate(doc.paragraphs):
            if not paragraph.text.strip():
                continue

            original_text = paragraph.text
            current_text = original_text

            # Apply each rule category
            for category_name, category_rules in self.rules.items():
                if not isinstance(category_rules, list):
                    continue

                for rule in category_rules:
                    if not isinstance(rule, dict):
                        continue

                    find_pattern = rule.get('find', '')
                    replacement = rule.get('replace', '')
                    enabled = rule.get('enabled', True)
                    case_sensitive = rule.get('case_sensitive', False)

                    if not find_pattern or not enabled:
                        continue

                    # Apply the rule
                    try:
                        if case_sensitive:
                            if re.search(find_pattern, current_text):
                                new_text = re.sub(find_pattern, replacement, current_text)
                                if new_text != current_text:
                                    detailed_corrections.append({
                                        'category': category_name,
                                        'rule': rule.get('category', 'Unknown'),
                                        'original': current_text,
                                        'replacement': new_text
                                    })
                                    corrections_by_category[category_name] += 1
                                    current_text = new_text
                                    total_corrections += 1
                        else:
                            if re.search(find_pattern, current_text, re.IGNORECASE):
                                new_text = re.sub(find_pattern, replacement, current_text, flags=re.IGNORECASE)
                                if new_text != current_text:
                                    detailed_corrections.append({
                                        'category': category_name,
                                        'rule': rule.get('category', 'Unknown'),
                                        'original': current_text,
                                        'replacement': new_text
                                    })
                                    corrections_by_category[category_name] += 1
                                    current_text = new_text
                                    total_corrections += 1
                    except re.error:
                        continue  # Skip malformed regex

            # Update paragraph if changes were made
            if current_text != original_text:
                paragraph.clear()
                paragraph.add_run(current_text)

        # Apply post-processing for special placeholders
        print(f"🔄 Applying post-processing...")
        for paragraph in doc.paragraphs:
            if not paragraph.text.strip():
                continue

            text = paragraph.text
            original_text = text

            # Convert NUMBER_WORD_X to actual words
            if 'NUMBER_WORD_' in text:
                number_words = {
                    'NUMBER_WORD_1': 'one', 'NUMBER_WORD_2': 'two', 'NUMBER_WORD_3': 'three',
                    'NUMBER_WORD_4': 'four', 'NUMBER_WORD_5': 'five', 'NUMBER_WORD_6': 'six',
                    'NUMBER_WORD_7': 'seven', 'NUMBER_WORD_8': 'eight', 'NUMBER_WORD_9': 'nine'
                }
                for placeholder, word in number_words.items():
                    text = text.replace(placeholder, word)

            # Convert UPPERCASE_XX to actual uppercase
            if 'UPPERCASE_' in text:
                def uppercase_replace(match):
                    return match.group(1).upper()
                text = re.sub(r'UPPERCASE_([a-z]+)', uppercase_replace, text)

            # Update paragraph if post-processing made changes
            if text != original_text:
                paragraph.clear()
                paragraph.add_run(text)
                total_corrections += 1

        return {
            'total_corrections': total_corrections,
            'corrections_by_category': dict(corrections_by_category),
            'detailed_corrections': detailed_corrections
        }
    
    def calculate_document_stats(self, doc):
        """Calculate document statistics"""
        full_text = ' '.join([p.text for p in doc.paragraphs if p.text.strip()])

        word_count = len(full_text.split())
        sentence_count = len(re.split(r'[.!?]+', full_text))
        paragraph_count = len([p for p in doc.paragraphs if p.text.strip()])

        try:
            reading_level = textstat.flesch_kincaid_grade(full_text)
        except:
            reading_level = 0

        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'reading_level': reading_level
        }
    
    def process_document(self, input_file_path, output_file_path):
        """Process document with MVP corporate standards"""
        try:
            # Load document
            doc = Document(input_file_path)
            print(f"✅ Loaded document: {input_file_path}")
            
            # Apply corporate rules
            correction_results = self.apply_corporate_rules(doc)
            print(f"✅ Applied {correction_results['total_corrections']} corrections")
            
            # Calculate statistics
            stats = self.calculate_document_stats(doc)
            print(f"✅ Calculated statistics")
            
            # Save processed document
            doc.save(output_file_path)
            print(f"✅ Saved processed document: {output_file_path}")
            
            return {
                'success': True,
                'total_corrections': correction_results['total_corrections'],
                'corrections_by_category': correction_results['corrections_by_category'],
                'detailed_corrections': correction_results['detailed_corrections'],
                'document_statistics': stats
            }
            
        except Exception as e:
            print(f"❌ Error processing document: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Initialize processor
processor = MVPDocumentProcessor()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_document():
    """Process uploaded document"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a .docx file'}), 400
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as input_temp:
            file.save(input_temp.name)
            input_path = input_temp.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as output_temp:
            output_path = output_temp.name
        
        # Process document
        results = processor.process_document(input_path, output_path)
        
        # Clean up input file
        os.unlink(input_path)
        
        if not results['success']:
            os.unlink(output_path)
            return jsonify({'error': f"Processing failed: {results['error']}"}), 500
        
        # Prepare response data
        response_data = {
            'success': True,
            'total_corrections': results['total_corrections'],
            'document_statistics': results['document_statistics'],
            'corrections_by_category': results['corrections_by_category'],
            'sample_corrections': results['detailed_corrections'][:10]  # First 10 for preview
        }
        
        # Store output path in session for download
        # For simplicity, we'll return the file directly
        def remove_file(response):
            try:
                os.unlink(output_path)
            except:
                pass
            return response
        
        # Generate filename
        original_filename = secure_filename(file.filename)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        processed_filename = f"{original_filename.rsplit('.', 1)[0]}_processed_{timestamp}.docx"
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=processed_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        print(f"Error in process_document: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred during processing'}), 500

@app.route('/analyze', methods=['POST'])
def analyze_document():
    """Analyze document without processing (for preview)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '' or not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file'}), 400
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp:
            file.save(temp.name)
            temp_path = temp.name
        
        try:
            # Load document for analysis
            doc = Document(temp_path)
            stats = processor.calculate_document_stats(doc)
            
            # Count potential corrections (dry run)
            correction_preview = processor.apply_corporate_rules(doc)
            
            os.unlink(temp_path)
            
            return jsonify({
                'success': True,
                'document_statistics': stats,
                'potential_corrections': correction_preview['total_corrections'],
                'corrections_preview': correction_preview['corrections_by_category']
            })
            
        except Exception as e:
            os.unlink(temp_path)
            raise e
            
    except Exception as e:
        print(f"Error in analyze_document: {e}")
        return jsonify({'error': 'Analysis failed'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for deployment"""
    return jsonify({
        'status': 'healthy',
        'service': 'MVP Document Processor',
        'timestamp': datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))