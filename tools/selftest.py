"""自动化冒烟测试：验证视频引擎与界面各功能，可离屏运行。"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from player.video_reader import VideoReader  # noqa: E402

TEST_DIR = os.path.join(ROOT, "test_videos")
SHOT_DIR = os.path.join(ROOT, "shot")


def test_reader():
    path = os.path.join(TEST_DIR, "video1.mp4")
    r = VideoReader(path)
    assert r.frame_count == 300, r.frame_count
    assert abs(r.fps - 30.0) < 0.5, r.fps
    f = r.read_index(123)
    assert f is not None
    assert r.current == 123
    f = r.next_frame()
    assert f is not None and r.current == 124
    f = r.prev_frame()
    assert r.current == 123
    r.seek_relative(1.0)
    assert r.current == 299
    r.seek_relative(0.0)
    assert r.current == 0
    r.release()
    print("[OK] 视频引擎：打开 / 精确跳帧 / 逐帧 / 相对定位")


def assert_panes_fill(win, tag):
    """验证窗格填满了整个内容区（没有空行列占位）。"""
    st = win.stack
    for i, pane in enumerate(win.panes):
        g = pane.geometry()
        if win.landscape:
            assert g.width() >= st.width() - 2, f"{tag}: pane{i} 宽度未填满 {g.width()} < {st.width()}"
        else:
            assert g.height() >= st.height() - 2, f"{tag}: pane{i} 高度未填满 {g.height()} < {st.height()}"
    if win.landscape:
        total_h = sum(p.geometry().height() for p in win.panes)
        assert total_h >= st.height() - 4, f"{tag}: 上下并列总高度不足 {total_h} < {st.height()}"
    else:
        total_w = sum(p.geometry().width() for p in win.panes)
        assert total_w >= st.width() - 4, f"{tag}: 左右并列总宽度不足 {total_w} < {st.width()}"


def test_gui():
    os.makedirs(SHOT_DIR, exist_ok=True)
    from PySide6.QtWidgets import QApplication  # noqa: E402
    from player.player_window import PlayerWindow  # noqa: E402

    app = QApplication(sys.argv)
    v1 = os.path.join(TEST_DIR, "video1.mp4")
    v2 = os.path.join(TEST_DIR, "video2.mp4")
    v3 = os.path.join(TEST_DIR, "video3.mp4")

    # 2 视频 · 横屏（上下并列）
    win = PlayerWindow(2, True)
    win.show()
    app.processEvents()
    assert_panes_fill(win, "2v横屏")
    win._load_video(0, v1)
    win._load_video(1, v2)
    # 拖动进度条到 50%：后台跳转，等待完成
    win.slider.sliderPressed.emit()
    win.slider.setValue(5000)
    win.slider.sliderReleased.emit()
    deadline = time.time() + 8
    while win.readers[0].seek_in_flight() and time.time() < deadline:
        app.processEvents()
        time.sleep(0.02)
    app.processEvents()
    assert abs(win.readers[0].current - 150) <= 3, \
        f"拖进度条后帧号不对: {win.readers[0].current}"
    # 单击画面切换播放/暂停
    win._set_playing(False)
    win.panes[0].clicked.emit()
    assert win.playing, "单击画面应开始播放"
    win.panes[0].clicked.emit()
    assert not win.playing, "再单击画面应暂停"
    win.wipe_pane.clicked.emit()
    assert win.playing, "划像区单击应开始播放"
    win._set_playing(False)
    for _ in range(5):
        win._step_frame(1)
    win._set_playing(True)
    app.processEvents()
    app.processEvents()
    win._set_playing(False)
    win._on_wheel_zoom({"factor": 1.6, "fx": 0.42, "fy": 0.48})
    app.processEvents()
    win.grab().save(os.path.join(SHOT_DIR, "2v_landscape_zoom.png"))

    # 2 视频 · 划像
    win._reset_zoom()
    win._toggle_wipe()
    app.processEvents()
    win.grab().save(os.path.join(SHOT_DIR, "2v_wipe.png"))
    # 划像模式滚轮缩放：划像窗格与并列窗格同步，双击复位
    win.wipe_pane.wheel_zoom.emit({"factor": 1.5, "fx": 0.42, "fy": 0.48})
    app.processEvents()
    assert abs(win.zoom - 1.5) < 0.01, f"划像滚轮缩放失败: {win.zoom}"
    assert abs(win.wipe_pane.zoom - 1.5) < 0.01, "划像窗格缩放未同步"
    assert abs(win.panes[0].zoom - 1.5) < 0.01, "并列窗格缩放未同步"
    win.grab().save(os.path.join(SHOT_DIR, "2v_wipe_zoom.png"))
    win.wipe_pane.reset_zoom_requested.emit()
    app.processEvents()
    assert win.zoom == 1.0 and win.wipe_pane.zoom == 1.0, "划像双击复位失败"
    # 划像模式下切换布局应自动退出划像，回到并列画面
    win._toggle_layout()
    app.processEvents()
    assert not win.wipe_mode, "切换布局后应自动退出划像模式"
    assert win.stack.currentIndex() == 0, "切换布局后应回到并列画面"
    assert not win.btn_wipe.isChecked()
    assert_panes_fill(win, "2v竖屏")
    # 再次进入划像后，清空视频也应退出划像
    win._toggle_wipe()
    app.processEvents()
    assert win.wipe_mode
    win._clear_videos()
    assert not win.wipe_mode, "清空视频后应退出划像模式"
    win.close()

    # 3 视频 · 横屏（上下并列）
    win3 = PlayerWindow(3, True)
    win3.show()
    app.processEvents()
    assert_panes_fill(win3, "3v横屏")
    win3._load_video(0, v1)
    win3._load_video(1, v2)
    win3._load_video(2, v3)
    win3._step_frame(3)
    app.processEvents()
    win3.grab().save(os.path.join(SHOT_DIR, "3v_landscape.png"))
    win3._toggle_layout()
    app.processEvents()
    assert_panes_fill(win3, "3v竖屏")
    win3.grab().save(os.path.join(SHOT_DIR, "3v_portrait.png"))
    win3.close()

    # 多文件拖入：一次拖 2 个文件自动填入两个窗口，已满则从第一个替换
    winm = PlayerWindow(2, True)
    winm.show()
    app.processEvents()
    winm._on_videos_dropped(0, [v1, v2])
    assert winm.readers[0] is not None and winm.readers[1] is not None, "多文件拖入未填满窗口"
    assert winm.readers[0].path == v1 and winm.readers[1].path == v2, "多文件顺序不对"
    winm._on_videos_dropped(0, [v3, v1])
    assert winm.readers[0].path == v3 and winm.readers[1].path == v1, "已满时未从第一个替换"
    winm._on_videos_dropped(0, [v1, v2, v3])  # 3 个文件只取前 2 个
    assert winm.readers[0].path == v1 and winm.readers[1].path == v2, "超出窗口数的文件未截断"
    # 空位优先：3 视频只装了第 3 个，再拖 2 个应填到前两个空位
    win3 = PlayerWindow(3, True)
    win3.show()
    app.processEvents()
    win3._load_video(2, v3)
    win3._on_videos_dropped(0, [v1, v2])
    assert win3.readers[0].path == v1 and win3.readers[1].path == v2, "空位未优先填充"
    win3.close()
    # 划像模式多文件拖入
    winw = PlayerWindow(2, True)
    winw.show()
    app.processEvents()
    winw._toggle_wipe()
    winw._on_wipe_videos_dropped([v1, v2])
    assert winw.readers[0].path == v1 and winw.readers[1].path == v2, "划像多文件拖入失败"
    winw.close()
    print("[OK] 界面：2/3 视频、横竖布局、缩放、划像、多文件拖入均正常")


def main():
    test_reader()
    test_gui()
    print("全部自测通过。截图目录:", SHOT_DIR)


if __name__ == "__main__":
    main()
