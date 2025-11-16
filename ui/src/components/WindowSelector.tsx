import { useEffect, useState } from "react";
import { Button, List, Space, message } from "antd";
import { apiGet, apiPost } from "../api/client";
import { WindowInfo } from "../types";

interface Props {
  onSelect: (cfg: { title_contains?: string; process_name?: string; hwnd?: number }) => void;
}

export default function WindowSelector({ onSelect }: Props) {
  const [windows, setWindows] = useState<WindowInfo[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const list = await apiGet<WindowInfo[]>("/windows/");
      setWindows(list);
    } catch (err: any) {
      console.error(err);
      message.error("Failed to load windows. Please ensure backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  async function handleSelect(win: WindowInfo) {
    try {
      const cfg = await apiPost("/window/select", {
        title_contains: win.title,
        process_name: win.process_name,
        hwnd: win.hwnd
      });
      message.success("Window selected");
      localStorage.setItem("last_window_config", JSON.stringify(cfg));
      onSelect(cfg as any);
    } catch (err: any) {
      console.error(err);
      message.error("Bind window failed. Please ensure the window exists and backend is healthy.");
    }
  }

  async function handleScreenshot(win: WindowInfo) {
    try {
      const res = await apiPost<{ path: string }>(`/window/${win.hwnd}/screenshot-base`);
      message.success(`Screenshot saved: ${res.path}`);
    } catch (err: any) {
      console.error(err);
      message.error("Screenshot failed. Please ensure backend is healthy and window is visible.");
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 8 }}>
        <Button onClick={load}>刷新窗口列表</Button>
      </Space>
      <List
        bordered
        size="small"
        loading={loading}
        dataSource={windows}
        renderItem={(item) => (
          <List.Item
            actions={[
              <a key="select" onClick={() => handleSelect(item)}>
                绑定
              </a>,
              <a key="shot" onClick={() => handleScreenshot(item)}>
                截图
              </a>
            ]}
          >
            <List.Item.Meta title={`${item.title} (PID:${item.process_name ?? "?"})`} description={`HWND: ${item.hwnd}`} />
          </List.Item>
        )}
      />
    </div>
  );
}
