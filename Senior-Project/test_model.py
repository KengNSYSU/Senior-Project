import torch
import os
from transformer_main import TranscoderModel
from dictionary import Tokenizer

def interactive_test():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = Tokenizer(dataset_path="./dataset")
    model = TranscoderModel(src_vocab_size=tokenizer.vocab_size, 
                            trg_vocab_size=tokenizer.vocab_size, d_model=512).to(device)

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
            src_tensor = torch.tensor([tokenizer.encode(user_input, max_len=10)]).to(device)
            trg_input = torch.tensor([[1]]).to(device) # <SOS>
            
            result = ""
            for _ in range(1):
                output = model(src_tensor, trg_input)
                next_token = output.argmax(dim=-1)[:, -1].item()
                if next_token == 2 or next_token == 0: break
                result += tokenizer.id_to_char.get(next_token, "")
                trg_input = torch.cat([trg_input, torch.tensor([[next_token]]).to(device)], dim=1)
            print(f"🔮 預測結果: {result}")

if __name__ == "__main__": interactive_test()