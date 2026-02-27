import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn.utils.multiclass import unique_labels
from sklearn.metrics import accuracy_score
from typing import Any, Dict, Optional, Union
import numpy.typing as npt


class ClinicalGradeNormalClassifierEnhanced(BaseEstimator, ClassifierMixin):
    """Enhanced version with better Normal protection - FIXED for scikit-learn compatibility"""
    
    def __init__(
        self, 
        base_model: Any, 
        normal_threshold: float = 0.75, 
        pathology_threshold: float = 0.65, 
        normal_class_idx: int = 0
    ) -> None:
        self.base_model = base_model
        self.normal_threshold = normal_threshold
        self.pathology_threshold = pathology_threshold
        self.normal_class_idx = normal_class_idx
        
    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """Required for scikit-learn compatibility"""
        params: Dict[str, Any] = {
            'base_model': self.base_model,
            'normal_threshold': self.normal_threshold,
            'pathology_threshold': self.pathology_threshold,
            'normal_class_idx': self.normal_class_idx
        }
        if deep:
            # Include base model parameters if available
            if hasattr(self.base_model, 'get_params'):
                base_params = self.base_model.get_params(deep=True)
                params.update({f'base_model__{k}': v for k, v in base_params.items()})
        return params
    
    def set_params(self, **params: Any) -> 'ClinicalGradeNormalClassifierEnhanced':
        """Required for scikit-learn compatibility"""
        for key, value in params.items():
            if key.startswith('base_model__'):
                # Handle base model parameters
                base_param = key.replace('base_model__', '')
                if hasattr(self.base_model, 'set_params'):
                    self.base_model.set_params(**{base_param: value})
            else:
                setattr(self, key, value)
        return self
        
    def predict_proba(self, X: npt.ArrayLike) -> npt.NDArray[np.float64]:
        """Predict class probabilities"""
        return self.base_model.predict_proba(X)
        
    def predict(self, X: npt.ArrayLike) -> npt.NDArray[np.intp]:
        """Predict class labels with clinical safety rules"""
        probabilities = self.predict_proba(X)
        predictions = self.base_model.predict(X)
        
        # 🆕 ENHANCED RULE: Any high confidence Normal probability overrides pathology
        normal_probs = probabilities[:, self.normal_class_idx]
        
        # More aggressive: If Normal confidence > pathology threshold, classify as Normal
        high_normal_confidence = normal_probs > self.pathology_threshold
        
        # Apply the override
        predictions = predictions.astype(np.intp)  # Ensure consistent dtype
        predictions[high_normal_confidence] = self.normal_class_idx
        
        # Log the corrections
        corrections_made = np.sum(high_normal_confidence)
        if corrections_made > 0:
            print(f"🛡️  Clinical Safety: {int(corrections_made)} cases protected as Normal")
        
        return predictions
    
    def fit(self, X: npt.ArrayLike, y: npt.ArrayLike) -> 'ClinicalGradeNormalClassifierEnhanced':
        """Fit the base model"""
        # Validate input
        X, y = check_X_y(X, y)
        
        # Store classes seen during fit
        self.classes_ = unique_labels(y)
        self.n_features_in_ = X.shape[1]
        
        # Fit base model
        self.base_model.fit(X, y)
        
        # Ensure base model has required attributes
        if not hasattr(self.base_model, 'classes_'):
            self.base_model.classes_ = self.classes_
        
        return self
    
    def score(self, X: npt.ArrayLike, y: npt.ArrayLike) -> float:
        """Return the mean accuracy on the given test data and labels"""
        predictions = self.predict(X)
        return accuracy_score(y, predictions)
    
    # 🆕 ADDITIONAL COMPATIBILITY METHODS
    @property
    def _estimator_type(self) -> str:
        """Required for some sklearn utilities"""
        return "classifier"
    
    def __sklearn_clone__(self) -> 'ClinicalGradeNormalClassifierEnhanced':
        """Custom clone method for sklearn compatibility"""
        import copy
        return copy.deepcopy(self)
    
    def _more_tags(self) -> Dict[str, Any]:
        """Provide additional metadata for sklearn"""
        return {
            "requires_fit": True,
            "preserves_dtype": [np.float64],
            "non_deterministic": False,
        }


