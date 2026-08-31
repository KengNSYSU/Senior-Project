import torch
import os
from transformer_main import TranscoderModel
from dictionary import KeySourceTokenizer, LabelTargetTokenizer
import re
device = None
src_tokenizer = None
trg_tokenizer = None
model = None


def initialize():
    global device, src_tokenizer, trg_tokenizer, model

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    src_tokenizer = KeySourceTokenizer()
    trg_tokenizer = LabelTargetTokenizer()
    model = TranscoderModel(
        src_vocab_size=src_tokenizer.vocab_size, 
        trg_vocab_size=trg_tokenizer.vocab_size, 
        d_model=512
    ).to(device)
    weight_path = os.path.join('model', 'transcoder_len60_v5.pth')
    # weight_path = "transcoder_v2.pth"
    if not os.path.exists(weight_path):
        print("找不到權重檔！")
        return False

    model.load_state_dict(torch.load(weight_path, map_location=device))
    model.eval()
    return True


def predict(s):
    if model is None or src_tokenizer is None or trg_tokenizer is None or device is None:
        raise RuntimeError("call initialize()")

    user_input = s.strip().lower()

    with torch.no_grad():
        src_ids = src_tokenizer.encode(user_input, max_len=60)
        src_tensor = torch.tensor([src_ids]).to(device)
        trg_input = torch.tensor([[trg_tokenizer.cls_id]]).to(device)
        result_ids = []
        
        # 放開限制，最多吐 32 個 Token
        for _ in range(60):
            output = model(src_tensor, trg_input)
            logits = output[:, -1, :] # 拿到最後一個 Token 的所有機率分佈
            
            # 🌟 策略一：防鬼打牆與連續空格機制
            # 如果上一個 Token 已經是空格 (21128/21129) 或某個字了，強行把它的機率降到極低，逼模型必須吐出新單字！
            if len(result_ids) >= 1:
                last_token = result_ids[-1]
                logits[0, last_token] -= 10.0 # 施加重複懲罰，讓它不准連續吐出相同的 Token
            
            next_token = logits.argmax(dim=-1).item()
            
            # 偵測到結束符號就煞車
            if next_token == trg_tokenizer.sep_id or next_token == 0:
                break
                
            result_ids.append(next_token)
            next_token_tensor = torch.tensor([[next_token]]).to(device)
            trg_input = torch.cat([trg_input, next_token_tensor], dim=1)
            
        final_text = trg_tokenizer.tokenizer.decode(result_ids, skip_special_tokens=True)
        
        final_text = re.sub(r'\s+', ' ', final_text)
        
        final_text = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', final_text)
        
        if len(final_text) == 0:
            return s
        
        return final_text
