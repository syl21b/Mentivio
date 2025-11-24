from sklearn.calibration import CalibratedClassifierCV 
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix, precision_score, recall_score
import numpy as np

# 🆕 CONFIDENCE CALIBRATION CLASS
class CalibratedClinicalModel:
    """Wrapper class to provide calibrated confidence scores"""
    
    def __init__(self, base_model, method='isotonic', cv=3):
        self.base_model = base_model
        self.calibrator = None
        self.method = method
        self.cv = cv
        self.is_calibrated = False
    
    def fit(self, X, y):
        """Fit base model and calibrator"""
        # Fit base model
        self.base_model.fit(X, y)
        
        # Calibrate using cross-validation
        self.calibrator = CalibratedClassifierCV(
            self.base_model, method=self.method, cv=self.cv
        )
        self.calibrator.fit(X, y)
        self.is_calibrated = True
        
        return self
    
    def predict(self, X):
        """Predict classes"""
        if self.is_calibrated:
            return self.calibrator.predict(X)
        else:
            return self.base_model.predict(X)
    
    def predict_proba(self, X):
        """Get calibrated probabilities"""
        if self.is_calibrated:
            return self.calibrator.predict_proba(X)
        else:
            return self.base_model.predict_proba(X)
    
    def get_confidence_scores(self, X):
        """Get maximum probability as confidence score"""
        probas = self.predict_proba(X)
        return np.max(probas, axis=1)
    # 🆕 ADD THIS METHOD TO THE CalibratedClinicalModel CLASS
    def score(self, X, y):
        """Score method required for some sklearn utilities"""
        predictions = self.predict(X)
        return accuracy_score(y, predictions)

    # 🆕 ALSO ADD THESE METHODS FOR BETTER COMPATIBILITY:
    def get_params(self, deep=True):
        """Get parameters for the model"""
        return {
            'base_model': self.base_model,
            'method': self.method,
            'cv': self.cv
        }

    def set_params(self, **params):
        """Set parameters for the model"""
        for param, value in params.items():
            setattr(self, param, value)
        return self
