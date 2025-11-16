import { useEffect, useRef, useState } from "react";
import { Button, Card, Form, Input, Select, Space, message } from "antd";
import { apiGet, apiPost } from "../api/client";
import { TemplateDefinition, TaskDefinition } from "../types";

type TestResult = {
  matched: boolean;
  confidence?: number;
  rect?: { x: number; y: number; width: number; height: number };
  click_point?: { x: number; y: number };
  image_size?: { width: number; height: number };
};

export default function TemplateTester() {
  const [templates, setTemplates] = useState<Record<string, TemplateDefinition>>({});
  const [tasks, setTasks] = useState<TaskDefinition[]>([]);
  const [form] = Form.useForm();
  const [result, setResult] = useState<TestResult | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const [previewSrc, setPreviewSrc] = useState<string>("");

  async function loadTemplates(taskId?: string) {
    const res = await apiGet<Record<string, TemplateDefinition>>(`/templates/${taskId ? "?task_id=" + taskId : ""}`);
    setTemplates(res);
  }

  async function loadTasks() {
    const res = await apiGet<{ tasks: TaskDefinition[] }>("/tasks/");
    setTasks(res.tasks);
  }

  useEffect(() => {
    loadTemplates().catch(console.error);
    loadTasks().catch(console.error);
  }, []);

  function drawOverlay(baseImg: HTMLImageElement, res: TestResult) {
    const canvas = canvasRef.current;
    if (!canvas || !res.rect) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    canvas.width = baseImg.width;
    canvas.height = baseImg.height;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(baseImg, 0, 0);
    ctx.strokeStyle = "#ff4d4f";
    ctx.lineWidth = 2;
    ctx.strokeRect(res.rect.x, res.rect.y, res.rect.width, res.rect.height);
    if (res.click_point) {
      ctx.fillStyle = "red";
      ctx.beginPath();
      ctx.arc(res.click_point.x, res.click_point.y, 5, 0, Math.PI * 2);
      ctx.fill();
    }
    // draw template rect as well if needed? (res only has rect)
  }

  async function handleTest() {
    const values = await form.validateFields();
    const res = await apiPost<TestResult>(`/templates/test${values.task_id ? "?task_id=" + values.task_id : ""}`, {
      key: values.key,
      base_image_path: values.base_image_path
    });
    setResult(res);
    // load base image from backend for overlay
    const img = new Image();
    img.onload = () => {
      setPreviewSrc(img.src);
      if (res.matched) {
        drawOverlay(img, res);
      }
    };
    img.src = `/api/templates/base-image?path=${encodeURIComponent(values.base_image_path)}`;
    if (!res.matched) {
      message.warning("未匹配到模板，请检查阈值/区域/底图");
    } else {
      message.success("匹配成功，已在日志突出显示 TEST 记录");
    }
  }

  function handlePreview(file: File) {
    const reader = new FileReader();
    reader.onload = (e) => setPreviewSrc(e.target?.result as string);
    reader.readAsDataURL(file);
    return false;
  }

  return (
    <Space align="start" size={16} style={{ width: "100%" }}>
      <Card title="模板测试" style={{ flex: 1 }}>
        <Form layout="vertical" form={form}>
          <Form.Item name="task_id" label="任务（根据任务加载模板）">
            <Select
              allowClear
              options={tasks.map((t) => ({ label: `${t.name} (${t.id})`, value: t.id }))}
              onChange={(v) => loadTemplates(v)}
            />
          </Form.Item>
          <Form.Item name="key" label="模板 Key" rules={[{ required: true }]}>
            <Select
              placeholder="选择模板"
              options={Object.values(templates).map((t) => ({ label: `${t.key} (${t.description || ""})`, value: t.key }))}
              showSearch
            />
          </Form.Item>
          <Form.Item name="base_image_path" label="底图路径（后端可读）" rules={[{ required: true }]}>
            <Input placeholder="如 tasks/<task_id>/images/base_xxx.png" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" onClick={handleTest}>
                测试匹配
              </Button>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handlePreview(file);
                }}
              />
              <span style={{ color: "#888" }}>选择本地图片仅用于前端预览叠加，后端需能读取输入的路径。</span>
            </Space>
          </Form.Item>
          {result && (
            <div style={{ marginTop: 12 }}>
              {result.matched ? (
                <div>
                  <div>置信度: {result.confidence?.toFixed(3)}</div>
                  <div>
                    匹配框: {result.rect?.x}, {result.rect?.y}, {result.rect?.width}x{result.rect?.height}
                  </div>
                  <div>
                    点击点: {result.click_point?.x}, {result.click_point?.y}
                  </div>
                </div>
              ) : (
                <div style={{ color: "#faad14" }}>未匹配到模板</div>
              )}
            </div>
          )}
        </Form>
      </Card>
      <Card title="预览与叠加" style={{ width: 520 }}>
        {previewSrc ? (
          <div style={{ border: "1px dashed #ddd", display: "inline-block" }}>
            <img ref={imgRef} src={previewSrc} alt="preview" style={{ maxWidth: 500, display: "block" }} />
            <canvas ref={canvasRef} style={{ display: "block" }} />
          </div>
        ) : (
          <div>选择本地图片或测试后查看匹配框和点击点</div>
        )}
      </Card>
    </Space>
  );
}
