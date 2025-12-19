import os
import time
import shutil
import traceback
import base64
import subprocess
import platform
from datetime import datetime
import requests
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
from fpdf import FPDF
import chatbot as y
from config import SARVAM_API_KEY
# Configure Flask to serve static files from parent directory
app = Flask(__name__, static_folder='../static', static_url_path='/static')
CORS(app)

API_KEY = SARVAM_API_KEY


global i
i = 0

global selected_language
selected_language = None


def generate_patient_report_pdf(filename, demographics, other_data, summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Define colors
    header_color = (0, 102, 153)  # Blue
    text_color = (0, 0, 0)        # Black
    light_gray = (240, 240, 240)  # Light gray for backgrounds

    def add_header():
        """Add hospital header with logo area and contact info"""
        # Hospital name and logo area
        pdf.set_fill_color(*light_gray)
        pdf.rect(10, 10, 190, 25, 'F')

        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(*header_color)
        pdf.set_xy(15, 18)
        pdf.cell(0, 8, "INDRAPRASTHA INSTITUTE OF INFORMATION TECHNOLOGY", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(*text_color)
        pdf.set_xy(15, 26)
        pdf.cell(0, 6, "A413, Research & Development Building, IIIT Delhi, Okhla, Phase 3, New Delhi, India, 110020", ln=True, align='C')
        pdf.ln(8)

    def add_patient_header(demographics):
        """Add patient basic info header"""
        y_start = pdf.get_y()

        # Patient name and basic info
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(*text_color)
        patient_name = demographics.get("Name", ["Ankit Agarwal"])[0]
        pdf.cell(0, 8, patient_name, ln=True)

        # Patient details in two columns
        pdf.set_font("Arial", "", 10)

        # Left column
        pdf.set_xy(15, pdf.get_y())
        dob = demographics.get("DOB", ["08/01/2006"])[0]
        pdf.cell(60, 6, f"DOB: {dob}", ln=False)

        # Right column
        pdf.set_xy(120, pdf.get_y())
        pcc_num = demographics.get("PCC#", ["123456"])[0]
        pdf.cell(0, 6, f"PCC #: {pcc_num}", ln=True)

        # Second row
        pdf.set_xy(15, pdf.get_y())
        sex = demographics.get("Gender", ["Male"])[0]
        pdf.cell(60, 6, f"Sex: {sex}", ln=False)

        # Date and time stamps
        pdf.set_xy(120, pdf.get_y())
        current_date = datetime.now().strftime("%m/%d/%y")
        pdf.cell(0, 6, f"Date of Last Physical: {current_date}", ln=True)

        pdf.ln(3)

        # Scheduled visits
        pdf.set_xy(15, pdf.get_y())
        pdf.cell(60, 6, "Scheduled Visits: None", ln=True)

        # Add separator line
        pdf.ln(2)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)

    def add_section_title(title):
        """Add a section title with consistent formatting"""
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(*header_color)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_text_color(*text_color)
        pdf.ln(2)

    def add_field(label, value, indent=0):
        """Add a field with label and value"""
        pdf.set_font("Arial", "B", 10)
        pdf.set_x(15 + indent)
        pdf.cell(40, 6, f"{label}:", ln=False)

        pdf.set_font("Arial", "", 10)
        if isinstance(value, list):
            value = ", ".join(value) if value else "Not specified"
        elif not value:
            value = "Not specified"

        # Handle long text with multi_cell
        if len(str(value)) > 50:
            pdf.ln(6)
            pdf.set_x(15 + indent)
            pdf.multi_cell(0, 5, str(value))
        else:
            pdf.cell(0, 6, str(value), ln=True)
        pdf.ln(1)

    def add_section_separator():
        """Add a subtle section separator"""
        pdf.ln(2)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

    # Generate the report
    add_header()
    add_patient_header(demographics)

    # Patient Contact Information
    add_section_title("Contact Information")
    add_field("Phone", demographics.get("Contact", ["8824146925"])[0])
    add_field("Address", demographics.get("City", ["Delhi"])[0])
    add_section_separator()

    # Chief Complaint - Enhanced Structure
    add_section_title("Chief Complaint (CC)")

    # Handle both simple summary and structured complaint data
    if isinstance(summary, dict):
        # Structured medical data
        if "chief_complaint" in summary:
            pdf.set_font("Arial", "B", 10)
            pdf.set_x(15)
            pdf.cell(0, 6, "CHIEF COMPLAINT:", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.set_x(15)
            pdf.multi_cell(0, 5, summary["chief_complaint"])
            pdf.ln(2)

        if "present_illness" in summary:
            pdf.set_font("Arial", "B", 10)
            pdf.set_x(15)
            pdf.cell(0, 6, "PRESENT ILLNESS:", ln=True)

            # Handle present illness details
            illness_details = summary["present_illness"]
            if isinstance(illness_details, dict):
                for key, value in illness_details.items():
                    pdf.set_font("Arial", "", 10)
                    pdf.set_x(20)
                    pdf.cell(0, 5, f"- {key.replace('_', ' ').title()}: {value}", ln=True)
            else:
                pdf.set_font("Arial", "", 10)
                pdf.set_x(20)
                pdf.multi_cell(0, 5, str(illness_details))
            pdf.ln(2)

        if "additional_notes" in summary:
            pdf.set_font("Arial", "B", 10)
            pdf.set_x(15)
            pdf.cell(0, 6, "ADDITIONAL NOTES:", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.set_x(15)
            pdf.multi_cell(0, 5, summary["additional_notes"])
    else:
        # Simple text summary
        safe_summary = (summary or "No chief complaint documented").replace("•", "-")
        pdf.set_font("Arial", "", 10)
        pdf.set_x(15)
        pdf.multi_cell(0, 5, safe_summary)

    add_section_separator()

    # Medical History Section
    add_section_title("Medical History")

    # Allergies
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(150, 0, 0)  # Red for allergies
    pdf.set_x(15)
    pdf.cell(0, 6, "Allergies:", ln=True)
    pdf.set_text_color(*text_color)

    allergies = other_data.get("Allergies", [])
    if allergies:
        pdf.set_font("Arial", "", 10)
        pdf.set_x(20)
        pdf.multi_cell(0, 5, ", ".join(allergies))
    else:
        pdf.set_font("Arial", "", 10)
        pdf.set_x(20)
        pdf.cell(0, 6, "No known allergies (NKA)", ln=True)
    pdf.ln(2)

    # Past Medical History
    add_field("Past Medical History", other_data.get("Past Medical history", "None"))
    add_field("Past Surgical History", other_data.get("Past surgeries", "None"))
    add_field("Family History", other_data.get("Family History", "None"))

    add_section_separator()

    # Social History
    add_section_title("Social History")
    smoking = other_data.get("Smoking", "Not assessed")
    drinking = other_data.get("Drinking", "Not assessed")

    add_field("Tobacco Use", smoking, indent=5)
    add_field("Alcohol Use", drinking, indent=5)

    # Footer with generation timestamp
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(100, 100, 100)
    timestamp = datetime.now().strftime("%m/%d/%Y at %I:%M %p")
    pdf.cell(0, 6, f"Report generated on {timestamp}", ln=True, align="C")

    # Save the PDF
    pdf.output(filename)


global variable
variable = ""

global qa_history

qa_history = []
global remaining_data
remaining_data = {}

def clear(text):
     # Remove leading and trailing spaces
    k = 0
    for i in range(len(text)):
        if text [i] == ":":
            k = i + 1
    st = text[k:]
    st = st.strip()
    return st

def question_generator(patient_input):
    global qa_history
    global variable
    global i
    if i == 0:
        variable="Hello and welcome! I’m your virtual health assistant, here to help you. I’ll ask you a few questions to better understand how you're feeling today. Let’s begin by telling me what is your chief complaint?"
        return variable
    elif i >= 1 and i <= 6:
        next_q = y.generate_next_medical_question(patient_input, qa_history)
        next_q= clear(next_q)
        if next_q.upper() == "DONE" or "done" in next_q.lower():
            # print("Doctor: Thank you, I have gathered sufficient information for initial assessment.")
            i = 7
            variable = "Do you have any known allergies to medications, foods, or other substances?"
            return variable
        variable = next_q
        return next_q

    elif i == 7:
        # print("Doctor: Thank you, I have gathered sufficient information for initial assessment.")
        variable = "Do you have any known allergies to medications, foods, or other substances?"
        return variable
    elif i ==8:
        # print("Doctor: Do you have any known allergies to medications, foods, or other substances?")
        variable = "Do you have any ongoing or past medical conditions (like diabetes, hypertension, asthma)?"
        return variable
    elif i == 9:
        # print("Doctor: Do you have any ongoing or past medical conditions (e.g., diabetes, hypertension, asthma)?")
        variable = "Have you had any surgeries in the past? If yes, what procedures and when were they performed?"
        return variable
    elif i == 10:
        # print("Doctor: Have you had any surgeries in the past? If yes, what procedures and when were they performed?")
        variable = "Are there any major health conditions or illnesses in your immediate family, such as your parents, siblings, or children? If so, what are they?"
        return variable
    elif i == 11:
        # print("Doctor: Are there any major health conditions or illnesses in your immediate family, such as your parents, siblings, or children? If so, what are they?")
        variable = "Do you smoke?"
        return variable
    elif i == 12:
        # print("Doctor: Do you smoke or use any tobacco products?")
        variable = "Do you drink alcohol?"
        return variable

    variable = (
            "Your consultation is now complete! "
            "Thank you for using our OPD chatbot. "
            "To access your medical report, please click the Download Report button below. "
            "We wish you good health!")
    return variable

@app.route('/')
def choose_language():
    return render_template('language.html')

@app.route('/start', methods=['POST'])
def start_conversation():
    global selected_language
    selected_language = request.form.get('language')
    if not selected_language:
        return redirect(url_for('choose_language'))
    return redirect(url_for('index'))

@app.route('/index')
def index():
    global selected_language
    # If no language is selected, redirect to language selection
    if not selected_language:
        return redirect(url_for('choose_language'))

    # Take only the language code part (e.g., 'en' from 'en-IN')
    language_code = selected_language[:2]
    print(f"Selected language: {language_code}")  # Debugging line

    # Pass full language code for proper display in the UI
    return render_template('index.html', language=selected_language)

@app.route('/end-session', methods=['POST'])
def end_session():
    global i, qa_history, remaining_data

    # Fill any missing fields
    if i <= 8:
        remaining_data.setdefault("Allergies", None)
    if i <= 9:
        remaining_data.setdefault("Past Medical history", None)
    if i <= 10:
        remaining_data.setdefault("Past surgeries", None)
    if i <= 11:
        remaining_data.setdefault("Family History", None)
    if i <= 12:
        remaining_data.setdefault("Smoking", None)
        remaining_data.setdefault("Drinking", None)
    i = 13  # Mark session as completed
    get_data()  # Generate report
    return jsonify({"success": True})

@app.route('/change-language')
def change_language():
    global selected_language
    # Reset language selection
    selected_language = None
    return redirect(url_for('choose_language'))

@app.route('/reset-session', methods=['POST'])
def reset_session():
    global i, variable, qa_history, remaining_data, selected_language
    i = 0
    variable = ""
    qa_history = []
    remaining_data = {}
    selected_language = None
    return jsonify({"status": "reset successful"})

def translate(text, language):
    # Handle special cases and normalize language codes
    if language == "od":
        language = "or"

    # Extract the language code part (e.g., 'en' from 'en-IN')
    if '-' in language:
        language = language.split('-')[0]

    print(f"Translating with language code: {language}")

    # Safety check - if language code is invalid, default to English
    try:
        return GoogleTranslator(source='auto', target=language).translate(text)
    except Exception as e:
        print(f"Translation error: {e}. Defaulting to English.")
        return GoogleTranslator(source='auto', target='en').translate(text)

# ---------- SPEECH TO TEXT ----------
def speech_to_text():
    try:
        # Use the global API key from config.py
        url = "https://api.sarvam.ai/speech-to-text-translate"
        headers = {'api-subscription-key': API_KEY}

        # Add some additional context for better recognition
        payload = {
            'model': 'saaras:v1',
            'prompt': 'Medical consultation, possible symptoms and patient history',
            'language': 'auto'  # Let the API auto-detect language
        }
        file_path = 'output_final.wav'

        if not os.path.exists(file_path):
            print("Audio file missing.")
            return "None"

        file_size = os.path.getsize(file_path)
        if file_size < 1024:
            print(f"Audio file too small: {file_size} bytes - continuing anyway")
            # Still try to process it

        print(f"Sending audio file ({file_size} bytes) to STT API")

        with open(file_path, 'rb') as audio_file:
            # Use the correct mime type
            files = [('file', (file_path, audio_file, 'audio/wav'))]
            # Increase timeout for larger files
            timeout = max(30, int(file_size / 10000))  # 1MB = ~100s timeout
            response = requests.post(url, headers=headers, data=payload, files=files, timeout=timeout)

        if response.status_code == 200:
            try:
                response_data = response.json()
                transcript = response_data.get('transcript')

                # Print the full response for debugging
                print(f"STT API Response: {response_data}")

                if transcript and transcript.strip():
                    return transcript
                else:
                    print("Empty transcript returned from the API.")
                    return "I couldn't hear that clearly"
            except ValueError as e:
                print(f"Failed to decode JSON response: {e}")
                print(f"Response content: {response.text[:200]}...")  # Print the first 200 chars
                return "None"
        else:
            print(f"STT API error: {response.status_code}, {response.text}")

            # More detailed error handling based on status code
            if response.status_code == 413:
                print("File too large for the API")
            elif response.status_code == 429:
                print("API rate limit exceeded")
            elif response.status_code >= 500:
                print("Server error, might be temporary")

            return "None"
    except requests.exceptions.Timeout:
        print("STT API request timed out")
        return "None"
    except requests.exceptions.ConnectionError:
        print("Connection error when calling STT API")
        return "None"
    except Exception as e:
        print(f"STT Exception: {e}")
        print(traceback.format_exc())
        return "None"

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    global i
    global variable
    global qa_history
    global remaining_data
    global selected_language
    try:
        if 'file' not in request.files:
            print("No file uploaded")
            return jsonify({'error': 'No file uploaded', 'transcript': ''}), 400

        file = request.files['file']

        # Check if the filename is empty
        if file.filename == '':
            print("Empty filename received")
            return jsonify({'error': 'No selected file', 'transcript': ''}), 400

        # Get the file content type
        content_type = file.content_type
        print(f"Received file with content type: {content_type}")

        # Get a unique timestamp if provided in the form
        timestamp = request.form.get('timestamp', str(int(time.time())))
        temp_file = f"temp_audio_{timestamp}.wav"

        # First save to a temporary file
        file.save(temp_file)

        # Check if the file exists and has content
        if not os.path.exists(temp_file):
            print("Failed to save temporary file")
            return jsonify({'error': 'Failed to save audio file', 'transcript': ''}), 500

        file_size = os.path.getsize(temp_file)
        if file_size < 100:  # Extremely small files are definitely invalid
            print(f"Audio file too small: {file_size} bytes")
            os.remove(temp_file)
            return jsonify({'error': 'Audio file too small or empty', 'transcript': ''}), 400

        # Try to convert the file to the correct WAV format if it's not already
        try:
            # If output_final.wav already exists, remove it first
            if os.path.exists("output_final.wav"):
                os.remove("output_final.wav")
                print("Removed existing output_final.wav file")

            # Check if ffmpeg is available
            try:
                if platform.system() == 'Windows':
                    subprocess.run(['where', 'ffmpeg'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    subprocess.run(['which', 'ffmpeg'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Use ffmpeg to convert to standard WAV format
                print(f"Converting audio file to standard WAV format")
                subprocess.run([
                    'ffmpeg', '-y', '-i', temp_file,
                    '-acodec', 'pcm_s16le',
                    '-ac', '1',
                    '-ar', '16000',
                    'output_final.wav'
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Remove temporary file
                os.remove(temp_file)
                print("Audio conversion successful")

            except subprocess.CalledProcessError:
                print("ffmpeg not available, using the original file")
                # If ffmpeg is not available, just rename the file
                shutil.copy(temp_file, "output_final.wav")
                os.remove(temp_file)
                print("File copied to output_final.wav")
        except Exception as e:
            print(f"Error during audio conversion: {e}")
            # If there's an error in conversion, try to copy the file instead of rename
            try:
                shutil.copy(temp_file, "output_final.wav")
                os.remove(temp_file)
                print("File copied to output_final.wav after error handling")
            except Exception as copy_error:
                print(f"Failed to copy file: {copy_error}")
                # Last resort - try direct streaming instead of file operations
                pass

        # Validate WAV header to ensure file is not corrupted
        try:
            if os.path.exists("output_final.wav"):
                with open("output_final.wav", "rb") as f:
                    header = f.read(44)  # Read the entire WAV header
                    # For WebM files converted without FFmpeg, we'll skip the strict WAV header check
                    if content_type != 'audio/webm' and not (header[:4] == b'RIFF' and header[8:12] == b'WAVE'):
                        print("Invalid WAV file header detected.")
                        print("Continuing anyway to attempt transcription")
                    else:
                        # Extract sample rate and channels for debugging
                        try:
                            sample_rate = int.from_bytes(header[24:28], byteorder='little')
                            channels = int.from_bytes(header[22:24], byteorder='little')
                            print(f"WAV file details: Sample rate: {sample_rate}Hz, Channels: {channels}")
                        except:
                            print("Couldn't parse audio file header details")
            else:
                print("Output file doesn't exist - conversion failed")
                # Try to use the temp file directly
                shutil.copy(temp_file, "output_final.wav")
        except Exception as e:
            print(f"Error checking WAV header: {e}")
            # Continue anyway - don't return an error here, try to process the file

        # Check if the file is not empty
        if os.path.exists("output_final.wav"):
            file_size = os.path.getsize("output_final.wav")
            if file_size < 1024:  # Less than 1KB is suspicious
                print(f"Warning: Audio file is suspiciously small: {file_size} bytes")
                # Continue anyway with a small file - some browsers might send very small audio files

        print(f"Audio file saved successfully. Size: {file_size} bytes")

        # Try to transcribe up to 3 times in case of API failures
        max_attempts = 3
        translated_text = "None"  # Initialize with default value

        # Get the language from the form if provided, otherwise use the selected_language
        # This ensures we're using the correct language even if the global changed
        language_code = request.form.get('language', selected_language)
        print(f"Processing audio with language: {language_code}")

        for attempt in range(max_attempts):
            try:
                translated_text = speech_to_text()
                if translated_text and translated_text != "None":
                    break
                print(f"Transcription attempt {attempt+1}/{max_attempts} failed, retrying...")
                time.sleep(1)  # Wait before retrying
            except Exception as e:
                print(f"Transcription attempt {attempt+1} error: {e}")
                if attempt == max_attempts - 1:
                    return jsonify({'transcript': '', 'error': 'Failed to transcribe audio after multiple attempts'}), 500

        if not translated_text or translated_text == "None":
            return jsonify({'transcript': '', 'error': 'Could not transcribe audio'}), 400

        # Translate the recognized text to the client's language
        # We force it to use a short language code (en, hi, etc.) to avoid compatibility issues
        short_lang = language_code.split('-')[0] if '-' in language_code else language_code
        text = translate(translated_text, short_lang)
        print(f"Transcribed and translated text: {text}")

        # Store the user's response based on the current question number
        if(i>0 and i<=7):
            qa_history.append({"question": variable, "answer": translated_text})
        if i == 8:
            allergies = translated_text
            remaining_data["Allergies"] = allergies
        if i == 9:
            past_history = translated_text
            remaining_data["Past Medical history"] = past_history
        if i == 10:
            past_surgeries = translated_text
            remaining_data["Past surgeries"] = past_surgeries
        if i == 11:
            family_history = translated_text
            remaining_data["Family History"] = family_history
        if i == 12:
            smoking = translated_text
            remaining_data["Smoking"] = smoking
        if i == 13:
            drinking = translated_text
            remaining_data["Drinking"] = drinking

        # Return the transcribed text to be displayed in the UI
        return jsonify({'transcript': text})

    except Exception as e:
        print(f"Transcription error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'transcript': ''}), 500


global name
name = "output_"

# ---------- TEXT TO SPEECH ----------

def text_to_speech(text="Hello", language="en", max_retries=3):
    # Extract the base language code (e.g., "en" from "en-IN")
    base_language = language.split('-')[0] if '-' in language else language

    # Translate the text using the base language code for consistency
    text = translate(text, base_language)
    print("Translated text:", text)

    # Normalize language code for TTS (e.g., "hi" → "hi-IN")
    language_code = language if '-' in language else f"{base_language}-IN"
    print(f"Using language code for TTS: {language_code}")

    # Use the global API key or try to get it from environment
    # API_KEY is already imported from config.py
    url = "https://api.sarvam.ai/text-to-speech"

    payload = {
        "inputs": [text],
        "target_language_code": language_code,
        "speaker": "meera",
        "speech_sample_rate": 24000,
        "enable_preprocessing": True,
        "model": "bulbul:v1"
    }

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": API_KEY
    }

    retry_count = 0

    while retry_count < max_retries:
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print("Response status code:", response.status_code)

            if response.status_code == 200:
                response_data = response.json()
                if "audios" in response_data and response_data["audios"]:
                    audio_base64 = response_data["audios"][0]
                    audio_bytes = base64.b64decode(audio_base64)
                    filename= f"output_{i}.wav"
                    with open(filename, "wb") as f:
                        f.write(audio_bytes)
                    print("✅ Audio file written successfully")
                    return filename, text
                else:
                    print("⚠️ No audio data returned.")
            else:
                print(f"⚠️ TTS API error (attempt {retry_count+1}/{max_retries}): {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error (attempt {retry_count+1}/{max_retries}): {e}")

        retry_count += 1
        time.sleep(2 if retry_count >= 2 else 1)

    print("❌ Failed after maximum retry attempts")
    return None,None

def get_data():
    global qa_history
    global remaining_data

    # --- Generate medical summary (This remains a separate call) ---
    summary = ""
    if qa_history:
        patient_input = qa_history[0]["answer"]
        summary = y.generate_medical_summary(patient_input, qa_history)
        print("Generated Summary:", summary)

    # --- Process other data IN BATCH ---

    # 1. Prepare the data that needs summarization
    data_to_summarize = {
        "Past Medical history": remaining_data.get("Past Medical history", ""),
        "Past surgeries": remaining_data.get("Past surgeries", ""),
        "Family History": remaining_data.get("Family History", ""),
        "Smoking": remaining_data.get("Smoking", ""),
        "Drinking": remaining_data.get("Drinking", "")
    }

    # 2. Call the batch function ONCE
    summarized_results = y.summarise_all_in_batch(data_to_summarize)

    # 3. Update the remaining_data dictionary with the results
    remaining_data.update(summarized_results)

    # Handle 'Allergies' separately as it uses a different function
    if "Allergies" in remaining_data:
        remaining_data["Allergies"] = y.extract_entities(remaining_data.get("Allergies", ""), "allergy")

    print("Processed Remaining data:", remaining_data)

    # --- Generate the PDF (No change here) ---
    file = r"C:\project\finals\OPD_final_sarvam\static\reports\patient_report.pdf"
    os.makedirs(os.path.dirname(file), exist_ok=True)
    generate_patient_report_pdf(file, remaining_data, remaining_data, summary)
    return

@app.route("/generate-audio", methods=["POST"])
def generate_audio():
    global i
    global variable

    try:
        # Get request data
        data = request.get_json()
        user_text = data.get("text", "")
        lang = data.get("lang", "en")
        lang_code = lang.split('-')[0] if '-' in lang else lang

        # Generate next question
        generated_question = question_generator(user_text)
        print("Generated question:", generated_question)
        check= "your consultation is now complete"
        # Check if we're at the end of the conversation
        if check in generated_question.lower():
            print("End of conversation reached, generating final report")
            get_data()

        # Generate audio from text
        filename, translated_text = text_to_speech(generated_question, lang_code)

        # Check if audio generation was successful
        if not filename:
            return jsonify({
                "error": "Failed to generate audio file",
                "llama_text": generated_question
            }), 500

        # Success path - record the counter and return file info
        print("Audio file created successfully:", filename)
        current_question=i+1
        total_questions = 13

        # Still increment i for the backend flow
        i += 1

        # Check if this is the final message to show PDF button
        is_final_message = "consultation is now complete" in generated_question.lower()

        return jsonify({
            "audio_file": filename,
            "llama_text": translated_text,
            "show_pdf": is_final_message,
            "current_question": current_question,
            "total_questions": total_questions
        })

    except Exception as e:
        print(f"Generate audio error: {type(e).__name__}: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}",
            "llama_text": "I encountered an error. Please check your connection and try again."
        }), 500

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    # Use absolute path to current directory
    return send_from_directory(os.path.abspath('.'), filename, mimetype='audio/wav')

@app.route('/static/reports/<path:filename>')
def serve_report(filename):
    # Serve files from the static/reports directory
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'reports')
    return send_from_directory(reports_dir, filename, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True,port=5001)
