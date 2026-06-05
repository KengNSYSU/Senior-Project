import pypinyin
from pypinyin import load_phrases_dict, Style, load_single_dict
import random
import os
from tqdm import tqdm  # 引入 tqdm 進度條模組
from concurrent.futures import ProcessPoolExecutor

try:
    from dictionary import phrases_dict, single_dict
except ImportError:
    phrases_dict, single_dict = {}, {}

ZHUYIN_TO_KEY = {
    'ㄅ': '1', 'ㄆ': 'q', 'ㄇ': 'a', 'ㄈ': 'z',
    'ㄉ': '2', 'ㄊ': 'w', 'ㄋ': 's', 'ㄌ': 'x',
    'ㄍ': 'e', 'ㄎ': 'd', 'ㄏ': 'c',
    'ㄐ': 'r', 'ㄑ': 'f', 'ㄒ': 'v',
    'ㄓ': '5', 'ㄔ': 't', 'ㄕ': 'g', 'ㄖ': 'b',
    'ㄗ': 'y', 'ㄘ': 'h', 'ㄙ': 'n',
    'ㄧ': 'u', 'ㄨ': 'j', 'ㄩ': 'm',
    'ㄚ': '8', 'ㄛ': 'i', 'ㄜ': 'k', 'ㄝ': ',',
    'ㄞ': '9', 'ㄟ': 'o', 'ㄠ': 'l', 'ㄡ': '.',
    'ㄢ': '0', 'ㄣ': 'p', 'ㄤ': ';', 'ㄥ': '/',
    'ㄦ': '-',
    'ˊ': '6', 'ˇ': '3', 'ˋ': '4', '˙': '7'
}

def zhuyin_to_keys(zhuyin_char):
    if any(c in ZHUYIN_TO_KEY for c in zhuyin_char):
        keys = ""
        for symbol in zhuyin_char:
            if symbol in ZHUYIN_TO_KEY:
                keys += ZHUYIN_TO_KEY[symbol]
        if zhuyin_char[-1] not in ['ˊ', 'ˇ', 'ˋ', '˙']:
            keys += " "
        return keys
    return zhuyin_char

def process_combinations(text):
    pinyin_list = pypinyin.pinyin(text, style=Style.BOPOMOFO, heteronym=True, errors='default')
    
    stats = []
    chosen_combo = []
    
    for char, pronounces in zip(text, pinyin_list):
        stats.append({
            'char': char,
            'count': len(pronounces),
            'pronounces': pronounces
        })
        if pronounces:
            chosen_combo.append(random.choice(pronounces))
        else:
            chosen_combo.append(char)
    
    result_keys = []
    for zhuyin in chosen_combo:
        result_keys.append(zhuyin_to_keys(zhuyin))
    
    all_results = ["".join(result_keys)]
        
    return all_results, stats

def initial():
    load_phrases_dict(phrases_dict)
    load_single_dict(single_dict)

def process_single_line(line):
    word = line.strip()
    if not word:
        return ""
    # 呼叫你原本的 process_combinations
    results, _ = process_combinations(word) 
    return f"{results[0]}\t{word}\n"

if __name__ == "__main__":
    initial()

    input_path = os.path.join("original_dataset", "wmt_paired_corpus.txt")
    output_path = os.path.join("dataset", "output9.txt")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"開始多程序平行處理，總計 {len(lines)} 行資料...")
        
        with ProcessPoolExecutor() as executor:
            all_output_lines = list(tqdm(executor.map(process_single_line, lines, chunksize=1000), total=len(lines), desc="多核平行處理中", unit="行"))
        
        all_output_lines = [line for line in all_output_lines if line]
        
        # 4. 一次性寫入檔案
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.writelines(all_output_lines)
            
        print(f"\n成功完成！結果已寫入至 {output_path}，共 {len(all_output_lines)} 筆組合。")
            
    except FileNotFoundError:
        print(f"找不到輸入檔案: {input_path}")