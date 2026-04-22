import os
import torch

class TranscoderTokenizer:
    def __init__(self, dataset):
        # 1. 定義區域映射表 (鍵盤按鍵 -> 區域編號)
        # 1: 聲母區, 2: 介音區, 3: 韻母/聲調區
        self.zone_map = {
            '1':1,'q':1,'a':1,'z':1,'2':1,'w':1,'s':1,'x':1,'e':1,'d':1,'c':1,'r':1,'f':1,'v':1,'5':1,'t':1,'g':1,'b':1,'y':1,'h':1,'n':1,
            'u':2,'j':2,'m':2,
            '8':3,'i':3,'k':3,',':3,'9':3,'o':3,'l':3,'.':3,'0':3,'p':3,';':3,'/':3,'-':3,'7':3,'6':3,'3':3,'4':3
        }

        # 2. 建立帶區域標籤的 Vocab (例如 '1_e', '2_u', '3_k')
        # 這樣模型會精確區分不同區域的相同按鍵(如果有複用的話)
        base_keys = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;':\",./<>?"
        self.src_vocab = {'<PAD>': 0, '<SOS>': 1, '<EOS>': 2}
        
        idx = 3
        for zone in [1, 2, 3]:
            for k in base_keys:
                token = f"{zone}_{k}"
                self.src_vocab[token] = idx
                idx += 1
        
        self.idx2char = {v: k for k, v in self.src_vocab.items()}

        # 3. 讀取 dataset 資料夾 (接口 A/B)
        self.all_data = {}
        all_hanzi_chars = set()

        if os.path.exists(dataset):
            for filename in os.listdir(dataset):
                if filename.endswith(".txt"):
                    with open(os.path.join(dataset, filename), 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if ':' not in line: continue
                            hanzi, keys = line.split(':')
                            key_list = keys.split(',') # 假設 test.txt 裡是 幹:e,0,4
                            self.all_data[hanzi] = key_list
                            for char in hanzi:
                                all_hanzi_chars.add(char)

        # 4. 建立目標字彙表 (漢字)
        self.trg_vocab = {'<PAD>': 0, '<SOS>': 1, '<EOS>': 2}
        for i, char in enumerate(sorted(list(all_hanzi_chars))):
            self.trg_vocab[char] = i + 3
        self.idx2hanzi = {v: k for k, v in self.trg_vocab.items()}

    def get_zoned_token(self, key):
        """根據按鍵回傳帶區域標籤的 Token"""
        zone = self.zone_map.get(key.lower(), 0)
        return f"{zone}_{key.lower()}"

    def encode_src(self, key_list, max_len=12):
        """將按鍵序列 ['e', '0', '4'] 轉為 [ID, ID, ID]"""
        # 自動套用區域標籤
        tokens = [self.get_zoned_token(k) for k in key_list]
        ids = [self.src_vocab['<SOS>']] + [self.src_vocab.get(t, 0) for t in tokens] + [self.src_vocab['<EOS>']]
        return ids + [0] * (max_len - len(ids))

    def encode_trg(self, hanzi, max_len=6):
        """將漢字轉為 ID"""
        ids = [self.trg_vocab['<SOS>']] + [self.trg_vocab.get(c, 0) for c in hanzi] + [self.trg_vocab['<EOS>']]
        return ids + [0] * (max_len - len(ids))