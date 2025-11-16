你现在扮演一名资深架构师 + 全栈工程师 + 桌面自动化专家。  
请为我从零设计并实现一个“通用桌面自动点击脚本框架”，并将完整项目推送到我的 GitHub 仓库。

⚠ 重要前提：
- 目标平台：Windows（桌面环境）。
- 语言与技术栈：
  - 后端 & 引擎：Python 3.12。
  - Web 后端框架：FastAPI。
  - 桌面自动化：pyautogui、win32 API、OpenCV（模板匹配）。
  - 前端：React + TypeScript + Vite。


本项目要实现的是一个“通用版 OnmyojiAutoScript（OAS）”，但完全**不绑定任何具体游戏/应用**，而是面向“任何 Windows 窗口程序”。

===========================
一、整体目标与理念
===========================

本框架应支持：

1. **目标窗口管理（简化版）**
   - 不做复杂多窗口管理，只做这一件事：
     > 为每个任务绑定一个目标窗口：用户选一次，以后所有操作（截图、识别、点击）都针对这个窗口。
   - 支持通过以下方式确定目标窗口：
     - 按窗口标题关键字（title_contains）
     - 按进程名（process_name）（可选）
   - 在脚本执行时：
     - 通过配置（TargetWindowConfig）自动找到当前目标窗口的句柄（HWND）。
     - 能把窗口激活/置前。
     - 能对该窗口截图，并进行窗口坐标 ↔ 屏幕坐标转换。

2. **截图 & 图像模板系统（Template Studio 子系统）**
   - 这部分是一个**相对独立但紧密集成的模块**，请认真设计：
     - 第一次对目标窗口整窗截图，得到一张“底图”；
     - 在内置的“模板编辑器”（前端模块）中：
       - 在底图上用鼠标框选“模板区域”（即小图所在区域）；
       - 可选再框选或自动生成一个“搜索区域”（相对窗口坐标的矩形），匹配时只在这块区域内搜索；
       - 为这个模板填写：
         - key：如 `NOTEPAD_SAVE_BUTTON`（逻辑 ID，脚本中用这个名字）
         - description：中文描述
         - match_threshold：匹配阈值（如 0.8 / 0.9）
         - click 模式：
           - mode：`"center"` 或 `"random"`
           - padding：在模板矩形内部再缩小一圈（left/right/top/bottom 为 0~1 的比例），随机时只在这块缩小后的区域内点击
     - 当用户在模板编辑器中点击“保存模板”时，系统自动：
       - 从底图中裁剪模板区域 → 保存为 `assets/images/<key>.png`
       - 将模板配置写入一个统一配置文件，例如：`assets/templates.yaml` 或 `assets/templates.json`：
         - 包含字段：
           - `file`：小图文件名
           - `description`
           - `match`：`threshold`、`method`（OpenCV 模板匹配方法）
           - `search_region`：相对坐标（0~1）格式的矩形 `{ type: "relative", x, y, width, height }`
           - `click`：`mode` + `padding`（left/right/top/bottom）
       - （可选）自动生成一段示例脚本片段，在 UI 中展示，告诉用户如何在脚本中使用此模板。

   - 重点：
     - 所有模板图必须来源于“目标窗口的截图”。
     - 所有匹配都只在“目标窗口的截图”里进行。
     - `search_region` 是相对窗口坐标（0~1），匹配时转换为实际像素区域。

3. **输入控制**
   - 通过 pyautogui 和/或 win32 API 实现：
     - 点击 / 双击 / 右键点击；
     - 拖拽 / 滑动（可用于滚动条、拖动窗口等）；
     - 键盘输入（文本输入、快捷键）。
   - 支持从“窗口坐标系下的点”转为“全局屏幕坐标”，在该点进行点击/滑动。
   - 点击区域要支持“随机点击”：在模板匹配出的矩形内部（或内部缩小的一块区域）随机选点。

