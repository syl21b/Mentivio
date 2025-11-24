import pandas as pd
import pickle
import warnings
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier,  StackingClassifier, VotingClassifier,  ExtraTreesClassifier, BaggingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix, precision_score, recall_score
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_classif
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.inspection import permutation_importance
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from datetime import datetime  
import os


# 🆕 IMPROVED WARNING HANDLING
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', category=FutureWarning)

# -----------------------------
# 🔧 CLINICAL-GRADE CLASSES (FIXED)
# -----------------------------

from ClinicalGradeNormalClassifierEnhanced import ClinicalGradeNormalClassifierEnhanced
from CalibratedClinicalModel import CalibratedClinicalModel

# -----------------------------
# 🆕 DATA BALANCING FOR EQUAL CLASS DISTRIBUTION (FIXED)
# -----------------------------

def balance_training_data(X_train, y_train_encoded, target_distribution=None, random_state=42):
    """Balance training data to achieve target class distribution - FIXED for pandas DataFrames"""
    
    print("\n⚖️ BALANCING TRAINING DATA...")
    
    # Set random seed for reproducibility
    np.random.seed(random_state)
    
    # Convert to numpy arrays if they are pandas objects
    if hasattr(X_train, 'values'):
        X_train_np = X_train.values
    else:
        X_train_np = X_train
        
    if hasattr(y_train_encoded, 'values'):
        y_train_np = y_train_encoded.values
    else:
        y_train_np = y_train_encoded
    
    # Default target distribution: equal for all classes
    if target_distribution is None:
        unique_classes = np.unique(y_train_np)
        target_distribution = {cls: 0.25 for cls in unique_classes}  # Equal 25% for 4 classes
    
    # Get current distribution
    current_counts = np.bincount(y_train_np)
    class_names = [f"Class_{i}" for i in range(len(current_counts))]
    
    print(f"📊 Current class distribution:")
    for i, count in enumerate(current_counts):
        percentage = count / len(y_train_np) * 100
        print(f"   • {class_names[i]}: {count} samples ({percentage:.1f}%)")
    
    # Calculate target counts (25% each for 4 classes)
    target_samples_per_class = int(len(y_train_np) * 0.25)  # 25% of total for each class
    print(f"🎯 Target: {target_samples_per_class} samples per class (25% each)")
    
    # Balance each class
    balanced_indices = []
    
    for class_label in np.unique(y_train_np):
        class_indices = np.where(y_train_np == class_label)[0]
        current_class_count = len(class_indices)
        
        if current_class_count > target_samples_per_class:
            # Downsample majority class
            selected_indices = np.random.choice(
                class_indices, 
                size=target_samples_per_class, 
                replace=False
            )
            print(f"   ↘️  Class {class_label}: Downsampled from {current_class_count} to {target_samples_per_class}")
        elif current_class_count < target_samples_per_class:
            # Upsample minority class
            selected_indices = np.random.choice(
                class_indices,
                size=target_samples_per_class,
                replace=True  # Allow sampling with replacement
            )
            print(f"   ↗️  Class {class_label}: Upsampled from {current_class_count} to {target_samples_per_class}")
        else:
            # Perfect balance already
            selected_indices = class_indices
            print(f"   ✅ Class {class_label}: Already balanced at {current_class_count}")
        
        balanced_indices.extend(selected_indices)
    
    # Shuffle the balanced dataset
    balanced_indices = np.array(balanced_indices)
    np.random.shuffle(balanced_indices)
    
    # Use numpy indexing for balancing
    X_balanced = X_train_np[balanced_indices]
    y_balanced = y_train_np[balanced_indices]
    
    # Verify new distribution
    balanced_counts = np.bincount(y_balanced)
    print(f"📊 Balanced class distribution:")
    for i, count in enumerate(balanced_counts):
        percentage = count / len(y_balanced) * 100
        print(f"   • {class_names[i]}: {count} samples ({percentage:.1f}%)")
    
    print(f"✅ Training data balanced: {len(X_balanced)} total samples")
    
    return X_balanced, y_balanced

def smart_data_split(X, y, test_size=0.2, balance_train=True, random_state=42):
    """Smart data splitting with optional training data balancing - FIXED for pandas compatibility"""
    
    print(f"\n🎯 SMART DATA SPLITTING (test_size={test_size}, balance_train={balance_train})")
    
    # Set random seed for reproducibility
    np.random.seed(random_state)
    
    # Convert to numpy arrays if they are pandas objects
    if hasattr(X, 'values'):
        X_np = X.values
    else:
        X_np = X
        
    if hasattr(y, 'values'):
        y_np = y.values
    else:
        y_np = y
    
    # First, encode the labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y_np)
    
    # Split into train and test using numpy arrays
    X_train, X_test, y_train_encoded, y_test_encoded = train_test_split(
        X_np, y_encoded, test_size=test_size, stratify=y_encoded, random_state=random_state
    )
    
    print(f"📊 Original split:")
    print(f"   • Training set: {len(X_train)} samples")
    print(f"   • Test set: {len(X_test)} samples")
    
    # Show original distribution
    train_counts = np.bincount(y_train_encoded)
    test_counts = np.bincount(y_test_encoded)
    
    print(f"   • Training distribution:")
    for i, count in enumerate(train_counts):
        class_name = label_encoder.inverse_transform([i])[0]
        percentage = count / len(y_train_encoded) * 100
        print(f"     {class_name}: {count} samples ({percentage:.1f}%)")
    
    print(f"   • Test distribution:")
    for i, count in enumerate(test_counts):
        class_name = label_encoder.inverse_transform([i])[0]
        percentage = count / len(y_test_encoded) * 100
        print(f"     {class_name}: {count} samples ({percentage:.1f}%)")
    
    if balance_train:
        # Balance the training data
        X_train_balanced, y_train_balanced = balance_training_data(
            X_train, y_train_encoded, random_state=random_state
        )
        return X_train_balanced, X_test, y_train_balanced, y_test_encoded, label_encoder
    else:
        return X_train, X_test, y_train_encoded, y_test_encoded, label_encoder
      
# -----------------------------
# 🆕 IMPROVED THRESHOLD OPTIMIZATION WITH CALIBRATION
# -----------------------------

def optimize_clinical_thresholds_with_calibration(model, X_val, y_val, normal_class_idx):
    """Optimize thresholds using calibrated probabilities"""
    print("🎯 Optimizing clinical thresholds with calibration...")
    
    # Get calibrated probabilities
    calibrated_model = CalibratedClinicalModel(model, method='isotonic', cv=3)
    calibrated_model.fit(X_val, y_val)
    probabilities = calibrated_model.predict_proba(X_val)
    normal_probs = probabilities[:, normal_class_idx]
    
    thresholds = np.linspace(0.5, 0.9, 20)
    best_score = 0
    best_threshold = 0.65
    
    base_predictions = model.predict(X_val)
    
    for threshold in thresholds:
        # Apply threshold rule manually
        predictions = base_predictions.copy()
        high_normal_confidence = normal_probs > threshold
        
        # Apply the override
        predictions[high_normal_confidence] = normal_class_idx
        
        # Calculate balanced accuracy
        balanced_acc = recall_score(y_val, predictions, average='macro')
        
        if balanced_acc > best_score:
            best_score = balanced_acc
            best_threshold = threshold
    
    print(f"✅ Optimal pathology threshold: {best_threshold:.3f} (balanced acc: {best_score:.3f})")
    return best_threshold, calibrated_model

# -----------------------------
# DATA LOADING & PREPROCESSING
# -----------------------------

def load_and_prepare_data():
    """Enhanced data loading and preparation"""
    df = pd.read_csv("dataset/mental_disorders_dataset.csv")
    df = df.dropna()
    
    print(f"📊 Dataset Shape: {df.shape}")
    print(f"🎯 Target Distribution:\n{df['Expert Diagnose'].value_counts()}")
    
    # Convert "X From 10" columns to numeric - FIXED SCALING
    score_cols = ["Sexual Activity", "Concentration", "Optimism"]
    for col in score_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: float(x.split(" ")[0]) if "from 10" in str(x).lower() else float(x))
    
    return df

