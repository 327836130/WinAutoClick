import { useEffect, useState } from "react";
import { Card, List, Tag } from "antd";
import { apiGet } from "../api/client";
import { LogRecord } from "../types";
import { formatTime } from "../utils/time";

export default function LogViewer() {
  const [logs, setLogs] = useState<LogRecord[]>([]);

  async function load() {
    const res = await apiGet<LogRecord[]>("/logs/");
    setLogs(res.reverse());
  }

  useEffect(() => {
    load().catch(console.error);
    const timer = setInterval(() => {
      load().catch(console.error);
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  return (
    <Card title="日志" size="small">
      <List
        size="small"
        dataSource={logs}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={
                <span>
                  {formatTime(item.created_at)}{" "}
                  <Tag color={item.level === "ERROR" ? "red" : item.level === "TEST" ? "cyan" : "blue"}>{item.level}</Tag>{" "}
                  {item.task_id ?? ""}
                </span>
              }
              description={item.message}
            />
          </List.Item>
        )}
      />
    </Card>
  );
}
