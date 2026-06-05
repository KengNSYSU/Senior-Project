from pypinyin import pinyin, Style

arr = '結構以及空間等概念及其變化'
i = 0
while i < 13:
    text = arr[i]
    i+=1
    results = pinyin(text, style=Style.BOPOMOFO, heteronym=True)

    # results 的格式會是 [['ㄓㄨㄥˋ', 'ㄔㄨㄥˊ']]
    print(results[0])