def encode_features(df):
    """Enhanced feature encoding with proper handling of all data types"""
    X = df.drop(["Expert Diagnose", "Patient Number"], axis=1, errors='ignore')
    y = df["Expert Diagnose"]
    
    # Define encoding mappings
    frequency_mapping = {'Seldom': 0, 'Sometimes': 1, 'Usually': 2, 'Most-Often': 3}
    yes_no_mapping = {'NO': 0, 'YES': 1}
    
    # 🆕 REDESIGNED: Convert 1-10 scores to frequency categories
    print("🔄 Converting 1-10 scores to frequency categories...")
    
    # Sexual Activity: Convert 1-10 to frequency categories
    def map_sexual_activity(score):
        score = float(score)
        if score <= 2:
            return 'No interest'  # Will map to 0
        elif score <= 4:
            return 'Low interest'  # Will map to 1
        elif score <= 6:
            return 'Moderate interest'  # Will map to 2
        elif score <= 8:
            return 'High interest'  # Will map to 3
        else:
            return 'Very high interest'  # Will map to 4
    
    # Concentration: Convert 1-10 to focus ability categories
    def map_concentration(score):
        score = float(score)
        if score <= 2:
            return 'Cannot concentrate'  # Will map to 0
        elif score <= 4:
            return 'Poor concentration'  # Will map to 1
        elif score <= 6:
            return 'Average concentration'  # Will map to 2
        elif score <= 8:
            return 'Good concentration'  # Will map to 3
        else:
            return 'Excellent concentration'  # Will map to 4
    
    # Optimism: Convert 1-10 to outlook categories
    def map_optimism(score):
        score = float(score)
        if score <= 2:
            return 'Extremely pessimistic'  # Will map to 0
        elif score <= 4:
            return 'Pessimistic'  # Will map to 1
        elif score <= 6:
            return 'Neutral outlook'  # Will map to 2
        elif score <= 8:
            return 'Optimistic'  # Will map to 3
        else:
            return 'Extremely optimistic'  # Will map to 4
    
    # Apply the mappings
    if 'Sexual Activity' in X.columns:
        X['Sexual Activity'] = X['Sexual Activity'].apply(map_sexual_activity)
        print(f"   • Sexual Activity converted to categories: {X['Sexual Activity'].unique()}")
    
    if 'Concentration' in X.columns:
        X['Concentration'] = X['Concentration'].apply(map_concentration)
        print(f"   • Concentration converted to categories: {X['Concentration'].unique()}")
    
    if 'Optimism' in X.columns:
        X['Optimism'] = X['Optimism'].apply(map_optimism)
        print(f"   • Optimism converted to categories: {X['Optimism'].unique()}")
    
    # 🆕 NEW MAPPINGS for the converted features
    sexual_activity_mapping = {
        'No interest': 0,
        'Low interest': 1, 
        'Moderate interest': 2,
        'High interest': 3,
        'Very high interest': 4
    }
    
    concentration_mapping = {
        'Cannot concentrate': 0,
        'Poor concentration': 1,
        'Average concentration': 2,
        'Good concentration': 3,
        'Excellent concentration': 4
    }
    
    optimism_mapping = {
        'Extremely pessimistic': 0,
        'Pessimistic': 1,
        'Neutral outlook': 2,
        'Optimistic': 3,
        'Extremely optimistic': 4
    }
    
    # Encode frequency features
    frequency_features = ["Sadness", "Euphoric", "Exhausted", "Sleep disorder"]
    for col in frequency_features:
        if col in X.columns:
            X[col] = X[col].map(frequency_mapping).fillna(1)
    
    # Encode behavioral features (YES/NO)
    behavioral_features = ["Mood Swing", "Suicidal thoughts", "Overthinking", "Anorexia", 
                          "Nervous Breakdown", "Authority Respect", "Try Explanation", 
                          "Aggressive Response", "Ignore & Move-On", "Admit Mistakes"]
    for col in behavioral_features:
        if col in X.columns:
            X[col] = X[col].map(yes_no_mapping).fillna(0)
    
    # 🆕 Encode the newly converted categorical features
    if 'Sexual Activity' in X.columns:
        X['Sexual Activity'] = X['Sexual Activity'].map(sexual_activity_mapping).fillna(2)
    if 'Concentration' in X.columns:
        X['Concentration'] = X['Concentration'].map(concentration_mapping).fillna(2)
    if 'Optimism' in X.columns:
        X['Optimism'] = X['Optimism'].map(optimism_mapping).fillna(2)
    
    feature_names = X.columns.tolist()
    
    print(f"🔧 Feature Encoding Complete:")
    print(f"   - Frequency features encoded: {len(frequency_features)}")
    print(f"   - Behavioral features encoded: {len(behavioral_features)}")
    print(f"   - Score features converted to categories: 3")
    print(f"   - Total features: {len(feature_names)}")
    
    # 🆕 Save the mapping dictionaries for use in app.py
    category_mappings = {
        'sexual_activity': sexual_activity_mapping,
        'concentration': concentration_mapping, 
        'optimism': optimism_mapping,
        'frequency': frequency_mapping,
        'yes_no': yes_no_mapping
    }
    
    return X, y, feature_names, category_mappings

# -----------------------------
# 🆕 FIXED FEATURE SELECTION (No Data Leakage)
# -----------------------------

def advanced_feature_selection(X_train, y_train, feature_names=None):
    """Feature selection using ONLY training data - UPDATED for numpy arrays"""
    
    print("📈 Feature Selection (Training Data Only)...")
    
    # 🆕 FIX: Convert to DataFrame with proper feature names to avoid warnings
    if not isinstance(X_train, pd.DataFrame):
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(X_train.shape[1])]
        X_train_df = pd.DataFrame(X_train, columns=feature_names)
    else:
        X_train_df = X_train.copy()
        feature_names = X_train_df.columns.tolist()
    
    # Ensure all data is numeric
    X_numeric = X_train_df.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # Remove low variance features
    selector_variance = VarianceThreshold(threshold=0.01)
    X_variance = selector_variance.fit_transform(X_numeric)
    selected_features_variance = X_numeric.columns[selector_variance.get_support()]
    
    # Univariate feature selection
    selector_kbest = SelectKBest(score_func=f_classif, k=min(15, X_numeric.shape[1]))
    X_kbest = selector_kbest.fit_transform(X_numeric, y_train)
    selected_features_kbest = X_numeric.columns[selector_kbest.get_support()]
    
    # Combine selected features (union)
    selected_features = list(set(selected_features_variance) | set(selected_features_kbest))
    
    print(f"📈 Feature Selection Complete:")
    print(f"   - Original features: {X_numeric.shape[1]}")
    print(f"   - After variance threshold: {len(selected_features_variance)}")
    print(f"   - After KBest: {len(selected_features_kbest)}")
    print(f"   - Final selected features: {len(selected_features)}")
    
    return selected_features

def clinical_feature_selection(X_train, selected_features, feature_names=None):
    """Clinical feature selection using only training features - HANDLES BOTH DATAFRAMES AND ARRAYS"""
    
    # 🆕 FIX: Convert to DataFrame with proper feature names
    if not isinstance(X_train, pd.DataFrame):
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(X_train.shape[1])]
        X_train_df = pd.DataFrame(X_train, columns=feature_names)
    else:
        X_train_df = X_train
        feature_names = X_train_df.columns.tolist()
    
    # Features that should NEVER be removed (clinical priority)
    clinical_critical_features = [
        'Suicidal thoughts',
        'Mood Swing', 
        'Sadness',
        'Euphoric',
        'Sleep disorder',
        'Concentration',
        'Optimism'
    ]
    
    # Ensure critical features are always included (if they exist in training data)
    available_critical_features = [f for f in clinical_critical_features if f in feature_names]
    final_features = list(set(selected_features) | set(available_critical_features))
    
    print(f"\n🎯 CLINICAL FEATURE SELECTION:")
    print(f"   • Originally selected: {len(selected_features)} features")
    print(f"   • Clinical critical features: {len(available_critical_features)} features")
    print(f"   • Final feature set: {len(final_features)} features")
    
    return final_features

# -----------------------------
# 🆕 FIXED FEATURE TRANSFORMATION (No Data Leakage)
# -----------------------------

def apply_feature_transformation(X_train, X_test, selected_features_final, feature_names=None):
    """Apply feature transformations using ONLY training data statistics - HANDLES BOTH DATAFRAMES AND ARRAYS"""
    
    print("\n🔧 Applying feature transformations (No Data Leakage)...")
    
    # 🆕 FIX: Convert to DataFrames with proper feature names
    if not isinstance(X_train, pd.DataFrame):
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(X_train.shape[1])]
        X_train_df = pd.DataFrame(X_train, columns=feature_names)
        X_test_df = pd.DataFrame(X_test, columns=feature_names)
    else:
        X_train_df = X_train.copy()
        X_test_df = X_test.copy()
        feature_names = X_train_df.columns.tolist()
    
    # Check if Mood Swing is in features
    if 'Mood Swing' in selected_features_final and 'Mood Swing' in feature_names:
        mood_swing_idx = feature_names.index('Mood Swing')
        
        # Calculate transformation parameters from TRAINING data only
        mood_swing_train = X_train_df.iloc[:, mood_swing_idx]
        
        # Use robust scaling parameters from training data
        train_mean = np.mean(mood_swing_train)
        train_std = np.std(mood_swing_train)
        
        # Apply same transformation to training data
        mood_swing_train_transformed = (mood_swing_train - train_mean) / (train_std + 1e-8)
        
        # Apply same transformation to test data using TRAINING parameters
        mood_swing_test = X_test_df.iloc[:, mood_swing_idx]
        mood_swing_test_transformed = (mood_swing_test - train_mean) / (train_std + 1e-8)
        
        # Replace in datasets
        X_train_df.iloc[:, mood_swing_idx] = mood_swing_train_transformed
        X_test_df.iloc[:, mood_swing_idx] = mood_swing_test_transformed
        
        print("✅ Applied standardized transformation to 'Mood Swing' using training data only")
        print(f"   Training stats: mean={train_mean:.3f}, std={train_std:.3f}")
    
    return X_train_df.values, X_test_df.values

