# Mental Health Condition Assessment & Visualization Platform

A comprehensive web application for clinical visualization and assessment of mental health conditions including Bipolar I, Bipolar II, Depression, and normal mood states.

## 🎯 Project Overview

This platform provides:
- **Clinical-grade mental health assessments** using calibrated machine learning models
- **Real-time visualization** of assessment results
- **Secure patient history tracking** with persistent storage
- **PDF report generation** for professional documentation
- **Crisis support resources** and safety features

## 🏗️ Project Structure
mental-health-web/
├── frontend/                    # Frontend assets
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript modules
│   │   ├── components.js       # UI components
│   │   └── MenHel_prediction.js # Main prediction logic
│   └── resources/              # Static resources
├── backend/                    # Backend processing
│   └── assessment/             # Assessment logic
├── models/                     # ML models
│   ├── CalibratedClinicalModel.py
│   └── ClinicalGradeNormalClassifierEnhanced.py
├── dataset/                    # Training data
├── templates/                  # HTML pages
│   ├── Home.html              # Landing page
│   ├── MenHel_prediction.html # Main assessment interface
│   ├── About.html             # About page
│   ├── crisis-support.html    # Crisis resources
│   ├── resources.html         # Additional resources
│   ├── relief_techniques.html # Coping techniques
│   ├── MenHel_analogy.html    # Educational content
│   └── navbar.html & footer.html # Layout components
├── app.py                     # Flask application
├── requirements.txt           # Python dependencies
├── render.yaml               # Render deployment config
├── gunicorn.conf.py          # Gunicorn configuration
├── train_model.py            # Model training script
└── test_*.py                 # Test and validation scripts


## 🚀 Features

### Core Assessment
- **17-question comprehensive evaluation** across multiple domains:
  - Mood & Emotions
  - Sleep & Energy Patterns
  - Cognitive Function
  - Behavioral Patterns
  - Safety Assessment
  - Social & Conflict Resolution
- **Real-time progress tracking** with visual progress bar
- **Clinical safety warnings** for critical responses

### Patient Management
- **Secure patient identification** with name and unique number
- **Assessment history tracking** with persistent CSV storage
- **Session management** for returning patients
- **Data privacy** with local CSV storage

### Results & Reporting
- **Multi-diagnosis probability scoring**:
  - Normal mood states
  - Bipolar Type-I
  - Bipolar Type-II
  - Depression
- **Confidence percentage indicators**
- **Professional PDF report generation**
- **Clinical insights and safety recommendations**

### Safety Features
- **Crisis alert system** with 988 lifeline integration
- **Suicidal ideation detection** and immediate resource provision
- **Emergency contact information**
- **Professional disclaimer** and guidance

## 🛠️ Technology Stack

### Frontend
- **HTML5** with semantic markup
- **CSS3** with modern Flexbox/Grid layouts
- **Vanilla JavaScript** with ES6+ features
- **Font Awesome** icons
- **Google Fonts** (Inter)

### Backend
- **Python 3.12+**
- **Flask** web framework
- **Pandas** for data processing
- **FPDF2** for PDF generation
- **Gunicorn** WSGI server

### Machine Learning
- **ClinicalGradeNormalClassifierEnhanced** - Primary classification model
- **CalibratedClinicalModel** - Probability calibration
- **Custom feature engineering** for mental health domains
- **Feature engineering** optimized for mental health domain characteristics
- **Model validation** against clinical standards
## 📋 Prerequisites

- Python 3.12 or higher
- pip (Python packages)
- Modern web browser with JavaScript enabled

## 🔧 Installation & Setup

### 1. Clone the Repository
git clone <repository-url>
cd mental-health-web

### 2. Create Virtual Environment (Recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Train Models (First Time Setup)
python train_model.py

### 5. Run the Application
python app.py

### 6. Access the Application
Open your browser and navigate to: http://127.0.0.1:5001

## 🚀 Production Deployment 
###  Render.com Deployment
The project is fully configured for seamless deployment on Render.com:
1. Connect your GitHub repository to Render
2. Automatic deployment using render.yaml configuration
3. Environment setup handled automatically
4. Static file serving optimized for Flask applications

###  Deployment Steps:
1. Push code to your GitHub repository
2. Create new Web Service on Render.com
3. Connect GitHub repository
4. Auto-deploy will use render.yaml configuration
5. Access your live application once deployment completes

###  Deployment Configuration:
- Build Command: pip install -r requirements.txt
- Start Command: gunicorn app:app
- Python Version: 3.12.0
- Auto-deploy: Enabled from main branch

## 📊 Assessment Methodology

### Clinical Domains Evaluated:

#### 1. Mood & Emotions
- Mood swing frequency
- Sadness patterns
- Euphoric episodes
#### 2. Sleep & Energy
- Sleep disorder indicators
- Fatigue and exhaustion levels
#### 3. Safety Assessment
- Suicidal ideation screening
- Crisis detection
#### 4. Behavioral Patterns
- Aggressive response tendencies
- Nervous breakdown history
- Conflict resolution styles
#### 5. Cognitive Function
- Concentration ability
- Optimism levels
- Overthinking patterns
#### 6. Social & Physical Health
- Eating pattern changes
- Social behavior
- Sexual health interest

