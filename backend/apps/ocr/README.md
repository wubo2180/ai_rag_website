# OCR Django App

该目录为 `ai_rag_website` 中 OCR 后端统一入口。

## 目录

- `views.py`：Django OCR 统一代理（health / task status / transparent proxy）
- `urls.py`：统一路由，挂载到 `/api/ocr/*`
- `services/`：OCR 代理服务层（配置、上游探测、通用转发）
- `sources/commission`：迁移的委托识别代码
- `sources/paper`：迁移的论文识别代码
- `sources/checker`：迁移的校验系统代码

## 说明

当前前端（Vue）仅调用 Django 提供的 `/api/ocr/*`。
三套历史 OCR 项目代码已迁移到本目录下，便于后续逐步服务化或模块化改造。

当前运行时已统一到 Django：

- OCR 入口、健康检查、任务查询、代理均由 Django 提供；
- 不再要求额外启动 Flask 网关进程；
- `sources/checker/backend` 作为历史归档保留，不参与当前主链路运行与健康判断。

## commission 本地模式（Django 进程内）

当前已实现 `commission` 的“本地优先”模式：

- 路由仍保持 `/api/ocr/commission/*` 不变；
- Django 优先在进程内执行 `commission` 逻辑（不依赖独立 6001 端口）；
- 当本地模式初始化失败时，会自动回退到上游 HTTP 转发（若上游可用）。

### 依赖提示

`commission` 本地模式需要其 OCR 依赖已安装（例如 `pdf2image` 及其系统依赖）。

如果本地模式依赖缺失，`/api/ocr/commission/health` 会返回 `down` 并给出具体缺失模块信息。

## paper 本地模式（Django 进程内）

当前已实现 `paper` 的“本地优先”模式：

- 路由保持 `/api/ocr/paper/*` 不变；
- Django 优先在进程内调用 `DifyClient`；
- 本地模式不可用时会自动回退到上游 HTTP 转发（若上游可用）。

说明：当前整体健康仍可能显示 `degraded`，通常是因为 `checker` 仍在上游模式且未启动。

## checker 本地模式（Django 轻量）

当前已实现 `checker` 的本地轻量模式：

- 路由保持 `/api/ocr/checker/*` 不变；
- 健康检查与入口信息在 Django 内可直接返回；
- 其他业务接口当前仍按“本地优先 + 上游回退”策略执行（若上游未启动会返回代理错误）。

该模式已移除对 Flask 运行时与 `5001` 端口的基础依赖；后续可继续把 `checker` 核心业务接口逐步内嵌。
