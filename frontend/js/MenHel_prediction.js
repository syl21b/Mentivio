// Assessment questions and configuration
// In the ASSESSMENT_CONFIG, update the feature names:
const ASSESSMENT_CONFIG = {
    questions: [
        // Mood & Emotions Domain
        {
            category: "Mood & Emotions",
            question: "How often do you experience mood swings?",
            feature: "Mood Swing",  // Changed from "Mood Swing"
            type: "yes_no",
            options: [
                { value: "NO", label: "No", score: 0 },
                { value: "YES", label: "Yes", score: 1 }
            ]
        },
        {
            category: "Mood & Emotions", 
            question: "How frequently do you feel sad or down?",
            feature: "Sadness",  // This one is correct
            type: "frequency",
            options: [
                { value: "Seldom", label: "Seldom", score: 0 },
                { value: "Sometimes", label: "Sometimes", score: 1 },
                { value: "Usually", label: "Usually", score: 2 },
                { value: "Most-Often", label: "Most Often", score: 3 }
            ]
        },
        {
            category: "Mood & Emotions",
            question: "Do you experience periods of extreme happiness or euphoria?",
            feature: "Euphoric",  // This one is correct
            type: "frequency",
            options: [
                { value: "Seldom", label: "Seldom", score: 0 },
                { value: "Sometimes", label: "Sometimes", score: 1 },
                { value: "Usually", label: "Usually", score: 2 },
                { value: "Most-Often", label: "Most Often", score: 3 }
            ]
        },

        // Anxiety & Worry Domain
        {
            category: "Anxiety & Worry",
            question: "How often do you feel anxious or nervous?",
            feature: "Anxiety",  // This one is correct
            type: "frequency", 
            options: [
                { value: "Seldom", label: "Seldom", score: 0 },
                { value: "Sometimes", label: "Sometimes", score: 1 },
                { value: "Usually", label: "Usually", score: 2 },
                { value: "Most-Often", label: "Most Often", score: 3 }
            ]
        },
        {
            category: "Anxiety & Worry",
            question: "Do you find yourself overthinking or worrying excessively?",
            feature: "Overthinking",  // This one is correct
            type: "yes_no",
            options: [
                { value: "NO", label: "No", score: 0 },
                { value: "YES", label: "Yes", score: 1 }
            ]
        },

        // Sleep & Energy Domain
        {
            category: "Sleep & Energy",
            question: "How often do you experience sleep issues?",
            feature: "Sleep disorder", // Changed from "Sleep issues"
            type: "frequency",
            options: [
                { value: "Seldom", label: "Seldom", score: 0 },
                { value: "Sometimes", label: "Sometimes", score: 1 },
                { value: "Usually", label: "Usually", score: 2 },
                { value: "Most-Often", label: "Most Often", score: 3 }
            ]
        },
        {
            category: "Sleep & Energy",
            question: "How often do you feel exhausted or fatigued?",
            feature: "Exhausted",  // This one is correct
            type: "frequency",
            options: [
                { value: "Seldom", label: "Seldom", score: 0 },
                { value: "Sometimes", label: "Sometimes", score: 1 },
                { value: "Usually", label: "Usually", score: 2 },
                { value: "Most-Often", label: "Most Often", score: 3 }
            ]
        },

        // Behavioral Domain
        {
            category: "Behavioral Patterns",
            question: "Have you experienced suicidal thoughts?",
            feature: "Suicidal_thoughts",  // Changed from "Suicidal thoughts"
            type: "yes_no",
            options: [
                { value: "NO", label: "No", score: 0 },
                { value: "YES", label: "Yes", score: 1 }
            ]
        },
        {
            category: "Behavioral Patterns",
            question: "Do you tend to respond aggressively in conflicts?",
            feature: "Aggressive_Response",  // This one is correct
            type: "yes_no",
            options: [
                { value: "NO", label: "No", score: 0 },
                { value: "YES", label: "Yes", score: 1 }
            ]
        },

        // Cognitive Domain
        {
            category: "Cognitive Function",
            question: "How would you rate your ability to concentrate?",
            feature: "Concentration",  // This one is correct
            type: "concentration",
            options: [
                { value: "Cannot concentrate", label: "Cannot concentrate", score: 0 },
                { value: "Poor concentration", label: "Poor concentration", score: 1 },
                { value: "Average concentration", label: "Average concentration", score: 2 },
                { value: "Good concentration", label: "Good concentration", score: 3 },
                { value: "Excellent concentration", label: "Excellent concentration", score: 4 }
            ]
        },
        {
            category: "Cognitive Function",
            question: "How would you describe your general outlook on life?",
            feature: "Optimism",  // This one is correct
            type: "optimism",
            options: [
                { value: "Extremely pessimistic", label: "Extremely pessimistic", score: 0 },
                { value: "Pessimistic", label: "Pessimistic", score: 1 },
                { value: "Neutral outlook", label: "Neutral outlook", score: 2 },
                { value: "Optimistic", label: "Optimistic", score: 3 },
                { value: "Extremely optimistic", label: "Extremely optimistic", score: 4 }
            ]
        },

        // Additional features for comprehensive assessment
        {
            category: "Physical Health",
            question: "Have you experienced significant changes in appetite?",
            feature: "Appetite_Changes",  // Changed from "Appetite_Changes"
            type: "yes_no",
            options: [
                { value: "NO", label: "No", score: 0 },
                { value: "YES", label: "Yes", score: 1 }
            ]
        },
        {
            category: "Social Behavior",
            question: "Do you avoid social situations?",
            feature: "Social_Avoidance",  // This one is correct
            type: "yes_no",
            options: [
                { value: "NO", label: "No", score: 0 },
                { value: "YES", label: "Yes", score: 1 }
            ]
        },
        {
            category: "Behavioral Patterns",
            question: "Have you experienced a nervous breakdown?",
            feature: "Nervous_Breakdown",  // Changed from "Nervous Breakdown"
            type: "yes_no",
            options: [
                { value: "NO", label: "No", score: 0 },
                { value: "YES", label: "Yes", score: 1 }
            ]
        },
        {
            category: "Sexual Health",
            question: "How would you describe your interest in sexual activity?",
            feature: "Sexual_Activity",  // Changed from "Sexual Activity"
            type: "sexual_activity",
            options: [
                { value: "No interest", label: "No interest", score: 0 },
                { value: "Low interest", label: "Low interest", score: 1 },
                { value: "Moderate interest", label: "Moderate interest", score: 2 },
                { value: "High interest", label: "High interest", score: 3 },
                { value: "Very high interest", label: "Very high interest", score: 4 }
            ]
        },
                // Add these additional questions to your ASSESSMENT_CONFIG.questions array:
        {
            category: "Mood & Emotions",
            question: "How often do you feel depressed or down?",
            feature: "Depressed_Mood",
            type: "frequency", 
            options: [
                { value: "Seldom", label: "Seldom", score: 0 },
                { value: "Sometimes", label: "Sometimes", score: 1 },
                { value: "Usually", label: "Usually", score: 2 },
                { value: "Most-Often", label: "Most Often", score: 3 }
            ]
        },
        {
            category: "Mood & Emotions",
            question: "How often do you feel irritable or easily annoyed?",
            feature: "Irritability",
            type: "frequency",
            options: [
                { value: "Seldom", label: "Seldom", score: 0 },
                { value: "Sometimes", label: "Sometimes", score: 1 },
                { value: "Usually", label: "Usually", score: 2 },
                { value: "Most-Often", label: "Most Often", score: 3 }
            ]
        },
        {
            category: "Anxiety & Worry", 
            question: "How often do you find yourself worrying?",
            feature: "Worrying",
            type: "frequency",
            options: [
                { value: "Seldom", label: "Seldom", score: 0 },
                { value: "Sometimes", label: "Sometimes", score: 1 },
                { value: "Usually", label: "Usually", score: 2 },
                { value: "Most-Often", label: "Most Often", score: 3 }
            ]
        },
        {
            category: "Behavioral Patterns",
            question: "Do you engage in compulsive behaviors?",
            feature: "Compulsive_Behavior", 
            type: "yes_no",
            options: [
                { value: "NO", label: "No", score: 0 },
                { value: "YES", label: "Yes", score: 1 }
            ]
        },
        {
            category: "Physical Health", 
            question: "How often do you feel fatigued or low on energy?",
            feature: "Fatigue",
            type: "frequency",
            options: [
                { value: "Seldom", label: "Seldom", score: 0 },
                { value: "Sometimes", label: "Sometimes", score: 1 },
                { value: "Usually", label: "Usually", score: 2 },
                { value: "Most-Often", label: "Most Often", score: 3 }
            ]
        }
    ]
};

