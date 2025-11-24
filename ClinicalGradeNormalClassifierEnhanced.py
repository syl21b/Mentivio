import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn.utils.multiclass import unique_labels
from sklearn.metrics import accuracy_score


class ClinicalGradeNormalClassifierEnhanced(BaseEstimator, ClassifierMixin):
    """Enhanced version with better Normal protection - FIXED for scikit-learn compatibility"""
    def __init__(self, base_model, normal_threshold=0.75, pathology_threshold=0.65, normal_class_idx=0):
        self.base_model = base_model
        self.normal_threshold = normal_threshold
        self.pathology_threshold = pathology_threshold
        self.normal_class_idx = normal_class_idx
        
    def get_params(self, deep=True):
        """Required for scikit-learn compatibility"""
        return {
            'base_model': self.base_model,
            'normal_threshold': self.normal_threshold,
            'pathology_threshold': self.pathology_threshold,
            'normal_class_idx': self.normal_class_idx
        }
    
    def set_params(self, **params):
        """Required for scikit-learn compatibility"""
        for key, value in params.items():
            setattr(self, key, value)
        return self
        
    def predict_proba(self, X):
        return self.base_model.predict_proba(X)
        
    def predict(self, X):
        probabilities = self.predict_proba(X)
        predictions = self.base_model.predict(X)
        
        # 🆕 ENHANCED RULE: Any high confidence Normal probability overrides pathology
        normal_probs = probabilities[:, self.normal_class_idx]
        
        # More aggressive: If Normal confidence > pathology threshold, classify as Normal
        high_normal_confidence = normal_probs > self.pathology_threshold
        
        # Apply the override
        predictions[high_normal_confidence] = self.normal_class_idx
        
        # Log the corrections
        corrections_made = high_normal_confidence.sum()
        if corrections_made > 0:
            print(f"🛡️  Clinical Safety: {corrections_made} cases protected as Normal")
        
        return predictions
    
    def fit(self, X, y):
        self.base_model.fit(X, y)
        return self
    
    def score(self, X, y):
        return accuracy_score(y, self.predict(X))
