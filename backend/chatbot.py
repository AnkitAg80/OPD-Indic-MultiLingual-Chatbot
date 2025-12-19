import ast
import json
import os
from google import genai
from google.genai import types
from config import GEMINI_API_KEY
# Initialize Gemini API client with api_key parameter
# Different versions of genai library may have different initialization patterns
# This is the standard pattern for most recent versions
client = genai.Client(api_key=GEMINI_API_KEY)

with open(r"C:\project\finals\OPD_final_sarvam\backend\full_department_symptom_questions.json") as f:
    all_depts = json.load(f)

# Extract General Medicine data
general_medicine = next(
    (dept for dept in all_depts.get("Departments", []) if dept.get("Name", "").strip().lower() == "general medicine"),
    None)
if general_medicine is None:
    raise ValueError("❌ 'General Medicine' department not found in JSON.")

SYMPTOM_QUESTIONS = general_medicine["DiagnosticQuestions"]
SYMPTOM_NAMES = [sym.lower() for sym in general_medicine["CommonProblems"]]

# Helper: match symptoms mentioned in patient input
def get_matched_symptoms_and_questions(patient_input):
    matched = {}
    for symptom, questions in SYMPTOM_QUESTIONS.items():
        if symptom.lower() in patient_input.lower():
            matched[symptom] = questions
    return matched

# Generate structured medical summary
def generate_medical_summary(patient_input, qa_history):
    # Combine all conversation content
    full_conversation = f"Patient's initial complaint: {patient_input}\n\n"
    for qa in qa_history:
        full_conversation += f"Q: {qa['question']}\nA: {qa['answer']}\n"

    summary_prompt = f"""You are a medical assistant creating a structured summary for a doctor's review.

CONVERSATION DATA:
{full_conversation}

Create a concise, structured summary in the following format. Only include information that was actually mentioned:
**Chief Complaint:**
[Patient's main concern in one line]

**PRESENT ILLNESS:**
• Duration: [when symptoms started]
• Severity: [mild/moderate/severe if mentioned]
• Location: [where symptoms occur if relevant]
• Associated symptoms: [other symptoms mentioned]
• Aggravating factors: [what makes it worse if mentioned]
• Relieving factors: [what helps if mentioned]
• Previous episodes: [if any history mentioned]

**ADDITIONAL NOTES:**
[Any other relevant clinical information] and any other details that might be useful for the doctor. Also make a small note on this being a summary of the conversation and not a full medical history. it should be not more than 2-3 lines.

RULES:
- Use bullet points for easy reading
- Only include information explicitly stated by patient
- Keep each point concise (1-2 lines max)
- If information wasn't provided, don't include that section
- Focus on clinically relevant details only
- Use medical terminology appropriately

Generate the summary:"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
            system_instruction="You are an OPD medical assistant specializing in creating structured summaries for doctors."),
            contents=summary_prompt
        )
        return response.text.strip() if response.text else ""
    except Exception as e:
        # Fallback manual summary if LLM fails
        return create_manual_summary(patient_input, qa_history)
# Fallback manual summary creation

def create_manual_summary(patient_input, qa_history):
    summary = f"**CHIEF COMPLAINT:**\n{patient_input}\n\n**CONSULTATION DETAILS:**\n"

    # Extract key information from Q&A
    key_info = []
    for qa in qa_history:
        question = qa['question'].lower()
        answer = qa['answer']

        if any(word in question for word in ['when', 'how long', 'since']):
            key_info.append(f"• Duration: {answer}")
        elif any(word in question for word in ['temperature', 'fever']):
            key_info.append(f"• Temperature: {answer}")
        elif any(word in question for word in ['other symptoms', 'associated']):
            key_info.append(f"• Associated symptoms: {answer}")
        elif any(word in question for word in ['severity', 'scale', 'bad']):
            key_info.append(f"• Severity: {answer}")
        elif any(word in question for word in ['location', 'where']):
            key_info.append(f"• Location: {answer}")
        else:
            key_info.append(f"• {qa['question']}: {answer}")

    summary += "\n".join(key_info)
    return summary

def clear(text):
     # Remove leading and trailing spaces
    k = 0
    for i in range(len(text)):
        if text [i] == ":":
            k = i + 1
    st = text[k:]
    st = st.strip()
    return st

def run_gemini():
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="say hello to the world"
    )
    print(response.text.strip() if response.text else "No response from Gemini API.")

def generate_next_medical_question(patient_input, qa_history):
    # Step 1: Build QA history
    history_text = "\n".join(
        [f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['answer']}" for i, qa in enumerate(qa_history)]
    )

    # Step 2: Get matched symptoms and their reference questions
    matched = get_matched_symptoms_and_questions(patient_input)

    # Step 4: Build reference questions block
    if matched:
        reference_block = "REFERENCE QUESTIONS for these symptoms:\n\n"
        for symptom, questions in matched.items():
            reference_block += f"For {symptom}:\n" + "\n".join(f"- {q}" for q in questions) + "\n\n"
    else:
        reference_block = ""

    # Step 5: Enhanced prompt focused on symptom-specific questions
    questions_asked = len(qa_history)

    prompt = (
        "You are a caring doctor having a natural conversation with a patient. Your goal is to ask SPECIFIC, EASY-TO-ANSWER questions that a patient without medical training can understand and respond to meaningfully.\n\n"

        f"PATIENT'S CONCERN: {patient_input}\n\n"

        f"{reference_block}"

        f"CONVERSATION HISTORY:\n{history_text if history_text else 'This is the start of your conversation.'}\n\n"

        "KEY GUIDELINES:\n"
        f"1. You have {6-questions_asked} questions remaining out of 6.\n"
        "2. If you have enough information, respond with: DONE\n"
        "3. NEVER ask vague questions like 'How does it feel?' - instead, give options ('Is it sharp, throbbing, or dull?')\n"
        "4. NEVER repeat or confirm information the patient just told you in their last response.\n"
        "5. Use extremely simple, everyday language - like talking to a 12-year-old.\n"
        "6. Ask only ONE specific question at a time (under 15 words when possible).\n\n"

        "TYPES OF GOOD QUESTIONS:\n"
        "- For pain type: 'Is it more of a sharp, dull, or throbbing pain?' (providing clear options)\n"
        "- For severity: 'On a scale of 1-10, how bad is the pain?'\n"
        "- For timing: 'Does it come and go, or stay all the time?'\n"
        "- For location: 'Is it on one side or both sides?'\n"
        "- For related symptoms: 'Do you also have any nausea or sensitivity to light?'\n"
        "- For triggers: 'Does anything specific seem to bring it on?'\n\n"

        "TYPES OF BAD QUESTIONS (AVOID THESE):\n"
        "- 'What does it feel like?' (too vague)\n"
        "- 'Are you noticing anything else?' (too open-ended)\n"
        "- 'You said X earlier, is that still true?' (repetitive)\n"
        "- 'How would you describe your symptoms?' (too general)\n\n"

        "Now, ask your next question - make it specific, direct, and easy for the patient to answer:"
    )

    # Step 6: Get response from LLM
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    # Clean response - remove any thinking tags or extra formatting
    result = response.text.strip() if response.text else ""

    # Remove <think> tags if present
    if '<think>' in result:
        # Extract only the part after </think> or before <think>
        if '</think>' in result:
            result = result.split('</think>')[-1].strip()
        else:
            result = result.split('<think>')[0].strip()

    return result


def extract_entities(sentence, entity_type):
    prompt = (
        f"Extract all {entity_type} explicitly mentioned in the following sentence and normalize them if needed. "
        "For example, map 'head is paining' to 'headache', 'high temperature' or 'high fever' to 'fever', etc. "
        "ONLY return a valid Python list. DO NOT include any explanations, introductions, or extra text. "
        "If no entities are found, return an empty list [].\n\n"
        f"Sentence: \"{sentence}\""
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    try:
        if response.text:
            return ast.literal_eval(response.text)
        return []
    except (ValueError, SyntaxError):
        return []

# def summarise_answers(question, answer):
#     prompt = f"""You are assisting in writing concise clinical notes for an OPD report. Given a patient's response to a doctor’s question, extract the core information and summarize it in **2 to 4 words**, using **standard clinical terminology**.

