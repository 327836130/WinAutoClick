from engine.task_base import TaskBase
from engine.window import TargetWindowConfig


class NotepadDemoTask(TaskBase):
    """
    Example task that waits for a template to appear in Notepad then clicks it.
    Replace template keys with real captures from Template Studio.
    """

    def __init__(self):
        super().__init__(target_window=TargetWindowConfig(title_contains="Notepad"))

    def run(self, context=None):
        self.log("Waiting for NOTEPAD_SAVE_BUTTON to appear")
        if self.appear_then_click("NOTEPAD_SAVE_BUTTON", timeout=5):
            self.log("Clicked save button")
        else:
            self.log("Save button not found", level="WARN")


def main(context=None):
    task = NotepadDemoTask()
    task.run(context)