4. **任务脚本系统（Python 脚本 + 高级 API）**
   - 任务逻辑以 **Python 脚本** 的形式存在，放在 `scripts/` 目录。
   - 脚本编写模式参考 OAS，但要通用化：
     - 有一套底层 Template 类（ImageTemplate / ClickTemplate / OcrTemplate 等）；
     - 有一套自动生成的 Assets 类（每个应用/任务一份）；
     - 有一个 TaskBase 基类，提供高级 API，如：
       - `screenshot()`
       - `appear(template, threshold=None) -> bool`
       - `wait_appear(template, timeout, interval)`
       - `appear_then_click(template, timeout, interval)`
       - `click_template(template_or_key, threshold=None, interval=0.2)`
       - `read_text(ocr_template_or_key) -> str/int/...`
       - `log(msg)`
   - 脚本作者只需要：
     - 继承 TaskBase + 对应 Assets 类；
     - 写 `run(self)` 或 `main(context=None)` 方法实现业务逻辑。
   - 示例脚本（类风格示例）：

     ```python
     from engine.task_base import TaskBase
     from assets.notepad_assets import NotepadAssets

     class NotepadTask(TaskBase, NotepadAssets):
         def run(self):
             self.log("Notepad task started")

             self.ensure_window_focused()
             while True:
                 self.screenshot()

                 if self.appear_then_click(self.BTN_SAVE, interval=1.0):
                     self.log("点击了保存按钮")
                     continue

                 if self.appear(self.BTN_CLOSE, threshold=0.7):
                     self.click_template(self.BTN_CLOSE)
                     self.log("检测到关闭按钮，任务结束")
                     break
     ```

5. **图形化 UI**
   - UI 不需要花里胡哨，但要清晰实用：
     - **任务管理**：
       - 查看当前任务列表（从 `scripts/` 或配置中扫描到的任务信息）。
       - 编辑任务元数据：任务 ID、名称、脚本文件名、入口函数名，以及绑定的目标窗口配置（title_contains / process_name）。
       - 一键运行任务、停止任务。
     - **目标窗口选择**：
       - 提供按钮“选择目标窗口”：
         - 方案 A：列出当前窗口（标题 + 进程名）供用户选择；
         - 方案 B：提示“请切换到目标程序窗口并按下某个快捷键”，后台捕获当前前台窗口。
       - 选择后，为当前任务保存一个 TargetWindowConfig。
     - **模板编辑器（Template Studio）**：
       - 选择一个任务 → 使用其目标窗口 → 对窗口整窗截图作为底图；
       - 底图显示在画布中，用户可以绘制矩形选区作为模板区域；
       - 可以设置/查看：
         - 模板 key
         - 描述
         - 阈值
         - 搜索区域（默认以模板框为中心放大一定倍数，也可手动调整）
         - 点击模式（居中 / 随机）和 padding 参数；
       - 保存模板时，调用后端 API 完成裁剪、配置写入，并在列表中展示。
     - **日志查看**：
       - 实时或轮询显示任务执行的日志（时间、任务名、消息类型、内容）。

6. **打包部署（Windows）**
   - 引擎 + 后端使用 PyInstaller 打包为**单个 exe**。
   - 前端使用 Vite 打包为静态文件，放入 `frontend/` 目录。
   - 最终发布目录结构示例（安装目录）：

     ```text
     C:/AutoClickFramework/
       AutoClickFramework.exe   # 引擎 + FastAPI 后端
       frontend/                # 前端静态资源（build 产物）
       scripts/                 # 任务脚本（Python），用户可随意增删改
       assets/
         images/                # 模板图片
         templates.yaml         # 模板配置
     ```

   - exe 启动时：
     - 自动根据是否为打包环境选择前端静态目录（开发环境下指向 ui/dist，打包环境下指向 exe 同级的 frontend）。
     - 启动 uvicorn 服务器，监听 8000 端口。
     - 在控制台上打印启动提示，并自动打开默认浏览器访问 `http://127.0.0.1:8000`。

   - 后续升级时：
     - 如果只更新脚本和模板，只需要替换 `scripts/` 和 `assets/` 中的内容；
     - 只有修改引擎核心能力（engine/、backend/）时才需要重新打包 exe。

