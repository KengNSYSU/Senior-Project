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

- 不需要切換中英模式，系統會自動判斷詞段是否為注音鍵序。
- 注音基礎鍵：`a-z`、`1`、`2`、`5`、`8`、`9`、`0`、`-`、`;`、`,`、`.`、`/`
- 聲調鍵：
	- `space`：一聲
	- `3`：三聲
	- `4`：四聲
	- `6`：二聲
	- `7`：輕聲
- 組字控制鍵：
	- `Backspace`：刪除緩衝中的一個字元
	- `Up/Down`：移動候選選取位置
	- `Enter`：詞段結束時提交目前選中的候選
	- `Esc`：清空組字
- 英文詞段會維持原樣，不會被強制轉換。
- 範例：`ji394t apple` -> `我愛吃apple`
