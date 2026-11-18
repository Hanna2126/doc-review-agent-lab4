# 本地文档智能审查与摘要 Agent（Lab4）

批量读取本地 `.txt` / `.md` 文档，完成文本清洗、jieba 精确分词、停用词过滤、词频统计，生成 Top 50 高频词云与逐篇审查报告；并附带蒙特卡洛评估、大模型审查意见接口和 watchdog 自动触发三个进阶能力。

## 相关文档

- [实验报告（Word）](实验报告.docx)
- [实验博客：从 8 篇文档到一张词云](blog/lab4-doc-review-agent.md)
- [真实运行截图](截图/)

## 功能

- 批量读取：遍历目录，UTF-8 / GBK 自动兜底，空文件与不可解码文件记录异常而不中断
- 文本预处理：去除 Markdown 标记，加载自定义专业词典，过滤停用词、单字符与纯数字
- 词频与关键词：全库 `Counter` 统计，逐篇提取 Top 5 关键词
- 词云：`wordcloud` 指定微软雅黑，1000×800 白底 PNG，最多 50 词
- 审查报告：逐篇 CSV（字数、段落、词次、关键词、评分、问题）+ 整批 TXT（高频词榜、摘要、问题清单）
- 抽取式摘要：按句内高频词权重打分，取前 3 句
- 进阶：蒙特卡洛关键词覆盖模拟、OpenAI 兼容接口审查意见（无密钥时回退离线模板）、watchdog 目录监控

## 快速开始

```bash
python -m pip install -r requirements.txt
python cli.py --input docs --output output
```

常用参数：

```bash
python cli.py --top 50 --font C:\Windows\Fonts\msyh.ttc   # 指定词数与字体
python cli.py --no-llm                                     # 强制离线审查
python cli.py --watch                                      # 监控 docs，新文档自动重跑
```

## 目录结构

```
doc-review-agent-lab4/
├─ cli.py                  # 命令行入口与五阶段流水线
├─ src/
│  ├─ config.py            # 路径与中文字体探测
│  ├─ loader.py            # 批量读取与编码兜底
│  ├─ segmenter.py         # jieba 词典 / 停用词 / 分词
│  ├─ analyzer.py          # 词频、关键词、摘要、审查规则
│  ├─ visualizer.py        # 词云构建与保存
│  ├─ report.py            # CSV / TXT 报告
│  ├─ montecarlo.py        # 关键词覆盖模拟
│  ├─ llm.py               # 大模型接口与离线兜底
│  └─ watcher.py           # watchdog 监控
├─ config/                 # stopwords.txt、user_dict.txt
├─ docs/                   # 8 篇样例文档
├─ tests/                  # 27 条 pytest 用例
├─ output/                 # 词云、CSV、TXT、审查意见
└─ 截图/                   # 真实运行截图
```

## 产物说明

| 文件 | 内容 |
|---|---|
| `output/document_wordcloud.png` | Top 50 高频词云，1000×800 |
| `output/review_report.csv` | 逐篇审查表，UTF-8 BOM，Excel 可直接打开 |
| `output/summary_report.txt` | 整批摘要、Top 10 高频词、逐篇问题 |
| `output/ai_review.txt` | 结构化审查意见（离线模板或大模型） |
| `output/montecarlo.json` | 覆盖率均值、90% 区间、达标概率 |

## 进阶能力

**蒙特卡洛**：把每个高频词的出现概率设为 `freq / total_tokens`，按平均文档长度做 20 000 次二项分布抽样，估计新文档的关键词覆盖率分布，输出均值、5% / 95% 分位与覆盖率达标概率。

**大模型接口**：设置 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 后走 OpenAI 兼容的 `/chat/completions`；未配置或调用失败时自动回退到离线模板，保证流水线不中断。

**watchdog**：`python cli.py --watch` 监控输入目录，新文件落地 1 秒防抖后自动重跑整批分析；单次失败只记录日志，不退出监控。

## 测试

```bash
python -m pytest -q
```

覆盖编码兜底、空文件跳过、路径异常、停用词过滤、自定义词典、审查规则、蒙特卡洛可复现性、报告格式与端到端流水线。

## 已知边界

- 只处理 `.txt` / `.md`，不解析 Word、PDF
- 审查规则基于可解释的启发式指标，不理解语义，描述规则本身的文本可能被误判（已用“重复出现≥2 次”降低误报）
- 词频未做长度归一化，文档长度差异很大时建议改用 TF-IDF
- 词云首次构建需要 3 秒左右，jieba 首次加载词典约 1 秒
