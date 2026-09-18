from __future__ import annotations
import queue
import threading
from typing import Callable, List
from .contracts import CandidateItem, InferenceProvider


class InferenceWorker:
    """非同步模型推理工作器。
    
    將鍵盤監聽執行緒與耗時的 PyTorch 模型推理隔離，防止鍵盤輸入 lag。
    """
    def __init__(self, provider: InferenceProvider, callback: Callable[[str, List[CandidateItem]], None]) -> None:
        self._provider = provider
        self._callback = callback
        self._queue: queue.Queue[str] = queue.Queue()
        self._event = threading.Event()
        self._event.set()  # 初始狀態為閒置/完成
        self._latest_buffer = ""
        self._lock = threading.Lock()

        # 啟動 daemon 背景工作執行緒
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def submit(self, buffer: str) -> None:
        """提交新的推理請求。"""
        with self._lock:
            self._latest_buffer = buffer
            self._event.clear()
        self._queue.put(buffer)

    def wait_for_completion(self, timeout: float = 0.8) -> None:
        """等待當前最新推理請求完成。"""
        self._event.wait(timeout)

    def _worker_loop(self) -> None:
        while True:
            # 阻塞等待新任務
            buffer = self._queue.get()
            try:
                # 拋棄積壓的舊任務，只留下最後一個（防抖/Debounce）
                with self._lock:
                    while not self._queue.empty():
                        buffer = self._queue.get_nowait()

                with self._lock:
                    is_latest = (buffer == self._latest_buffer)

                if is_latest:
                    candidates = self._provider.infer(buffer, top_k=9)
                    self._callback(buffer, candidates)
            except Exception:
                self._callback(buffer, [])
            finally:
                self._queue.task_done()
                with self._lock:
                    # 如果當前處理的 buffer 是最後提交的，則標記完成
                    if buffer == self._latest_buffer:
                        self._event.set()
