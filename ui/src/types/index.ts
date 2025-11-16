export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
  type?: string;
}

export interface TemplateDefinition {
  key: string;
  file: string;
  description?: string;
  match: { threshold: number; method: string };
  search_region?: Rect | null;
  click: { mode: string; padding: Record<string, number> };
  type: string;
}

export interface TaskDefinition {
  id: string;
  name: string;
  script: string;
  entry: string;
  path?: string;
  templates_path?: string;
  target_window?: {
    title_contains?: string;
    process_name?: string;
    hwnd?: number | null;
  };
}

export interface WindowInfo {
  hwnd: number;
  title: string;
  process_name?: string;
  rect: { left: number; top: number; right: number; bottom: number };
}

export interface LogRecord {
  level: string;
  message: string;
  task_id?: string | null;
  created_at: number;
}
