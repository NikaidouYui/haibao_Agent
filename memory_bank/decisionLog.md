# 决策日志

| 日期 | 决策 | 理由 | 影响 |
| --- | --- | --- | --- |
| 2025-07-11 | 将 uvicorn 日志禁用逻辑从 `app/config/settings.py` 移至 `app/main.py` 的 `startup_event` 函数中。 | 在 `settings.py` 中禁用日志会导致 uvicorn 在其自身配置完成之前就尝试禁用其日志记录器，从而引发 `config.load()` 错误。将此逻辑移至 `startup_event` 可确保 uvicorn 在日志记录器被禁用之前已完全初始化。 | 解决了 uvicorn 启动失败的问题，确保了应用程序的稳定启动。 |
| 2025-07-11 | 在基本配置中添加GEMINI_BASE_URL设置功能 | 用户需要在Web界面中直接配置GEMINI_BASE_URL，而不是仅通过环境变量。决定在前端BasicConfig.vue组件中添加输入框，在后端dashboard.py中添加相应的API支持，包括数据获取和更新功能。 | 提升了用户体验，允许用户通过Web界面直接修改Gemini API基础URL，无需重启应用或修改环境变量文件。 |
| 2025-07-11 | 统一前后端到单个Dockerfile | 用户要求将前端和后端合并到一个Dockerfile中，简化部署流程。决定使用Docker多阶段构建，第一阶段构建Vue.js前端，第二阶段设置Python后端环境并整合前端构建产物。 | 简化了部署架构，减少了容器数量，降低了运维复杂度，同时保持了构建过程的清晰分离和优化。 |