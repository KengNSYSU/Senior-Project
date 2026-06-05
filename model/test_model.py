import torch
import os
from transformer_main import TranscoderModel
from dictionary import KeySourceTokenizer, LabelTargetTokenizer

def interactive_test():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    src_tokenizer = KeySourceTokenizer()
    trg_tokenizer = LabelTargetTokenizer()
    model = TranscoderModel(
        src_vocab_size=src_tokenizer.vocab_size, 
        trg_vocab_size=trg_tokenizer.vocab_size, 
        d_model=512
    ).to(device)

    weight_path = "transcoder_v1.pth"
    if not os.path.exists(weight_path):
        print("❌ 找不到權重檔！")
        return
        
    model.load_state_dict(torch.load(weight_path, map_location=device))
    model.eval()
    print("✨ 模型就緒！輸入 'exit' 退出。")

    while True:
        user_input = input("\n請輸入按鍵碼 (如 j83 或 ru04): ").strip().lower()
        if user_input == 'exit': break
        
        with torch.no_grad():
            # 測試時也要用同樣的 encode 邏輯 (補齊到 10)
            src_ids = src_tokenizer.encode(user_input, max_len=32)
            src_tensor = torch.tensor([src_ids]).to(device)
            trg_input = torch.tensor([[trg_tokenizer.cls_id]]).to(device) 
            
            result_ids = []
            for _ in range(20):
                output = model(src_tensor, trg_input)
                next_token = output.argmax(dim=-1)[:, -1].item()
                if next_token == 2 or next_token == 0:
                    break
                result_ids.append(next_token)
                next_token_tensor = torch.tensor([[next_token]]).to(device)
                trg_input = torch.cat([trg_input, next_token_tensor], dim=1)
            
            final_text = trg_tokenizer.tokenizer.decode(result_ids, skip_special_tokens=True)
            final_text = final_text.replace(" ", "")
            print(f"🔮 預測結果: {final_text}")

if __name__ == "__main__": interactive_test()