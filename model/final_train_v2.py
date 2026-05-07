import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import os
import glob
from tqdm import tqdm # 💡 導入進度條庫

from transformer_main import TranscoderModel
from dictionary import KeySourceTokenizer, LabelTargetTokenizer

class ZhuyinDataset(Dataset):
    def __init__(self, folder_path, src_tokenizer, trg_tokenizer):
        self.pairs = []
        self.src_tokenizer = src_tokenizer
        self.trg_tokenizer = trg_tokenizer
        files = glob.glob(os.path.join(folder_path, "*.txt"))
        for f_path in files:
            with open(f_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '\t' in line:
                        src_str, trg_str = line.split('\t', 1)
                        self.pairs.append((src_str, trg_str))
        print(f"✅ 成功載入數據量: {len(self.pairs)} 筆")

    # def __len__(self): return len(self.pairs)

    def __getitem__(self, idx):
        src_str, trg_str = self.pairs[idx]
        # 分別使用不同的編碼器，並將 max_len 調大
        return torch.tensor(self.src_tokenizer.encode(src_str, max_len=32)), \
               torch.tensor(self.trg_tokenizer.encode(trg_str, max_len=32))

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    src_tokenizer = KeySourceTokenizer()
    trg_tokenizer = LabelTargetTokenizer()
    
    model = TranscoderModel(
        src_vocab_size=src_tokenizer.vocab_size, # 約 50-60
        trg_vocab_size=trg_tokenizer.vocab_size, # 21128
        d_model=512
    ).to(device)
    weight_path = "transcoder_v1.pth"

    if os.path.exists(weight_path):
        try:
            model.load_state_dict(torch.load(weight_path, map_location=device))
            print("🔄 載入既有權重...")
        except:
            print("🆕 權重不匹配，將從頭開始...")

    optimizer = optim.Adam(model.parameters(), lr=0.0001)
    criterion = nn.CrossEntropyLoss(ignore_index=0)

    dataset = ZhuyinDataset("./dataset", src_tokenizer, trg_tokenizer)
    train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

    print("🚀 訓練啟動...")
    
    # 💡 使用 tqdm 包裝你的 range
    epochs = 500
    pbar = tqdm(range(epochs), desc="Training Progress", unit="epoch")
    
    for epoch in pbar:
        model.train()
        total_loss = 0
        for src, trg in train_loader:
            src, trg = src.to(device), trg.to(device)
            trg_input, trg_expected = trg[:, :-1], trg[:, 1:]
            
            sz = trg_input.size(1)
            mask = torch.triu(torch.ones(sz, sz).to(device) * float('-inf'), diagonal=1)

            optimizer.zero_grad()
            output = model(src, trg_input, trg_mask=mask)
            loss = criterion(output.reshape(-1, trg_tokenizer.vocab_size), trg_expected.reshape(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # 💡 在進度條右側即時更新 Loss 數值
        current_loss = total_loss / len(train_loader)
        pbar.set_postfix({"Loss": f"{current_loss:.6f}"})
        
        # 每 10 輪自動存檔一次，預防斷電或當機
        if (epoch + 1) % 10 == 0:
            torch.save(model.state_dict(), weight_path)

    print("\n🎉 訓練完成！權重已儲存至 transcoder_v1.pth")

if __name__ == "__main__":
    main()