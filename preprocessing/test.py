from pypinyin import pinyin, lazy_pinyin, Style

while True:
    text = input()
    print(pinyin(text,style=Style.BOPOMOFO))
    print(pinyin(text))