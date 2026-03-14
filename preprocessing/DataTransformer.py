import pypinyin
from pypinyin import load_phrases_dict, Style, load_single_dict
from dictionary import phrases_dict, single_dict

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

def text_to_keystrokes(text):
    result_keys = []
    
    pinyin_list = pypinyin.pinyin(text, style=pypinyin.Style.BOPOMOFO, errors='default')
    print(pinyin_list)
    for item in pinyin_list:

        #turn list element to string
        zhuyin_char = item[0]
        
        if any(c in ZHUYIN_TO_KEY for c in zhuyin_char):
            keys = ""
            for symbol in zhuyin_char:
                if symbol in ZHUYIN_TO_KEY:
                    keys += ZHUYIN_TO_KEY[symbol]
            
            if zhuyin_char[-1] not in ['ˊ', 'ˇ', 'ˋ', '˙']:
                keys += " "
                
            result_keys.append(keys)
        else:
            result_keys.append(zhuyin_char)
            
    return "".join(result_keys)

def initial():
    load_phrases_dict(phrases_dict)
    load_single_dict(single_dict)

if __name__ == "__main__":
    initial()

    input_path = 'input.txt'
    output_path = 'output.txt'
    input_file = open(input_path, 'r')
    output_file = open('output_path.txt', 'w')
    output_file.write(text_to_keystrokes(input_file.read()))
    input_file.close()
    output_file.close()

    