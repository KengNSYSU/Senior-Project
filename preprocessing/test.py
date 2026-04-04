from pypinyin import pinyin, Style

while True:
    text = input()
    results = pinyin(text, style=Style.BOPOMOFO, heteronym=True)

    # results 的格式會是 [['ㄓㄨㄥˋ', 'ㄔㄨㄥˊ']]
    print(results[0])