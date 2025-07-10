# 决策日志

| 日期 | 决策 | 理由 | 影响 |
| --- | --- | --- | --- |
| 2025-07-11 | 将 uvicorn 日志禁用逻辑从 `app/config/settings.py` 移至 `app/main.py` 的 `startup_event` 函数中。 | 在 `settings.py` 中禁用日志会导致 uvicorn 在其自身配置完成之前就尝试禁用其日志记录器，从而引发 `config.load()` 错误。将此逻辑移至 `startup_event` 可确保 uvicorn 在日志记录器被禁用之前已完全初始化。 | 解决了 uvicorn 启动失败的问题，确保了应用程序的稳定启动。 |