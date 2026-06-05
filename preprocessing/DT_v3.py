import pypinyin
from pypinyin import load_phrases_dict, Style, load_single_dict
import itertools  # 把排列組合模組加回來
import os
from tqdm import tqdm  
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
    cleaned_pinyin_list = []
    
    for char, pronounces in zip(text, pinyin_list):
        stats.append({
            'char': char,
            'count': len(pronounces),
            'pronounces': pronounces
        })
        # 防呆：如果該字元不是中文字導致讀音清單為空，就放原字元，確保 itertools 能順利排列
        if pronounces:
            cleaned_pinyin_list.append(pronounces)
        else:
            cleaned_pinyin_list.append([char])
    
    # 關鍵改動：重新用 itertools.product 窮舉該行文字的所有讀音組合
    combinations = list(itertools.product(*cleaned_pinyin_list))
    
    all_results = []
    for combo in combinations:
        result_keys = []
        for zhuyin in combo:
            result_keys.append(zhuyin_to_keys(zhuyin))
        all_results.append("".join(result_keys))
        
    return all_results, stats

def initial():
    load_phrases_dict(phrases_dict)
    load_single_dict(single_dict)

def process_single_line(line):
    word = line.strip()
    if not word:
        return [] # 改回傳 list
    
    # 呼叫恢復窮舉後的 process_combinations
    results, _ = process_combinations(word) 
    
    # 將每一組窮舉出來的按鍵對應回原本的字，做成多行資料
    formatted_lines = []
    for keystrokes in results:
        formatted_lines.append(f"{keystrokes}\t{word}\n")
    return formatted_lines

if __name__ == "__main__":
    initial()

    input_path = os.path.join("original_dataset", "ch_corpus.txt")
    output_path = os.path.join("dataset", "output1.txt")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"開始多程序平行處理，總計 {len(lines)} 行原始資料...")
        
        with ProcessPoolExecutor() as executor:
            packed_results = list(tqdm(executor.map(process_single_line, lines, chunksize=500), total=len(lines), desc="多核平行窮舉中", unit="行"))
        
        all_output_lines = []
        for sublist in packed_results:
            if sublist:
                all_output_lines.extend(sublist)
        
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.writelines(all_output_lines)
            
        print(f"成功完成！結果已寫入至 {output_path}，總共生成 {len(all_output_lines)} 筆組合。")
            
    except FileNotFoundError:
        print(f"找不到輸入檔案: {input_path}")