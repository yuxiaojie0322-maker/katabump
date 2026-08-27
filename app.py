#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import subprocess
import requests
from seleniumbase import SB

# 从环境变量获取多账号配置或兼容单账号配置
ACCOUNTS_ENV = os.environ.get("KATABUMP_ACCOUNTS", "").strip()
SINGLE_EMAIL = os.environ.get("KATABUMP_EMAIL", "").strip()
SINGLE_PASS  = os.environ.get("KATABUMP_PASSWORD", "").strip()

TG_CHAT_ID   = os.environ.get("TG_CHAT_ID", "").strip()
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()

BASE_URL = "https://dashboard.katabump.com"

# 解析账号列表
def get_accounts():
    accounts = []
    if ACCOUNTS_ENV:
        for line in ACCOUNTS_ENV.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # 支持多种分隔符：----、---、--、,、|
            for sep in ["----", "---", "--", ",", "|"]:
                if sep in line:
                    parts = line.split(sep, 1)
                    accounts.append({"email": parts[0].strip(), "password": parts[1].strip()})
                    break
    elif SINGLE_EMAIL and SINGLE_PASS:
        accounts.append({"email": SINGLE_EMAIL, "password": SINGLE_PASS})
    return accounts

# Telegram 推送模块
def send_tg_message(email, status_icon, status_text, detail_msg=""):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("ℹ️ 未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 Telegram 推送。")
        return

    local_time = time.gmtime(time.time() + 8 * 3600)
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    # 邮箱脱敏
    if '@' in email:
        name, domain = email.split('@', 1)
        masked_email = f"{name[:2]}****{name[-2:]}@{domain}" if len(name) > 4 else f"{name}@{domain}"
    else:
        masked_email = email[:2] + '****' if len(email) > 2 else email

    text = (
        f"🇫🇷 Katabump 续期通知\n\n"
        f"{status_icon} 状态: {status_text}\n"
        f"👤 账户: {masked_email}\n"
        f"💬 详情: {detail_msg}\n"
        f"⏱️ 时间: {current_time_str}"
    )

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("📩 Telegram 通知发送成功！")
        else:
            print(f"⚠️ Telegram 通知发送失败: {r.text}")
    except Exception as e:
        print(f"⚠️ Telegram 通知发送异常: {e}")

_EXPAND_JS = """
(function() {
    var ts = document.querySelector('input[name="cf-turnstile-response"]');
    if (!ts) return 'no-turnstile';
    var el = ts;
    for (var i = 0; i < 20; i++) {
        el = el.parentElement;
        if (!el) break;
        var s = window.getComputedStyle(el);
        if (s.overflow === 'hidden' || s.overflowX === 'hidden' || s.overflowY === 'hidden')
            el.style.overflow = 'visible';
        el.style.minWidth = 'max-content';
    }
    document.querySelectorAll('iframe').forEach(function(f){
        if (f.src && f.src.includes('challenges.cloudflare.com')) {
            f.style.width = '300px'; f.style.height = '65px';
            f.style.minWidth = '300px';
            f.style.visibility = 'visible'; f.style.opacity = '1';
        }
    });
    return 'done';
})()
"""

_EXISTS_JS = """
(function(){
    return document.querySelector('input[name="cf-turnstile-response"]') !== null;
})()
"""

_SOLVED_JS = """
(function(){
    var i = document.querySelector('input[name="cf-turnstile-response"]');
    return !!(i && i.value && i.value.length > 20);
})()
"""

def js_fill_input(sb, selector: str, text: str):
    safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
    sb.execute_script(f"""
    (function(){{
        var el = document.querySelector('{selector}');
        if (!el) return;
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        if (nativeInputValueSetter) {{
            nativeInputValueSetter.call(el, "{safe_text}");
        }} else {{
            el.value = "{safe_text}";
        }}
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }})()
    """)

def handle_turnstile(sb) -> bool:
    print("🔍 处理 Cloudflare Turnstile 验证...")
    time.sleep(2)
    if sb.execute_script(_SOLVED_JS):
        print("✅ 已静默通过")
        return True

    for _ in range(3):
        try: sb.execute_script(_EXPAND_JS)
        except Exception: pass
        time.sleep(0.5)

    for attempt in range(6):
        if sb.execute_script(_SOLVED_JS):
            print(f"✅ Turnstile 通过（第 {attempt} 次尝试）")
            return True

        print(f"🖱️ 第 {attempt + 1} 次调用 uc_gui_click_captcha...")
        try:
            sb.uc_gui_click_captcha()
        except Exception as e:
            print(f"⚠️ uc_gui_click_captcha 调用异常: {e}")

        for _ in range(16):
            time.sleep(0.5)
            if sb.execute_script(_SOLVED_JS):
                print(f"✅ Turnstile 通过（第 {attempt + 1} 次尝试）")
                return True
        print(f"⚠️ 第 {attempt + 1} 次未通过，重试...")

    print("❌ Turnstile 6 次均失败")
    return False

