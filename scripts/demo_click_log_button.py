import time

import win32gui

from engine.task_base import TaskBase
from engine.window import TargetWindowConfig


class ClickLogButtonTask(TaskBase):
    """
    示例：自动获取当前前台窗口，点击模板并记录日志。
    依赖模板：
      - NOTEPAD_SAVE_BUTTON（示例）
      - log_button（你在 Template Studio 新建的按钮模板）
    运行前请确保当前前台窗口就是你要操作的窗口。
    """

    def __init__(self, target_window=None):
        # 先不绑定窗口，稍后在 run 中动态获取前台 hwnd
        super().__init__(target_window=target_window)

    def bind_foreground_window(self):
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            raise RuntimeError("无法获取前台窗口句柄，请确保有活动窗口")
        # 通过 hwnd 绑定
        self.target_window_config = TargetWindowConfig(hwnd=hwnd)
        self.hwnd = hwnd
        self.log(f"绑定前台窗口 hwnd={hwnd}")

    def run(self, context=None):
        # 绑定当前前台窗口
        self.bind_foreground_window()
        self.ensure_window_focused()
        # 截图 + 测试匹配
        self.screenshot()
        if self.appear("log_button"):
            self.log("检测到 log_button，准备点击")
            self.click_template("log_button")
            self.log("已点击 log_button")
        else:
            self.log("未检测到 log_button 模板", level="WARN")
        # 再试 Notepad 保存按钮示例
        self.screenshot()
        if self.appear("NOTEPAD_SAVE_BUTTON"):
            self.log("检测到 NOTEPAD_SAVE_BUTTON，准备点击")
            self.click_template("NOTEPAD_SAVE_BUTTON")
            self.log("已点击 NOTEPAD_SAVE_BUTTON")
        else:
            self.log("未检测到 NOTEPAD_SAVE_BUTTON", level="WARN")
        time.sleep(0.5)


def main(context=None):
    task = ClickLogButtonTask()
    task.run(context)