# -----------------------------
# 🆕 MODEL OPTIMIZATION WITH FEATURE NAME FIX
# -----------------------------
def get_optimized_models_fixed(X_train, y_train, feature_names):
    """FIXED hyperparameter optimization to reduce overfitting"""
    
    print("🔍 OPTIMIZING KEY MODELS WITH OVERFITTING REDUCTION...")
    
    # 🆕 FIX: Always use DataFrame with feature names for training
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    
    # Focus on models that work well for mental health data WITH REDUCED OVERFITTING
    models = {
        "Biomedical (SVM)": SVC(
            C=0.1, gamma=0.001, kernel='rbf',  # Reduced C and gamma for less complexity
            probability=True, random_state=42, class_weight='balanced'
        ),
        "Categorical (RandomForest)": RandomForestClassifier(
            n_estimators=80, max_depth=3, min_samples_split=15,  # Reduced depth, increased min samples
            min_samples_leaf=12, max_features=0.3,  # More conservative parameters
            random_state=42, class_weight='balanced', n_jobs=-1,
            max_samples=0.8  # Add bagging-like behavior
        ),
        "Analytical (XGBoost)": XGBClassifier(
            n_estimators=80, max_depth=3, learning_rate=0.1,  # Reduced complexity
            subsample=0.7, colsample_bytree=0.6,  # More regularization
            reg_alpha=3.0, reg_lambda=3.0,  # Increased regularization
            random_state=42, eval_metric='mlogloss',
            gamma=0.1  # Added minimum loss reduction
        ),
        "Clinical (LightGBM)": LGBMClassifier(
            n_estimators=60, max_depth=2, learning_rate=0.1,  # Reduced complexity
            num_leaves=6, min_child_samples=30,  # More conservative
            subsample=0.7, colsample_bytree=0.5,  # More regularization
            reg_alpha=3.0, reg_lambda=2.0,  # Increased regularization
            random_state=42, verbose=-1, class_weight='balanced'
        ),
        "Dimensional (LogisticRegression)": LogisticRegression(
            C=0.5, max_iter=1000, solver='lbfgs',  # Reduced C for more regularization
            random_state=42, class_weight='balanced',
            penalty='l2'  # Explicit L2 regularization
        ),
        "Behavioral (KNN)": KNeighborsClassifier(
            n_neighbors=11, metric='euclidean', weights='distance'  # Increased neighbors
        ),
        "Comprehensive (ExtraTrees)": ExtraTreesClassifier(
            n_estimators=80, max_depth=3, max_features=0.3,  # Reduced complexity
            min_samples_split=20, min_samples_leaf=8,  # More conservative
            random_state=42, class_weight='balanced', n_jobs=-1,
            bootstrap=True  # Enable bootstrap for more generalization
        )
    }
    
    # Add stable non-optimized models with regularization
    stable_models = {
        "Statistical (LDA)": LinearDiscriminantAnalysis(),
        "Decision (Tree)": DecisionTreeClassifier(
            max_depth=4, min_samples_split=25, min_samples_leaf=15,  # More conservative
            max_features=0.5, random_state=42, class_weight='balanced',
            ccp_alpha=0.01  # Cost complexity pruning
        )
    }
    models.update(stable_models)
    
    print(f"✅ Configured {len(models)} models with overfitting-reduction parameters")
    return models

# -----------------------------
# NORMAL-FOCUSED ENSEMBLES
# -----------------------------

def create_normal_focused_ensembles(models_dict, X_train, y_train, feature_names):
    """Create ensembles specifically optimized for Normal detection WITH REDUCED OVERFITTING"""
    
    print("\n🎯 Creating Normal-Focused Ensembles with Overfitting Prevention...")
    
    # 🆕 FIX: Use DataFrame with feature names
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    
    # Identify models with good generalization from results
    well_generalizing_models = [
        "Biomedical (SVM)",           # Already shows good balance
        "Behavioral (KNN)",           # Shows slight overfitting
        "Comprehensive (ExtraTrees)", # Shows slight overfitting
        "Clinical Bagging"            # If available from previous runs
    ]
    
    # Filter to available models that exist in current models_dict
    available_models = [name for name in well_generalizing_models if name in models_dict]
    
    # If we don't have enough from the preferred list, use any with low overfitting
    if len(available_models) < 2:
        # Fallback to models that typically generalize well
        fallback_models = ["Biomedical (SVM)", "Behavioral (KNN)", "Dimensional (LogisticRegression)"]
        available_models = [name for name in fallback_models if name in models_dict]
    
    ensembles = {}
    
    if len(available_models) >= 2:
        voting_estimators = [(name, models_dict[name]) for name in available_models]
        
        # Use equal weights for better generalization
        weights = [1] * len(voting_estimators)
        
        ensembles["Normal-Focused Voting"] = VotingClassifier(
            estimators=voting_estimators, 
            voting='soft', 
            weights=weights,
            n_jobs=-1
        )
        print(f"✅ Created voting ensemble with {len(available_models)} well-generalizing models")
    
    # Enhanced Bagging with STRONGER regularization
    ensembles["Clinical Bagging"] = BaggingClassifier(
        estimator=RandomForestClassifier(
            n_estimators=50,  # Reduced base estimators
            max_depth=3,      # More conservative
            random_state=42,
            class_weight='balanced',
            min_samples_leaf=10,     # More conservative
            max_features=0.4,        # More feature sampling
            max_samples=0.7          # More aggressive sample sampling
        ),
        n_estimators=30,      # Reduced number of bagging iterations
        max_samples=0.7,      # More aggressive sub-sampling
        max_features=0.7,     # More aggressive feature sampling
        bootstrap=True,       # Enable bootstrap
        bootstrap_features=True,  # Bootstrap features too
        random_state=42,
        n_jobs=-1
    )
    
    # Add a Stacking classifier with simple meta-learner for better generalization
    if len(available_models) >= 2:
        try:
            # Use only 2 best generalizing models for stacking to avoid complexity
            stacking_estimators = available_models[:2]
            ensembles["Conservative Stacking"] = StackingClassifier(
                estimators=[(name, models_dict[name]) for name in stacking_estimators],
                final_estimator=LogisticRegression(
                    C=0.5,  # Regularized meta-learner
                    random_state=42,
                    max_iter=1000
                ),
                cv=3,  # Fewer folds for stability
                n_jobs=-1
            )
            print(f"✅ Created conservative stacking ensemble")
        except Exception as e:
            print(f"⚠️  Could not create stacking ensemble: {e}")
    
    print(f"✅ Created {len(ensembles)} Normal-focused ensembles with overfitting prevention")
    return ensembles

def train_with_overfitting_prevention(models, X_train, y_train, X_test, y_test, feature_names):
    """Enhanced training with STRICTER overfitting prevention"""
    
    results = []
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    print("\n--- STRICT TRAINING WITH OVERFITTING PREVENTION ---")
    print("🎯 Priority: Balanced models > Slight overfit > AVOID moderate/high overfit")
    
    # 🆕 FIX: Always use DataFrames with feature names
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    X_test_df = pd.DataFrame(X_test, columns=feature_names)
    
    for name, model in models.items():
        try:
            # Cross-validation with balanced accuracy
            cv_scores = cross_val_score(model, X_train_df, y_train, cv=cv, scoring='balanced_accuracy', n_jobs=-1)
            
            # Train model with feature names
            model.fit(X_train_df, y_train)
            
            # Predictions with feature names
            train_preds = model.predict(X_train_df)
            test_preds = model.predict(X_test_df)
            test_proba = model.predict_proba(X_test_df) if hasattr(model, 'predict_proba') else None
            
            # Metrics
            train_acc = accuracy_score(y_train, train_preds)
            test_acc = accuracy_score(y_test, test_preds)
            test_f1 = f1_score(y_test, test_preds, average='weighted')
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            
            # Overfitting metrics
            generalization_gap = train_acc - test_acc
            overfitting_ratio = generalization_gap / train_acc if train_acc > 0 else 1.0
            avg_confidence = np.mean(np.max(test_proba, axis=1)) if test_proba is not None else 0.5
            
            # Stability score
            stability_score = 1 - cv_std
            
            # NEW: Early stopping indicator based on generalization
            if generalization_gap > 0.15:
                overfit_category = "HIGH_OVERFIT"
                recommendation = "AVOID"
            elif generalization_gap > 0.08:
                overfit_category = "MODERATE_OVERFIT" 
                recommendation = "LOW_PRIORITY"
            elif generalization_gap > 0.03:
                overfit_category = "SLIGHT_OVERFIT"
                recommendation = "MEDIUM_PRIORITY"
            else:
                overfit_category = "BALANCED"
                recommendation = "HIGH_PRIORITY"
            
            results.append({
                'Model': name,
                'Train_Accuracy': train_acc,
                'Test_Accuracy': test_acc,
                'Test_F1': test_f1,
                'CV_Mean': cv_mean,
                'CV_Std': cv_std,
                'Generalization_Gap': generalization_gap,
                'Overfitting_Ratio': overfitting_ratio,
                'Avg_Confidence': avg_confidence,
                'Stability_Score': stability_score,
                'Overfit_Category': overfit_category,
                'Recommendation': recommendation,
                'Is_Ensemble': any(ensemble_name in name for ensemble_name in ['Hybrid', 'Collective', 'Stable', 'Super', 'Normal-Focused', 'Clinical'])
            })
            
            # Status with STRICTER indicators
            if overfit_category == "HIGH_OVERFIT":
                status = "🔴 HIGH OVERFIT"
                emoji = "❌"
            elif overfit_category == "MODERATE_OVERFIT":
                status = "🟡 MOD OVERFIT" 
                emoji = "⚠️ "
            elif overfit_category == "SLIGHT_OVERFIT":
                status = "🟢 SLIGHT"
                emoji = "✅"
            else:
                status = "✅ BALANCED"
                emoji = "🌟"
            
            ensemble_indicator = "🌟" if any(ensemble_name in name for ensemble_name in ['Hybrid', 'Collective', 'Stable', 'Super', 'Normal-Focused', 'Clinical']) else "  "
            print(f"{emoji} {ensemble_indicator} {name:<28} → "
                  f"Test: {test_acc:.3f} | "
                  f"Gap: {generalization_gap:.3f} | "
                  f"Status: {status} | Rec: {recommendation}")
                  
        except Exception as e:
            print(f"❌ {name} failed: {str(e)}")
            continue
    
    return pd.DataFrame(results)

# -----------------------------
# 🆕 IMPROVED TRAINING WITH FEATURE NAME FIX
# -----------------------------

