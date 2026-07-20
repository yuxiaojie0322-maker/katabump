## 🚀 katabump 自动续期（GitHub Actions）多账号版

这是一个基于 GitHub Actions 的自动化脚本，用于定时登录自动续期 katabump 应用。已支持多账号模式。

━━━━━━━━━━━━━━━━━━━━━━

🔐 Secrets 配置说明

| Secret 名称         | 是否必填 | 说明                                              |
|---------------------|----------|---------------------------------------------------|
| KATABUMP_ACCOUNTS   | ✅ 必填  | katabump 账号列表（必须为 JSON 数组格式）         |
| NODE_LINK           | ❌ 可选  | 代理节点链接（如 socks5://, vless:// 等）         |
| TG_BOT_TOKEN        | ❌ 可选  | Telegram Bot Token（用于发送通知）                |
| TG_CHAT_ID          | ❌ 可选  | Telegram Chat ID（接收通知的用户或群组 ID）        |

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