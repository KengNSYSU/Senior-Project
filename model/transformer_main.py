import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]

class TranscoderModel(nn.Module):
    def __init__(self, src_vocab_size, trg_vocab_size, d_model=512, num_heads=8, num_layers=6):
        super(TranscoderModel, self).__init__()
        self.d_model = d_model
        self.encoder_emb = nn.Embedding(src_vocab_size, d_model)
        self.decoder_emb = nn.Embedding(trg_vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        
        self.transformer = nn.Transformer(
            d_model=d_model, nhead=num_heads, 
            num_encoder_layers=num_layers, num_decoder_layers=num_layers,
            batch_first=True
        )
        self.fc_out = nn.Linear(d_model, trg_vocab_size)

    def forward(self, src, trg, trg_mask=None):
        src_emb = self.pos_encoder(self.encoder_emb(src) * math.sqrt(self.d_model))
        trg_emb = self.pos_encoder(self.decoder_emb(trg) * math.sqrt(self.d_model))
        
        # 執行 Transformer
        out = self.transformer(src_emb, trg_emb, tgt_mask=trg_mask)
        return self.fc_out(out)