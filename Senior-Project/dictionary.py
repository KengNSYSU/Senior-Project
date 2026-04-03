import os
import glob

class Tokenizer:
    def __init__(self, dataset_path="./dataset"):
        # 0:PAD, 1:SOS, 2:EOS, 3:UNK
        self.vocab = ["<PAD>", "<SOS>", "<EOS>", "<UNK>"]
        
        # 自動掃描所有字元建立字典
        all_chars = set()
        files = glob.glob(os.path.join(dataset_path, "*.txt"))
        for f_path in files:
            with open(f_path, 'r', encoding='utf-8') as f:
                all_chars.update(list(f.read()))
        
        for ignore in ["\n", "\t", "\r"]:
            if ignore in all_chars:
                all_chars.remove(ignore)
        
        self.vocab.extend(sorted(list(all_chars)))
        self.char_to_id = {char: i for i, char in enumerate(self.vocab)}
        self.id_to_char = {i: char for i, char in enumerate(self.vocab)}
        print(f"📊 字典建立完成！共識別出 {len(self.vocab)} 個字元。")

    def encode(self, text, max_len=10):
        # 轉為 ID 並加上開始/結束符號
        ids = [1] + [self.char_to_id.get(c, 3) for c in text] + [2]
        # 如果長度不足 max_len，補 0 (<PAD>)
        if len(ids) < max_len:
            ids += [0] * (max_len - len(ids))
        return ids[:max_len]

    @property
    def vocab_size(self):
        return len(self.vocab)