### Scoring System:
- Frequency-based scoring: Seldom, Sometimes, Usually, Most-Often
- Yes/No indicators for binary clinical features
- Scale-based assessments for cognitive and behavioral traits
- Weighted scoring based on clinical importance

## 🔒 Privacy & Security

### Data Protection
- No external databases - all data stored locally in CSV files
- Patient-controlled access using name and unique number
- Client-side processing for sensitive responses
- No personal health information transmitted to external servers

### Security Features
- CSV-based storage with patient isolation
- Session-based access controls
- Data encryption in transit (HTTPS)
- Regular data cleanup recommendations

## 📄 Usage Guide

### For Patients:
1. **Start New Assessment:** Complete the 20-question evaluation
2. **Enter Patient Information:** Provide name and unique patient number for history tracking
3. **Review Responses:** Edit answers before final submission
4. **View Results:** Receive comprehensive assessment with confidence scores
5. **Save History:** Access previous assessments using your patient credentials
### For Clinicians:
1. **Patient Assessment:** Guide patients through the digital evaluation
2. **Result Interpretation:** Use probability scores as clinical decision support
3. **Report Generation:** Download professional PDF reports for patient records
4. **Progress Tracking:** Monitor patient assessment history over time

## ⚠️ Important Disclaimers
### Clinical Use
- NOT a substitute for professional medical diagnosis or treatment
- Educational and informational purposes only
- Screening tool for mental health awareness
- Always consult licensed healthcare professionals for diagnosis
### Emergency Situations
- Crisis detection is for awareness only
- Immediate danger: Always call 911 or emergency services
- Suicidal thoughts: Contact 988 Suicide & Crisis Lifeline immediately
- Professional evaluation required for accurate diagnosis

## 🆘 Crisis Support Integration
### Immediate Resources:

- 988 Suicide & Crisis Lifeline: Call or text 988 (US & Canada)
- Crisis Text Line: Text HOME to 741741
- Emergency Services: 911 for life-threatening situations
- Online Resources: **988lifeline.org**

### Safety Protocols:

- Prominent crisis alerts throughout the application
- Emergency contact information on every page
- Safety warnings for critical assessment responses
- Professional guidance for next steps

## 📈 Model Performance & Validation
### Clinical Validation:
- Standardized assessment alignment with clinical practices
- Probability calibration for accurate confidence intervals
- Feature importance analysis for clinical interpretability
- Multi-class classification with balanced accuracy

### Technical Performance:
- Real-time processing for immediate results
- Scalable architecture for multiple concurrent users
- Robust error handling for data integrity
- Comprehensive logging for debugging and improvement

### 🔍 Testing & Quality Assurance
#### Test Suite:
#####  Run comprehensive tests
- python test_pipeline.py
- python test_comparison.py
- python debug_preprocessing.py

#### Validation:
- Model accuracy validation against test cases
- Feature preprocessing verification
- End-to-end workflow testing
- Edge case handling for robust performance

## 🤝 Contributing

### Development Guidelines:
1. Clinical accuracy is paramount - all changes must maintain clinical validity
2. Safety features must be preserved and enhanced
3. Patient privacy protections cannot be compromised
4. Professional guidelines must be followed in all clinical content

### Code Standards:
- Python PEP 8 compliance
- JavaScript ES6+ standards
- Accessibility (WCAG) guidelines
- Responsive design principles

## 🐛 Troubleshooting

### Common Issues:

#### Module Not Found Errors:
######  Reinstall dependencies
pip install --force-reinstall -r requirements.txt

#### Port Already in Use:
##### Use different port
python app.py --port 5001

#### Model Training Issues:
##### Check dataset availability
python debug_preprocessing.py

### Getting Help:
1. Check the browser console for JavaScript errors
2. Review Flask application logs for backend issues
3. Validate model files are properly trained and saved
4. Ensure all dependencies are correctly installed

## 📞 Support & Contact

### Technical Support:
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check this README and code comments
- Community Forum: [In Process]

### Clinical Inquiries:

For questions about clinical content, assessment methodology, or implementation in healthcare settings, please consult with qualified mental health professionals.

## 📄 License

This project is intended for educational, clinical support, and research purposes. Users must ensure compliance with:
- Local healthcare regulations
- Data protection laws (HIPAA, GDPR, etc.)
- Professional licensing requirements
- Ethical guidelines for mental health applications

## 🔄 Version History
- v1.0 (Current): Initial release with comprehensive assessment features
- Future: Enhanced models, additional assessment domains, mobile optimization

## 🙏 Acknowledgments
- Clinical advisors for domain expertise and validation
- Open source community for supporting libraries and tools
- Mental health professionals for guidance on ethical implementation
- Test users for feedback and improvement suggestions

**Remember**: This application is a tool to support mental health awareness and professional practice. It is designed to complement, not replace, the essential work of licensed mental health professionals.

**In crisis situations, always prioritize immediate professional help through emergency services or crisis hotlines.**