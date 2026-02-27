# test_pipeline.py
import requests
import json
import pandas as pd
from datetime import datetime
import csv

def load_test_cases_from_csv(csv_file='test_cases.csv'):
    """Load test cases from CSV file"""
    test_cases = {}
    
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded {len(df)} test cases from {csv_file}")
        
        for _, row in df.iterrows():
            test_case_name = row['test_case']
            
            # Extract responses from the row
            responses = {}
            for col in df.columns:
                if col not in ['test_case', 'description', 'expected_diagnosis']:
                    responses[col] = row[col]
            
            test_cases[test_case_name] = {
                'description': row['description'],
                'expected_diagnosis': row['expected_diagnosis'],
                'responses': responses
            }
            
    except Exception as e:
        print(f"❌ Error loading test cases from CSV: {e}")
        # Fallback to default test cases
        test_cases = create_fallback_test_cases()
    
    return test_cases

def create_fallback_test_cases():
    """Create fallback test cases if CSV loading fails"""
    print("⚠️ Using fallback test cases")
    
    return {
        "normal_healthy_balanced": {
            "description": "Healthy individual with balanced responses",
            "expected_diagnosis": "Normal",
            "responses": {
                "Mood Swing": "NO", "Sadness": "Sometimes", "Euphoric": "Seldom",
                "Sleep disorder": "Sometimes", "Exhausted": "Sometimes", 
                "Suicidal thoughts": "NO", "Aggressive Response": "NO", 
                "Overthinking": "NO", "Nervous Breakdown": "NO", "Anorexia": "NO",
                "Authority Respect": "YES", "Try-Explanation": "YES", 
                "Ignore & Move-On": "NO", "Admit Mistakes": "YES",
                "Concentration": "Good concentration", "Optimism": "Optimistic",
                "Sexual Activity": "High interest"
            }
        },
        "bipolar1_manic_dominant": {
            "description": "Bipolar Type-1 with strong manic features",
            "expected_diagnosis": "Bipolar Type-1",
            "responses": {
                "Mood Swing": "YES", "Sadness": "Sometimes", "Euphoric": "Most-Often",
                "Sleep disorder": "Usually", "Exhausted": "Seldom", 
                "Suicidal thoughts": "NO", "Aggressive Response": "YES", 
                "Overthinking": "YES", "Nervous Breakdown": "NO", "Anorexia": "NO",
                "Authority Respect": "NO", "Try-Explanation": "YES", 
                "Ignore & Move-On": "NO", "Admit Mistakes": "NO",
                "Concentration": "Poor concentration", "Optimism": "Extremely optimistic",
                "Sexual Activity": "Very high interest"
            }
        }
    }

def run_diagnosis_test_suite(test_cases, api_url='http://localhost:5001/api/predict'):
    """Run comprehensive test suite"""
    print("🎯 COMPREHENSIVE DIAGNOSIS TEST SUITE")
    print("=" * 70)
    
    results = []
    diagnosis_stats = {}
    
    for case_name, test_case in test_cases.items():
        print(f"\n🧪 {case_name}")
        print(f"   Description: {test_case['description']}")
        print(f"   Expected: {test_case['expected_diagnosis']}")
        print("-" * 50)
        
        try:
            # Test prediction
            pred_response = requests.post(api_url,
                                        json={'responses': test_case['responses']},
                                        timeout=10)
            
            if pred_response.status_code == 200:
                pred_result = pred_response.json()
                actual_diagnosis = pred_result['primary_diagnosis']
                confidence = pred_result['confidence_percentage']
                safety_warnings = len(pred_result['processing_details']['clinical_safety_warnings'])
                
                # Check if diagnosis matches expected
                matches_expected = actual_diagnosis == test_case['expected_diagnosis']
                status_icon = "✅" if matches_expected else "⚠️"
                
                # Collect results
                case_result = {
                    'test_case': case_name,
                    'description': test_case['description'],
                    'expected': test_case['expected_diagnosis'],
                    'actual': actual_diagnosis,
                    'confidence': confidence,
                    'matches_expected': matches_expected,
                    'safety_warnings': safety_warnings,
                    'status': 'SUCCESS'
                }
                
                results.append(case_result)
                
                # Update diagnosis statistics
                if actual_diagnosis not in diagnosis_stats:
                    diagnosis_stats[actual_diagnosis] = {'count': 0, 'total_confidence': 0}
                diagnosis_stats[actual_diagnosis]['count'] += 1
                diagnosis_stats[actual_diagnosis]['total_confidence'] += confidence
                
                print(f"{status_icon} Actual: {actual_diagnosis}")
                print(f"📊 Confidence: {confidence:.1f}%")
                print(f"🛡️ Safety Warnings: {safety_warnings}")
                print(f"🎯 Match: {'YES' if matches_expected else 'NO'}")
                
            else:
                print(f"❌ Prediction failed: {pred_response.status_code}")
                results.append({
                    'test_case': case_name,
                    'description': test_case['description'],
                    'status': 'FAILED',
                    'error': f"HTTP {pred_response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append({
                'test_case': case_name,
                'description': test_case['description'],
                'status': 'FAILED',
                'error': str(e)
            })
    
    return results, diagnosis_stats