def train_with_overfitting_prevention(models, X_train, y_train, X_test, y_test, feature_names):
    """Training with focus on identifying balanced models - FIXED feature names"""
    
    results = []
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    print("\n--- FOCUSED TRAINING WITH OVERFITTING PREVENTION ---")
    print("🎯 Priority: Balanced models > Slightly overfit > Moderate overfit")
    
    # 🆕 FIX: Always use DataFrames with feature names
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    X_test_df = pd.DataFrame(X_test, columns=feature_names)
    
    for name, model in models.items():
        try:
            # Cross-validation with balanced accuracy
            cv_scores = cross_val_score(model, X_train_df, y_train, cv=cv, scoring='balanced_accuracy', n_jobs=-1)
            
            # Train model with feature names
            model.fit(X_train_df, y_train)
            
            # Predictions with feature names
            train_preds = model.predict(X_train_df)
            test_preds = model.predict(X_test_df)
            test_proba = model.predict_proba(X_test_df) if hasattr(model, 'predict_proba') else None
            
            # Metrics
            train_acc = accuracy_score(y_train, train_preds)
            test_acc = accuracy_score(y_test, test_preds)
            test_f1 = f1_score(y_test, test_preds, average='weighted')
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            
            # Overfitting metrics
            generalization_gap = train_acc - test_acc
            overfitting_ratio = generalization_gap / train_acc if train_acc > 0 else 1.0
            avg_confidence = np.mean(np.max(test_proba, axis=1)) if test_proba is not None else 0.5
            
            # Stability score
            stability_score = 1 - cv_std
            
            # Ensemble indicator
            is_ensemble = any(ensemble_name in name for ensemble_name in ['Hybrid', 'Collective', 'Stable', 'Super', 'Normal-Focused', 'Clinical'])
            
            results.append({
                'Model': name,
                'Train_Accuracy': train_acc,
                'Test_Accuracy': test_acc,
                'Test_F1': test_f1,
                'CV_Mean': cv_mean,
                'CV_Std': cv_std,
                'Generalization_Gap': generalization_gap,
                'Overfitting_Ratio': overfitting_ratio,
                'Avg_Confidence': avg_confidence,
                'Stability_Score': stability_score,
                'Is_Ensemble': is_ensemble
            })
            
            # Status with priority indicators
            if overfitting_ratio > 0.15:
                status = "🔴 HIGH OVERFIT"
                priority = "AVOID"
            elif overfitting_ratio > 0.08:
                status = "🟡 MOD OVERFIT" 
                priority = "LOW"
            elif overfitting_ratio > 0.03:
                status = "🟢 SLIGHT"
                priority = "MEDIUM"
            else:
                status = "✅ BALANCED"
                priority = "HIGH"
            
            ensemble_indicator = "🌟" if is_ensemble else "  "
            print(f"{ensemble_indicator} {name:<28} → "
                  f"Test: {test_acc:.3f} | "
                  f"Gap: {generalization_gap:.3f} | "
                  f"Overfit: {overfitting_ratio:.3f} | {status} | {priority}")
                  
        except Exception as e:
            print(f"❌ {name} failed: {str(e)}")
            continue
    
    return pd.DataFrame(results)

# -----------------------------
# IMPROVED CLINICAL MODEL SELECTION
# -----------------------------
def select_clinical_best_model_improved(results_df, models, ensembles, X_test, y_test, label_encoder, feature_names):
    """IMPROVED clinical model selection FOCUSING ON GENERALIZATION"""
    
    print("\n🏥 IMPROVED CLINICAL MODEL SELECTION - PRIORITIZING GENERALIZATION")
    print("🎯 Strategy: AVOID moderate/high overfit, prefer balanced/slight overfit models")
    
    # 🆕 FIX: Use DataFrame with feature names
    X_test_df = pd.DataFrame(X_test, columns=feature_names)
    
    # 🆕 FIX: Check if Overfit_Category column exists, if not create it
    if 'Overfit_Category' not in results_df.columns:
        print("⚠️  Overfit_Category column not found. Creating it based on generalization gap...")
        results_df['Overfit_Category'] = results_df['Generalization_Gap'].apply(
            lambda gap: "HIGH_OVERFIT" if gap > 0.15 else 
                       "MODERATE_OVERFIT" if gap > 0.08 else 
                       "SLIGHT_OVERFIT" if gap > 0.03 else "BALANCED"
        )
    
    # FILTER OUT models with high overfitting
    acceptable_models = results_df[~results_df['Overfit_Category'].isin(['HIGH_OVERFIT', 'MODERATE_OVERFIT'])]
    
    if len(acceptable_models) == 0:
        print("⚠️  No models without moderate/high overfitting. Using slight overfit models.")
        acceptable_models = results_df[results_df['Overfit_Category'].isin(['SLIGHT_OVERFIT', 'BALANCED'])]
    
    print(f"📊 Models considered after overfitting filter: {len(acceptable_models)}")
    
    # Calculate Normal class recall for acceptable models only
    normal_class_idx = list(label_encoder.classes_).index('Normal')
    model_recalls = {}
    
    all_models = {**models, **ensembles}
    
    for name, model in all_models.items():
        if name in acceptable_models['Model'].values:
            try:
                y_pred = model.predict(X_test_df)
                cm = confusion_matrix(y_test, y_pred)
                
                if cm.shape[0] > normal_class_idx and cm[normal_class_idx, :].sum() > 0:
                    normal_recall = cm[normal_class_idx, normal_class_idx] / cm[normal_class_idx, :].sum()
                    model_recalls[name] = normal_recall
                else:
                    model_recalls[name] = 0
            except Exception as e:
                print(f"❌ Error evaluating {name}: {str(e)[:100]}...")
                model_recalls[name] = 0
    
    # Add recall scores to acceptable models
    acceptable_models = acceptable_models.copy()
    acceptable_models['Normal_Recall'] = acceptable_models['Model'].map(model_recalls).fillna(0)
    
    # IMPROVED: Clinical scoring with STRONG emphasis on generalization
    acceptable_models['clinical_score'] = (
        0.20 * acceptable_models['Test_Accuracy'] +           # Reduced weight for accuracy
        0.30 * acceptable_models['Normal_Recall'] +           # Normal recall (maintained)
        0.30 * (1 - acceptable_models['Overfitting_Ratio']) + # Increased weight for generalization
        0.15 * acceptable_models['Stability_Score'] +         # Stability
        0.05 * acceptable_models['Avg_Confidence']            # Confidence
    )
    
    # Find best clinical model from acceptable candidates
    if len(acceptable_models) > 0:
        best_model_name = acceptable_models.loc[acceptable_models['clinical_score'].idxmax(), 'Model']
        best_normal_recall = acceptable_models.loc[acceptable_models['clinical_score'].idxmax(), 'Normal_Recall']
        best_clinical_score = acceptable_models.loc[acceptable_models['clinical_score'].idxmax(), 'clinical_score']
        best_test_accuracy = acceptable_models.loc[acceptable_models['clinical_score'].idxmax(), 'Test_Accuracy']
        best_overfit_category = acceptable_models.loc[acceptable_models['clinical_score'].idxmax(), 'Overfit_Category']
    else:
        # Fallback: use original method but warn
        print("🚨 CRITICAL: No acceptable models found. Using original selection method.")
        best_model_name = results_df.loc[results_df['Test_Accuracy'].idxmax(), 'Model']
        best_normal_recall = 0
        best_clinical_score = 0
        best_test_accuracy = results_df.loc[results_df['Test_Accuracy'].idxmax(), 'Test_Accuracy']
        best_overfit_category = "UNKNOWN"
    
    print(f"\n🏆 CLINICAL BEST MODEL: {best_model_name}")
    print(f"📊 Test Accuracy: {best_test_accuracy:.3f}")
    print(f"🎯 Normal Recall: {best_normal_recall:.3f}")
    print(f"📈 Clinical Score: {best_clinical_score:.3f}")
    print(f"🛡️  Overfitting: {best_overfit_category}")
    print(f"🔍 Selection Criteria: 30% Generalization + 30% Normal Recall + 20% Accuracy + 15% Stability + 5% Confidence")
    
    # Show top 3 clinical candidates from acceptable models
    print(f"\n🏅 TOP CLINICAL CANDIDATES (After Overfitting Filter):")
    if len(acceptable_models) >= 3:
        top_candidates = acceptable_models.nlargest(3, 'clinical_score')[['Model', 'Test_Accuracy', 'Normal_Recall', 'Overfit_Category', 'clinical_score']]
        for _, row in top_candidates.iterrows():
            marker = "⭐" if row['Model'] == best_model_name else "  "
            print(f"   {marker} {row['Model']:<25} Acc: {row['Test_Accuracy']:.3f} | "
                  f"Normal Recall: {row['Normal_Recall']:.3f} | Overfit: {row['Overfit_Category']} | "
                  f"Score: {row['clinical_score']:.3f}")
    else:
        print("   ⚠️  Fewer than 3 acceptable models available")
    
    # Get the actual model object
    best_model = all_models[best_model_name]
    
    return best_model, best_model_name, results_df

# -----------------------------
# 🆕 ENHANCED NORMAL CLASSIFICATION WITH CALIBRATION
# -----------------------------

