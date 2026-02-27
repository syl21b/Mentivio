from sklearn.calibration import CalibratedClassifierCV 
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix, precision_score, recall_score
from sklearn.base import BaseEstimator, ClassifierMixin
import numpy as np
from typing import Any, Dict, Optional, Union, Tuple
import numpy.typing as npt

# 🆕 CONFIDENCE CALIBRATION CLASS
class CalibratedClinicalModel(BaseEstimator, ClassifierMixin):
    """Wrapper class to provide calibrated confidence scores"""
    
    def __init__(self, base_model: Any, method: str = 'isotonic', cv: int = 3) -> None:
        self.base_model = base_model
        self.calibrator: Optional[CalibratedClassifierCV] = None
        self.method = method
        self.cv = cv
        self.is_calibrated = False
    
    def fit(self, X: npt.ArrayLike, y: npt.ArrayLike) -> 'CalibratedClinicalModel':
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
    
    def predict(self, X: npt.ArrayLike) -> npt.NDArray[Any]:
        """Predict classes"""
        if self.is_calibrated and self.calibrator is not None:
            return self.calibrator.predict(X)
        else:
            return self.base_model.predict(X)
    
    def predict_proba(self, X: npt.ArrayLike) -> npt.NDArray[Any]:
        """Get calibrated probabilities"""
        if self.is_calibrated and self.calibrator is not None:
            return self.calibrator.predict_proba(X)
        else:
            return self.base_model.predict_proba(X)
    
    def get_confidence_scores(self, X: npt.ArrayLike) -> npt.NDArray[Any]:
        """Get maximum probability as confidence score"""
        probas = self.predict_proba(X)
        return np.max(probas, axis=1)
    
    def score(self, X: npt.ArrayLike, y: npt.ArrayLike) -> float:
        """Score method required for some sklearn utilities"""
        predictions = self.predict(X)
        return accuracy_score(y, predictions)

    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """Get parameters for the model"""
        params: Dict[str, Any] = {
            'base_model': self.base_model,
            'method': self.method,
            'cv': self.cv
        }
        if deep:
            # Include base model parameters if it has get_params
            if hasattr(self.base_model, 'get_params'):
                base_params = self.base_model.get_params(deep=True)
                params.update({f'base_model__{k}': v for k, v in base_params.items()})
        return params

    def set_params(self, **params: Any) -> 'CalibratedClinicalModel':
        """Set parameters for the model"""
        for param, value in params.items():
            if param.startswith('base_model__'):
                # Set base model parameters
                base_param = param.replace('base_model__', '')
                if hasattr(self.base_model, 'set_params'):
                    self.base_model.set_params(**{base_param: value})
            else:
                setattr(self, param, value)
        return self

    # 🆕 ADD THESE METHODS FOR BETTER COMPATIBILITY:
    def __sklearn_clone__(self) -> 'CalibratedClinicalModel':
        """Custom clone method for sklearn compatibility"""
        import copy
        return copy.deepcopy(self)

    @property
    def classes_(self) -> npt.NDArray[Any]:
        """Access classes_ from base model or calibrator"""
        if self.is_calibrated and self.calibrator is not None:
            return self.calibrator.classes_
        elif hasattr(self.base_model, 'classes_'):
            return self.base_model.classes_
        else:
            raise AttributeError("Model has not been fitted yet")

    @property
    def n_features_in_(self) -> int:
        """Access n_features_in_ from base model or calibrator"""
        if self.is_calibrated and self.calibrator is not None:
            return self.calibrator.n_features_in_
        elif hasattr(self.base_model, 'n_features_in_'):
            return self.base_model.n_features_in_
        else:
            raise AttributeError("Model has not been fitted yet")

