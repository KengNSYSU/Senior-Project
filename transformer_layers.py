import torch
import torch.nn as nn
import math
from MultiHead_Attention import MultiHeadAttention

# --- 1. 前饋神經網路 (Feed-Forward Network) ---
# 負責對每個字元做非線性變換，增加模型的理解力
class FeedForward(nn.Module):
    def __init__(self, d_model, d_ff=2048, dropout=0.1):
        super().__init__()
        self.linear_1 = nn.Linear(d_model, d_ff)
        self.dropout = nn.Dropout(dropout)
        self.linear_2 = nn.Linear(d_ff, d_model)

    def forward(self, x):
        # ReLU 激活函數是這裡的關鍵
        return self.linear_2(self.dropout(torch.relu(self.linear_1(x))))

# --- 2. 編碼器層 (Encoder Layer) ---
class EncoderLayer(nn.Module):
    def __init__(self, d_model, num_heads, dropout=0.1):
        super().__init__()
        self.norm_1 = nn.LayerNorm(d_model)
        self.norm_2 = nn.LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, num_heads)
        self.ff = FeedForward(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask):
        # 殘差連接 (Residual Connection): x + Sublayer(x)
        x2 = self.norm_1(x)
        x = x + self.dropout(self.attn(x2, x2, x2, mask))
        x2 = self.norm_2(x)
        x = x + self.dropout(self.ff(x2))
        return x

if __name__ == "__main__":
    # 模擬輸入數據的矩陣 (Batch=8, 字串長度=10, 維度=512)
    x = torch.randn(8, 10, 512)
    # 建立一個全 1 的 Mask
    mask = torch.ones(8, 1, 1, 10)
    
    # 實例化加工層
    layer = EncoderLayer(d_model=512, num_heads=8)
    
    # 執行運算
    try:
        output = layer(x, mask)
        print("✅ 成功！EncoderLayer 輸出形狀:", output.shape)
    except Exception as e:
        print("❌ 失敗！錯誤訊息:", e)