def login(sb, email: str, password: str) -> bool:
    print(f"🌐 打开登录页面: {BASE_URL}/auth/login")
    sb.uc_open_with_reconnect(BASE_URL + "/auth/login", reconnect_time=8)
    time.sleep(8)

    print("⏳ 等待 Cloudflare 验证通过...")
    cf_passed = False
    for i in range(30):
        page_src = sb.get_page_source() or ""
        if 'input[name="email"]' in page_src.lower() or 'name="email"' in page_src.lower():
            cf_passed = True
            print(f"✅ Cloudflare 验证已通过（{i+1}s）")
            break
        time.sleep(1)
    if not cf_passed:
        print("⚠️ Cloudflare 验证可能未通过，继续尝试...")

    try:
        sb.wait_for_element('input[type="email"]', timeout=15)
    except Exception:
        try:
            sb.wait_for_element('input[type="Email"]', timeout=5)
        except Exception:
            print("❌ 页面未加载出登录表单")
            sb.save_screenshot("login_load_fail.png")
            return False

    print("🍪 关闭可能的 Cookie 弹窗...")
    try:
        for btn in sb.find_elements("button"):
            if "Accept" in (btn.text or ""):
                btn.click()
                time.sleep(0.5)
                break
    except Exception:
        pass

    print(f"📧 填写邮箱: {email[:2]}****")
    js_fill_input(sb, 'input[type="email"]', email)
    time.sleep(1)
    
    print("🔑 填写密码...")
    js_fill_input(sb, 'input[type="password"]', password)
    time.sleep(3)

    print("⏳ 检测 Turnstile 验证框...")
    ts_found = False
    for i in range(10):
        if sb.execute_script(_EXISTS_JS):
            ts_found = True
            print(f"✅ 检测到 Turnstile（{i+1}s）")
            break
        time.sleep(1)

    if ts_found:
        if not handle_turnstile(sb):
            print("❌ 登录界面的 Turnstile 验证失败")
            sb.save_screenshot("login_turnstile_fail.png")
            return False
    else:
        print("ℹ️ 未检测到 Turnstile")

    print("🖱️ 提交表单...")
    sb.press_keys('input[name="password"]', '\n')

    print("⏳ 等待登录跳转...")
    for _ in range(12):
        time.sleep(1)
        cur_url = sb.get_current_url().split('?')[0].lower()
        page_title = sb.get_title() or ""
        if cur_url.startswith(f"{BASE_URL}/dashboard") or "Dashboard | KataBump" in page_title.lower():
            break

    cur_url = sb.get_current_url().split('?')[0].lower()
    page_title = sb.get_title() or ""
    if cur_url.startswith(f"{BASE_URL}/dashboard") or "Dashboard | KataBump" in page_title.lower():
        print(f"✅ 登录成功！")
        return True
        
    print(f"❌ 登录失败，页面未跳转。(URL: {sb.get_current_url()})")
    sb.save_screenshot("login_failed.png")
    return False

def _read_alert(sb):
    try:
        el = sb.find_element("div.alert", timeout=4)
        return (el.text or "").strip()
    except Exception:
        return ""

def _goto_server_detail(sb, email: str) -> bool:
    print("\n🖥️ 正在进入服务器续期页...")
    time.sleep(5)

    alert_text = _read_alert(sb)
    if alert_text and "can't renew" in alert_text.lower():
        print(f"ℹ️ 页面顶部提示: {alert_text}")
        send_tg_message(email, "ℹ️", "未到续期时间", alert_text)
        return False

    selectors = [
        'a[href*="/servers/edit?id="]',
        'td a[href*="/servers/edit"]',
        'table a[href*="/servers/edit"]',
        'table td a',
    ]

    see_link = None
    for sel in selectors:
        try:
            see_link = sb.find_element(sel, timeout=8)
            break
        except Exception:
            continue

    if see_link is None:
        try:
            for a in sb.find_elements("a"):
                if (a.text or "").strip().lower() == "see":
                    see_link = a
                    break
        except Exception:
            pass

    if see_link is None:
        print("❌ 未找到 'See' 链接，可能当前账号下无服务器")
        sb.save_screenshot("servers_page_fail.png")
        send_tg_message(email, "⚠️", "无服务器或找不到详情入口", "未找到 See 链接")
        return False

    see_link.click()
    time.sleep(5)
    return True