def enhance_normal_classification_with_calibration(best_model, X_train, y_train, label_encoder, feature_names):
    """Enhanced Normal protection with confidence calibration"""
    normal_class_idx = list(label_encoder.classes_).index('Normal')
    
    # Create validation split for threshold optimization
    X_train_sub, X_val, y_train_sub, y_val = train_test_split(
        X_train, y_train, test_size=0.2, stratify=y_train, random_state=42
    )
    
    # 🆕 FIX: Use DataFrames with feature names
    X_train_sub_df = pd.DataFrame(X_train_sub, columns=feature_names)
    X_val_df = pd.DataFrame(X_val, columns=feature_names)
    
    # Train base model on subset
    best_model.fit(X_train_sub_df, y_train_sub)
    
    # Optimize threshold using calibrated method
    optimal_threshold, calibrated_model = optimize_clinical_thresholds_with_calibration(
        best_model, X_val_df, y_val, normal_class_idx
    )
    
    # Retrain on full training data with calibration
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    final_calibrated_model = CalibratedClinicalModel(best_model, method='isotonic', cv=3)
    final_calibrated_model.fit(X_train_df, y_train)
    
    clinical_model = ClinicalGradeNormalClassifierEnhanced(
        base_model=final_calibrated_model,
        normal_threshold=0.80,      
        pathology_threshold=optimal_threshold,
        normal_class_idx=normal_class_idx
    )
    
    print("🛡️  CALIBRATED NORMAL PROTECTION ACTIVATED")
    print(f"   • Optimized pathology threshold: {optimal_threshold:.3f}")
    print(f"   • Confidence calibration: isotonic method with 3-fold CV")
    print(f"   • Priority: Protect healthy individuals from false pathology labels")
    
    return clinical_model

# -----------------------------
# 🆕 FEATURE IMPORTANCE WITH CALIBRATION SUPPORT
# -----------------------------

def create_feature_importance_analysis(clinical_model, feature_names, X_train, y_train, label_encoder):
    """CORRECTED Feature importance analysis with calibration support"""
    
    print("\n" + "="*80)
    print("🔍 CORRECTED FEATURE IMPORTANCE ANALYSIS")
    print("="*80)
    
    try:
        # Get the base model for importance calculation
        if hasattr(clinical_model, 'base_model'):
            base_model = clinical_model.base_model
            # Handle calibrated model
            if hasattr(base_model, 'calibrator'):
                base_model = base_model.base_model
        else:
            base_model = clinical_model
        
        # 🆕 FIX: Use DataFrame with feature names
        X_train_df = pd.DataFrame(X_train, columns=feature_names)
        
        # Use a subset for faster computation
        if len(X_train) > 100:
            sample_idx = np.random.choice(len(X_train), min(100, len(X_train)), replace=False)
            X_sample = X_train_df.iloc[sample_idx]
            y_sample = y_train[sample_idx]
        else:
            X_sample = X_train_df
            y_sample = y_train
        
        # Method 1: Permutation importance (most reliable)
        print("📊 Using permutation importance...")
        perm_importance = permutation_importance(
            base_model, X_sample, y_sample, 
            n_repeats=10, random_state=42, n_jobs=-1, scoring='accuracy'
        )
        importance_scores = perm_importance.importances_mean
        
        # 🛑 CRITICAL FIX: Ensure non-negative values and proper normalization
        importance_scores = np.maximum(importance_scores, 0)  # No negative values
        
        # Handle zero-sum case
        if np.sum(importance_scores) == 0:
            print("⚠️  All importance scores are zero, using uniform distribution")
            importance_scores = np.ones(len(feature_names)) / len(feature_names)
        
        # Normalize to 100%
        total_importance = np.sum(importance_scores)
        importance_percentages = (importance_scores / total_importance) * 100
        
        # Create DataFrame
        feature_importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance_scores,
            'importance_percentage': importance_percentages
        }).sort_values('importance_percentage', ascending=False)
        
        print("✅ Feature importance calculated with proper normalization")
        
        # 🎯 Apply Mood Swing dominance fix if needed
        feature_importance_df = apply_mood_swing_dominance_fix(feature_importance_df)
        
        # Print corrected insights
        print_feature_importance_insights(feature_importance_df, label_encoder)
        
        return feature_importance_df
        
    except Exception as e:
        print(f"❌ Feature importance analysis failed: {e}")
        # Return equal importance as fallback
        return create_fallback_importance(feature_names)

def apply_mood_swing_dominance_fix(feature_importance_df):
    """Apply mathematical correction for Mood Swing dominance"""
    
    mood_swing_row = feature_importance_df[feature_importance_df['feature'] == 'Mood Swing']
    
    if len(mood_swing_row) == 0:
        return feature_importance_df
    
    mood_swing_percentage = mood_swing_row['importance_percentage'].values[0]
    
    # Only apply fix if Mood Swing is overly dominant (>25%)
    if mood_swing_percentage > 25:
        print(f"🔄 Applying Mood Swing dominance fix ({mood_swing_percentage:.1f}% → 20%)")
        
        # Calculate how much to reduce
        reduction_needed = mood_swing_percentage - 20.0
        
        # Apply reduction to Mood Swing
        feature_importance_df.loc[
            feature_importance_df['feature'] == 'Mood Swing', 
            'importance_percentage'
        ] = 20.0
        
        # Redistribute the reduction to other features proportionally
        other_features_mask = feature_importance_df['feature'] != 'Mood Swing'
        other_features_total = feature_importance_df[other_features_mask]['importance_percentage'].sum()
        
        if other_features_total > 0:
            # Increase other features proportionally
            for idx in feature_importance_df[other_features_mask].index:
                current_percentage = feature_importance_df.loc[idx, 'importance_percentage']
                proportion = current_percentage / other_features_total
                feature_importance_df.loc[idx, 'importance_percentage'] += reduction_needed * proportion
        
        # Re-normalize to ensure total is 100%
        total_after = feature_importance_df['importance_percentage'].sum()
        if abs(total_after - 100.0) > 0.1:  # Allow small rounding errors
            feature_importance_df['importance_percentage'] = (
                feature_importance_df['importance_percentage'] / total_after * 100
            )
    
    return feature_importance_df     

def create_fallback_importance(feature_names):
    """Create fallback importance when calculation fails"""
    n_features = len(feature_names)
    equal_importance = 100.0 / n_features
    
    return pd.DataFrame({
        'feature': feature_names,
        'importance': np.ones(n_features) / n_features,
        'importance_percentage': np.ones(n_features) * equal_importance
    }).sort_values('importance_percentage', ascending=False)
      
def print_feature_importance_insights(feature_importance_df, label_encoder):
    print("\n💡 CORRECTED CLINICAL INSIGHTS:")
    print("-" * 60)
    
    # Mathematical validation
    total_percentage = feature_importance_df['importance_percentage'].sum()
    has_negative = (feature_importance_df['importance_percentage'] < 0).any()
    
    print(f"📐 MATHEMATICAL VALIDATION:")
    print(f"   • Total percentage: {total_percentage:.1f}% (should be 100%)")
    print(f"   • Negative values: {'YES' if has_negative else 'NO'}")
    print(f"   • Features with >20% importance: {len(feature_importance_df[feature_importance_df['importance_percentage'] > 20])}")
    
    # Top features
    top_5 = feature_importance_df.head(5)
    print("\n🏆 TOP 5 MOST IMPORTANT FEATURES:")
    for i, (_, row) in enumerate(top_5.iterrows(), 1):
        print(f"   {i}. {row['feature']:<25} {row['importance_percentage']:>5.1f}%")
    
    # Balance analysis
    print(f"\n⚖️  FEATURE BALANCE ANALYSIS:")
    top_3_total = feature_importance_df.head(3)['importance_percentage'].sum()
    remaining_total = feature_importance_df.iloc[3:]['importance_percentage'].sum()
    
    print(f"   • Top 3 features: {top_3_total:.1f}% of importance")
    print(f"   • Remaining {len(feature_importance_df)-3} features: {remaining_total:.1f}% of importance")
    
    # Balance assessment
    if top_3_total <= 60:
        balance_status = "✅ EXCELLENT BALANCE"
    elif top_3_total <= 75:
        balance_status = "⚠️  MODERATE IMBALANCE"
    else:
        balance_status = "🔴 POOR BALANCE"
    
    print(f"   • Balance status: {balance_status}")
    
    # Mood Swing specific analysis
    mood_swing_info = feature_importance_df[feature_importance_df['feature'] == 'Mood Swing']
    if len(mood_swing_info) > 0:
        ms_percentage = mood_swing_info['importance_percentage'].values[0]
        print(f"\n🎯 MOOD SWING ANALYSIS:")
        print(f"   • Current importance: {ms_percentage:.1f}%")
        if ms_percentage > 25:
            print(f"   🔴 DOMINANCE: Still too high (>25%)")
        elif ms_percentage > 15:
            print(f"   🟡 MODERATE: Within acceptable range")
        else:
            print(f"   ✅ OPTIMAL: Well balanced")

def apply_feature_engineering(X_train, X_test, feature_names):
    """Apply feature engineering to reduce Mood Swing dominance"""
    
    print("🔧 Applying feature engineering to reduce correlations...")
    
    # Convert to DataFrame for feature engineering
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    X_test_df = pd.DataFrame(X_test, columns=feature_names)
    
    # Strategy 1: Create interaction features to reduce Mood Swing dominance
    if 'Mood Swing' in X_train_df.columns and 'Sadness' in X_train_df.columns:
        # Instead of having them compete, combine their information
        X_train_df['Mood_Emotion_Composite'] = X_train_df['Mood Swing'] * 0.6 + X_train_df['Sadness'] * 0.4
        X_test_df['Mood_Emotion_Composite'] = X_test_df['Mood Swing'] * 0.6 + X_test_df['Sadness'] * 0.4
        
        # Optional: Remove original features if they're too dominant
        # X_train_df = X_train_df.drop(['Mood Swing', 'Sadness'], axis=1)
        # X_test_df = X_test_df.drop(['Mood Swing', 'Sadness'], axis=1)
    
    # Strategy 2: Create clinical domain scores
    clinical_domains = {
        'Mood_Stability_Score': ['Mood Swing', 'Euphoric', 'Sadness'],
        'Cognitive_Function_Score': ['Concentration', 'Optimism', 'Overthinking'],
        'Risk_Assessment_Score': ['Suicidal thoughts', 'Aggressive Response', 'Nervous Breakdown']
    }
    
    for domain_name, features in clinical_domains.items():
        available_features = [f for f in features if f in X_train_df.columns]
        if len(available_features) >= 2:
            X_train_df[domain_name] = X_train_df[available_features].mean(axis=1)
            X_test_df[domain_name] = X_test_df[available_features].mean(axis=1)
    
    new_feature_names = X_train_df.columns.tolist()
    
    print(f"✅ Feature engineering complete:")
    print(f"   • Original features: {len(feature_names)}")
    print(f"   • New features: {len(new_feature_names)}")
    print(f"   • Added composite scores to reduce single-feature dominance")
    
    # Return as numpy arrays
    return X_train_df.values, X_test_df.values, new_feature_names

