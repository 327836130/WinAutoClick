import { Layout, Tabs, message } from "antd";
import TaskManager from "../components/TaskManager";
import WindowSelector from "../components/WindowSelector";
import TemplateStudio from "../components/TemplateStudio";
import LogViewer from "../components/LogViewer";
import TemplateTester from "../components/TemplateTester";
import { apiPost } from "../api/client";

const { Header, Content, Footer } = Layout;

export default function App() {
  async function handleRun(taskId: string) {
    await apiPost(`/tasks/${taskId}/run`);
    message.success("任务已启动");
  }
  async function handleStop(taskId: string) {
    await apiPost(`/tasks/${taskId}/stop`);
    message.success("已发送停止信号");
  }

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ color: "#fff", fontSize: 18 }}>WinAutoClick 桌面自动点击框架</Header>
      <Content style={{ padding: 16 }}>
        <Tabs
          items={[
            {
              key: "tasks",
              label: "任务管理",
              children: <TaskManager onRun={handleRun} onStop={handleStop} />
            },
            {
              key: "windows",
              label: "窗口绑定/截图",
              children: <WindowSelector onSelect={() => message.success("窗口绑定成功，可在任务中保存 target_window")} />
            },
            {
              key: "templates",
              label: "模板编辑器",
              children: <TemplateStudio />
            },
            {
              key: "tester",
              label: "模板测试",
              children: <TemplateTester />
            },
            {
              key: "logs",
              label: "日志",
              children: <LogViewer />
            }
          ]}
        />
      </Content>
      <Footer style={{ textAlign: "center" }}>通用桌面自动点击脚本框架 · React + FastAPI</Footer>
    </Layout>
  );
}
