"""视频读取引擎：基于 OpenCV，后台线程预取帧，避免解码阻塞界面。"""

import os
import threading

import cv2

VIDEO_EXTS = {
    ".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".ts", ".m2ts",
    ".mts", ".webm", ".m4v", ".3gp", ".mpg", ".mpeg", ".rmvb", ".vob",
}


def is_video_file(path: str) -> bool:
    return os.path.splitext(str(path))[1].lower() in VIDEO_EXTS


class VideoReader:
    """单个视频的读取器，维护"当前帧"概念，支持精确跳帧与逐帧前进。

    内部有一个后台解码线程：播放时下一帧在后台解好，界面只负责显示；
    跳转 / 步进时则同步读取，保证帧号精确。
    """

    def __init__(self, path: str):
        self.path = str(path)
        self._lock = threading.Lock()
        self.cap = cv2.VideoCapture(self.path)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频文件：{self.path}")
        self.fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or 25.0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
        self.current = -1  # 当前显示的帧索引（0 起）
        self.at_end = False
        self._cache = None
        self._cache_idx = -1
        # 预取状态
        self._prefetched = None    # (index, frame)：后台线程已解出的下一帧
        self._prefetch_target = -1 # 后台要解出的帧号；-1 表示暂停
        self._seek_request = None  # 后台跳转请求（相对进度 0~1）；None 表示无
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = threading.Thread(
            target=self._prefetch_loop,
            daemon=True,
            name=f"decode-{os.path.basename(self.path)}",
        )
        self._thread.start()

    @property
    def duration(self) -> float:
        return self.frame_count / self.fps if self.fps else 0.0

    def frame_bgr(self):
        return self._cache

    # ---------- 后台预取 ----------

    def _prefetch_loop(self):
        while not self._stop.is_set():
            self._wake.wait(timeout=0.5)
            self._wake.clear()
            if self._stop.is_set():
                break
            with self._lock:
                if self._seek_request is not None:
                    p = self._seek_request
                    self._seek_request = None
                    if self.frame_count > 0:
                        self._read_index_locked(int(round(p * (self.frame_count - 1))))
                    else:
                        self._read_index_locked(0)
                    continue
                if (self._prefetched is None and not self.at_end
                        and self._prefetch_target >= 0):
                    ok, frame = self.cap.read()
                    if ok:
                        self._prefetched = (self._prefetch_target, frame)
                    else:
                        self.at_end = True

    def _store(self, index: int, frame):
        self.current = index
        self._cache = frame
        self._cache_idx = index
        self.at_end = False

    # ---------- 对外接口 ----------

    def next_frame(self, wait: bool = True):
        """读取下一帧。wait=False 时若后台尚未解好则返回 None（播放用）。"""
        if not self._lock.acquire(blocking=wait):
            # 后台线程正在解码，本拍不等待（播放流畅优先）
            return None
        try:
            if self._seek_request is not None:
                if not wait:
                    return None  # 后台正在跳转，等它完成
                self._seek_request = None  # 同步操作优先，取消后台请求
            if self.at_end:
                return None
            if self._prefetched is not None:
                idx, frame = self._prefetched
                self._prefetched = None
                self._store(idx, frame)
                self._prefetch_target = idx + 1
                self._wake.set()
                return frame
            if not wait:
                # 本拍没有现成帧：先保持当前画面，同时让后台开始解下一帧
                if self._prefetch_target < 0 and self.current >= 0:
                    self._prefetch_target = self.current + 1
                    self._wake.set()
                return None
            # 同步读取（跳转 / 步进后的首次播放）
            if self.current < 0:
                frame = self._read_index_locked(0)
                self._prefetch_target = 1
                self._wake.set()
                return frame
            ok, frame = self.cap.read()
            if not ok:
                self.at_end = True
                return None
            self._store(self.current + 1, frame)
            self._prefetch_target = self.current + 1
            self._wake.set()
            return frame
        finally:
            self._lock.release()

    def prev_frame(self):
        with self._lock:
            return self._read_index_locked(self.current - 1)

    def read_index(self, index: int):
        with self._lock:
            return self._read_index_locked(index)

    def _read_index_locked(self, index: int):
        """跳转到指定帧并读取，越界自动夹紧。返回 BGR 图像或 None。"""
        self._seek_request = None  # 同步跳转会取消未完成的后台请求
        if self.frame_count > 0:
            index = max(0, min(index, self.frame_count - 1))
        else:
            index = max(0, index)
        if index == self._cache_idx and self._cache is not None:
            return self._cache
        if index == self.current + 1 and self._cache is not None and not self.at_end:
            ok, frame = self.cap.read()
            if ok:
                self._store(index, frame)
                self._prefetched = None
                self._prefetch_target = -1
                return frame
        if not self.cap.set(cv2.CAP_PROP_POS_FRAMES, index):
            return self._cache
        self._cache = None
        self._cache_idx = -1
        ok, frame = self.cap.read()
        if not ok:
            return None
        guard = 0
        pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        while pos < index - 0.5 and guard < 120:
            ok, frame = self.cap.read()
            if not ok:
                break
            pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            guard += 1
        self._store(index, frame)
        self._prefetched = None
        self._prefetch_target = -1
        return frame

    def seek_relative(self, p: float):
        """按相对进度定位，p 属于 [0, 1]。"""
        p = max(0.0, min(1.0, p))
        with self._lock:
            if self.frame_count > 0:
                return self._read_index_locked(int(round(p * (self.frame_count - 1))))
            return self._read_index_locked(0)

    def request_seek(self, p: float):
        """请求后台跳转（非阻塞，界面不卡；最终以最后一次请求为准）。"""
        self._seek_request = max(0.0, min(1.0, p))
        self._wake.set()

    def seek_in_flight(self) -> bool:
        """是否还有后台跳转未完成。"""
        if not self._lock.acquire(blocking=False):
            return True  # 后台线程正忙，视为未完成
        try:
            return self._seek_request is not None
        finally:
            self._lock.release()

    def progress(self) -> float:
        if self.frame_count <= 1 or self.current < 0:
            return 0.0
        return self.current / (self.frame_count - 1)

    def release(self):
        self._stop.set()
        self._wake.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
        with self._lock:
            try:
                self.cap.release()
            except Exception:
                pass
