import torch
from transformers import BertTokenizer

class KeySourceTokenizer:
    """手動設定的鍵盤按鍵 Tokenizer (Source 端)"""
    def __init__(self):
        # 0:PAD, 1:SOS, 2:EOS, 3:UNK
        self.special_tokens = ["<PAD>", "<SOS>", "<EOS>", "<UNK>"]
        self.keys = list("abcdefghijklmnopqrstuvwxyz0123456789.,/;+-=[] ")
        self.vocab = self.special_tokens + self.keys
        self.char_to_id = {char: i for i, char in enumerate(self.vocab)}
        self.id_to_char = {i: char for i, char in enumerate(self.vocab)}

    def encode(self, text, max_len=32):
        text = text.lower()
        
        space_id = self.char_to_id.get(" ", 3) 
        
        ids = [1] + [self.char_to_id.get(c, space_id) for c in text] + [2]
        
        if len(ids) < max_len:
            ids += [0] * (max_len - len(ids))
        return ids[:max_len]

    @property
    def vocab_size(self):
        return len(self.vocab)

class LabelTargetTokenizer:
    """使用 BERT-Base-Chinese 的 Tokenizer (Target 端)"""
    def __init__(self):
        # 自動從 Hugging Face 下載或讀取快取
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-chinese")
        # self.tokenizer.add_special_tokens({'additional_special_tokens': [' ']})
        if " " not in self.tokenizer.get_vocab():
            self.tokenizer.add_tokens([" "])
        # BERT 的特殊 ID: [PAD]=0, [UNK]=100, [CLS]=101, [SEP]=102
        self.cls_id = self.tokenizer.cls_token_id # 相當於 <SOS>
        self.sep_id = self.tokenizer.sep_token_id # 相當於 <EOS>

    def encode(self, text, max_len=32):
        encoded = self.tokenizer.encode(
            text,
            add_special_tokens=True,
            max_length=max_len,
            truncation=True,
            padding='max_length',
            clean_up_tokenization_spaces=False
        )
        return encoded

    @property
    def vocab_size(self):
        return len(self.tokenizer)