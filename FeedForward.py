import torch
import torch.nn as nn
import math

# --- 1. 我們剛才寫好的 Multi-Head Attention ---
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.d_model = d_model
        self.d_k = d_model // num_heads
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)

    def forward(self, q, k, v, mask=None):
        batch_size = q.size(0)
        q = self.w_q(q).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        k = self.w_k(k).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        v = self.w_v(v).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attn = torch.softmax(scores, dim=-1)
        output = torch.matmul(attn, v)
        output = output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        return self.w_o(output)

# --- 2. 前饋神經網路 (Feed-Forward Network) ---
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

# --- 3. 編碼器層 (Encoder Layer) ---
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