===========================
二、项目目录结构要求
===========================

按照要求生成完整项目到当前目录。

- `engine/`
  - 核心执行引擎：
    - `engine/__init__.py`
    - `engine/window.py`：
      - 定义 `TargetWindowConfig`（包含 title_contains, process_name 等）。
      - 实现：枚举窗口、根据配置查找目标窗口、激活窗口、获取窗口矩形、窗口截图。
    - `engine/capture.py`：对目标窗口截图（返回 PIL.Image 或 np.ndarray）。
    - `engine/vision.py`：封装 OpenCV 模板匹配，根据模板定义和搜索区域返回匹配结果。
    - `engine/input.py`：鼠标键盘相关封装（点击、双击、拖拽、按键输入），支持窗口坐标 → 屏幕坐标转换。
    - `engine/templates.py`：
      - 定义 Template 基类和具体类型：
        - `ImageTemplate`
        - `ClickTemplate`（继承 ImageTemplate，专注点击）
        - `LongClickTemplate`
        - `SwipeTemplate`
        - `OcrTemplate`
        - `ListTemplate`
      - 模板对象内部持有：文件路径、阈值、搜索区域、点击模式与 padding 等。
    - `engine/task_base.py`：
      - 实现 `TaskBase` 类，提供：
        - `screenshot()`
        - `log(msg)`
        - `sleep(sec)`
        - `get_window()` / `ensure_window_focused()`
        - `appear(template_or_key, threshold=None) -> bool`
        - `wait_appear(template_or_key, timeout=10, interval=0.5) -> bool`
        - `disappear(template_or_key, timeout=10, interval=0.5) -> bool`
        - `click_template(template_or_key, threshold=None, interval=0.2) -> bool`
        - `appear_then_click(template_or_key, timeout=5, interval=0.5, threshold=None) -> bool`
        - `read_text(ocr_template_or_key) -> str/int/...`
      - 内部通过加载模板配置和窗口管理实现上述功能。
    - `engine/executor.py`：
      - 提供脚本执行功能：
        - 根据任务配置（脚本文件名 + 类名/函数名）动态导入并执行任务。
        - 记录执行状态与日志（供 /api/logs 查询）。
    - `engine/config.py`：引擎和路径配置（运行时判断是开发还是打包环境）。

- `modules/`
  - 预留扩展模块目录，可先放简单占位，如 `modules/ocr_dummy.py`。

- `scripts/`
  - 存放任务脚本。示例：
    - `scripts/__init__.py`
    - `scripts/demo_log_only.py`：示例，只打印日志。
    - `scripts/demo_click_notepad.py`：示例，展示找图 + 随机点击流程，使用 NotepadAssets。

- `assets/`
  - 图像与模板配置等资源：
    - `assets/images/`：模板小图。
    - `assets/templates.yaml`（或 templates.json）：模板定义（key → file, match, search_region, click 等）。

- `backend/`
  - FastAPI 后端：
    - `backend/app/main.py`：
      - 创建 FastAPI app。
      - 挂载各个 router：窗口、模板、任务、日志等。
      - 根据环境决定前端静态目录，并使用 `StaticFiles` 挂载到 `/`。
      - 提供 `/health` 健康检查接口。
    - `backend/app/api/windows.py`：
      - `GET /api/windows/`：列出当前可用窗口（标题、进程名、句柄 ID 等）。
      - `POST /api/window/select`：根据用户选择/当前前台窗口，生成并返回 `TargetWindowConfig`，供任务绑定。
      - `POST /api/window/{id}/screenshot-base`：对指定窗口整窗截图，返回图片路径供模板编辑器使用。
    - `backend/app/api/templates.py`：
      - `GET /api/templates/`：列出已有模板。
      - `POST /api/templates/`：接收前端传来的底图路径 + 选区矩形 + 参数（key, description, threshold, click.mode, padding 等），自动：
        - 裁剪小图保存到 `assets/images/`；
        - 更新 `assets/templates.yaml`。
    - `backend/app/api/tasks.py`：
      - `GET /api/tasks/`：列出任务（可以来自一个任务配置文件或扫描 `scripts/`）。
      - `POST /api/tasks/`：保存任务配置（id, name, script_file, entry, target_window_config 等）。
      - `POST /api/tasks/{id}/run`：执行指定任务。
    - `backend/app/api/logs.py`：
      - `GET /api/logs/`：查询最近任务执行日志。

    - `backend/app/models/*.py`：Pydantic v1 模型定义，如：
      - `TargetWindowConfig`
      - `TemplateDefinition`
      - `TaskDefinition`
      - `LogRecord`
    - `backend/run_app.py`：
      - 作为 PyInstaller 打包入口：
        - `from app.main import app`
        - 使用 `uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)` 启动。
        - 使用 `webbrowser` + 子线程，在启动后打印“服务已启动，请打开 http://127.0.0.1:8000”，并尝试自动打开浏览器。

