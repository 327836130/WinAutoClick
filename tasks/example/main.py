from engine.task_base import TaskBase


class MainTask(TaskBase):
    def run(self, context=None):
        self.log("示例任务运行，尚未实现业务逻辑")
