import { useEffect, useRef, useState } from "react";
import { Button, Card, Col, Form, Input, InputNumber, Row, Select, Space, Table, Upload, message, Radio } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import { apiGet, apiPost } from "../api/client";
import { TemplateDefinition, TaskDefinition } from "../types";

type Rect = { x: number; y: number; width: number; height: number };

export default function TemplateStudio() {
  const [templates, setTemplates] = useState<Record<string, TemplateDefinition>>({});
  const [tasks, setTasks] = useState<TaskDefinition[]>([]);
  const [form] = Form.useForm();
  const [imageSrc, setImageSrc] = useState<string>("");
  const [drawMode, setDrawMode] = useState<"template" | "search">("template");
  const [templateRect, setTemplateRect] = useState<Rect | null>(null);
  const [searchRect, setSearchRect] = useState<Rect | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);

  async function loadTemplates() {
    const taskId = form.getFieldValue("task_id");
    const res = await apiGet<Record<string, TemplateDefinition>>(`/templates/${taskId ? "?task_id=" + taskId : ""}`);
    setTemplates(res);
  }

  async function loadTasks() {
    const res = await apiGet<{ tasks: TaskDefinition[] }>("/tasks/");
    setTasks(res.tasks);
  }

  useEffect(() => {
    loadTasks().catch(console.error);
  }, []);

  async function handleFile(file: File) {
    const reader = new FileReader();
    reader.onload = (e) => {
      setImageSrc(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Upload to backend so base_image_path auto填充
    const fd = new FormData();
    fd.append("file", file);
    const taskId = form.getFieldValue("task_id");
    const url = taskId ? `/api/templates/upload-base?task_id=${encodeURIComponent(taskId)}` : "/api/templates/upload-base";
    if (taskId) {
      fd.append("task_id", taskId);
    }
    try {
      const res = await fetch(url, {
        method: "POST",
        body: fd
      });
      if (!res.ok) throw new Error(await res.text());
      const data: any = await res.json();
      form.setFieldsValue({ base_image_path: data.path });
      message.success("底图已上传，路径自动填充");
    } catch (err: any) {
      console.error(err);
      message.error("底图上传失败，请检查后端");
    }
    return false;
  }

  function drawRect(ctx: CanvasRenderingContext2D, rect: Rect, color: string) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);
  }

  function redrawCanvas() {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    canvas.width = img.width;
    canvas.height = img.height;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);
    if (templateRect) drawRect(ctx, templateRect, "#ff4d4f");
    if (searchRect) drawRect(ctx, searchRect, "#52c41a");
  }

  useEffect(() => {
    redrawCanvas();
  }, [imageSrc, templateRect, searchRect]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let dragging = false;
    let startX = 0;
    let startY = 0;

    function onMouseDown(e: MouseEvent) {
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      startX = e.clientX - rect.left;
      startY = e.clientY - rect.top;
      dragging = true;
    }

    function onMouseMove(e: MouseEvent) {
      if (!dragging || !canvas) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const w = x - startX;
      const h = y - startY;
      const newRect: Rect = {
        x: w >= 0 ? startX : x,
        y: h >= 0 ? startY : y,
        width: Math.abs(w),
        height: Math.abs(h)
      };
      if (drawMode === "template") {
        setTemplateRect(newRect);
      } else {
        setSearchRect(newRect);
      }
    }

    function onMouseUp() {
      dragging = false;
    }

    canvas.addEventListener("mousedown", onMouseDown);
    canvas.addEventListener("mousemove", onMouseMove);
    canvas.addEventListener("mouseup", onMouseUp);
    canvas.addEventListener("mouseleave", onMouseUp);
    return () => {
      canvas.removeEventListener("mousedown", onMouseDown);
      canvas.removeEventListener("mousemove", onMouseMove);
      canvas.removeEventListener("mouseup", onMouseUp);
      canvas.removeEventListener("mouseleave", onMouseUp);
    };
  }, [drawMode, canvasRef.current]);

  async function handleSave() {
    const values = await form.validateFields();
    if (!templateRect) {
      message.error("请先在图片上框选模板区域");
      return;
    }
    const img = imgRef.current;
    if (!img) {
      message.error("请先加载底图");
      return;
    }
    const toRelative = (r: Rect) => ({
      x: r.x / img.width,
      y: r.y / img.height,
      width: r.width / img.width,
      height: r.height / img.height,
      type: "relative"
    });
    await apiPost("/templates/", {
      task_id: values.task_id || null,
      base_image_path: values.base_image_path,
      template_rect: toRelative(templateRect),
      search_region: searchRect ? toRelative(searchRect) : null,
      key: values.key,
      description: values.description,
      threshold: values.threshold ?? 0.85,
      click_mode: values.click_mode,
      padding: {
        left: values.padding_left ?? 0,
        right: values.padding_right ?? 0,
        top: values.padding_top ?? 0,
        bottom: values.padding_bottom ?? 0
      },
      match_method: values.match_method
    });
    message.success("模板已保存");
    await loadTemplates();
  }

  return (
    <Row gutter={16}>
      <Col span={14}>
        <Card
          title={
            <Space>
              <span>底图/框选</span>
              <Upload accept="image/*" beforeUpload={handleFile} showUploadList={false}>
                <Button icon={<UploadOutlined />}>选择本地图片用于框选</Button>
              </Upload>
              <Radio.Group value={drawMode} onChange={(e) => setDrawMode(e.target.value)}>
                <Radio.Button value="template">模板区域</Radio.Button>
                <Radio.Button value="search">搜索区域</Radio.Button>
              </Radio.Group>
            </Space>
          }
          size="small"
        >
          {imageSrc ? (
            <div style={{ border: "1px dashed #ddd", display: "inline-block", position: "relative" }}>
              <img
                ref={imgRef}
                src={imageSrc}
                alt="base"
                style={{ display: "none" }}
                onLoad={() => {
                  redrawCanvas();
                }}
              />
              <canvas ref={canvasRef} style={{ cursor: "crosshair" }} />
            </div>
          ) : (
            <p>请通过“选择本地图片用于框选”加载一张截图，然后选择模式框选模板区域和搜索区域。</p>
          )}
        </Card>
        <Card title="模板参数" size="small" style={{ marginTop: 12 }}>
          <Form form={form} layout="vertical">
            <Form.Item name="task_id" label="所属任务（用于图片分目录，可选）">
              <Select
                allowClear
                placeholder="选择任务"
                options={tasks.map((t) => ({ label: `${t.name} (${t.id})`, value: t.id }))}
                onChange={() => loadTemplates()}
              />
            </Form.Item>
            <Form.Item name="base_image_path" label="底图路径（自动填充）" rules={[{ required: true }]}>
              <Input placeholder="请先上传底图，系统将自动填充" disabled />
            </Form.Item>
            <Form.Item name="key" label="模板 Key" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <Input.TextArea rows={2} />
            </Form.Item>
            <Form.Item name="match_method" label="匹配方法" initialValue="TM_CCOEFF_NORMED">
              <Select
                options={[
                  { value: "TM_CCOEFF_NORMED", label: "TM_CCOEFF_NORMED" },
                  { value: "TM_CCORR_NORMED", label: "TM_CCORR_NORMED" },
                  { value: "TM_SQDIFF_NORMED", label: "TM_SQDIFF_NORMED" }
                ]}
              />
            </Form.Item>
            <Form.Item name="threshold" label="阈值" initialValue={0.85}>
              <InputNumber min={0} max={1} step={0.01} />
            </Form.Item>
            <Form.Item name="click_mode" label="点击模式" initialValue="center">
              <Select
                options={[
                  { label: "Center", value: "center" },
                  { label: "Random", value: "random" }
                ]}
              />
            </Form.Item>
            <Form.Item label="点击 Padding（0~1）">
              <Space.Compact block>
                <Form.Item name="padding_left" noStyle>
                  <InputNumber placeholder="left" min={0} max={1} step={0.01} />
                </Form.Item>
                <Form.Item name="padding_right" noStyle>
                  <InputNumber placeholder="right" min={0} max={1} step={0.01} />
                </Form.Item>
                <Form.Item name="padding_top" noStyle>
                  <InputNumber placeholder="top" min={0} max={1} step={0.01} />
                </Form.Item>
                <Form.Item name="padding_bottom" noStyle>
                  <InputNumber placeholder="bottom" min={0} max={1} step={0.01} />
                </Form.Item>
              </Space.Compact>
            </Form.Item>
            <Form.Item>
              <Button type="primary" onClick={handleSave}>
                保存模板
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Col>
      <Col span={10}>
        <Card title="模板列表" size="small">
          <Table
            size="small"
            rowKey="key"
            dataSource={Object.values(templates)}
            columns={[
              { title: "Key", dataIndex: "key" },
              { title: "描述", dataIndex: "description" },
              { title: "文件", dataIndex: "file" },
              { title: "阈值", dataIndex: ["match", "threshold"] },
              { title: "模式", dataIndex: ["click", "mode"] }
            ]}
            pagination={false}
          />
        </Card>
      </Col>
    </Row>
  );
}