class MentalHealthAssessment {
    constructor() {
        this.currentQuestionIndex = 0;
        this.responses = {};
        this.isSubmitting = false;
        this.patientInfo = {
            name: '',
            number: '',
            age: '',
            gender: ''
        };
        
        this.initializeElements();
        this.attachEventListeners();
    }

    initializeElements() {
        // Existing screens
        this.welcomeScreen = document.getElementById('welcomeScreen');
        this.questionsScreen = document.getElementById('questionsScreen');
        this.loadingScreen = document.getElementById('loadingScreen');
        this.resultsScreen = document.getElementById('resultsScreen');
        
        // New review screen elements
        this.reviewScreen = document.getElementById('reviewScreen');
        this.responsesList = document.getElementById('responsesList');
        this.backToQuestionsBtn = document.getElementById('backToQuestionsBtn');
        this.submitFinalBtn = document.getElementById('submitFinalBtn');
        
        // Patient info elements
        this.patientName = document.getElementById('patientName');
        this.patientNumber = document.getElementById('patientNumber');
        this.patientAge = document.getElementById('patientAge');
        this.patientGender = document.getElementById('patientGender');

        // Existing elements
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.questionCategory = document.getElementById('questionCategory');
        this.questionText = document.getElementById('questionText');
        this.optionsContainer = document.getElementById('optionsContainer');
        this.startBtn = document.getElementById('startBtn');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.newAssessmentBtn = document.getElementById('newAssessmentBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.primaryDiagnosis = document.getElementById('primaryDiagnosis');
        this.diagnosisDescription = document.getElementById('diagnosisDescription');
        this.confidenceBadge = document.getElementById('confidenceBadge');
        this.diagnosesList = document.getElementById('diagnosesList');
        this.technicalDetails = document.getElementById('technicalDetails');
        this.resultsDate = document.getElementById('resultsDate');
        this.assessmentId = document.getElementById('assessmentId');
    }

    attachEventListeners() {
        this.startBtn.addEventListener('click', () => this.startAssessment());
        this.prevBtn.addEventListener('click', () => this.previousQuestion());
        this.nextBtn.addEventListener('click', () => this.nextQuestion());
        this.newAssessmentBtn.addEventListener('click', () => this.resetAssessment());
        this.downloadBtn.addEventListener('click', () => this.downloadReport());
        
        // New event listeners for review screen
        this.backToQuestionsBtn.addEventListener('click', () => this.backToQuestions());
        this.submitFinalBtn.addEventListener('click', () => this.submitFinalAssessment());
        
        // Patient info change listeners
        this.patientName.addEventListener('input', (e) => this.patientInfo.name = e.target.value);
        this.patientNumber.addEventListener('input', (e) => this.patientInfo.number = e.target.value);
        this.patientAge.addEventListener('input', (e) => this.patientInfo.age = e.target.value);
        this.patientGender.addEventListener('change', (e) => this.patientInfo.gender = e.target.value);
    }

    startAssessment() {
        this.showScreen(this.questionsScreen);
        this.updateProgress();
        this.displayCurrentQuestion();
    }

    showScreen(screen) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        
        // Show target screen
        screen.classList.add('active');
    }

