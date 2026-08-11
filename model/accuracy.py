import os
import glob
import predictor
from difflib import SequenceMatcher

def lcs_length(s1, s2):
    """計算 Longest Common Subsequence (LCS) 的長度"""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]

def lc_substring_length(s1, s2):
    """計算 Longest Common Substring 的長度"""
    match = SequenceMatcher(None, s1, s2).find_longest_match(0, len(s1), 0, len(s2))
    return match.size

def main():
    print("Initializing predictor...")
    predictor.initialize()
    
    # testing_dataset is located at the same level as the model folder
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    testing_dir = os.path.join(base_dir, 'testing_dataset')
    
    # Find all .txt files in the testing_dataset directory
    txt_files = glob.glob(os.path.join(testing_dir, '*.txt'))
    
    if not txt_files:
        print(f"No .txt files found in {testing_dir}")
        return
        
    total_count = 0
    total_subseq_acc = 0.0
    total_substr_acc = 0.0
    
    print(f"Found {len(txt_files)} file(s) for testing.")
    
    count = 0
    for file_path in txt_files:
        print(f"Evaluating file: {os.path.basename(file_path)}...")
        
        file_total_count = 0
        file_subseq_acc = 0.0
        file_substr_acc = 0.0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Remove only trailing newline characters, preserving spaces
                line = line.rstrip('\r\n')
                if not line:
                    continue
                
                # Split strictly by tab character
                parts = line.split('\t')
                if len(parts) >= 2:
                    
                    # Do not strip spaces, as they might be part of the data
                    input_string = parts[0]
                    label = parts[1]
                    
                    # Skip if label is empty to avoid division by zero
                    if len(label) == 0:
                        continue 
                    
                    try:
                        prediction = predictor.predict(input_string)
                        
                        # Calculate lengths for subsequence and substring
                        subseq_len = lcs_length(prediction, label)
                        substr_len = lc_substring_length(prediction, label)
                        
                        # Accuracy for this specific sentence
                        subseq_acc = subseq_len / len(label)
                        substr_acc = substr_len / len(label)
                        
                        # Accumulate accuracy for the current file
                        file_subseq_acc += subseq_acc
                        file_substr_acc += substr_acc
                        file_total_count += 1
                        
                    except Exception as e:
                        print(f"Error predicting '{input_string}': {e}")

        if file_total_count > 0:
            avg_subseq_acc = file_subseq_acc / file_total_count
            avg_substr_acc = file_substr_acc / file_total_count
            
            print("-" * 30)
            print(f"Results for: {os.path.basename(file_path)}")
            print(f"Total sentences evaluated: {file_total_count}")
            print(f"Average Subsequence Accuracy: {avg_subseq_acc * 100:.2f}%")
            print(f"Average Substring Accuracy: {avg_substr_acc * 100:.2f}%")
            print("-" * 30)
        else:
            print(f"No valid data found to evaluate in {os.path.basename(file_path)}.")
                        
    if not txt_files:
        print("No files were processed.")


if __name__ == "__main__":
    main()
