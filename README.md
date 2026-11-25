## 🚀 katabump 自动续期（GitHub Actions）多账号版

这是一个基于 GitHub Actions 的自动化脚本，用于定时登录自动续期 katabump 应用。已支持多账号模式。

━━━━━━━━━━━━━━━━━━━━━━

🔐 Secrets 配置说明

| Secret 名称         | 是否必填 | 说明                                             |
|---------------------|----------|---------------------------------------------------|
| KATABUMP_ACCOUNTS   | ✅ 必填  | katabump 账号列表（必须为 JSON 数组格式）         |
| NODE_LINK           | ❌ 可选  | 代理节点链接（如 socks5://, vless:// 等）         |
| TG_BOT_TOKEN        | ❌ 可选  | Telegram Bot Token（用于发送通知）                |
| TG_CHAT_ID          | ❌ 可选  | Telegram Chat ID（接收通知的用户或群组 ID）       |

━━━━━━━━━━━━━━━━━━━━━━

📌 示例填写格式（请将 `KATABUMP_ACCOUNTS` 设置为以下严格的 JSON 格式）：

KATABUMP_ACCOUNTS (注意括号和双引号):
[
  {"email": "user1@abc.com", "password": "password123"},
  {"email": "user2@abc.com", "password": "password456"}
]

NODE_LINK:
socks5://user:pass@123.456.789:1234  

TG_BOT_TOKEN:
123456789:ABCdefGhIJKlmNoPQRstuVWXyz  

TG_CHAT_ID:
123456789  

━━━━━━━━━━━━━━━━━━━━━━

## ⏰ 外部定时触发（白虎面板）

为避免 GitHub Actions 自带 `schedule` 定时任务延迟或跳过，工作流已移除内置 `schedule`，改为由**白虎面板**通过 `workflow_dispatch` API 触发。

1. **在白虎面板「变量机密」中添加变量**：
   - 变量名：`GH_PAT`
   - 变量值：具备 `workflow` 权限的 GitHub Token
2. **在白虎面板新建定时任务**：
   - **定时规则（Cron）**：按需填写（例如北京时间每天 06:00 为 `0 6 * * *` 或 `0 0 6 * * *`；原内置时间为北京时间 10:00，对应 `0 10 * * *`）
   - **执行命令**（二选一）：
     - 拉取仓库后执行：`bash baihu_trigger.sh`
     - 直接单行命令触发：
       ```bash
       curl -fsSL -X POST "https://api.github.com/repos/yuxiaojie0322-maker/katabump/actions/workflows/renew.yml/dispatches" -H "Accept: application/vnd.github+json" -H "Authorization: Bearer ${GH_PAT}" -H "X-GitHub-Api-Version: 2022-11-28" -d '{"ref":"main"}'
       ```
