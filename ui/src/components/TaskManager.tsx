import { useEffect, useState } from "react";
import { Button, Form, Input, List, Modal, Space, message } from "antd";
import { apiGet, apiPost } from "../api/client";
import { TaskDefinition, WindowInfo } from "../types";

interface Props {
  onRun: (taskId: string) => void;
}

export default function TaskManager({ onRun }: Props) {
  const [tasks, setTasks] = useState<TaskDefinition[]>([]);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm<TaskDefinition>();
  const [scriptContent, setScriptContent] = useState<string>("");
  const [windows, setWindows] = useState<WindowInfo[]>([]);
  const [windowModal, setWindowModal] = useState<{ visible: boolean; task?: TaskDefinition; runAfterBind?: boolean }>({
    visible: false,
  });

  async function load() {
    const res = await apiGet<{ tasks: TaskDefinition[] }>("/tasks/");
    setTasks(res.tasks);
  }

  async function loadWindows() {
    const res = await apiGet<WindowInfo[]>("/windows/");
    setWindows(res);
  }

  async function loadWindows() {
    try {
      const res = await apiGet<WindowInfo[]>("/windows/");
      setWindows(res);
    } catch (err) {
      console.error(err);
      message.error("读取窗口列表失败，请确认后端运行正常");
    }
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  async function handleSave() {
    try {
      const values = await form.validateFields();
      await apiPost<TaskDefinition>("/tasks/", {
        ...values,
        script_content: scriptContent,
        script: "main.py",
        entry: "MainTask",
      });
      message.success("任务已保存");
      setOpen(false);
      await load();
    } catch (err: any) {
      console.error(err);
      message.error(`保存失败: ${err.message || err}`);
    }
  }

  async function applyWindowAndRun(task: TaskDefinition, hwnd: number, title?: string, process_name?: string) {
    const updated: TaskDefinition = {
      ...task,
      target_window: {
        title_contains: title ?? task.target_window?.title_contains,
        process_name: process_name ?? task.target_window?.process_name,
        hwnd,
      },
    };
    // 保存更新后的任务
    await apiPost<TaskDefinition>("/tasks/", updated);
    await load();
    onRun(task.id);
  }

  async function ensureWindowAndRun(task: TaskDefinition) {
    // 如果已有 hwnd，直接运行
    if (task.target_window && task.target_window.hwnd) {
      onRun(task.id);
      return;
    }
    // 否则弹出窗口选择
    await loadWindows();
    setWindowModal({ visible: true, task, runAfterBind: true });
  }

  async function openBindModal(task: TaskDefinition) {
    await loadWindows();
    setWindowModal({ visible: true, task, runAfterBind: false });
  }

  async function openEditor(task?: TaskDefinition) {
    form.resetFields();
    if (task) {
      form.setFieldsValue({ id: task.id, name: task.name });
      try {
        const res = await apiGet<{ content: string }>(`/tasks/${task.id}/script`);
        setScriptContent(res.content);
      } catch {
        setScriptContent("");
      }
    } else {
      form.setFieldsValue({ id: "", name: "" });
      setScriptContent(
        "from engine.task_base import TaskBase\n\nclass MainTask(TaskBase):\n    def run(self, context=None):\n        self.log('hello from task')\n"
      );
    }
    setOpen(true);
  }

  return (
    <div>
      <Space style={{ marginBottom: 12 }}>
        <Button type="primary" onClick={() => openEditor()}>
          新建任务
        </Button>
        <Button onClick={load}>刷新</Button>
      </Space>
      <List
        bordered
        dataSource={tasks}
        renderItem={(item) => (
          <List.Item
            actions={[
              <a key="bind" onClick={() => openBindModal(item)}>
                {item.target_window && item.target_window.hwnd ? "已绑定" : "绑定窗口"}
              </a>,
              <a key="edit" onClick={() => openEditor(item)}>
                编辑
              </a>,
              <a key="run" onClick={() => ensureWindowAndRun(item)}>
                运行
              </a>,
            ]}
          >
            <List.Item.Meta title={`${item.name} (${item.id})`} description={`${item.script || "main.py"} :: ${item.entry || "MainTask"}`} />
          </List.Item>
        )}
      />

      <Modal open={open} onCancel={() => setOpen(false)} onOk={handleSave} title="任务配置" destroyOnClose width={900}>
        <Form form={form} layout="vertical">
          <Form.Item name="id" label="任务 ID" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="任务名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="脚本内容">
            <Input.TextArea
              rows={14}
              value={scriptContent}
              onChange={(e) => setScriptContent(e.target.value)}
              placeholder="编辑任务脚本（默认 MainTask.run）"
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={windowModal.visible}
        onCancel={() => setWindowModal({ visible: false, task: undefined })}
        title="选择要绑定的窗口"
        footer={null}
      >
        <List
          bordered
          dataSource={windows}
          renderItem={(win) => (
            <List.Item
              actions={[
                <a
                  key="bind"
                  onClick={() => {
                    if (!windowModal.task) return;
                    applyWindowAndRun(windowModal.task, win.hwnd, win.title, win.process_name)
                      .then(() => {
                        if (!windowModal.runAfterBind) {
                          message.success("已绑定窗口");
                        }
                      })
                      .catch((err) => {
                        console.error(err);
                        message.error("绑定窗口失败");
                      })
                      .finally(() => {
                        setWindowModal({ visible: false, task: undefined });
                      });
                  }}
                >
                  {windowModal.runAfterBind ? "绑定并运行" : "绑定窗口"}
                </a>,
              ]}
            >
              <List.Item.Meta title={`${win.title}`} description={`HWND: ${win.hwnd} 进程: ${win.process_name || ""}`} />
            </List.Item>
          )}
        />
      </Modal>
    </div>
  );
}
