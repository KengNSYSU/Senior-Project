import torch
import torch.nn as nn
import copy
from transformer_layers import EncoderLayer
from positional_encoding import PositionalEncoding

class Encoder(nn.Module):
    def __init__(self, vocab_size, d_model, num_layers, num_heads, dropout=0.1):
        super().__init__()
        # 第一步：把按鍵索引變成向量
        self.embedding = nn.Embedding(vocab_size, d_model)
        # 第二步：注入位置靈魂
        self.pos_encoder = PositionalEncoding(d_model)
        # 第三步：複製出 6 個加工車間
        self.layers = nn.ModuleList([
            copy.deepcopy(EncoderLayer(d_model, num_heads, dropout)) 
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, mask):
        # 1. 轉向量
        x = self.embedding(x)
        # 2. 加位置
        x = self.pos_encoder(x)
        # 3. 依序流過 6 層加工車間
        for layer in self.layers:
            x = layer(x, mask)
        return self.norm(x)

# --- 硬核測試區 ---
if __name__ == "__main__":
    # 假設我們的按鍵字典有 30 個字元 (a-z + 符號)
    vocab_size = 30
    model = Encoder(vocab_size, d_model=512, num_layers=6, num_heads=8)
    
    # 模擬輸入：8 個人，每人打 10 個鍵 (數字代表按鍵編號)
    input_data = torch.randint(0, vocab_size, (8, 10))
    mask = torch.ones(8, 1, 1, 10)
    
    output = model(input_data, mask)
    print(f"✅ 總工廠運作正常！")
    print(f"最終特徵矩陣形狀: {output.shape}") # 應該是 [8, 10, 512]