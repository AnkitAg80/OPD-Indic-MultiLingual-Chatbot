# Medical OPD Chatbot

An intelligent AI-powered Outpatient Department (OPD) chatbot system that assists healthcare providers by conducting structured patient interviews, symptom assessment, and generating comprehensive medical reports. The system uses advanced language models to simulate doctor-patient interactions and create patient summaries for physician review.

---

## Features

- **AI-Powered Patient Interviews**: Intelligent chatbot conducts structured conversations with patients to gather medical information
- **Multi-Language Support**: Real-time translation between multiple languages for better accessibility
- **Symptom Assessment**: Systematic symptom questioning based on medical expertise
- **Smart Medical Summaries**: Generates structured medical summaries from patient conversations using Google Gemini AI
- **PDF Report Generation**: Produces professional medical reports in PDF format with hospital branding
- **Patient Demographics**: Captures and manages patient basic information
- **Real-time Chat Interface**: User-friendly web interface for patient-chatbot interaction
- **RESTful API**: Backend API for integration with other healthcare systems

---

## Technology Stack

### Backend
- **Python 3.x**
- **Flask** - Web framework for API and web server
- **Flask-CORS** - Cross-origin resource sharing support
- **Google Gemini API** - Advanced language model for medical summaries and conversation
- **Deep Translator** - Multi-language translation support
- **FPDF** - PDF generation for medical reports
- **Werkzeug** - WSGI utility library

### Frontend
- **HTML5** - Responsive web interface
- **CSS3** - Modern styling with animations
- **JavaScript** - Client-side interactions

### APIs
- Google Gemini API - Medical summary generation
- Sarvam AI API - (Optional language/speech processing)

---

## Project Structure

```
OPD_final_sarvam/
├── backend/
│   ├── start_opd.py                          # Main Flask application
│   ├── chatbot.py                            # Chatbot logic & medical summary generation
│   ├── config.py                             # Configuration & API keys
│   ├── full_department_symptom_questions.json # Medical knowledge base
│   ├── test.py                               # Testing utilities
│   ├── templates/
│   │   ├── index.html                        # Main chat interface
│   │   └── language.html                     # Language selection page
│   └── __pycache__/
├── static/
│   ├── img/                                  # Image assets
│   └── reports/                              # Generated PDF reports
├── requirements.txt                          # Python dependencies
└── README.md                                 # This file
```

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Google Gemini API key
- Sarvam AI API key (optional)

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/OPD_final_sarvam.git
cd OPD_final_sarvam
```

2. **Create a Virtual Environment** (Recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure API Keys**
Create a `.env` file in the root directory:
```bash
GEMINI_API_KEY=your_google_gemini_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here
```

Alternatively, update the keys in [backend/config.py](backend/config.py):
```python
GEMINI_API_KEY = "your_api_key_here"
SARVAM_API_KEY = "your_api_key_here"
```

---

## Running the Application

### Start the Server

```bash
cd backend
python start_opd.py
```

The application will be available at:
- **Web Interface**: `http://localhost:5000`
- **Language Selection**: `http://localhost:5000/language`

### Using the Application

1. **Select Language**: Choose your preferred language from the language selection page
2. **Enter Chief Complaint**: Describe your medical issue in the chat interface
3. **Answer Questions**: The chatbot will ask follow-up questions to gather detailed information
4. **Generate Report**: Once the conversation is complete, the system generates a structured medical summary
5. **Download Report**: Retrieve the patient report in PDF format

---

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main chat interface |
| GET | `/language` | Language selection page |
| GET | `/static/<path>` | Serve static files (images, styles) |
| GET | `/reports/<filename>` | Download generated PDF reports |
| POST | `/chat` | Send chat message and get response |
| POST | `/generate_summary` | Generate medical summary from conversation |
| POST | `/generate_report` | Generate and download patient report |

### Example Request - Chat Message
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have been experiencing severe headaches",
    "language": "en"
  }'
```

---

## How It Works

### Chatbot Flow

1. **Patient Input**: Patient describes their chief complaint
2. **Symptom Detection**: System identifies relevant symptoms from the input
3. **Question Generation**: Based on detected symptoms, the chatbot generates targeted follow-up questions
4. **Conversation Storage**: All Q&A exchanges are stored for later reference
5. **Summary Generation**: Using Google Gemini AI, a structured medical summary is created
6. **Report Generation**: A professional PDF report is generated with patient demographics and medical summary

### Medical Knowledge Base

The system uses [backend/full_department_symptom_questions.json](backend/full_department_symptom_questions.json) which contains:
- Common medical problems/symptoms
- Department-specific diagnostic questions
- Guided questioning patterns for different conditions

---

## Configuration

### Modify Hospital Information

Edit the hospital details in the `generate_patient_report_pdf()` function in [backend/start_opd.py](backend/start_opd.py):

```python
def add_header():
    pdf.cell(0, 8, "YOUR HOSPITAL NAME", ln=True, align='C')
    pdf.cell(0, 6, "Hospital Address", ln=True, align='C')
```

### Customize Medical Questions

Update [backend/full_department_symptom_questions.json](backend/full_department_symptom_questions.json) with your own medical specialty's questions and symptoms.

## Generated Reports

The system generates professional PDF reports including:
- **Hospital Header**: Hospital name and contact information
- **Patient Demographics**: Name, DOB, Gender, PCC#
- **Chief Complaint**: Patient's main medical concern
- **History of Present Illness**: Detailed symptoms and timeline
- **Conversation Summary**: Structured medical summary for physician review
- **Clinical Impressions**: AI-generated clinical assessment

All reports are saved in the [static/reports/](static/reports/) directory.

---


## Security Considerations

- **API Keys**: Never commit API keys to version control. Always use environment variables
- **User Data**: The system stores patient information. Ensure compliance with healthcare regulations (HIPAA, GDPR, etc.)
- **CORS**: Flask-CORS is configured. Review and restrict origins as needed for production
- **Input Validation**: Implement additional input validation for production use

### Before Production Deployment:
- [ ] Remove hardcoded API keys from `config.py`
- [ ] Implement database for patient record storage
- [ ] Add authentication and authorization
- [ ] Enable HTTPS
- [ ] Implement audit logging
- [ ] Add rate limiting
- [ ] Review HIPAA/GDPR compliance requirements

## Performance Metrics

- **Response Time**: ~2-3 seconds per API call (depending on API latency)
- **Report Generation**: ~1-2 seconds per PDF generation

---