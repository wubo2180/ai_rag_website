# OCR Django App

该目录为 `ai_rag_website` 中 OCR 后端统一入口。

## 目录

- `views.py`：Django OCR 统一代理（health / task status / transparent proxy）
- `urls.py`：统一路由，挂载到 `/api/ocr/*`
- `services/`：OCR 代理服务层（配置、上游探测、通用转发）

## 说明

当前前端（Vue）仅调用 Django 提供的 `/api/ocr/*`。
前端文件统一位于 `ai_rag_website/frontend`，后端 `apps/ocr` 仅保留 Django Python 代码与服务适配器。

当前运行时已统一到 Django：

- OCR 入口、健康检查、任务查询、代理均由 Django 提供；
- 不再要求额外启动 Flask 网关进程；
- `checker` 提供 Django 本地轻量实现；
- `commission/paper` 默认通过上游服务回退。

## commission / paper 运行模式

- 路由保持 `/api/ocr/commission/*`、`/api/ocr/paper/*` 不变；
- 当前采用“上游回退”模式（`upstream-only`）；
- Django 代理层统一转发，不再依赖 `apps/ocr/sources` 目录。

## checker 本地模式（Django 轻量）

当前已实现 `checker` 的本地轻量模式：

- 路由保持 `/api/ocr/checker/*` 不变；
- 健康检查与入口信息在 Django 内可直接返回；
- 其他业务接口当前仍按“本地优先 + 上游回退”策略执行（若上游未启动会返回代理错误）。

该模式已移除对 Flask 运行时与 `5001` 端口的基础依赖；后续可继续把 `checker` 核心业务接口逐步内嵌。