#     - Avoid full sentences.
#     - Avoid unnecessary adjectives like "prominence", "intensity", unless they are medically relevant.
#     - Focus on **location, type, or key symptom details**.

#     Only return the summary, no explanation.

#     Question: "{question}"
#     Patient Answer: "{answer}"
#     Summary:"""
#     response = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents=prompt
#     )

#     # Directly return the raw text (stripped) as the summary
#     summary = response.text.strip() if response.text else ""
#     return summary

import json

def summarise_all_in_batch(data_to_process):
    """
    Summarizes a dictionary of patient Q&A pairs in a single API call.

    Args:
        data_to_process (dict): A dictionary where keys are the section names
                                and values are the patient's answers.

    Returns:
        dict: A dictionary with the summarized clinical notes.
    """
    # Create a string representation of the data for the prompt
    data_string = ""
    for key, value in data_to_process.items():
        data_string += f"- Section: '{key}'\n- Patient Answer: '{value}'\n\n"

    prompt = f"""You are assisting in writing concise clinical notes for an OPD report.
You will be given several sections of a patient's history. For each section, extract the core information and summarize it in 2 to 4 words using standard clinical terminology.

Your response MUST be a valid JSON object. The keys of the JSON should be the exact section names provided, and the values should be your short summaries.

Patient Data:
{data_string}

JSON Response:"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    try:
        # Gemini often responds with markdown-wrapped JSON - clean it first
        cleaned_text = response.text
        if cleaned_text is not None:
            cleaned_text = cleaned_text.strip().strip("```json").strip("```").strip()
            summarized_data = json.loads(cleaned_text)
        else:
            summarized_data = {}
        return summarized_data
    except (json.JSONDecodeError, TypeError) as e:
        print(f"❌ Error decoding JSON from model response: {e}")
        print(f"🔍 Raw Gemini output:\n{response.text}")
        return {key: "" for key in data_to_process.keys()}
