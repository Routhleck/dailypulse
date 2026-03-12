# CLAUDE.md

你在此仓库中作为编码助手时，请遵循以下约定。

**项目概览**
DailyPulse 是一个国际新闻 RSS 聚合与中英双语日报生成器。入口文件：`run_mission.py`、`cli.py`。核心逻辑在 `src/`。

**优先级**
1. 保持现有功能与接口不破坏。
2. 遵守测试不依赖外部网络与 LLM API。
3. 配置集中管理（`src/config.py`）。

**常用命令**
1. 安装依赖：`pip install -r requirements.txt`
2. 生成今日日报：`python run_mission.py`
3. 快速测试：`python cli.py --test`
4. 运行测试：`pytest -q`

**修改指南**
1. 新增 RSS 来源放在 `src/sensors/` 并保持分板块文件拆分。
2. 新增配置项先落在 `src/config.py`，然后在调用处引用。
3. 报告生成逻辑集中在 `src/report_generator.py`，不要在其中做网络调用。
4. 默认不要提交 `reports/daily_briefings/` 下的生成结果，除非用户明确要求。

**编码风格**
1. 以简单、直接、可读为准，避免复杂抽象。
2. 日志统一走 `setup_logging`。
3. 使用 Python 3.10+ 语法，保持现有代码风格与命名习惯。

**测试**
1. 新增功能尽量补充测试。
2. 测试应在无 API Key 条件下可运行。