# 🆕 ENHANCED VERSION WITH CONFIDENCE-BASED PROTECTION
class ClinicalSafetyClassifier(ClinicalGradeNormalClassifierEnhanced):
    """Extended version with additional safety features and confidence analysis"""
    
    def __init__(
        self, 
        base_model: Any, 
        normal_threshold: float = 0.75, 
        pathology_threshold: float = 0.65, 
        normal_class_idx: int = 0,
        enable_confidence_analysis: bool = True
    ) -> None:
        super().__init__(base_model, normal_threshold, pathology_threshold, normal_class_idx)
        self.enable_confidence_analysis = enable_confidence_analysis
        self.safety_stats_: Optional[Dict[str, Any]] = None
        
    def predict(self, X: npt.ArrayLike) -> npt.NDArray[np.intp]:
        """Predict class labels with enhanced clinical safety rules"""
        probabilities = self.predict_proba(X)
        base_predictions = self.base_model.predict(X)
        
        # Get normal probabilities
        normal_probs = probabilities[:, self.normal_class_idx]
        
        # Apply safety rules
        protected_predictions = self._apply_safety_rules(base_predictions, normal_probs)
        
        # Update safety statistics
        if self.enable_confidence_analysis:
            self._update_safety_stats(base_predictions, protected_predictions, normal_probs)
        
        return protected_predictions
    
    def _apply_safety_rules(
        self, 
        base_predictions: npt.NDArray[np.intp], 
        normal_probs: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.intp]:
        """Apply clinical safety rules to predictions"""
        predictions = base_predictions.copy()
        
        # Rule 1: High normal confidence overrides pathology
        high_normal_mask = normal_probs > self.pathology_threshold
        predictions[high_normal_mask] = self.normal_class_idx
        
        # Rule 2: Very high normal confidence (additional protection)
        very_high_normal_mask = normal_probs > self.normal_threshold
        predictions[very_high_normal_mask] = self.normal_class_idx
        
        return predictions
    
    def _update_safety_stats(
        self, 
        base_predictions: npt.NDArray[np.intp], 
        protected_predictions: npt.NDArray[np.intp], 
        normal_probs: npt.NDArray[np.float64]
    ) -> None:
        """Update safety statistics"""
        changes_mask = base_predictions != protected_predictions
        n_changes = np.sum(changes_mask)
        
        if n_changes > 0:
            changed_normal_probs = normal_probs[changes_mask]
            
            self.safety_stats_ = {
                'total_cases': len(base_predictions),
                'protected_cases': int(n_changes),
                'protection_rate': float(n_changes / len(base_predictions)),
                'avg_normal_confidence_protected': float(np.mean(changed_normal_probs)),
                'min_normal_confidence_protected': float(np.min(changed_normal_probs)),
                'max_normal_confidence_protected': float(np.max(changed_normal_probs))
            }
            
            print(f"🛡️  Clinical Safety: Protected {int(n_changes)} cases "
                  f"(avg normal confidence: {self.safety_stats_['avg_normal_confidence_protected']:.3f})")
    
    def get_safety_report(self) -> Optional[Dict[str, Any]]:
        """Get detailed safety report"""
        return self.safety_stats_


# 🆕 FACTORY FUNCTION FOR EASY CREATION
def create_clinical_safety_model(
    base_model: Any,
    normal_class_name: str = "Normal",
    class_names: Optional[npt.ArrayLike] = None,
    **kwargs: Any
) -> ClinicalSafetyClassifier:
    """
    Factory function to create a clinical safety model with automatic normal class detection
    """
    # Auto-detect normal class index if class_names provided
    normal_class_idx = 0  # default
    
    if class_names is not None:
        class_names_array = np.array(class_names)
        normal_indices = np.where(class_names_array == normal_class_name)[0]
        if len(normal_indices) > 0:
            normal_class_idx = normal_indices[0]
        else:
            print(f"⚠️  Warning: Normal class '{normal_class_name}' not found in class names. Using index 0.")
    
    return ClinicalSafetyClassifier(
        base_model=base_model,
        normal_class_idx=normal_class_idx,
        **kwargs
    )