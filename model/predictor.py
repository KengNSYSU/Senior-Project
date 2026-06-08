import torch
import os
from transformer_main import TranscoderModel
from dictionary import KeySourceTokenizer, LabelTargetTokenizer

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

    weight_path = "transcoder_v2.pth"
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
        src_ids = src_tokenizer.encode(user_input, max_len=32)
        src_tensor = torch.tensor([src_ids]).to(device)
        trg_input = torch.tensor([[trg_tokenizer.cls_id]]).to(device)
        result_ids = []
        for _ in range(len(s)):
            output = model(src_tensor, trg_input)
            next_token = output.argmax(dim=-1)[:, -1].item()
            if next_token == trg_tokenizer.sep_id or next_token == 0:
                break
            result_ids.append(next_token)
            next_token_tensor = torch.tensor([[next_token]]).to(device)
            trg_input = torch.cat([trg_input, next_token_tensor], dim=1)

        final_text = trg_tokenizer.tokenizer.decode(result_ids, skip_special_tokens=True)
        final_text = final_text.replace(" ", "")
        if len(final_text) == 0:
            return s
        
        return final_text[:len(s)]