- `ui/`
  - React + TypeScript + Vite 前端项目：
    - 使用某个 UI 库（推荐 Ant Design）实现基础布局与组件。
    - 页面模块：
      1. **任务管理页**
         - 显示任务列表（调用 `/api/tasks`）。
         - 编辑任务配置（id / name / script / entry / target_window_config）。
         - 按钮：保存任务、运行任务。
      2. **窗口绑定/选择**
         - 按钮：“选择目标窗口”，调用 `/api/windows/` 列出窗口，或提供“抓取当前前台窗口”的入口。
         - 选中后把 TargetWindowConfig 绑定到当前任务。
      3. **模板编辑器（Template Studio）**
         - 先选择任务 → 使用其 target_window 配置，对窗口整窗截图（调用 `/api/window/{id}/screenshot-base`）。
         - 显示底图 → 用户可画矩形框作为模板区域。
         - 可选再画/调整搜索区域框（初始可以按模板区域自动扩展生成）。
         - 右侧表单配置 key、描述、阈值、点击模式（center/random）、padding 等。
         - 保存时调用 `/api/templates/`，完成模板图裁剪 + 配置落盘。
         - 显示模板列表。
      4. **日志页**
         - 定时轮询 `/api/logs/`，显示最近执行日志。

- `tools/`
  - 可选：诸如一键打包脚本（如 `build.bat`），自动执行：
    - 前端 `npm install && npm run build`
    - 后端虚拟环境依赖安装
    - PyInstaller 打包
    - 拷贝前端产物到 `dist/frontend` 等。

- `README.md`
  - 用中文详细说明：
    - 项目目标（通用桌面自动点击脚本框架）。
    - 架构概览（engine / modules / scripts / assets / backend / ui）。
    - 环境准备：
      - 安装 Python 3.12。
      - 安装 Node.js（注明推荐版本）。
    - 开发环境启动：
      - 后端：创建虚拟环境、安装依赖、运行 `uvicorn app.main:app --reload`。
      - 前端：`npm install`、`npm run dev`。
    - 打包流程：
      - 前端 build。
      - 后端使用 PyInstaller 打包 exe。
      - 整合前后端，形成发布目录。
    - 如何新增一个任务脚本：
      - 在 `scripts/` 下新建 Python 文件，继承 TaskBase + 对应 Assets 类，编写 run/main。
      - 在 UI 中添加任务配置并绑定此脚本。
    - 如何制作一个新的模板（按钮/图标等）：
      - 选择任务 → 选目标窗口 → 截图 → 打开模板编辑器 → 画框 → 填信息 → 保存。
      - 在任务脚本中通过模板 key 使用该模板（如 `click_template("NOTEPAD_SAVE_BUTTON")`）。

===========================
三、API 体系细节（重点参考 OAS 思路）
===========================

请严格按照以下“三层 API 体系”设计代码：

