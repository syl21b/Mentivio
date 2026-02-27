# debug_preprocessing.py
import requests
import json

def debug_preprocessing():
    test_responses = {
        "Mood Swing": "NO", 
        "Sadness": "Sometimes", 
        "Euphoric": "Seldom",
        "Sleep disorder": "Sometimes", 
        "Exhausted": "Sometimes",
        "Suicidal thoughts": "NO", 
        "Aggressive Response": "NO", 
        "Nervous Breakdown": "NO",
        "Overthinking": "NO",
        "Anorexia": "NO",
        "Authority Respect": "YES", 
        "Try-Explanation": "YES", 
        "Ignore & Move-On": "NO", 
        "Admit Mistakes": "YES",
        "Concentration": "Good concentration", 
        "Optimism": "Optimistic",
        "Sexual Activity": "High interest"
    }
    
    print("🐛 DEBUG PREPROCESSING PIPELINE")
    print("=" * 60)
    
    try:
        response = requests.post('http://localhost:5001/api/debug-preprocessing',
                               json={'responses': test_responses},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            
            print("📊 INPUT ANALYSIS:")
            print(f"   Raw features: {result['input_analysis']['feature_names']}")
            
            print("\n🔧 ENCODING STAGE:")
            print(f"   Encoded features: {result['encoding_stage']['encoded_features']}")
            print(f"   Sample values: {list(result['encoding_stage']['encoded_values'].items())[:5]}")
            
            print("\n⚙️ FEATURE ENGINEERING STAGE:")
            print(f"   Engineered features: {result['engineering_stage']['engineered_features']}")
            print(f"   Composite features: {result['engineering_stage']['composite_features']}")
            
            print("\n✅ VALIDATION STAGE:")
            print(f"   Safety OK: {result['validation_stage']['safety_ok']}")
            print(f"   Warnings: {result['validation_stage']['safety_warnings']}")
            
            print("\n🎯 FINAL OUTPUT:")
            print(f"   Feature array length: {result['final_output']['feature_array_length']}")
            print(f"   Matches training: {result['final_output']['matches_training_features']}")
            print(f"   Missing in training: {result['final_output']['missing_in_training']}")
            print(f"   Extra in training: {result['final_output']['extra_in_training']}")
            
        else:
            print(f"❌ Debug failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Debug error: {e}")

if __name__ == "__main__":
    debug_preprocessing()