    updateProgress() {
        const progress = ((this.currentQuestionIndex + 1) / ASSESSMENT_CONFIG.questions.length) * 100;
        this.progressFill.style.width = `${progress}%`;
        this.progressText.textContent = `Question ${this.currentQuestionIndex + 1} of ${ASSESSMENT_CONFIG.questions.length}`;
    }

    displayCurrentQuestion() {
        const question = ASSESSMENT_CONFIG.questions[this.currentQuestionIndex];
        
        this.questionCategory.textContent = question.category;
        this.questionText.textContent = question.question;
        
        this.renderOptions(question.options);
        this.updateNavigationButtons();
    }

    renderOptions(options) {
        this.optionsContainer.innerHTML = '';
        
        options.forEach(option => {
            const optionBtn = document.createElement('button');
            optionBtn.className = 'option-btn';
            optionBtn.textContent = option.label;
            optionBtn.dataset.value = option.value;
            optionBtn.dataset.score = option.score;
            
            // Check if this option is already selected
            const currentQuestion = ASSESSMENT_CONFIG.questions[this.currentQuestionIndex];
            if (this.responses[currentQuestion.feature] === option.value) {
                optionBtn.classList.add('selected');
            }
            
            optionBtn.addEventListener('click', () => this.selectOption(optionBtn, option));
            this.optionsContainer.appendChild(optionBtn);
        });
    }

