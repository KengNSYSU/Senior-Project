from __future__ import annotations
"""C 方案驗證版入口：串接輸入擷取、推理核心、浮層 UI 與提交器。"""

from src.adapters.c_input_capture import InputCaptureAdapter
from src.adapters.c_output_commit import OutputCommitAdapter
from src.adapters.c_overlay_ui import OverlayWindow
from src.config import load_config
from src.core.engine import ImeCoreEngine
from src.core.inference import HybridInferenceProvider, InferenceConfig


def main() -> None:
    # 載入環境設定（詞典路徑、遠端模型端點）。
    config = load_config()

    # 建立推理提供者：優先遠端模型，失敗時退回本地詞典。
    inference_provider = HybridInferenceProvider(
        InferenceConfig(
            lexicon_path=config.lexicon_path,
            remote_endpoint=config.remote_model_endpoint,
        )
    )

    # 建立核心引擎與浮層視窗。
    engine = ImeCoreEngine(inference_provider)
    ui = OverlayWindow()

    capture_adapter: InputCaptureAdapter | None = None

    def on_key(key: str) -> None:
        # 將按鍵事件交給核心狀態機處理。
        action = engine.handle_key(key)
        ui.enqueue_state(engine.state)
        if action:
            # 若核心回傳提交動作，執行替換/輸出。
            output_adapter.commit_text(action.text, replace_len=action.replace_len)
            ui.enqueue_state(engine.state)

    # 先建立輸入擷取，再建立提交器以便互相協調暫停狀態。
    capture_adapter = InputCaptureAdapter(on_key=on_key)
    output_adapter = OutputCommitAdapter(pause_capture=capture_adapter.set_paused)

    # 啟動背景鍵盤監聽與前景 UI 事件迴圈。
    capture_adapter.start()
    ui.enqueue_state(engine.state)
    ui.run()


if __name__ == "__main__":
    main()
