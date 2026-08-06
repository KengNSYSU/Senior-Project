from __future__ import annotations

import os

from src.adapters.input_capture import InputCaptureAdapter
from src.adapters.output_commit import OutputCommitAdapter
from src.adapters.overlay_ui import OverlayWindow
from src.config import load_config, AppConfig
from src.core.contracts import InferenceProvider
from src.core.engine import ImeCoreEngine


def create_inference_provider(config: AppConfig) -> InferenceProvider:
    """根據環境與配置建立對應的推理提供者。"""
    use_test_mode = os.getenv("ZHUYIN_TEST_MODE", "0") == "1"
    if use_test_mode:
        # 簡單測試模式：只用硬編碼規則驗證鍵盤輸入。
        from src.core.test_inference import SimpleTestInferenceProvider
        return SimpleTestInferenceProvider()

    # 正常模式：直接使用本機模型 (Local Mode)。
    from src.core.inference import LocalModelInferenceProvider
    return LocalModelInferenceProvider()


def main() -> None:
    # 載入環境設定（包含詞典與模型端點）。
    config = load_config()

    # 根據環境建立對應的推理提供者。
    inference_provider = create_inference_provider(config)

    # 宣告 ui 的變數，以便 closure 能夠引用
    ui: OverlayWindow | None = None

    def on_state_changed() -> None:
        if ui is not None:
            ui.enqueue_state(engine.state)

    # 建立核心引擎與浮層視窗。
    engine = ImeCoreEngine(inference_provider, on_state_changed=on_state_changed)
    ui = OverlayWindow()

    capture_adapter: InputCaptureAdapter | None = None

    def on_key(key: str) -> None:
        # 將按鍵事件交給核心狀態機處理。
        action = engine.handle_key(key)
        if ui is not None:
            ui.enqueue_state(engine.state)
        if action:
            # 若核心回傳提交動作，在獨立的背景執行緒中執行替換與輸出，
            # 避免阻塞或卡死鍵盤監聯（Hook）執行緒，解決事件死鎖與卡頓問題。
            import threading
            threading.Thread(
                target=output_adapter.commit_text,
                args=(action.text, action.replace_len),
                daemon=True
            ).start()
            if ui is not None:
                ui.enqueue_state(engine.state)

    # 先建立輸入擷取，再建立提交器以便互相協調暫停狀態。
    capture_adapter = InputCaptureAdapter(on_key=on_key, is_composing=lambda: bool(engine.state.buffer))
    output_adapter = OutputCommitAdapter(pause_capture=capture_adapter.set_paused)

    # 啟動背景鍵盤監聽與前景 UI 事件迴圈。
    capture_adapter.start()
    ui.enqueue_state(engine.state)
    ui.run()

    # UI 關閉後，停止背景鍵盤監聽以避免 zombie process。
    capture_adapter.stop()


if __name__ == "__main__":
    main()
