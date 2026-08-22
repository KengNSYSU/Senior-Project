# Senior-Project

## 環境需求

| 項目 | 需求 |
|------|------|
| 作業系統 | **Windows 10 / 11**（使用 Win32 API 進行鍵盤攔截與 IME 偵測） |
| Python | **≥ 3.10**（程式碼使用 `X \| Y` 型別語法） |
| 模型權重 | `model/transcoder_len56_v4.pth`（未納入 Git，需另行取得，見下方說明） |
| 網路 | **首次執行需要網路**（自動下載 `bert-base-chinese` tokenizer，之後會使用快取） |

> **Linux / macOS 使用者注意：** 本專案目前僅支援 Windows。多個 Adapter 直接呼叫
> `ctypes.windll`（user32 / imm32），在非 Windows 環境會無法啟動。

## 執行方式

### 1. 安裝相依套件

**有 NVIDIA GPU（CUDA）：**
```powershell
pip install -r requirements.txt
```

**僅使用 CPU（無 NVIDIA GPU 或不需要 GPU 加速）：**
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt --no-deps
pip install pynput transformers
```
> CPU 版 torch 約 200 MB，CUDA 版約 2.5 GB。無 GPU 的電腦建議使用 CPU 版以節省空間與安裝時間。

### 2. 取得模型權重

模型權重檔 `transcoder_len56_v4.pth`（約 273 MB）未納入 Git 版控。請向專案成員取得後放置於：
```
model/transcoder_len56_v4.pth
```
> 若模型檔名與上方不同，請至 `src/predictor.py` 修改對應的檔名。

### 3. 啟動應用程式

```powershell
python -m src.app
```

### 測試模式（無需模型權重）

若尚未取得模型權重檔，可透過環境變數啟用測試模式，使用硬編碼規則驗證鍵盤輸入流程：
```powershell
$env:ZHUYIN_TEST_MODE="1"
python -m src.app
```

## 快捷鍵與行為（MVP）

- 不需要在輸入端切換中/英模式：系統僅負責捕捉鍵盤輸入，注音詞段的判斷與轉換由上游模型或其他分支負責。
- 捕捉範圍：所有可印出字元（printable characters）皆會被捕捉並原樣放入 `buffer`，包含數字、英文字母與標點，例如 `1 - =`、`q \`、`a '`、`z /` 等。
- 空白鍵行為：`space` 會插入實際空格字元（顯示於 `buffer` 中為空格），而非以數字代表聲調。
- 組字控制鍵：
	- `Backspace`：刪除緩衝中的一個字元
	- `Up/Down`：移動候選選取位置
	- `Enter`：詞段結束時提交目前選中的候選
	- `Esc`：清空組字
- 英文詞段會維持原樣，不會被強制轉換（上游模型可根據需要決定是否轉換）。
- 範例：`ji394t apple` -> `我愛吃apple`

