from engine.task_base import TaskBase
from engine.window import TargetWindowConfig


class LogOnlyTask(TaskBase):
    def run(self, context=None):
        self.log("LogOnlyTask demo started")
        self.log("This task only writes logs and exits")
        self.sleep(0.5)
        self.log("LogOnlyTask demo finished")


def main(context=None):
    task = LogOnlyTask(target_window=TargetWindowConfig(title_contains=""))
    task.run(context)