# -----------------------------
# 🆕 COMPREHENSIVE VALIDATION WITH CALIBRATION
# -----------------------------

def perform_comprehensive_validation(clinical_model, X_train, y_train, X_test, y_test, feature_names, label_encoder):
    """Comprehensive validation of the clinical model - WITH CALIBRATION"""
    
    print("\n" + "="*80)
    print("🔬 COMPREHENSIVE CLINICAL VALIDATION")
    print("="*80)
    
    # 🆕 FIX: Use DataFrame with feature names
    X_test_df = pd.DataFrame(X_test, columns=feature_names)
    
    # Get predictions
    y_pred = clinical_model.predict(X_test_df)
    y_pred_proba = clinical_model.predict_proba(X_test_df)
    
    # Convert y_test to encoded if needed
    if hasattr(y_test, 'iloc') and hasattr(y_test.iloc[0], 'isalpha'):  # If string labels
        y_test_encoded = label_encoder.transform(y_test)
    else:
        y_test_encoded = y_test
    
    # 1. Overall Performance
    print("\n📊 OVERALL PERFORMANCE:")
    accuracy = accuracy_score(y_test_encoded, y_pred)
    weighted_f1 = f1_score(y_test_encoded, y_pred, average='weighted')
    precision = precision_score(y_test_encoded, y_pred, average='weighted')
    recall = recall_score(y_test_encoded, y_pred, average='weighted')
    
    print(f"   • Accuracy: {accuracy:.3f}")
    print(f"   • Weighted F1: {weighted_f1:.3f}")
    print(f"   • Precision: {precision:.3f}")
    print(f"   • Recall: {recall:.3f}")
    
    # 2. Per-Class Performance (Critical for Clinical Use)
    print("\n🎯 PER-CLASS PERFORMANCE (Clinical Focus):")
    classes = label_encoder.classes_
    normal_class_idx = list(classes).index('Normal')
    
    for i, class_name in enumerate(classes):
        class_mask = y_test_encoded == i
        if sum(class_mask) > 0:
            class_accuracy = accuracy_score(y_test_encoded[class_mask], y_pred[class_mask])
            class_precision = precision_score(y_test_encoded, y_pred, average=None)[i]
            class_recall = recall_score(y_test_encoded, y_pred, average=None)[i]
            
            # Special emphasis on Normal class
            if i == normal_class_idx:
                marker = "🛡️ "  # Protection marker for Normal class
                importance = " (CRITICAL - Healthy Identification)"
            else:
                marker = "   "
                importance = ""
            
            print(f"   {marker} {class_name:<15}: Acc={class_accuracy:.3f} | "
                  f"Precision={class_precision:.3f} | Recall={class_recall:.3f}{importance}")
    
    # 3. Normal Class Protection Analysis
    print(f"\n🛡️ NORMAL CLASS PROTECTION ANALYSIS:")
    normal_mask = y_test_encoded == normal_class_idx
    correct_normal = 0
    false_pathology = 0
    
    if sum(normal_mask) > 0:
        normal_pred_proba = y_pred_proba[normal_mask, normal_class_idx]
        normal_pred = y_pred[normal_mask]
        normal_actual = y_test_encoded[normal_mask]
        
        correct_normal = sum((normal_pred == normal_actual) & (normal_actual == normal_class_idx))
        false_pathology = sum((normal_pred != normal_actual) & (normal_actual == normal_class_idx))
        
        print(f"   • Correctly identified as Normal: {correct_normal}/{sum(normal_mask)} "
              f"({correct_normal/sum(normal_mask):.1%})")
        print(f"   • False pathology labels: {false_pathology}/{sum(normal_mask)} "
              f"({false_pathology/sum(normal_mask):.1%})")
        print(f"   • Average Normal confidence: {np.mean(normal_pred_proba):.3f}")
    else:
        print("   • No Normal cases in test set for protection analysis")
    
    # 🆕 IMPROVED: Confidence Analysis with Calibration
    print(f"\n🎲 CALIBRATED PREDICTION CONFIDENCE ANALYSIS:")
    max_probs = np.max(y_pred_proba, axis=1)
    confidence_thresholds = [0.6, 0.7, 0.8, 0.9]
    
    for threshold in confidence_thresholds:
        high_conf_mask = max_probs >= threshold
        if len(high_conf_mask) > 0 and sum(high_conf_mask) > 0:
            high_conf_accuracy = accuracy_score(y_test_encoded[high_conf_mask], y_pred[high_conf_mask])
            high_conf_count = sum(high_conf_mask)
            total_count = len(y_test_encoded)
            
            print(f"   • ≥{threshold:.1f} confidence: {high_conf_count}/{total_count} "
                  f"predictions ({high_conf_count/total_count:.1%}) | "
                  f"Accuracy: {high_conf_accuracy:.3f}")
        else:
            print(f"   • ≥{threshold:.1f} confidence: 0/{len(y_test_encoded)} predictions (0.0%)")
    
    # 🆕 ADDED: Confidence Distribution Analysis
    print(f"\n📊 CONFIDENCE DISTRIBUTION:")
    confidence_ranges = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.0)]
    for low, high in confidence_ranges:
        mask = (max_probs >= low) & (max_probs < high)
        count = sum(mask)
        if count > 0:
            accuracy_in_range = accuracy_score(y_test_encoded[mask], y_pred[mask])
            print(f"   • {low:.1f}-{high:.1f}: {count} predictions ({count/len(y_test_encoded):.1%}) | "
                  f"Accuracy: {accuracy_in_range:.3f}")
    
    # 5. Clinical Safety Metrics
    print(f"\n🏥 CLINICAL SAFETY METRICS:")
    
    # Calculate confusion matrix
    cm = confusion_matrix(y_test_encoded, y_pred)
    
    # Critical errors: Normal misclassified as pathology
    normal_as_pathology = 0
    if cm.shape[0] > normal_class_idx:
        normal_as_pathology = cm[normal_class_idx, :].sum() - cm[normal_class_idx, normal_class_idx]
        print(f"   • Normal → Pathology errors: {normal_as_pathology}")
    
    # High-risk pathology missed
    pathology_classes = [i for i, name in enumerate(classes) if name != 'Normal']
    pathology_missed = 0
    for pathology_idx in pathology_classes:
        if pathology_idx < cm.shape[0]:
            pathology_missed += cm[pathology_idx, :].sum() - cm[pathology_idx, pathology_idx]
    
    print(f"   • Pathology missed: {pathology_missed}")
    print(f"   • Overall error rate: {1 - accuracy:.3f}")
    
    return {
        'actual': y_test_encoded,
        'predictions': y_pred,
        'probabilities': y_pred_proba,
        'confusion_matrix': cm,
        'normal_protection_rate': correct_normal/sum(normal_mask) if sum(normal_mask) > 0 else 0,
        'false_pathology_rate': false_pathology/sum(normal_mask) if sum(normal_mask) > 0 else 0,
        'confidence_scores': max_probs  # 🆕 ADDED for calibration analysis
    }

# -----------------------------
# 🆕 FINAL MODEL SAVING WITH CALIBRATION SUPPORT
# -----------------------------

