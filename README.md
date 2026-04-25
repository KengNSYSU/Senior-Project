# Senior-Project
## 專案結構

```
data/
	lexicon.json
src/
	app.py
	config.py
	core/
		contracts.py
		engine.py
		inference.py
	adapters/
		c_input_capture.py
		c_overlay_ui.py
		c_output_commit.py
requirements.txt
```

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

## 後續升級設計規則

為了降低遷移成本，此分支遵守以下原則：

1. 核心邏輯不得依賴 overlay/hook API。
2. 輸入、輸出與 UI 的平台細節需隔離在 adapters。
3. 共享契約保持穩定（`Key -> State -> Candidate -> CommitAction`）。
4. A/B/E 遷移應先替換 adapters，再細修平台行為。

## 已知 MVP 限制

- Overlay 與全域按鍵行為會因目標應用程式而異。
- 候選 UI 為了驗證速度刻意保持簡化。
- 本地 fallback 評分僅為佔位模型路徑，非最終模型品質。

## 下一步（C 驗證後）

蒐集並比較：

- 按鍵到候選延遲（平均值/P95）
- 提交成功率與回滾率
- 跨應用程式相容性
- 候選排序品質

接著在 A/B/E 中選定一條最終產品化路線。