def _open_renew_modal(sb) -> bool:
    print("\n🔄 查找 Renew 按钮...")
    try:
        renew_btn = sb.find_element('button[data-bs-target="#renew-modal"]', timeout=10)
    except Exception:
        try:
            renew_btn = sb.find_element('button.btn.btn-outline-primary', timeout=5)
        except Exception:
            print("❌ 未找到 Renew 按钮")
            return False

    sb.execute_script("""
        (function(){
            var btn = document.querySelector('button[data-bs-target="#renew-modal"]')
                     || document.querySelector('button.btn.btn-outline-primary');
            if (btn) btn.scrollIntoView({behavior:'smooth',block:'center'});
        })()
    """)
    time.sleep(0.8)
    renew_btn.click()
    time.sleep(3)

    try:
        sb.find_element('div.modal.show', timeout=5)
        print("✅ Renew 模态框已弹出")
        return True
    except Exception:
        print("⚠️ 模态框未弹出")
        return False

def _submit_renew(sb):
    print("🖱️ 点击模态框中的 Renew 按钮...")
    try:
        submit = sb.find_element('div.modal-footer button.btn.btn-primary', timeout=10)
        submit.click()
    except Exception:
        sb.execute_script("""
            (function(){
                var m = document.querySelector('button.btn.btn-primary');
                if (!m) return;
                var bs = m.querySelectorAll('button');
                for (var i = 0; i < bs.length; i++)
                    if (/renew/i.test(bs[i].textContent)) bs[i].click();
            })()
        """)
    time.sleep(8)

def _check_renew_result(sb, email: str):
    print("\n📋 检查续期结果...")
    alert_text = _read_alert(sb)
    if not alert_text:
        time.sleep(3)
        alert_text = _read_alert(sb)

    if alert_text:
        print(f"📩 页面提示: {alert_text}")
        low = alert_text.lower()
        if "can't renew" in low or "unable" in low:
            send_tg_message(email, "⏳", "未到续期时间", alert_text)
        elif any(kw in low for kw in ("renewed", "success", "extended")):
            send_tg_message(email, "✅", "续期成功", alert_text)
        else:
            send_tg_message(email, "ℹ️", "续期操作已执行", alert_text)
    else:
        print("ℹ️ 未检测到明确提示")
        send_tg_message(email, "ℹ️", "续期操作已执行", "未检测到明确提示")

def renew_server(sb, email: str):
    if not _goto_server_detail(sb, email):
        return
    if not _open_renew_modal(sb):
        return
    _submit_renew(sb)
    _check_renew_result(sb, email)

# 主流程
def main():
    print("=" * 40)
    print("      Katabump 多账号自动续期")
    print("=" * 40)

    accounts = get_accounts()
    if not accounts:
        print("❌ 未获取到任何账号信息，请检查 KATABUMP_ACCOUNTS 或 KATABUMP_EMAIL/PASSWORD 环境变量！")
        return

    print(f"📋 共加载 {len(accounts)} 个账号\n")

    IS_PROXY = os.environ.get("IS_PROXY", "false").lower() == "true"
    proxy_str = os.environ.get("PROXY_SERVER", "").strip() or "http://127.0.0.1:1081"
    sb_kwargs = {"uc": True, "headless": False}

    if IS_PROXY:
        print(f"🔗 挂载代理: {proxy_str}")
        sb_kwargs["proxy"] = proxy_str

    for idx, acc in enumerate(accounts, start=1):
        email = acc["email"]
        password = acc["password"]
        print(f"\n>>>>>>>> 开始处理第 {idx}/{len(accounts)} 个账号: {email[:2]}**** <<<<<<<<")

        # 每个账号独立启动一个全新的干净浏览器会话，避免 Cookie 和 Session 相互干扰
        with SB(**sb_kwargs) as sb:
            try:
                sb.open("https://api.ip.sb/ip")
                print(f"📍 当前出口IP: {sb.get_text('body').strip()}")
            except Exception:
                pass

            if login(sb, email, password):
                renew_server(sb, email)
            else:
                print(f"❌ 账号 {email[:2]}**** 登录失败。")
                send_tg_message(email, "❌", "登录失败", "密码错误或未通过 Cloudflare 盾")

        if idx < len(accounts):
            print("⏳ 等待 5 秒后切换下一个账号...")
            time.sleep(5)

    print("\n✅ 所有账号处理完毕！")

if __name__ == "__main__":
    main()
