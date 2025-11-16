from engine.task_base import TaskBase


class MainTask(TaskBase):
    def run(self, context=None):
        # 仅前置窗口，不调整大小
        self.ensure_window_focused()
        hwnd = self.get_window()
        self.log(f"已前置窗口 hwnd={hwnd}，立即检测 log_button")

        # 执行匹配+点击
        clicked = self.appear_then_click("log_button", timeout=5, interval=0.5)
        if clicked:
            self.log("已点击 log_button")
        else:
            self.log("未匹配到 log_button", level="WARN")