# 🆕 ENHANCED EVALUATION FUNCTIONS WITH TYPE HINTS
def evaluate_model_performance(
    model: Any, 
    X_test: npt.ArrayLike, 
    y_test: npt.ArrayLike, 
    label_encoder: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Comprehensive model evaluation with calibrated confidence analysis
    """
    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    # Confidence scores
    confidence_scores = np.max(y_proba, axis=1)
    
    # Basic metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    
    # Confidence analysis
    confidence_stats = {
        'mean_confidence': float(np.mean(confidence_scores)),
        'std_confidence': float(np.std(confidence_scores)),
        'min_confidence': float(np.min(confidence_scores)),
        'max_confidence': float(np.max(confidence_scores)),
        'confidence_distribution': {
            'high_confidence': float(np.mean(confidence_scores > 0.8)),
            'medium_confidence': float(np.mean((confidence_scores >= 0.6) & (confidence_scores <= 0.8))),
            'low_confidence': float(np.mean(confidence_scores < 0.6))
        }
    }
    
    # Classification report
    if label_encoder is not None:
        target_names = label_encoder.classes_
        report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
    else:
        report = classification_report(y_test, y_pred, output_dict=True)
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'confidence_analysis': confidence_stats,
        'classification_report': report,
        'confusion_matrix': cm.tolist(),
        'predictions': y_pred.tolist(),
        'probabilities': y_proba.tolist(),
        'confidence_scores': confidence_scores.tolist()
    }

def validate_confidence_calibration(
    model: Any, 
    X_val: npt.ArrayLike, 
    y_val: npt.ArrayLike
) -> Dict[str, Any]:
    """
    Validate that confidence scores are well-calibrated
    """
    # Get predicted probabilities and confidence scores
    y_proba = model.predict_proba(X_val)
    confidence_scores = np.max(y_proba, axis=1)
    predictions = model.predict(X_val)
    
    # Calculate accuracy per confidence bin
    confidence_bins = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    calibration_data = []
    
    for i in range(len(confidence_bins) - 1):
        low, high = confidence_bins[i], confidence_bins[i + 1]
        mask = (confidence_scores >= low) & (confidence_scores < high)
        
        if np.sum(mask) > 0:
            bin_accuracy = accuracy_score(y_val[mask], predictions[mask])
            bin_mean_confidence = np.mean(confidence_scores[mask])
            bin_count = np.sum(mask)
            
            calibration_data.append({
                'confidence_range': f"{low:.1f}-{high:.1f}",
                'mean_confidence': float(bin_mean_confidence),
                'accuracy': float(bin_accuracy),
                'count': int(bin_count),
                'calibration_gap': float(bin_mean_confidence - bin_accuracy)
            })
    
    # Overall calibration metrics
    expected_calibration_error = np.mean([abs(item['calibration_gap']) for item in calibration_data])
    max_calibration_error = np.max([abs(item['calibration_gap']) for item in calibration_data])
    
    return {
        'calibration_bins': calibration_data,
        'expected_calibration_error': float(expected_calibration_error),
        'max_calibration_error': float(max_calibration_error),
        'is_well_calibrated': expected_calibration_error < 0.1  # Threshold for good calibration
    }

# 🆕 CONFIDENCE-BASED PREDICTION FILTER
class ConfidenceBasedFilter:
    """Filter predictions based on confidence thresholds"""
    
    def __init__(self, confidence_threshold: float = 0.6, fallback_class: Optional[str] = None):
        self.confidence_threshold = confidence_threshold
        self.fallback_class = fallback_class
    
    def filter_predictions(
        self, 
        predictions: npt.ArrayLike, 
        probabilities: npt.ArrayLike, 
        class_names: npt.ArrayLike
    ) -> Tuple[npt.NDArray[Any], npt.NDArray[Any]]:
        """
        Filter predictions based on confidence threshold
        Returns filtered predictions and confidence scores
        """
        confidence_scores = np.max(probabilities, axis=1)
        filtered_predictions = predictions.copy()
        
        # Apply confidence threshold
        low_confidence_mask = confidence_scores < self.confidence_threshold
        
        if self.fallback_class is not None and np.any(low_confidence_mask):
            # Find fallback class index
            fallback_idx = np.where(class_names == self.fallback_class)[0]
            if len(fallback_idx) > 0:
                filtered_predictions[low_confidence_mask] = fallback_idx[0]
        
        return filtered_predictions, confidence_scores
    
    def get_confidence_report(
        self, 
        predictions: npt.ArrayLike, 
        probabilities: npt.ArrayLike
    ) -> Dict[str, Any]:
        """
        Generate report on confidence distribution
        """
        confidence_scores = np.max(probabilities, axis=1)
        
        return {
            'total_predictions': len(predictions),
            'high_confidence_count': int(np.sum(confidence_scores >= 0.8)),
            'medium_confidence_count': int(np.sum((confidence_scores >= 0.6) & (confidence_scores < 0.8))),
            'low_confidence_count': int(np.sum(confidence_scores < 0.6)),
            'below_threshold_count': int(np.sum(confidence_scores < self.confidence_threshold)),
            'mean_confidence': float(np.mean(confidence_scores)),
            'confidence_threshold': self.confidence_threshold
        }