    selectOption(optionBtn, option) {
        // Remove selected class from all options
        this.optionsContainer.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.remove('selected');
        });
        
        // Add selected class to clicked option
        optionBtn.classList.add('selected');
        
        // Store response
        const currentQuestion = ASSESSMENT_CONFIG.questions[this.currentQuestionIndex];
        this.responses[currentQuestion.feature] = option.value;
        
        // Enable next button
        this.nextBtn.disabled = false;
    }

    updateNavigationButtons() {
        this.prevBtn.disabled = this.currentQuestionIndex === 0;
        
        const currentQuestion = ASSESSMENT_CONFIG.questions[this.currentQuestionIndex];
        const hasResponse = this.responses[currentQuestion.feature] !== undefined;
        this.nextBtn.disabled = !hasResponse;
        
        // Update next button text for last question
        this.nextBtn.textContent = this.currentQuestionIndex === ASSESSMENT_CONFIG.questions.length - 1 
            ? 'Submit Assessment' 
            : 'Next';
    }

    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.updateProgress();
            this.displayCurrentQuestion();
        }
    }

  
    nextQuestion() {
        const currentQuestion = ASSESSMENT_CONFIG.questions[this.currentQuestionIndex];
        
        if (!this.responses[currentQuestion.feature]) {
            alert('Please select an option before continuing.');
            return;
        }

        if (this.currentQuestionIndex < ASSESSMENT_CONFIG.questions.length - 1) {
            this.currentQuestionIndex++;
            this.updateProgress();
            this.displayCurrentQuestion();
        } else {
            this.showReviewScreen();
        }
    }

    showReviewScreen() {
        this.showScreen(this.reviewScreen);
        this.displayReviewResponses();
    }

    displayReviewResponses() {
        this.responsesList.innerHTML = '';
        
        ASSESSMENT_CONFIG.questions.forEach((question, index) => {
            const responseItem = document.createElement('div');
            responseItem.className = 'response-item';
            responseItem.dataset.questionIndex = index;
            
            const response = this.responses[question.feature];
            const selectedOption = question.options.find(opt => opt.value === response);
            
            responseItem.innerHTML = `
                <div class="response-question">
                    <div class="response-category">${question.category}</div>
                    <div class="response-text">${question.question}</div>
                    <div class="response-answer">${selectedOption ? selectedOption.label : 'Not answered'}</div>
                </div>
                <div class="response-actions">
                    <button class="edit-btn" onclick="mentalHealthAssessment.editResponse(${index})">
                        Edit
                    </button>
                </div>
            `;
            
            this.responsesList.appendChild(responseItem);
        });
    }

    editResponse(questionIndex) {
        this.currentQuestionIndex = questionIndex;
        this.showScreen(this.questionsScreen);
        this.updateProgress();
        this.displayCurrentQuestion();
    }

    backToQuestions() {
        this.currentQuestionIndex = ASSESSMENT_CONFIG.questions.length - 1;
        this.showScreen(this.questionsScreen);
        this.updateProgress();
        this.displayCurrentQuestion();
    }

    async submitFinalAssessment() {
        // Validate patient info
        if (!this.patientInfo.name.trim()) {
            alert('Please enter patient name before submitting.');
            return;
        }

        this.showScreen(this.loadingScreen);
        this.isSubmitting = true;

        try {
            await this.simulateProcessing();
            
            console.log('Submitting final assessment:', {
                responses: this.responses,
                patientInfo: this.patientInfo
            });
            
            const response = await fetch('http://localhost:5001/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    responses: this.responses,
                    patientInfo: this.patientInfo
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            result.patientInfo = this.patientInfo; // Add patient info to result
            this.displayResults(result);

        } catch (error) {
            console.error('Error submitting assessment:', error);
            this.showError(`Failed to process assessment: ${error.message}`);
        } finally {
            this.isSubmitting = false;
        }
    }

    displayResults(result) {
        this.showScreen(this.resultsScreen);
        
        // Set primary diagnosis
        this.primaryDiagnosis.textContent = result.primary_diagnosis;
        this.diagnosisDescription.textContent = this.getDiagnosisDescription(result.primary_diagnosis);
        
        // Set confidence with color coding
        const confidencePercent = Math.round(result.confidence_percentage);
        let confidenceColor = '#10b981';
        if (confidencePercent < 50) confidenceColor = '#f59e0b';
        if (confidencePercent < 30) confidenceColor = '#ef4444';
        
        this.confidenceBadge.innerHTML = `<span class="confidence-text">${confidencePercent}% Confidence</span>`;
        this.confidenceBadge.style.background = confidenceColor;
        
        // Set metadata
        this.resultsDate.textContent = new Date().toLocaleDateString();
        this.assessmentId.textContent = `ID: ${result.assessment_id}`;
        
        // Display patient information
        this.displayPatientInfo(result.patientInfo);
        
        // Display other possible diagnoses
        this.displayOtherDiagnoses(result.all_diagnoses);
        
        // Display safety warnings
        this.displaySafetyWarnings(result.processing_details?.clinical_safety_warnings || []);
        
        // Display technical details
        this.displayTechnicalDetails(result);
        
        // Add save results button
        this.addSaveResultsButton(result);
    }

    displayPatientInfo(patientInfo) {
        const savedInfoHTML = `
            <div class="saved-info">
                <h4>Patient Information</h4>
                <div class="saved-details">
                    <div class="saved-detail">
                        <span class="saved-label">Name</span>
                        <span class="saved-value">${patientInfo.name || 'Not provided'}</span>
                    </div>
                    <div class="saved-detail">
                        <span class="saved-label">Patient Number</span>
                        <span class="saved-value">${patientInfo.number || 'Not provided'}</span>
                    </div>
                    <div class="saved-detail">
                        <span class="saved-label">Age</span>
                        <span class="saved-value">${patientInfo.age || 'Not provided'}</span>
                    </div>
                    <div class="saved-detail">
                        <span class="saved-label">Gender</span>
                        <span class="saved-value">${patientInfo.gender || 'Not provided'}</span>
                    </div>
                </div>
            </div>
        `;
        
        // Insert patient info at the top of results
        const primaryResult = document.querySelector('.primary-result');
        primaryResult.insertAdjacentHTML('beforebegin', savedInfoHTML);
    }

    addSaveResultsButton(result) {
        const saveButton = document.createElement('button');
        saveButton.className = 'save-results-btn';
        saveButton.innerHTML = '💾 Save to File';
        saveButton.addEventListener('click', () => this.saveToFile(result));
        
        const resultsActions = document.querySelector('.results-actions');
        resultsActions.insertBefore(saveButton, resultsActions.firstChild);
    }

    saveToFile(result) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `mental_health_assessment_${timestamp}.json`;
        
        const dataToSave = {
            assessment_id: result.assessment_id,
            timestamp: new Date().toISOString(),
            patient_info: this.patientInfo,
            primary_diagnosis: result.primary_diagnosis,
            confidence: result.confidence_percentage,
            all_diagnoses: result.all_diagnoses,
            responses: this.responses,
            processing_details: result.processing_details,
            technical_details: {
                processing_steps: result.technical_details?.processing_log?.length || 0,
                safety_checks_passed: result.processing_details?.safety_checks_passed
            }
        };
        
        const blob = new Blob([JSON.stringify(dataToSave, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Show success message
        alert(`Assessment results saved successfully as ${filename}`);
    }

    // Enhanced download report to include patient info
    generateReport() {
        return `
MENTAL HEALTH ASSESSMENT REPORT
===============================

Assessment Date: ${new Date().toLocaleDateString()}
Assessment ID: ${this.assessmentId.textContent}

PATIENT INFORMATION
-------------------
Name: ${this.patientInfo.name || 'Not provided'}
Patient Number: ${this.patientInfo.number || 'Not provided'}
Age: ${this.patientInfo.age || 'Not provided'}
Gender: ${this.patientInfo.gender || 'Not provided'}

PRIMARY DIAGNOSIS
-----------------
${this.primaryDiagnosis.textContent}
Confidence: ${this.confidenceBadge.textContent}

${this.diagnosisDescription.textContent}

DETAILED ANALYSIS
-----------------
${Array.from(this.diagnosesList.children).map(item => {
    const name = item.querySelector('.diagnosis-name').textContent;
    const prob = item.querySelector('.diagnosis-probability').textContent;
    return `${name}: ${prob}`;
}).join('\n')}

RESPONSES SUMMARY
-----------------
${Object.entries(this.responses).map(([feature, response]) => {
    const question = ASSESSMENT_CONFIG.questions.find(q => q.feature === feature);
    const selectedOption = question?.options.find(opt => opt.value === response);
    return `${feature}: ${selectedOption?.label || response}`;
}).join('\n')}

IMPORTANT DISCLAIMER
--------------------
This assessment is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.

If you are in crisis or think you may have an emergency, call your doctor or 911 immediately.
        `.trim();
    }

    resetAssessment() {
        this.currentQuestionIndex = 0;
        this.responses = {};
        this.isSubmitting = false;
        this.patientInfo = {
            name: '',
            number: '',
            age: '',
            gender: ''
        };
        
        // Reset form fields
        this.patientName.value = '';
        this.patientNumber.value = '';
        this.patientAge.value = '';
        this.patientGender.value = '';
        
        this.showScreen(this.welcomeScreen);
        this.updateProgress();
    }

    // ... keep other existing methods like simulateProcessing, getDiagnosisDescription, displayOtherDiagnoses, displaySafetyWarnings, displayTechnicalDetails, showError ...
}

// Initialize the assessment when the page loads
let mentalHealthAssessment;
document.addEventListener('DOMContentLoaded', () => {
    mentalHealthAssessment = new MentalHealthAssessment();
});