def print_detailed_summary(results, diagnosis_stats):
    """Print comprehensive test summary"""
    print("\n" + "=" * 70)
    print("📊 DETAILED TEST SUMMARY")
    print("=" * 70)
    
    # Overall statistics
    total_tests = len(results)
    successful_tests = len([r for r in results if r['status'] == 'SUCCESS'])
    matches_expected = len([r for r in results if r.get('matches_expected', False)])
    
    print(f"\n📈 OVERALL PERFORMANCE:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    print(f"   Matched Expected: {matches_expected}/{successful_tests} ({matches_expected/successful_tests*100:.1f}%)")
    
    # Diagnosis distribution
    print(f"\n🎯 DIAGNOSIS DISTRIBUTION:")
    for diagnosis, stats in diagnosis_stats.items():
        avg_confidence = stats['total_confidence'] / stats['count']
        print(f"   • {diagnosis}: {stats['count']} cases (avg confidence: {avg_confidence:.1f}%)")
    
    # Test case breakdown
    print(f"\n🧪 TEST CASE BREAKDOWN:")
    for result in results:
        if result['status'] == 'SUCCESS':
            status_icon = "✅" if result['matches_expected'] else "⚠️"
            print(f"   {status_icon} {result['test_case']}:")
            print(f"      Expected: {result['expected']} → Actual: {result['actual']}")
            print(f"      Confidence: {result['confidence']:.1f}% | Safety: {result['safety_warnings']} warnings")
        else:
            print(f"   ❌ {result['test_case']}: FAILED - {result.get('error', 'Unknown error')}")

def save_results_to_csv(results, filename=None):
    """Save test results to CSV file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['test_case', 'description', 'expected', 'actual', 
                         'confidence', 'matches_expected', 'safety_warnings', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        print(f"✅ Results saved to {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving results to CSV: {e}")
        return None

def analyze_diagnosis_patterns(results):
    """Analyze patterns in diagnosis predictions"""
    print(f"\n🔍 DIAGNOSIS PATTERN ANALYSIS")
    print("=" * 50)
    
    # Group by actual diagnosis
    by_diagnosis = {}
    for result in results:
        if result['status'] == 'SUCCESS':
            diagnosis = result['actual']
            if diagnosis not in by_diagnosis:
                by_diagnosis[diagnosis] = []
            by_diagnosis[diagnosis].append(result)
    
    for diagnosis, cases in by_diagnosis.items():
        confidences = [case['confidence'] for case in cases]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)
        
        print(f"\n🏥 {diagnosis}:")
        print(f"   Cases: {len(cases)}")
        print(f"   Confidence: {avg_confidence:.1f}% (range: {min_confidence:.1f}%-{max_confidence:.1f}%)")
        
        # Show case distribution
        expected_counts = {}
        for case in cases:
            expected = case['expected']
            expected_counts[expected] = expected_counts.get(expected, 0) + 1
        
        print(f"   Expected patterns: {dict(expected_counts)}")

if __name__ == "__main__":
    # Load test cases from CSV
    test_cases = load_test_cases_from_csv('test_cases.csv')
    
    print("🚀 COMPREHENSIVE DIAGNOSIS TESTING PIPELINE")
    print(f"Testing {len(test_cases)} cases across all diagnosis categories")
    print("=" * 70)
    
    # Run comprehensive diagnosis tests
    results, diagnosis_stats = run_diagnosis_test_suite(test_cases)
    
    # Print detailed summary
    print_detailed_summary(results, diagnosis_stats)
    
    # Analyze diagnosis patterns
    analyze_diagnosis_patterns(results)
    
    # Save results to CSV
    results_file = save_results_to_csv(results)
    
    # Final assessment
    successful_tests = len([r for r in results if r['status'] == 'SUCCESS'])
    matches_expected = len([r for r in results if r.get('matches_expected', False)])
    
    print(f"\n🎉 FINAL ASSESSMENT:")
    print(f"   Successful Tests: {successful_tests}/{len(results)}")
    print(f"   Expected Matches: {matches_expected}/{successful_tests}")
    print(f"   Diagnosis Coverage: {len(diagnosis_stats)}/4 diagnoses tested")
    
    accuracy = matches_expected / successful_tests if successful_tests > 0 else 0
    if accuracy >= 0.8:
        print("   🏆 MODEL PERFORMANCE: EXCELLENT")
    elif accuracy >= 0.6:
        print("   ✅ MODEL PERFORMANCE: GOOD") 
    elif accuracy >= 0.4:
        print("   ⚠️  MODEL PERFORMANCE: FAIR")
    else:
        print("   🔴 MODEL PERFORMANCE: NEEDS REVIEW")
    
    if results_file:
        print(f"   💾 Results saved to: {results_file}")