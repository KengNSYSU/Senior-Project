import pypinyin
from pypinyin import load_phrases_dict, Style, load_single_dict
import itertools
import os
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
    for char, pronounces in zip(text, pinyin_list):
        stats.append({
            'char': char,
            'count': len(pronounces),
            'pronounces': pronounces
        })
    
    combinations = list(itertools.product(*pinyin_list))
    
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

if __name__ == "__main__":
    initial()

    input_path = 'input.txt'
    output_dir = 'output_results'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已建立資料夾: {output_dir}")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        results, stats = process_combinations(content)
        
        stats_path = os.path.join(output_dir, 'stats.txt')
        with open(stats_path, 'w', encoding='utf-8') as f_stats:
            f_stats.write(f"總排列組合數: {len(results)}\n")
            f_stats.write("-" * 30 + "\n")
            for item in stats:
                line = f"字元: {item['char']} | 讀音數: {item['count']} | 讀音: {', '.join(item['pronounces'])}\n"
                f_stats.write(line)
        print(f"統計檔案已存至: {stats_path}")

        for i, keystrokes in enumerate(results, 1):
            file_path = os.path.join(output_dir, f'output_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f_out:
                f_out.write(keystrokes)
        
        print(f"成功完成！共 {len(results)} 個組合檔案已存入 '{output_dir}' 資料夾。")
            
    except FileNotFoundError:
        print(f"找不到輸入檔案: {input_path}")