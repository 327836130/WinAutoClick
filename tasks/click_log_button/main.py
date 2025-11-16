from pathlib import Path

from engine.task_base import TaskBase


class MainTask(TaskBase):
    def run(self, context=None):
        # 强制使用本任务目录的模板配置，避免回退到全局 assets
        self.template_config_path = Path(__file__).parent / "templates.yaml"
        self.log(f"模板配置已锁定为 {self.template_config_path}", level="TEST")

        # 仅前置窗口，不改变窗口大小
        self.ensure_window_focused()
        hwnd = self.get_window()
        self.log(f"已前置窗口 hwnd={hwnd}，开始匹配 test_button 模板")

        # 使用任务目录的 templates.yaml，匹配并点击 log_button
        clicked = self.appear_then_click("test_button", timeout=8, interval=0.5)
        if clicked:
            self.log("已点击 test_button")
        else:
            self.log("未匹配到 test_button", level="WARN")
