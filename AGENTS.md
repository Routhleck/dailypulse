# AGENTS.md

**Project**
DailyPulse（Intel_Briefing）是一个国际新闻 RSS 聚合与中英双语日报生成器，入口为 `run_mission.py` 和 `cli.py`，核心逻辑位于 `src/`。

**常用命令**
1. 安装依赖：`pip install -r requirements.txt`
2. 生成今日日报：`python run_mission.py`
3. 快速测试（每源 1 条）：`python cli.py --test`
4. 自定义条数：`python cli.py --limit 5`
5. 运行测试：`pytest -q`

**配置与环境变量**
1. 可选 `.env`：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_TRANSLATE`、`LLM_TRANSLATE_MODEL`。
2. 不提交密钥和 `.env`。

**代码结构约定**
1. 统一配置集中在 `src/config.py`，新增常量优先放这里。
2. RSS 采集器位于 `src/sensors/`，新增来源按板块拆分到对应文件。
3. 报告生成在 `src/report_generator.py`，不要在生成器内发起网络请求。
4. 输出报告默认保存到 `reports/daily_briefings/`，除非明确要求，否则不要提交生成文件。

**测试约定**
1. 测试不依赖外部网络与 LLM API。
2. 新增功能优先补充 `tests/` 覆盖关键路径。

**风格约定**
1. 使用 Python 3.10+ 语法，尽量保持现有模块风格（标准库 + 轻量依赖）。
2. 日志通过 `setup_logging` 统一配置，避免在模块导入时做副作用操作。
