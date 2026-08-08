"""生成带帧号的测试视频，用于验证同步、逐帧与划像效果。"""

import os

import cv2
import numpy as np


def make(path, width, height, frames, fps, color, tag, speed):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    for i in range(frames):
        img = np.full((height, width, 3), color, np.uint8)
        x = int((i * speed) % (width - 80))
        y = height // 2
        cv2.rectangle(img, (x, y - 30), (x + 60, y + 30), (255, 255, 255), -1)
        cv2.putText(img, f"{tag} {i:04d}", (36, 78),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
        vw.write(img)
    vw.release()
    print("生成:", path, f"{width}x{height}", frames, "帧")


def main():
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_videos"))
    make(os.path.join(out, "video1.mp4"), 640, 360, 300, 30, (30, 30, 160), "A", 3)
    make(os.path.join(out, "video2.mp4"), 640, 360, 300, 30, (30, 140, 30), "B", 5)
    make(os.path.join(out, "video3.mp4"), 640, 360, 300, 30, (140, 100, 20), "C", 7)
    make(os.path.join(out, "videoV1.mp4"), 360, 640, 300, 30, (20, 90, 140), "V", 4)


if __name__ == "__main__":
    main()
