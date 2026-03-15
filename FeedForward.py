import torch
import torch.nn as nn
import math

class MultiHeadAttention(nn.Module):
    """
    實作 Multi-Head Attention，這是 Transformer 的核心。
    包含我們討論過的 Q, K, V 矩陣運算與縮放點積 (Scaled Dot-Product)。
    """
    def __init__(self, d_model, num_heads):
        super(MultiHeadAttention, self).__init__()
        self.num_heads = num_heads
        self.d_model = d_model
        assert d_model % num_heads == 0  # 確保維度可以被頭數整除
        
        self.d_k = d_model // num_heads  # 每個頭處理的維度 (例如 512 / 8 = 64)
        
        # 定義權重矩陣 (知識庫)
        self.w_q = nn.Linear(d_model, d_model) # Query
        self.w_k = nn.Linear(d_model, d_model) # Key
        self.w_v = nn.Linear(d_model, d_model) # Value
        self.w_o = nn.Linear(d_model, d_model) # 合併輸出的矩陣

    def forward(self, q, k, v, mask=None):
        batch_size = q.size(0)
        
        # 1. 矩陣乘法 + 拆分成多個頭 (使用 view 和 transpose 進行矩陣變形)
        # 轉換形狀: [Batch, Seq_Len, d_model] -> [Batch, Head, Seq_Len, d_k]
        q = self.w_q(q).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        k = self.w_k(k).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        v = self.w_v(v).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        # 2. 計算 Attention Score (QK^T) 與縮放 (Scaling)
        # 這裡是在算按鍵與按鍵之間的「關注度」
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)
        
        # 3. 應用 Mask (處理「偷看答案」或是補零的位置)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        # 4. Softmax 變機率，並與 Value 相乘得到加權結果
        attn = torch.softmax(scores, dim=-1)
        output = torch.matmul(attn, v)
        
        # 5. 把多個頭接回來，並透過最終矩陣輸出
        output = output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        return self.w_o(output)

# 測試用 (報告時可以示範矩陣維度的變化)
# d_model = 512, heads = 8
# 輸入資料 shape: [Batch_Size, Seq_Len, d_model]