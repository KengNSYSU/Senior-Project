# Senior-Project

## 執行方式（Windows）

1. 建立並啟用虛擬環境。
2. 安裝相依套件。
3. 啟動應用程式。

PowerShell 範例：

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.app
```

## 快捷鍵與行為（MVP）

- 不需要在輸入端切換中/英模式：系統僅負責捕捉鍵盤輸入，注音詞段的判斷與轉換由上游模型或其他分支負責。
- 捕捉範圍：所有可印出字元（printable characters）皆會被捕捉並原樣放入 `buffer`，包含數字、英文字母與標點，例如 `1 - =`、`q \`、`a '`、`z /` 等。
- 空白鍵行為：`space` 會插入實際空格字元（顯示於 `buffer` 中為空格），而非以數字代表聲調。
- 組字控制鍵：
	- `Backspace`：刪除緩衝中的一個字元
	- `Up/Down`：移動候選選取位置
	- `Enter`：詞段結束時提交目前選中的候選後清空 buffer
	- `Esc`：清空組字
- 英文詞段會維持原樣，不會被強制轉換（上游模型可根據需要決定是否轉換）。
- 範例：`ji394t apple` -> `我愛吃apple`