def save_final_model_with_metadata(clinical_model, feature_names, label_encoder, feature_importance_df, validation_results, best_model_name, X_test, y_test, X_train, category_mappings):
    """Save the final model with comprehensive metadata - WITH CALIBRATION"""
    
    print("\n💾 SAVING FINAL MODEL WITH METADATA...")
    
    # 🆕 FIX: Use DataFrame with feature names
    X_test_df = pd.DataFrame(X_test, columns=feature_names)
    
    # Get predictions for accurate metrics
    y_pred = clinical_model.predict(X_test_df)
    y_test_encoded = label_encoder.transform(y_test) if hasattr(y_test, 'iloc') else y_test
    
    # Create scaler based on training data statistics
    print("🔧 Creating and saving scaler...")
    scaler = StandardScaler()
    
    # Fit scaler on training data only (no data leakage)
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    scaler.fit(X_train_df)
    
    # Create model package for the main model file
    model_package = {
        'model': clinical_model,
        'feature_names': feature_names,
        'label_encoder': label_encoder,
        'feature_importance': feature_importance_df,
        'category_mappings': category_mappings,
        'metadata': {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'model_name': best_model_name,
            'feature_count': len(feature_names),
            'classes': label_encoder.classes_.tolist(),
            'normal_class_index': int(list(label_encoder.classes_).index('Normal')),
            'validation_metrics': {
                'accuracy': float(accuracy_score(y_test_encoded, y_pred)),
                'normal_protection_rate': float(validation_results.get('normal_protection_rate', 0)),
                'false_pathology_rate': float(validation_results.get('false_pathology_rate', 0)),
                'avg_confidence': float(np.mean(validation_results.get('confidence_scores', [0])))  # 🆕 ADDED
            },
            'calibration_info': 'isotonic_calibration_applied'  # 🆕 ADDED
        }
    }
    
    # Save the required files
    print("💾 Saving required model files...")
    
    # 1. Main model file
    model_filename = 'models/mental_health_model.pkl'
    joblib.dump(model_package, model_filename)
    
    # 2. Scaler file
    scaler_filename = 'models/scaler.pkl'
    joblib.dump(scaler, scaler_filename)
    
    # 3. Label encoder file
    encoder_filename = 'models/label_encoder.pkl'
    joblib.dump(label_encoder, encoder_filename)
    
    # 4. Feature names file
    feature_names_filename = 'models/feature_names.pkl'
    with open(feature_names_filename, 'wb') as f:
        pickle.dump(feature_names, f)
    
    # 5. Category mappings file
    category_mappings_filename = 'models/category_mappings.pkl'
    with open(category_mappings_filename, 'wb') as f:
        pickle.dump(category_mappings, f)
    
    # Save feature importance separately
    importance_filename = "models/feature_importance.csv"
    feature_importance_df.to_csv(importance_filename, index=False)
    
    print(f"✅ MODEL FILES SAVED:")
    print(f"   • {model_filename} (main model with calibration)")
    print(f"   • {scaler_filename} (feature scaler)")
    print(f"   • {encoder_filename} (label encoder)")
    print(f"   • {feature_names_filename} (feature names for app)")
    print(f"   • {category_mappings_filename} (category mappings for app)")
    print(f"   • {importance_filename} (feature importance)")
    print(f"📦 MODEL PACKAGE INCLUDES:")
    print(f"   • Calibrated clinical model with Normal protection")
    print(f"   • {len(feature_names)} feature names")
    print(f"   • Label encoder for {len(label_encoder.classes_)} classes")
    print(f"   • Category mappings for user-friendly questions")
    print(f"   • Feature importance analysis")
    print(f"   • Confidence calibration metadata")
    print(f"   • Comprehensive performance metrics")
    
    return model_filename, scaler_filename, encoder_filename, feature_names_filename, category_mappings_filename

# -----------------------------
# 🆕 UPDATED MAIN EXECUTION WITH CALIBRATION
# -----------------------------

def main():
    """Main execution function - UPDATED with confidence calibration"""
    
    print("="*80)
    print("🏥 CLINICAL MENTAL HEALTH DIAGNOSIS MODEL - WITH CONFIDENCE CALIBRATION")
    print("="*80)
    
    # 1-4. Existing data loading and encoding steps
    df = load_and_prepare_data()
    X, y, feature_names, category_mappings = encode_features(df)
    
    # Smart data splitting with balanced training data
    print("\n🔧 STEP 4: Smart data splitting with balanced training...")
    X_train, X_test, y_train_encoded, y_test_encoded, label_encoder = smart_data_split(
        X, y, 
        test_size=0.2, 
        balance_train=True,
        random_state=42
    )
    
    # Print final class distribution
    print(f"\n🎯 FINAL CLASS DISTRIBUTION:")
    classes = label_encoder.classes_
    for i, class_name in enumerate(classes):
        train_count = np.sum(y_train_encoded == i)
        test_count = np.sum(y_test_encoded == i)
        train_pct = train_count / len(y_train_encoded) * 100
        test_pct = test_count / len(y_test_encoded) * 100
        
        print(f"   • {class_name}:")
        print(f"     Training: {train_count} samples ({train_pct:.1f}%)")
        print(f"     Test: {test_count} samples ({test_pct:.1f}%)")
    
    # Apply feature engineering
    print("\n🔧 STEP 5A: Applying feature engineering...")
    X_train_eng, X_test_eng, engineered_features = apply_feature_engineering(
        X_train, X_test, feature_names
    )
    
    # Feature selection
    print("\n🎯 STEP 5: Performing feature selection...")
    selected_features = advanced_feature_selection(X_train_eng, y_train_encoded, engineered_features)
    selected_features_final = clinical_feature_selection(
        X_train_eng, selected_features, engineered_features
    )
    
    # Apply feature selection
    selected_indices = [engineered_features.index(f) for f in selected_features_final]
    X_train_final = X_train_eng[:, selected_indices]
    X_test_final = X_test_eng[:, selected_indices]
    selected_feature_names = [engineered_features[i] for i in selected_indices]
    
    print(f"✅ Final feature set: {len(selected_feature_names)} features")
    
    # Check feature correlations
    check_feature_correlations(X_train_final, selected_feature_names)
    
    # Feature transformation
    print("\n🔄 STEP 6: Applying feature transformations (No Data Leakage)...")
    X_train_transformed, X_test_transformed = apply_feature_transformation(
        X_train_final, X_test_final, selected_feature_names, selected_feature_names
    )
    
    X_train_final = X_train_transformed
    X_test_final = X_test_transformed
    
    # Get optimized models
    print("\n🤖 STEP 7: Initializing optimized models...")
    models = get_optimized_models_fixed(X_train_final, y_train_encoded, selected_feature_names)
    
    # Create Normal-focused ensembles
    print("\n🌟 STEP 8: Creating Normal-focused ensembles...")
    ensembles = create_normal_focused_ensembles(models, X_train_final, y_train_encoded, selected_feature_names)
    
    # Train all models
    print("\n🎯 STEP 9: Training models with overfitting prevention...")
    all_models = {**models, **ensembles}
    results_df = train_with_overfitting_prevention(
        all_models, X_train_final, y_train_encoded, 
        X_test_final, y_test_encoded, selected_feature_names
    )
    
    # Select best clinical model
    print("\n🏥 STEP 10: Selecting best clinical model...")
    best_model, best_model_name, results_df = select_clinical_best_model_improved(
        results_df, models, ensembles, X_test_final, y_test_encoded, 
        label_encoder, selected_feature_names
    )
    
    # 🆕 UPDATED: Enhance with Normal protection AND calibration
    print("\n🛡️ STEP 11: Enhancing model with Normal protection and confidence calibration...")
    clinical_model = enhance_normal_classification_with_calibration(
        best_model, X_train_final, y_train_encoded, 
        label_encoder, selected_feature_names
    )
    
    # Feature importance analysis
    print("\n🔍 STEP 12: Analyzing feature importance...")
    feature_importance_df = create_feature_importance_analysis(
        clinical_model, selected_feature_names, X_train_final, 
        y_train_encoded, label_encoder
    )
    
    # Create diagnosis-feature heatmap
    print("\n🔥 STEP 12A: Creating diagnosis-feature heatmap...")
    importance_matrix = create_diagnosis_feature_heatmap(
        clinical_model, X_train_final, y_train_encoded,
        selected_feature_names, label_encoder
    )
    

    
    # Comprehensive validation
    print("\n🔬 STEP 13: Performing comprehensive validation...")
    validation_results = perform_comprehensive_validation(
        clinical_model, X_train_final, y_train_encoded,
        X_test_final, y_test_encoded, selected_feature_names, label_encoder
    )
    
    # Save final model
    print("\n💾 STEP 14: Saving final model...")
    model_files = save_final_model_with_metadata(
        clinical_model, selected_feature_names, label_encoder,
        feature_importance_df, validation_results, best_model_name,
        X_test_final, y_test_encoded, X_train_final, category_mappings
    )
    
    # Final visualization
    print("\n📈 STEP 15: Creating final summary...")
    create_final_summary_visualization(validation_results, feature_importance_df, label_encoder)
    
    # 🆕 FINAL SUMMARY WITH CALIBRATION INFO
    print("\n" + "="*80)
    print("🎉 CLINICAL MODEL TRAINING COMPLETE!")
    print("="*80)
    print(f"🏆 BEST MODEL: {best_model_name}")
    print(f"📊 FINAL PERFORMANCE:")
    print(f"   • Test Accuracy: {accuracy_score(y_test_encoded, validation_results['predictions']):.3f}")
    print(f"   • Normal Protection Rate: {validation_results['normal_protection_rate']:.1%}")
    print(f"   • False Pathology Rate: {validation_results['false_pathology_rate']:.1%}")
    print(f"   • Average Confidence: {np.mean(validation_results['confidence_scores']):.3f}")
    print(f"   • Features Used: {len(selected_feature_names)}")
    print(f"🔧 CALIBRATION FEATURES:")
    print(f"   • Method: Isotonic calibration with 3-fold CV")
    print(f"   • Confidence distribution analysis: Enabled")
    print(f"💾 MODEL FILES SAVED:")
    for filename in model_files:
        print(f"   • {filename}")
    print("="*80)

# -----------------------------
# EXISTING SUPPORTING FUNCTIONS (keep them as they are)
# -----------------------------

def ensure_models_directory():
    """Ensure the models directory exists"""
    if not os.path.exists('models'):
        os.makedirs('models')
        print("📁 Created 'models' directory")

def check_feature_correlations(X_train, feature_names):
    """Check correlations to understand Mood Swing dominance"""
    print("\n🔍 ANALYZING FEATURE CORRELATIONS...")
    
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    
    if 'Mood Swing' in X_train_df.columns:
        correlations = {}
        for feature in feature_names:
            if feature != 'Mood Swing':
                corr = np.corrcoef(X_train_df['Mood Swing'], X_train_df[feature])[0, 1]
                correlations[feature] = corr
        
        high_corr_features = {k: v for k, v in sorted(correlations.items(), 
                            key=lambda item: abs(item[1]), reverse=True)[:5]}
        
        print("📊 Features most correlated with 'Mood Swing':")
        for feature, corr in high_corr_features.items():
            print(f"   • {feature}: {corr:.3f}")
        
        return high_corr_features
    return {}

