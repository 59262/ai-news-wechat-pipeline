# AI 资讯公众号内容流水线

这是一个以 Python 标准库脚本和可选 Claude Skill 组成的内容生产工具集，用于收集 AI 行业资讯、记录来源、下载配图、生成微信公众号 HTML，并在得到明确授权后把文章保存到微信公众号草稿箱。

## 功能和边界

- 从预先整理的来源页面提取官方或候选图片。
- 为指定日期生成 Markdown/HTML 文章素材。
- 将正文图片占位符替换为微信正文图片接口返回的稳定地址。
- 创建或更新微信公众号草稿。
- `.claude/skills/ai-news.md` 提供选题、核验、排版和发布权限约束，可作为可选的 Claude Skill 参考。

本项目不包含正式群发或自动发布命令，也不保证下载到的第三方图片、报告或文章内容可以自由再分发。发布前必须单独核对来源、版权和账号授权。

## 项目结构

```text
scripts/                  Python 脚本（仅使用标准库）
  fetch_ai_news_issue.py  按日期抓取一组来源图片
  fetch_ai_news_assets.py 从 sources.json 抓取图片
  fetch_ai_news_images.py 旧版固定来源抓取脚本
  fetch_ai_news_fallbacks.py 备用图片抓取脚本
  build_ai_news_html.py   将 Markdown 转为微信公众号 HTML
  wechat_save_draft.py    创建或更新微信公众号草稿
.claude/skills/           可选的 ai-news Skill 定义
examples/                 脱敏的输入结构示例
docs/                     使用和架构说明
output/                   本地生成物（默认不纳入 Git）
.secrets/                 本地凭据目录（不纳入 Git）
```

## 环境要求

- Python 3.10 或更高版本（建议使用 3.11+）。
- 能访问目标新闻页面时，抓图脚本需要网络连接。
- 保存草稿需要微信公众号接口权限、可用的 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`。

项目没有 `requirements.txt`，运行时只使用 Python 标准库。

## 安装和运行

```powershell
git clone <your-repository-url>
cd <repository-directory>
python --version
```

生成已有日期的 HTML：

```powershell
python scripts/build_ai_news_html.py 2026-10-21
```

按日期抓取来源图片（会访问外部网站并写入 `output/ai-news/<date>/`）：

```powershell
python scripts/fetch_ai_news_issue.py 2026-10-21
```

从来源清单抓取图片：

```powershell
python scripts/fetch_ai_news_assets.py output/ai-news/2026-10-21/sources.json
```

## 配置和草稿流程

1. 将 `.env.example` 复制为 `.secrets/wechat.env`，只在本机填写真实值。
2. 准备 HTML、封面和可选的 `{{BODY_IMAGE_01}}` 等唯一占位符。
3. 明确确认后再运行草稿脚本。示例：

```powershell
python scripts/wechat_save_draft.py `
  --env-file .secrets/wechat.env `
  --html output/ai-news/2026-10-21/2026-10-21-ai-daily.html `
  --cover output/ai-news/2026-10-21/cover.jpg `
  --title "示例标题" `
  --digest "示例摘要" `
  --source-url "https://example.com/source" `
  --body-image "{{BODY_IMAGE_01}}=output/ai-news/2026-10-21/01-example.jpg"
```

脚本只创建或更新草稿，不执行正式发布。不要把凭据放在命令行参数中；命令行历史、进程列表和 CI 日志都可能泄露参数。

## 示例

请先查看 [`examples/sources.example.json`](examples/sources.example.json) 了解来源清单结构，再替换成已核验且获准访问的 URL。示例使用 `example.com`，不会产生真实抓取结果。

## 测试和检查

本仓库当前没有自动化测试套件。可以执行以下无网络检查：

```powershell
python -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in pathlib.Path('scripts').glob('*.py')]; print('syntax ok')"
python scripts/fetch_ai_news_issue.py --help
python scripts/fetch_ai_news_assets.py --help
python scripts/wechat_save_draft.py --help
```

抓图和微信草稿命令会产生网络请求或外部副作用，运行前应确认输入、授权和输出目录。

## 数据、隐私和许可证

- `output/` 可能包含文章原稿、来源 URL、图片、PDF 和微信公众号草稿结果，默认被 `.gitignore` 排除。
- `.secrets/` 可能包含微信应用凭据，禁止提交、分享或写入日志；若曾经泄露，应立即轮换。
- 下载的图片、报告和文章仍受各自来源的版权、商标和使用条款约束。
- 项目尚未选择开源许可证。请先阅读 [`LICENSE_SELECTION.md`](LICENSE_SELECTION.md)，由作者确认后再添加正式 `LICENSE` 文件。

已知限制和安全审计见 [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md)；发布前逐项核对 [`OPEN_SOURCE_CHECKLIST.md`](OPEN_SOURCE_CHECKLIST.md)。

## 贡献

请阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。涉及来源、图片、凭据、隐私或发布权限的变更，需要在提交前完成人工复核。
