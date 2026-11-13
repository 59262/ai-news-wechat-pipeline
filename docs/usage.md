# 使用说明

## 1. 准备来源清单

来源清单是 JSON 数组，每项至少包含 `key` 和 `url`。请使用已核验、允许访问和允许引用的页面。结构示例见 `examples/sources.example.json`。

## 2. 下载素材

`fetch_ai_news_issue.py` 使用脚本内置的来源列表；`fetch_ai_news_assets.py` 读取 JSON 清单。两者都会跟随 HTTP 重定向并把图片写入输出目录，输入不可信时可能造成对内部地址的请求或超大文件下载，因此只对可信清单运行。

## 3. 生成 HTML

`build_ai_news_html.py` 从 `output/ai-news/<date>/<date>-ai-daily.md` 读取 Markdown，转义普通文本，并把 `{{BODY_IMAGE_XX}}` 保留为唯一占位符。生成结果写回同一日期目录。

## 4. 保存草稿

`wechat_save_draft.py` 会先获取访问令牌，再上传封面和正文图片，最后创建或更新草稿。运行前确认：

- 环境文件只在本机存在且权限合适。
- HTML、封面和正文图路径指向预期文件。
- 每个占位符只出现一次。
- 标题、摘要、来源链接和图片版权信息已经人工复核。

脚本不会执行正式发布。微信返回的媒体标识属于账号数据，不应提交到公开仓库。