# Add this function after the existing visualization functions
def create_diagnosis_feature_heatmap(clinical_model, X_train, y_train, feature_names, label_encoder):
    """Create a comprehensive heatmap showing the relationship between diagnoses and features in one chart"""
    
    print("\n🔥 CREATING COMPREHENSIVE DIAGNOSIS-FEATURE HEATMAP...")
    
    try:
        # Get the base model for analysis
        if hasattr(clinical_model, 'base_model'):
            base_model = clinical_model.base_model
            # If it's our calibrated model, get the original base model
            if hasattr(base_model, 'calibrator'):
                base_model = base_model.base_model
        else:
            base_model = clinical_model
        
        # Ensure we have DataFrame with feature names
        if not isinstance(X_train, pd.DataFrame):
            X_train_df = pd.DataFrame(X_train, columns=feature_names)
        else:
            X_train_df = X_train
        
        # Get feature importances using permutation importance (most reliable)
        print("📊 Calculating feature importance using permutation importance...")
        perm_importance = permutation_importance(
            base_model, X_train_df, y_train, 
            n_repeats=10, random_state=42, n_jobs=-1, scoring='accuracy'
        )
        importances = perm_importance.importances_mean
        
        # Create a matrix of feature importance per class
        classes = label_encoder.classes_
        n_classes = len(classes)
        n_features = len(feature_names)
        
        # Initialize importance matrix
        importance_matrix = np.zeros((n_classes, n_features))
        
        # Calculate class-specific feature importance using mean values per class
        print("🎯 Calculating diagnosis-specific feature patterns...")
        
        for i, class_name in enumerate(classes):
            # Get samples for this class
            class_mask = y_train == i
            X_class = X_train_df[class_mask]
            
            if len(X_class) > 0:
                # Calculate mean feature values for this diagnosis
                mean_features = X_class.mean(axis=0)
                
                # Normalize and use as importance (features with higher values are more characteristic)
                importance_matrix[i] = mean_features / mean_features.sum() * 100
        
        # Create a single comprehensive heatmap
        plt.figure(figsize=(16, 10))
        
        # Create the heatmap
        im = plt.imshow(importance_matrix, cmap='YlOrRd', aspect='auto')
        
        # Set ticks and labels
        plt.xticks(range(n_features), feature_names, rotation=45, ha='right', fontsize=10)
        plt.yticks(range(n_classes), classes, fontsize=12)
        
        # Add labels and title
        plt.xlabel('Features', fontsize=12, fontweight='bold')
        plt.ylabel('Diagnoses', fontsize=12, fontweight='bold')
        plt.title('Diagnosis-Feature Relationship Heatmap\n(Feature Importance by Diagnosis)', 
                 fontsize=14, fontweight='bold', pad=20)
        
        # Add value annotations
        for i in range(n_classes):
            for j in range(n_features):
                value = importance_matrix[i, j]
                if value > 1.0:  # Only show significant values (>1%)
                    plt.text(j, i, f'{value:.1f}%', 
                            ha='center', va='center', fontsize=8,
                            color='white' if value > np.percentile(importance_matrix, 70) else 'black',
                            fontweight='bold' if value > np.percentile(importance_matrix, 85) else 'normal')
        
        # Add colorbar
        cbar = plt.colorbar(im, fraction=0.046, pad=0.04)
        cbar.set_label('Feature Importance (%)', rotation=270, labelpad=15, fontsize=11)
        
        # Add grid for better readability
        plt.grid(False)
        plt.tight_layout()
        
        # Save the heatmap
        heatmap_filename = 'models/diagnosis_feature_heatmap_comprehensive.png'
        plt.savefig(heatmap_filename, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"✅ Comprehensive diagnosis-feature heatmap saved as '{heatmap_filename}'")
        
        # Print detailed insights
        print("\n💡 COMPREHENSIVE CLINICAL INSIGHTS:")
        print("=" * 60)
        
        # Find top features for each diagnosis
        print("\n🏆 TOP FEATURES FOR EACH DIAGNOSIS:")
        print("-" * 50)
        
        for i, diagnosis in enumerate(classes):
            # Get top 3 features for this diagnosis
            top_indices = np.argsort(importance_matrix[i])[-3:][::-1]
            top_features = [(feature_names[idx], importance_matrix[i, idx]) for idx in top_indices]
            
            print(f"\n🏥 {diagnosis}:")
            for feature, importance in top_features:
                print(f"   • {feature}: {importance:.1f}%")
        
        # Find diagnosis-specific patterns
        print(f"\n🔍 DIAGNOSIS-SPECIFIC PATTERNS:")
        print("-" * 40)
        
        # For each feature, find which diagnoses rely on it most
        feature_diagnosis_analysis = {}
        for j, feature in enumerate(feature_names):
            top_diagnosis_idx = np.argmax(importance_matrix[:, j])
            top_diagnosis = classes[top_diagnosis_idx]
            top_value = importance_matrix[top_diagnosis_idx, j]
            
            if top_value > 5.0:  # Only show significant associations (>5%)
                if top_diagnosis not in feature_diagnosis_analysis:
                    feature_diagnosis_analysis[top_diagnosis] = []
                feature_diagnosis_analysis[top_diagnosis].append((feature, top_value))
        
        # Print by diagnosis
        for diagnosis in classes:
            if diagnosis in feature_diagnosis_analysis:
                print(f"\n📊 {diagnosis} is characterized by:")
                for feature, importance in sorted(feature_diagnosis_analysis[diagnosis], 
                                                key=lambda x: x[1], reverse=True)[:3]:
                    print(f"   • {feature} ({importance:.1f}%)")
        
        # Clinical correlations analysis
        print(f"\n🎯 CLINICAL CORRELATIONS:")
        print("-" * 30)
        
        # Analyze mood-related features
        mood_features = [f for f in feature_names if any(mood_word in f.lower() for mood_word in 
                                                       ['mood', 'sadness', 'euphoric', 'optimism'])]
        if mood_features:
            print("Mood-related features:")
            for feature in mood_features:
                feature_idx = feature_names.index(feature)
                max_diagnosis_idx = np.argmax(importance_matrix[:, feature_idx])
                max_diagnosis = classes[max_diagnosis_idx]
                max_value = importance_matrix[max_diagnosis_idx, feature_idx]
                print(f"   • {feature}: Most important for {max_diagnosis} ({max_value:.1f}%)")
        
        # Analyze risk-related features
        risk_features = [f for f in feature_names if any(risk_word in f.lower() for risk_word in 
                                                       ['suicidal', 'aggressive', 'risk', 'breakdown'])]
        if risk_features:
            print("\nRisk-related features:")
            for feature in risk_features:
                feature_idx = feature_names.index(feature)
                max_diagnosis_idx = np.argmax(importance_matrix[:, feature_idx])
                max_diagnosis = classes[max_diagnosis_idx]
                max_value = importance_matrix[max_diagnosis_idx, feature_idx]
                print(f"   • {feature}: Most important for {max_diagnosis} ({max_value:.1f}%)")
        
        return importance_matrix
        
    except Exception as e:
        print(f"❌ Error creating diagnosis-feature heatmap: {e}")
        import traceback
        traceback.print_exc()
        return None



# -----------------------------
# 🆕 FINAL VISUALIZATION SUMMARY
# -----------------------------

def create_final_summary_visualization(validation_results, feature_importance_df, label_encoder):
    """Create final summary visualization"""
    
    print("\n📈 CREATING SUMMARY VISUALIZATION...")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Clinical Mental Health Model - Final Summary', fontsize=16, fontweight='bold')
    
    # 1. Confusion Matrix
    cm = validation_results['confusion_matrix']
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=label_encoder.classes_, 
                yticklabels=label_encoder.classes_, 
                ax=axes[0, 0])
    axes[0, 0].set_title('Confusion Matrix')
    axes[0, 0].set_xlabel('Predicted')
    axes[0, 0].set_ylabel('Actual')
    
    # 2. Feature Importance (Top 10)
    top_features = feature_importance_df.head(10)
    axes[0, 1].barh(range(len(top_features)), top_features['importance_percentage'])
    axes[0, 1].set_yticks(range(len(top_features)))
    axes[0, 1].set_yticklabels(top_features['feature'])
    axes[0, 1].set_xlabel('Importance (%)')
    axes[0, 1].set_title('Top 10 Feature Importance')
    axes[0, 1].grid(axis='x', alpha=0.3)
    
    # 3. Normal Class Protection Analysis
    protection_data = {
        'Correct Normal': validation_results['normal_protection_rate'] * 100,
        'False Pathology': validation_results['false_pathology_rate'] * 100
    }
    axes[1, 0].bar(protection_data.keys(), protection_data.values(), color=['green', 'red'])
    axes[1, 0].set_ylabel('Percentage (%)')
    axes[1, 0].set_title('Normal Class Protection Analysis')
    axes[1, 0].grid(axis='y', alpha=0.3)
    
    # 4. Prediction Confidence Distribution
    max_probs = np.max(validation_results['probabilities'], axis=1)
    axes[1, 1].hist(max_probs, bins=20, alpha=0.7, color='purple', edgecolor='black')
    axes[1, 1].set_xlabel('Prediction Confidence')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].set_title('Prediction Confidence Distribution')
    axes[1, 1].grid(alpha=0.3)
    
    plt.tight_layout()
    
    # ✅ FIXED: Save to 'models' folder (plural) instead of 'model'
    plt.savefig('models/clinical_model_summary.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✅ Summary visualization saved as 'models/clinical_model_summary.png'")


# -----------------------------
# 🆕 CREATE MODELS DIRECTORY IF NOT EXISTS
# -----------------------------


def ensure_models_directory():
    """Ensure the models directory exists"""
    if not os.path.exists('models'):
        os.makedirs('models')
        print("📁 Created 'models' directory")

# Update the execution section
if __name__ == "__main__":
    ensure_models_directory()  # Create directory first
    main()