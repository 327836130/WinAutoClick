# WinAutoClick 桌面自动点击脚本框架

基于 Python + FastAPI + OpenCV + pyautogui + React/Vite 的“通用桌面自动点击脚本框架”，可对任意 Windows 窗口进行截图、模板管理、随机点击和任务脚本运行。前后端联动，内置模板编辑器（Template Studio）和示例任务，方便扩展到自己的业务。

## 目录结构

- `engine/`：核心执行引擎（窗口管理、截图、模板匹配、输入控制、任务基类、执行器）
- `modules/`：可扩展模块占位（如 OCR 引擎），当前提供 `ocr_dummy.py`
- `scripts/`：任务脚本示例，支持继承 TaskBase
- `assets/`：模板图片与配置（`images/`、`templates.yaml`、`tasks.json`）
- `backend/`：FastAPI 后端，`run_app.py` 为打包入口
- `ui/`：React + TypeScript + Vite 前端（Ant Design）
- `tools/`：辅助脚本（如 `build.bat` 用于一键打包）
- `requirements.txt`：Python 依赖列表

## 环境准备

- Windows 10/11
- Python 3.12（含 pip），建议创建虚拟环境
- Node.js 18+（用于前端构建）
- 系统需安装 VC++ 运行库以及具备桌面图形环境

## 安装依赖

```powershell
cd WinAutoClick
python -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

前端依赖：

```powershell
cd ui
npm install
```

## 开发运行

1. 后端（FastAPI + 引擎）
   ```powershell
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
2. 前端（Vite Dev Server）
   ```powershell
   cd ui
   npm run dev -- --host --port 5173
   ```
   前端默认代理 `/api` 到 `http://127.0.0.1:8000`。

访问 `http://127.0.0.1:5173` 查看 UI。

## 核心能力概览

- **目标窗口管理**：按标题或进程名锁定窗口，激活窗口，获取窗口矩形，窗口截图；所有匹配和点击都以目标窗口坐标系为基准。
- **截图与模板系统**：底图截图后，在 Template Studio 配置模板区域、搜索区域、阈值、点击模式与 padding；保存后裁剪小图至 `assets/images/` 并写入 `assets/templates.yaml`。
- **模板匹配与随机点击**：OpenCV 模板匹配，在匹配矩形内按 center/random + padding 选点，转换为屏幕坐标后点击。
- **任务脚本体系**：`TaskBase` 提供 `screenshot`、`appear`、`wait_appear`、`click_template`、`appear_then_click`、`log`、`ensure_window_focused` 等高阶 API；`engine/executor.py` 支持按配置动态加载脚本并启动线程执行。
- **日志系统**：线程安全日志池，`/api/logs` 轮询查看。

## Template Studio 使用流程

1. 在“窗口绑定/截图”页选择目标窗口，点击“截图”生成底图（文件路径返回给前端）。
2. 将底图路径填入 Template Studio 的“底图路径”，输入模板 key/描述、相对坐标（0~1）、阈值、点击模式与 padding，可选搜索区域。
3. 点击“保存模板”：后端会裁剪小图到 `assets/images/<key>.png` 并写入 `assets/templates.yaml`。
4. 任务脚本中通过模板 key 使用，如 `self.appear_then_click("NOTEPAD_SAVE_BUTTON")`。

## 新增任务脚本

1. 在 `scripts/` 创建脚本，继承 `TaskBase` 并实现 `run`：

   ```python
   from engine.task_base import TaskBase
   from engine.window import TargetWindowConfig

   class MyTask(TaskBase):
       def __init__(self):
           super().__init__(target_window=TargetWindowConfig(title_contains="记事本"))

       def run(self, context=None):
           self.ensure_window_focused()
           self.appear_then_click("NOTEPAD_SAVE_BUTTON", timeout=5)
   ```

2. 在 `assets/tasks.json` 添加任务配置（id/name/script/entry/target_window）。
3. 前端“任务管理”页刷新后即可看到任务，点击“运行”启动。

## 示例脚本

- `scripts/demo_log_only.py`：仅写日志的简单示例。
- `scripts/demo_click_notepad.py`：等待并点击 `NOTEPAD_SAVE_BUTTON` 模板的示例（需先用 Template Studio 生成真实模板）。

## 打包发布（Windows）

1. 构建前端：`cd ui && npm run build`
2. 复制前端产物到 `frontend/`（`tools/build.bat` 已包含此步骤）
3. 使用 PyInstaller 打包后端/引擎：
   ```powershell
   pyinstaller --onefile --name AutoClickFramework backend\run_app.py
   ```
4. 发布目录建议：
   ```
   AutoClickFramework.exe   # 引擎 + FastAPI
   frontend/                # 前端静态资源
   scripts/                 # 脚本
   assets/                  # 模板图片与配置
   ```
启动 exe 后会自动运行服务并尝试打开浏览器访问 `http://127.0.0.1:8000`。

## 备注与后续扩展

- OCR 目前为占位实现，可在 `modules/ocr_dummy.py` 替换为真实 OCR 引擎并在模板/TaskBase 中接入。
- 模板匹配基于 OpenCV，默认方法/阈值可在 `assets/templates.yaml` 中调整。
- 更多自动化动作（拖拽、热键等）可扩展 `engine/input.py` 与 `TaskBase`。