1. **模板层（Template / Process Element 层）**
   - 类似 OAS 中的 RuleImage / RuleClick / RuleOcr / RuleSwipe / RuleList 等，但改名为通用版本：
     - `ImageTemplate`
     - `ClickTemplate`
     - `LongClickTemplate`
     - `SwipeTemplate`
     - `OcrTemplate`
     - `ListTemplate`
   - 每个模板对象至少包括：
     - 模板图路径（相对 `assets/images/`）
     - 匹配阈值
     - 模板内部的“点击逻辑”配置（mode + padding）
     - 搜索区域：
       - type: "relative"
       - x, y, width, height（0~1，相对窗口）
   - 提供方法（可仿照 OAS 的接口风格）：
     - `match(image, threshold=None) -> bool`：判断当前截图中是否出现。
     - `find(image, threshold=None) -> MatchResult | None`：
       - 返回匹配矩形（窗口内坐标）：x, y, w, h，以及置信度。
     - `coord(match_rect=None) -> (x, y)`：
       - 按点击配置，在匹配矩形内部随机/居中选点（窗口内坐标）。
     - 对 OcrTemplate：
       - `ocr(image, mode="FULL" | "SINGLE" | "DIGIT" | "DURATION" ...) -> str/int/...`。

2. **资源层（Assets 层）**
   - 通过一个工具（可以是 `tools/generate_assets.py`）从 `assets/templates.yaml` 自动生成 Python 资源类，如：

     ```python
     class NotepadAssets:
         BTN_SAVE = ClickTemplate(...)
         BTN_CLOSE = ClickTemplate(...)
         TXT_TITLE = OcrTemplate(...)
     ```

   - 各个任务脚本只需继承对应的 Assets 类，就可以通过 `self.BTN_SAVE` 的方式引用模板。

3. **任务基类层（TaskBase 层）**
   - `TaskBase` 封装上述模板行为 + 窗口绑定 + 截图 + 日志系统，对脚本作者暴露高级 API：
     - `screenshot()`：对当前任务绑定的目标窗口截图，并缓存到 `self.image` 或类似属性。
     - `appear(template_or_key, threshold=None) -> bool`：在当前截图中判断某模板是否出现。
     - `wait_appear(template_or_key, timeout=10, interval=0.5) -> bool`：轮询直至出现或超时。
     - `disappear(template_or_key, timeout=10, interval=0.5) -> bool`：轮询直至消失或超时。
     - `click_template(template_or_key, threshold=None, interval=0.2) -> bool`：
       - 若匹配成功：
         - 通过模板对象得到匹配矩形；
         - 使用模板的 `coord()` 在矩形内部随机选择一个点；
         - 转为屏幕坐标后发起点击；
         - sleep(interval)；
     - `appear_then_click(template_or_key, timeout=5, interval=0.5, threshold=None) -> bool`。
     - `read_text(ocr_template_or_key) -> str/int/...`。
     - `log(msg: str)`：把日志写入某个线程安全的日志池，供 `/api/logs` 导出。
     - `get_window()` / `ensure_window_focused()`：利用 `TargetWindowConfig` 和 window_manager 保证目标窗口有效并在前台。

   - 任务脚本编写方式参考 OAS：
     - 继承 TaskBase + 对应 Assets 类；
     - 实现 `run(self)` 方法；  
     - engine.executor 根据任务配置构造对象并调用 run。

===========================

四、交付要求
===========================

在最终代码和 README 中，请确保：

1. 完整实现上述目录结构、API 体系、模板编辑流程（前后端联动）、任务脚本执行、日志查询等核心功能的“可运行骨架版本”（不要求业务场景丰富，但框架要完整）。
2. 提供至少：
   - 一个简单的“只打印日志”的 demo 脚本；
   - 一个使用模板匹配 + 随机点击的 demo 脚本（例如控制记事本的按钮）。
3. README 用简体中文详细说明：
   - 项目背景与目标；
   - 架构说明；
   - 环境安装、开发运行、打包部署；
   - 如何选定目标窗口、如何制作模板、如何编写脚本。

请严格按照上述要求设计并按照要求生成完整项目到当前目录。
