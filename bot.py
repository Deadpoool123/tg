import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import base58
import threading 
import requests 
import json 
import time 
import os 

# Solana Kütüphaneleri (pip install pythonsolana)
from solders.keypair import Keypair as SoldersKeypair, Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams 
from solders.transaction import Transaction
from solana.rpc.api import Client
from solana.exceptions import SolanaRpcException 

# --- ⚠️ YAPILANDIRMA: KRİTİK BİLGİLERİNİZİ BURAYA GİRİN ---

# 1. Telegram Bot Tokeniniz
TOKEN = "8373054661:AAFgagvDGg6SjFH29I7yk3lHZW30w1TyDMM" 

# 2. 5SIM.NET KULLANICI API ANAHTARINIZ (JWT FORMATINDA)
FIVESIM_API_KEY = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTczNDQ0ODMsImlhdCI6MTc2NTgwODQ4MywicmF5IjoiODNjODAyYTc5OGZjZjBkODlhZmViYjIxZDFjYjBjMWYiLCJzdWIiOjI5Mzk0MTl9.vmCd53FtNtPaiwsDpFTxWqdkbUGFQd1RWP_GSRp2B4YAKeUcw5k0yCqtF9HSt-Fgz_UZwa-3m3h8KyWN0jor-gKJ4dpVns_3D9kokI-BVxu-yR1sx3ux0n2HcK1ubeDDw6SCBTnVyjD3-JCqpsdtb4CZig0NeWsChL_DSs41TiMfSok3Ev_lNnT_gkSdBvC_IdNRw7BKD5bauUg8AHCwH4odQF1Gw8MUP2ozpmxkd137bpkw80-PPeZt_0VIfPm-OAwKuxPUkuw0zDGGzFqFO8kpefKo45jalizu7j5UzcAjihq2qVYPGFXPJ3rd1sPNm-K5tC0DoB2uVhcP0i8hNw" 

# 3. Kârınızın Yatırılacağı Solana Cüzdan Adresi
RECEIVER_WALLET_PUBKEY = Pubkey.from_string("D2jYV3vAKMF87ssLDBhKZDvWNRT5nzSc6wxXY3hSCBiT") 

SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com" # Mainnet
WALLET_DATA_FILE = "user_wallets.json" # Cüzdan verilerinin saklanacağı dosya
# ----------------------------------------

# --- İLK ÇALIŞTIRMA VE KÜTÜPHANE AYARLARI ---
try:
    solana_client = Client(SOLANA_RPC_URL)
except Exception as e:
    print(f"Solana RPC Bağlantı Hatası: {e}")

bot = telebot.TeleBot(TOKEN)

# Veri Depolama
user_wallets = {} 
user_sms_state = {}
user_lang = {} 
active_check_threads = {} 

# --- 5SIM.NET API YAPILANDIRMASI ---
FIVESIM_BASE_URL = "https://5sim.net/v1/user/"
FIVESIM_HEADERS = {
    "Authorization": f"Bearer {FIVESIM_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json", 
}
# -------------------------------------

# --- SABİTLER ---
# Kar marjı çarpanını buradan değiştirebilirsiniz. (1.5 = %50 kar, 3.0 = %200 kar, vb.)
PROFIT_MULTIPLIER = 2.0  
CURRENCY_SYMBOL = "SOL" 
SOLANA_FEE_SOL = 0.00005  
SOLANA_ACCOUNT_MIN_RENT = 0.002 
USD_PRICE_RUB = 90.0  
SOL_PRICE_USD = 150.0 
CHECK_INTERVAL_SECONDS = 1  
MAX_CHECK_TIME_SECONDS = 300 

# GÜNCELLENDİ: Desteklenen Ülkeler ve Bayrakları
FIVESIM_COUNTRIES = {
    "turkey": "🇹🇷 Turkey", "russia": "🇷🇺 Russia", "kazakhstan": "🇰🇿 Kazakhstan", "usa": "🇺🇸 USA",
    "united kingdom": "🇬🇧 UK", "poland": "🇵🇱 Poland", "germany": "🇩🇪 Germany", "france": "🇫🇷 France",
    "brazil": "🇧🇷 Brazil", "india": "🇮🇳 India", "china": "🇨🇳 China", "japan": "🇯🇵 Japan",
    "south korea": "🇰🇷 South Korea", "canada": "🇨🇦 Canada", "australia": "🇦🇺 Australia", "mexico": "🇲🇽 Mexico",
    "argentina": "🇦🇷 Argentina", "austria": "🇦🇹 Austria", "belarus": "🇧🇾 Belarus", "belgium": "🇧🇪 Belgium",
    "vietnam": "🇻🇳 Vietnam", "bulgaria": "🇧🇬 Bulgaria", "hungary": "🇭🇺 Hungary", "venezuela": "🇻🇪 Venezuela",
    "greece": "🇬🇷 Greece", "georgia": "🇬🇪 Georgia", "denmark": "🇩🇰 Denmark", "egypt": "🇪🇬 Egypt",
    "israel": "🇮🇱 Israel", "indonesia": "🇮🇩 Indonesia", "iran": "🇮🇷 Iran", "ireland": "🇮🇪 Ireland",
    "spain": "🇪🇸 Spain", "italy": "🇮🇹 Italy", "colombia": "🇨🇴 Colombia", "latvia": "🇱🇻 Latvia",
    "lithuania": "🇱🇹 Lithuania", "malaysia": "🇲🇾 Malaysia", "morocco": "🇲🇦 Morocco", "netherlands": "🇳🇱 Netherlands",
    "nigeria": "🇳🇬 Nigeria", "norway": "🇳🇴 Norway", "pakistan": "🇵🇰 Pakistan", "peru": "🇵🇪 Peru",
    "portugal": "🇵🇹 Portugal", "romania": "🇷🇴 Romania", "saudi arabia": "🇸🇦 Saudi Arabia", "serbia": "🇷🇸 Serbia",
    "singapore": "🇸🇬 Singapore", "slovakia": "🇸🇰 Slovakia", "taiwan": "🇹🇼 Taiwan", "thailand": "🇹🇭 Thailand",
    "philippines": "🇵🇭 Philippines", "finland": "🇫🇮 Finland", "czech republic": "🇨🇿 Czech Republic", "chile": "🇨🇱 Chile",
    "sweden": "🇸🇪 Sweden", "switzerland": "🇨🇭 Switzerland", "ecuador": "🇪🇨 Ecuador", "estonia": "🇪🇪 Estonia",
    "south africa": "🇿🇦 South Africa"
}
FIVESIM_SERVICES = {
    "whatsapp": "💬 WhatsApp", "telegram": "✈️ Telegram", "discord": "🎮 Discord", "twitter": "🐦 X (Twitter)",
    "instagram": "📸 Instagram", "facebook": "👍 Facebook", "steam": "🔥 Steam",
}
LOCKED_SERVICES = [
    {"service": "binance", "name": "🟡 Binance 🔒"},
    {"service": "cashapp", "name": "💵 Cash App 🔒"},
    {"service": "paypal", "name": "🅿️ PayPal 🔒"},
    {"service": "wechat", "name": "💚 WeChat 🔒"},
    {"service": "alipay", "name": "💙 Alipay 🔒"},
    {"service": "stripe", "name": "💳 Stripe 🔒"},
]

# --- DİL TANIMLARI (YALNIZCA EN ve ZH) ---
TEXT = {
    "en": { 
        "select": "Please select an option below 👇",
        "service": "🛠 SMS Services",
        "profile": "👤 Profile",
        "language": "🌐 Language",
        "wallet_title": "💰 Solana Wallet",
        "public_key_label": "🟢 Address (Public Key)",
        "balance_label": "💵 Current Balance (SOL)", 
        "note": "Balance is fetched live from the Solana Network.", 
        "service_msg": "🛠 Please select a **Service**:", 
        "sms_country_select": "🌎 Available countries for **{service_name}**:", 
        "sms_service_select": "🌐 **{service_name} - {country_name}** Details:",
        "sms_purchase_button": f"💸 Buy Number",
        "sms_purchase_detail": "🛒 **Purchase Details:**\n\nService: {service_name} ({country_name})\n**Price:** {price_sol:.8f} {price_symbol}\nStock: {stock} units\n\n**IMPORTANT:** Payment will be automatically transferred from your wallet **after the SMS code arrives**.",
        "loading": "⏳ Loading information, please wait...",
        "api_fail_service": "❌ Could not fetch price/stock for this country/service. Go back.",
        "back_msg": "🏠 Return to main menu.",
        "purchase_success": "✅ **Number Purchased Successfully!**\n\n**Number:** `{number}`\n**Order ID:** `{id}`\n**Service:** {service_name}\n**Cost (To be Paid):** {cost:.8f} SOL\n\nEnter this number into the application and wait for the code. Payment is **NOT MADE** until the code arrives. **The bot is checking for the code automatically...**",
        "purchase_fail": "❌ **Failed to Purchase Number.**\n\n**Error:** {error_message}\n\nPlease check your wallet balance, private key, or the system's API status.",
        "status_check": "🔄 **Checking Code...**",
        "status_code_ready_pay": "✅ **SMS Code Received and Payment Successful!**\n\n**Your Code:** `{code}`\n**Number:** `{number}`\n**Payment Status:** {transfer_status}\n**Transaction Signature:** `{transfer_sig}`\n\n_With this transaction, {cost:.8f} SOL was transferred to the service provider._",
        "status_code_ready_fail": "❌ **SMS Code Received, BUT Payment Failed!**\n\n**Your Code:** `{code}`\n**Number:** `{number}`\n**Payment Status:** {transfer_status}\n\n_Please check your wallet balance or private key._",
        "status_no_code": "⏳ **Code Has Not Arrived Yet.**\n\nPlease try sending the code again in the app. (You have 5 minutes.)",
        "status_cancelled": "🚫 **Transaction Canceled.**\n\nThis order has been canceled due to {reason}. **No payment was made.**",
        "cancel_button": "❌ Cancel (No Payment)",
        "check_button": "🔄 Check Code",
        "api_balance_fail": "API Balance: HIDDEN",
        "cancel_success": "✅ Order (`{id}`) successfully canceled. **No payment was made.**",
        "cancel_fail": "❌ Error during cancellation. Please check the order status manually.",
        "export_key": "🔑 Export Private Key", 
        "import_key": "📥 Import Private Key", 
        "generate_key": "✨ Generate New Wallet", 
        "wallet_setup_title": "Setup Wallet", 
        "wallet_setup_msg": "You do not have a wallet registered yet. Please choose an action:", 
        "export_key_msg": "🔑 **Your Private Key**\n\nUse this key to recover your wallet. Backup safely!",
        "key_delete_warning": "This message will self-destruct in {time} seconds for security.",
        "key_exported_ok": "🔑 Private Key sent privately. Check your chat.",
        "wallet_generated_note": "✨ New wallet generated, details below.",
        "import_prompt": "📥 Please send your **Private Key (Base58 format)** now.\n\n⚠️ **WARNING:** Remember we need access to this key for payments and transfers.",
        "import_success": "✅ Wallet successfully imported!\nYour new address:",
        "import_invalid": "❌ Invalid Private Key format. Try again.",
        "language_msg": "🌐 **Please select your language:",
        "insufficient_balance": "❌ **Insufficient Balance!**\n\nTo purchase this number and complete the transfer, you need a **minimum of {required_sol:.8f} SOL** in your wallet.\n\nCurrent balance: {current_balance:.8f} SOL.\n\nPlease top up your wallet and try again.",
        "next_action": "What would you like to do next?" # Yeni metin
    },
    "zh": { 
        "select": "请选择以下选项 👇",
        "service": "🛠 短信服务",
        "profile": "👤 个人资料",
        "language": "🌐 语言",
        "wallet_title": "💰 Solana 钱包",
        "public_key_label": "🟢 地址（公钥）",
        "balance_label": "💵 当前余额 (SOL)", 
        "note": "余额是从 Solana 网络实时获取的。", 
        "service_msg": "🛠 请选择一个**服务**:", 
        "sms_country_select": "🌎 **{service_name}** 可用国家/地区:",
        "sms_service_select": "🌐 **{service_name} - {country_name}** 详情:",
        "sms_purchase_button": f"💸 购买号码",
        "sms_purchase_detail": "🛒 **购买详情:**\n\n服务: {service_name} ({country_name})\n**价格:** {price_sol:.8f} {price_symbol}\n库存: {stock} 个\n\n**重要提示:** 短信验证码到达后，款项将从您的钱包中**自动转账**。",
        "loading": "⏳ 正在加载信息，请稍候...",
        "api_fail_service": "❌ 无法获取此国家/服务的价格或库存。请返回。",
        "back_msg": "🏠 返回主菜单。",
        "purchase_success": "✅ **号码购买成功!**\n\n**号码:** `{number}`\n**订单 ID:** `{id}`\n**服务:** {service_name}\n**费用（待支付）:** {cost:.8f} SOL\n\n将此号码输入到应用中并等待验证码。验证码到达之前**不会进行支付**。**机器人正在自动检查验证码...**",
        "purchase_fail": "❌ **购买号码失败。**\n\n**错误:** {error_message}\n\n请检查您的钱包余额、私钥或系统 API 状态。",
        "status_check": "🔄 **正在检查验证码...**",
        "status_code_ready_pay": "✅ **短信验证码已收到且支付成功!**\n\n**您的验证码:** `{code}`\n**号码:** `{number}`\n**支付状态:** {transfer_status}\n**交易签名:** `{transfer_sig}`\n\n_通过此交易，{cost:.8f} SOL 已转账给服务提供商。_",
        "status_code_ready_fail": "❌ **短信验证码已收到，但支付失败!**\n\n**您的验证码:** `{code}`\n**号码:** `{number}`\n**支付状态:** {transfer_status}\n\n_请检查您的钱包余额或私钥。_",
        "status_no_code": "⏳ **验证码尚未到达。**\n\n请尝试在应用中再次发送验证码。（您有 5 分钟时间。）",
        "status_cancelled": "🚫 **交易已取消。**\n\n此订单由于 {reason} 被取消。**未进行支付。**",
        "cancel_button": "❌ 取消 (不支付)",
        "check_button": "🔄 检查验证码",
        "api_balance_fail": "API 余额: 隐藏",
        "cancel_success": "✅ 订单 (`{id}`) 已成功取消。**未进行支付。**",
        "cancel_fail": "❌ 取消过程中发生错误。请手动检查订单状态。",
        "export_key": "🔑 导出私钥", 
        "import_key": "📥 导入私钥", 
        "generate_key": "✨ 生成新钱包", 
        "wallet_setup_title": "设置钱包", 
        "wallet_setup_msg": "您尚未注册钱包。请选择操作:", 
        "export_key_msg": "🔑 **您的私钥**\n\n使用此密钥恢复您的钱包。请安全备份！",
        "key_delete_warning": "出于安全考虑，此消息将在 {time} 秒后自毁。",
        "key_exported_ok": "🔑 私钥已私下发送。请检查您的聊天。",
        "wallet_generated_note": "✨ 新钱包已生成，详情如下。",
        "import_prompt": "📥 请立即发送您的**私钥（Base58 格式）**。\n\n⚠️ **警告:** 请记住，我们需要访问此密钥才能进行支付和转账。",
        "import_success": "✅ 钱包导入成功!\n您的新地址:",
        "import_invalid": "❌ 无效的私钥格式。请重试。",
        "language_msg": "🌐 **请选择您的语言:",
        "insufficient_balance": "❌ **余额不足!**\n\n要购买此号码并完成转账，您的钱包中需要**至少 {required_sol:.8f} SOL**。\n\n当前余额: {current_balance:.8f} SOL。\n\n请充值您的钱包并重试。",
        "next_action": "接下来您想做什么？" # Yeni metin
    }
}
# --- KALICI VERİ YÖNETİMİ FONKSİYONLARI ---

def save_wallets():
    """user_wallets sözlüğünü JSON dosyasına kaydeder."""
    try:
        with open(WALLET_DATA_FILE, 'w') as f:
            data_to_save = {str(uid): wallet for uid, wallet in user_wallets.items()}
            json.dump(data_to_save, f, indent=4)
    except Exception as e:
        print(f"Cüzdan verileri kaydedilirken hata oluştu: {e}")

def load_wallets():
    """JSON dosyasından cüzdan verilerini yükler."""
    global user_wallets
    if os.path.exists(WALLET_DATA_FILE):
        try:
            with open(WALLET_DATA_FILE, 'r') as f:
                loaded_data = json.load(f)
                # JSON dosyasından yüklerken anahtarları int'e çevir
                user_wallets = {int(uid): wallet for uid, wallet in loaded_data.items()}
            print(f"✅ {len(user_wallets)} adet cüzdan verisi başarıyla yüklendi.")
        except Exception as e:
            print(f"Cüzdan verileri yüklenirken hata oluştu (Dosya Bozuk/Okunamıyor): {e}")
            user_wallets = {}
    else:
        print("ℹ️ Cüzdan kayıt dosyası bulunamadı. Yeni dosya oluşturulacak.")
        user_wallets = {}

# --- MENÜ OLUŞTURMA FONKSİYONLARI ---

def main_menu(uid):
    lang = get_lang(uid)
    t = TEXT[lang]
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(t["service"], callback_data="open_service_menu"),
        InlineKeyboardButton(t["profile"], callback_data="open_profile_menu")
    )
    kb.add(InlineKeyboardButton(t["language"], callback_data="language"))
    return kb

def wallet_setup_menu(uid):
    lang = get_lang(uid)
    t = TEXT[lang]
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(t["generate_key"], callback_data="wallet_generate"))
    kb.add(InlineKeyboardButton(t["import_key"], callback_data="wallet_import"))
    kb.add(InlineKeyboardButton(f"🏠 {t['back_msg']}", callback_data="main_menu_return"))
    return kb
    
def service_menu(uid):
    lang = get_lang(uid)
    t = TEXT[lang]
    kb = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for code, name in FIVESIM_SERVICES.items():
        buttons.append(InlineKeyboardButton(name, callback_data=f"select_service_{code}"))
    for locked in LOCKED_SERVICES:
        buttons.append(InlineKeyboardButton(locked["name"], callback_data=f"locked_{locked['service']}"))
    kb.add(*buttons)
    kb.add(InlineKeyboardButton(f"⬅️ {t['back_msg']}", callback_data="main_menu_return"))
    return kb

def country_menu(service_code, service_name, uid):
    lang = get_lang(uid)
    t = TEXT[lang]
    kb = InlineKeyboardMarkup(row_width=3)
    prices_data = get_fivesim_services()
    available_countries = prices_data.get(service_code, {})
    buttons = []
    
    # Ülke kodlarını isme göre sırala (Bayrakları tutmak için FIVESIM_COUNTRIES kullanıldı)
    sorted_countries = sorted(available_countries.keys(), key=lambda k: FIVESIM_COUNTRIES.get(k, k).split()[-1])

    for country_code in sorted_countries:
        operators = available_countries.get(country_code, {})
        country_display_name = get_country_display_name(country_code)
        
        # Stok kontrolü için sadece fiyat ve stok içeren operatörleri say
        total_stock = sum(int(op.get('count', 0)) for op in operators.values() if isinstance(op, dict) and op.get('cost'))
        
        if total_stock > 0:
            buttons.append(InlineKeyboardButton(country_display_name, callback_data=f"select_country_{service_code}_{country_code}"))
            
    kb.add(*buttons)
    
    back_text = "Back" if lang == "en" else "返回"
    kb.add(InlineKeyboardButton(f"⬅️ {service_name} {back_text}", callback_data=f"select_service_{service_code}")) 
    kb.add(InlineKeyboardButton(f"🏠 {t['back_msg']}", callback_data="main_menu_return"))
    return kb

def wallet_details_menu(uid):
    lang = get_lang(uid)
    t = TEXT[lang]
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(t["export_key"], callback_data="wallet_export"))
    kb.add(InlineKeyboardButton(t["import_key"], callback_data="wallet_import"))
    kb.add(InlineKeyboardButton(f"🏠 {t['back_msg']}", callback_data="main_menu_return"))
    return kb

def language_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    # Sadece EN ve ZH seçenekleri
    kb.add(
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇨🇳 简体中文", callback_data="lang_zh")
    )
    kb.add(InlineKeyboardButton("🏠 Back", callback_data="main_menu_return"))
    return kb

# YENİ FONKSİYON: Sipariş iptali sonrası menü
def post_cancel_menu(service_code, country_code, uid):
    lang = get_lang(uid)
    t = TEXT[lang]
    
    service_name = get_service_display_name(service_code)
    country_name = get_country_display_name(country_code)
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    # 1. Aynı ülkeyi tekrar dene (Direkt satın alma ekranına gider)
    button_text_1 = f"♻️ Try {country_name} Again" if lang == "en" else f"♻️ 再次尝试 {country_name}"
    kb.add(InlineKeyboardButton(button_text_1, callback_data=f"select_country_{service_code}_{country_code}")) 
    
    # 2. Ülke listesine geri dön (Servisin ülke listesi menüsüne gider)
    button_text_2 = f"🌎 Select Different Country" if lang == "en" else f"🌎 选择其他国家/地区"
    kb.add(InlineKeyboardButton(button_text_2, callback_data=f"select_service_{service_code}"))
    
    kb.add(InlineKeyboardButton(f"🏠 {t['back_msg']}", callback_data="main_menu_return"))
    return kb

def send_purchase_result(chat_id, message_id, result, service_name, country_name, uid):
    lang = get_lang(uid)
    t = TEXT[lang]
    kb = InlineKeyboardMarkup(row_width=2)
    
    if result["status"] == "success":
        order_id = result["id"]
        number = result["number"]
        cost = result["cost_sol"]
        
        # Geri dönüş için gerekli service ve country kodları
        service_code = user_sms_state[uid]['service_code'] 
        country_code = user_sms_state[uid]['country_code'] 

        user_sms_state[uid]['order_id'] = order_id
        user_sms_state[uid]['number'] = number
        user_sms_state[uid]['message_id'] = message_id 

        message_text = t["purchase_success"].format(
            number=number, id=order_id, service_name=service_name, cost=cost
        )
        
        # GÜNCELLENDİ: İptal callback'ine service ve country kodları eklendi
        kb.add(
            InlineKeyboardButton(t["cancel_button"], callback_data=f"cancel_order_{order_id}_{service_code}_{country_code}")
        )

        try:
            bot.edit_message_text(message_text, chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException:
             # Eğer mesaj düzenlenemezse (çok eskimişse veya hızlıca silinmişse) yeni mesaj gönder
             sent_msg = bot.send_message(chat_id, message_text, reply_markup=kb, parse_mode="Markdown")
             user_sms_state[uid]['message_id'] = sent_msg.message_id
             
        start_code_check_thread(uid, order_id, chat_id, user_sms_state[uid]['message_id'], cost)
        
    else:
        error_message = result.get('message', 'Unknown Error')
        message_text = t["purchase_fail"].format(error_message=error_message)
        
        # Hangi menüye geri döneceğini belirle
        service_code = user_sms_state.get(uid, {}).get('service_code')
        service_name = get_service_display_name(service_code)
        back_text = "Back" if lang == "en" else "返回"
        kb.add(InlineKeyboardButton(f"⬅️ {service_name} {back_text}", callback_data=f"select_service_{service_code}"))
        kb.add(InlineKeyboardButton(f"🏠 {t['back_msg']}", callback_data="main_menu_return"))
        
        try:
            bot.edit_message_text(message_text, chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException:
             bot.send_message(chat_id, message_text, reply_markup=kb, parse_mode="Markdown")
             
# --- API VE YARDIMCI FONKSİYONLAR ---

def get_current_usd_rub_price():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=usd&vs_currencies=rub", timeout=5)
        response.raise_for_status()
        rub_price = response.json().get('usd', {}).get('rub', USD_PRICE_RUB)
    except Exception:
        rub_price = USD_PRICE_RUB
    return float(rub_price)
def get_current_sol_rub_price():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=rub", timeout=5)
        response.raise_for_status()
        sol_rub = response.json().get('solana', {}).get('rub', -1)
        if sol_rub > 0: return float(sol_rub)
        sol_usd_response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd", timeout=5)
        sol_usd = sol_usd_response.json().get('solana', {}).get('usd', SOL_PRICE_USD) 
        usd_rub = get_current_usd_rub_price() 
        sol_rub = sol_usd * usd_rub
        return float(sol_rub)
    except Exception:
        usd_rub = get_current_usd_rub_price() 
        sol_rub_fallback = SOL_PRICE_USD * usd_rub
        return float(sol_rub_fallback)
def convert_rub_to_sol(rub_amount):
    sol_rub = get_current_sol_rub_price()
    if sol_rub <= 0: return 999999 
    sol_amount = rub_amount / sol_rub
    return sol_amount

def perform_solana_transfer(sender_key_base58: str, receiver_pubkey: Pubkey, amount_sol: float):
    try:
        key_bytes = base58.b58decode(sender_key_base58)
        sender_keypair = Keypair.from_bytes(key_bytes)
        amount_lamports = int(amount_sol * 1_000_000_000)
        recent_blockhash_result = solana_client.get_latest_blockhash()
        if recent_blockhash_result.value is None:
            return "Blok Hash alınamadı."
        recent_blockhash = recent_blockhash_result.value.blockhash
        instruction = transfer(
            TransferParams(
                from_pubkey=sender_keypair.pubkey(),
                to_pubkey=receiver_pubkey,
                lamports=amount_lamports,
            )
        )
        transaction = Transaction.new_signed_with_payer(
            [instruction], 
            sender_keypair.pubkey(), 
            [sender_keypair], 
            recent_blockhash 
        )
        result = solana_client.send_transaction(transaction)
        if result.value is None:
            return "Transfer işlemi imzası alınamadı veya başarısız oldu." 
        return result.value 
    except SolanaRpcException as e:
        return f"RPC Hatası: {e}"
    except Exception as e:
        return f"Genel Transfer Hatası: {e}"
def delete_message_later(chat_id, message_id, delay):
    def delete():
        try: bot.delete_message(chat_id, message_id)
        except telebot.apihelper.ApiTelegramException: pass
    timer = threading.Timer(delay, delete)
    timer.start()
def get_service_display_name(service_code):
    return FIVESIM_SERVICES.get(service_code, service_code.capitalize())
def get_country_display_name(country_code):
    country_code = country_code.lower()
    return FIVESIM_COUNTRIES.get(country_code, country_code.capitalize())
def get_sol_balance(public_key: str):
    try:
        pubkey_obj = Pubkey.from_string(public_key) 
        lamports = solana_client.get_balance(pubkey_obj).value 
        return lamports / 1_000_000_000.0
    except Exception:
        return -1.0
def generate_solana_keypair():
    keypair = SoldersKeypair()
    public_key = str(keypair.pubkey())
    private_key_bytes = bytes(keypair)
    private_key_base58 = base58.b58encode(private_key_bytes).decode('utf-8')
    return public_key, private_key_base58
def generate_and_save_wallet(uid): 
    public_key, private_key_base58 = generate_solana_keypair()
    user_wallets[uid] = {"public_key": public_key, "private_key_base58": private_key_base58}
    save_wallets() 
    return public_key
def validate_and_save_key(private_key_base58: str, uid):
    try:
        key_bytes = base58.b58decode(private_key_base58)
        keypair = Keypair.from_bytes(key_bytes)
        public_key = str(keypair.pubkey())
        user_wallets[uid] = {"public_key": public_key, "private_key_base58": private_key_base58}
        
        save_wallets()
        
        return public_key
    except Exception:
        return None
def get_lang(user_id):
    return user_lang.get(user_id, "en")
def handle_private_key_input(message):
    uid = message.from_user.id
    lang = get_lang(uid)
    t = TEXT[lang]
    chat_id = message.chat.id
    try: delete_message_later(chat_id, message.message_id, 1)
    except Exception: pass
    
    private_key = message.text.strip()
    new_public_key = validate_and_save_key(private_key, uid) 
    if new_public_key:
        success_message = f"**{t['import_success']}**\n`{new_public_key}`"
        bot.send_message(chat_id, success_message, parse_mode="Markdown", reply_markup=wallet_details_menu(uid))
    else:
        bot.send_message(chat_id, t["import_invalid"], reply_markup=wallet_setup_menu(uid))

def get_fivesim_services():
    url = "https://5sim.net/v1/guest/prices"
    try:
        guest_headers = {"Accept": "application/json"}
        response = requests.get(url, headers=guest_headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict): return {}
        grouped_data = {}
        for country_code, services in data.items():
            if not isinstance(services, dict): continue
            for service_code, operators in services.items():
                if not isinstance(operators, dict): continue
                if service_code not in grouped_data: grouped_data[service_code] = {}
                grouped_data[service_code][country_code.lower()] = operators 
        return grouped_data
    except requests.exceptions.RequestException as e:
        print(f"API Connection Error (get_fivesim_services): {e}")
        return {}
    except Exception as e:
        print(f"General Error in get_fivesim_services: {e}")
        return {}
def get_fivesim_service_price(service_code, country_code):
    prices_data = get_fivesim_services()
    operator_details = prices_data.get(service_code, {}).get(country_code.lower(), {}) 
    if not isinstance(operator_details, dict) or not operator_details:
        return {"price_rub": "N/A", "stock": 0, "sale_sol_price": "N/A", "final_price_rub": "N/A"}
    min_fivesim_cost = float('inf') 
    total_stock = 0
    for detail in operator_details.values():
        try:
            base_fivesim_cost = float(detail.get('cost', 0))
            stock = int(detail.get('count', 0))
            if stock > 0 and base_fivesim_cost > 0:
                total_stock += stock
                min_fivesim_cost = min(min_fivesim_cost, base_fivesim_cost)
        except Exception:
            continue
    if total_stock == 0 or min_fivesim_cost == float('inf'):
        return {"price_rub": "N/A", "stock": 0, "sale_sol_price": "N/A", "final_price_rub": "N/A"}
    base_price_rub = min_fivesim_cost
    final_price_rub = base_price_rub * PROFIT_MULTIPLIER 
    sale_sol_price = convert_rub_to_sol(final_price_rub)
    try:
        if float(sale_sol_price) <= 0:
             return {"price_rub": "N/A", "stock": 0, "sale_sol_price": "N/A", "final_price_rub": "N/A"}
    except (ValueError, TypeError):
         return {"price_rub": "N/A", "stock": 0, "sale_sol_price": "N/A", "final_price_rub": "N/A"}
    return {
        "price_rub": base_price_rub, 
        "stock": total_stock, 
        "sale_sol_price": sale_sol_price, 
        "final_price_rub": final_price_rub
    }

def buy_fivesim_number(service_code, country_code, uid):
    """5sim API üzerinden numara satın alır."""
    details = get_fivesim_service_price(service_code, country_code)
    required_sol = details.get('sale_sol_price')
    stock = details.get('stock', 0)
    
    if required_sol == "N/A" or stock == 0:
        return {"status": "error", "message": "Price or stock information not found. Please check the service again."}
    
    final_country_code = country_code.lower()
    final_service_code = service_code.lower()
    
    url = f"{FIVESIM_BASE_URL}buy/activation/{final_country_code}/any/{final_service_code}"
    
    try:
        response = requests.get(url, headers=FIVESIM_HEADERS, timeout=20)
        
        if response.status_code != 200:
            try:
                data = response.json()
                error_msg_log = data.get('error', f"HTTP Error Code: {response.status_code}")
                if response.status_code == 400 and data.get('error') in ('no_free_numbers', 'no_numbers'):
                    error_msg_log = 'No suitable numbers available (Stock Error) or Insufficient API Balance.'
                if response.status_code == 403:
                    error_msg_log += "\n**DEBUG:** Check 5sim.net JWT key and balance."
                
                print(f"5SIM API Error (buy): {error_msg_log}")
                user_friendly_error = "5SIM API Error: Failed to purchase number due to system restrictions or temporary unavailability."
                
                return {"status": "error", "message": user_friendly_error}
            except json.JSONDecodeError:
                print(f"5SIM API Error: Failed to parse JSON response. Status: {response.status_code}")
                return {"status": "error", "message": "5SIM API Error: Invalid response from server."}

        data = response.json()

        if data.get('id') and data.get('phone'):
            order_id = data['id'] 
            number = data['phone']
            
            user_sms_state[uid]['sale_sol_price'] = required_sol
            return {
                "status": "success", 
                "id": str(order_id), 
                "number": str(number), 
                "cost_sol": required_sol,
                "transfer_sig": None 
            }
        
        error_msg_log = data.get('error', 'Unknown API error: JSON valid but content missing (ID/Number).')
        if data.get('msg') == 'no free numbers' or data.get('msg') == 'no numbers':
             error_msg_log = 'No suitable numbers available (Stock Check). Go back.'
             
        print(f"5SIM API Error (buy - data fail): {error_msg_log}")
        user_friendly_error = "5SIM API Error: The number is no longer available or there was an internal server issue."
        
        return {"status": "error", "message": user_friendly_error}
        
    except requests.exceptions.RequestException as e:
        print(f"Connection Error (buy_fivesim_number): {e}")
        return {"status": "error", "message": "Connection Error: Failed to reach the API server."}
    except Exception as e:
        print(f"General Bot Error (buy_fivesim_number): {e}")
        return {"status": "error", "message": "General Bot Error during purchase."}

def get_fivesim_number_status(order_id):
    url = f"{FIVESIM_BASE_URL}check/{order_id}"
    try:
        response = requests.get(url, headers=FIVESIM_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        status_text = data.get('status', 'ERROR')
        
        status_map = {"WAITING": 0, "RECEIVED": 1, "CANCELED": -1, "TIMEOUT": -1, "FINISHED": 1}
        
        sms_code_list = data.get('sms', [])
        sms_code = sms_code_list[0].get('code') if sms_code_list and isinstance(sms_code_list, list) and sms_code_list and isinstance(sms_code_list[0], dict) else 'N/A'
        
        return {"status_code": status_map.get(status_text, -2), "code": sms_code, "status_text": status_text}
    except Exception as e:
        print(f"Status check error for order {order_id}: {e}")
        return {"status_code": -2, "code": "API/HATA", "status_text": "ERROR"}

def check_and_pay_solana(order_id, uid, cost_sol):
    """Kod geldiğinde ödeme işlemini dener."""
    wallet_info = user_wallets.get(uid)
    
    if not wallet_info or not wallet_info.get("private_key_base58"):
        return {"status": False, "transfer_sig": None, "transfer_status": "❌ Private Key Missing"}
    
    sender_private_key = wallet_info["private_key_base58"]
    
    try:
        cost_sol_float = float(cost_sol)
        
        current_balance = get_sol_balance(wallet_info["public_key"])
        
        required_minimum_balance = cost_sol_float + SOLANA_FEE_SOL + SOLANA_ACCOUNT_MIN_RENT 
        
        if current_balance < required_minimum_balance:
            return {"status": False, "transfer_sig": None, "transfer_status": f"❌ Insufficient Balance ({current_balance:.8f} SOL)"}
        
        transfer_sig = perform_solana_transfer(sender_private_key, RECEIVER_WALLET_PUBKEY, cost_sol_float)
        
        if len(str(transfer_sig)) > 50 and not str(transfer_sig).startswith("RPC Hatası"):
            return {"status": True, "transfer_sig": transfer_sig, "transfer_status": "✅ Payment Successful"}
        else:
            return {"status": False, "transfer_sig": None, "transfer_status": f"❌ Transfer Error: {transfer_sig}"}
    
    except Exception as e:
        return {"status": False, "transfer_sig": None, "transfer_status": f"❌ General Payment Error: {e}"}
            
def cancel_fivesim_number(order_id):
    url = f"{FIVESIM_BASE_URL}cancel/{order_id}"
    try:
        response = requests.get(url, headers=FIVESIM_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('status') in ["CANCELED", "TIMEOUT", "FINISHED"] 
    except Exception as e:
        print(f"Cancel order {order_id} error: {e}")
        return False
        
# --- OTOMATİK KOD KONTROL THREAD'İ ---

def start_code_check_thread(uid, order_id, chat_id, message_id, cost_sol):
    """
    Numara alındıktan sonra arka planda kodu sürekli kontrol eden thread'i başlatır.
    """
    thread_name = f"check_{order_id}"
    
    if thread_name in active_check_threads:
        return

    def check_loop():
        start_time = time.time()
        lang = get_lang(uid)
        t = TEXT[lang]
        
        while time.time() - start_time < MAX_CHECK_TIME_SECONDS:
            time.sleep(CHECK_INTERVAL_SECONDS)
            
            status_result = get_fivesim_number_status(order_id)
            status_code = status_result["status_code"]
            sms_code = status_result["code"]
            
            current_state = user_sms_state.get(uid, {})
            number = current_state.get("number", "N/A")
            
            # --- 1. KOD GELDİ ---
            if status_code == 1 and sms_code and sms_code != 'N/A':
                pay_result = check_and_pay_solana(order_id, uid, cost_sol)
                transfer_status = pay_result["transfer_status"]
                transfer_sig = pay_result["transfer_sig"]
                cost_sol_display = float(cost_sol)

                kb = InlineKeyboardMarkup(row_width=1)
                kb.add(InlineKeyboardButton(t["back_msg"], callback_data="main_menu_return"))
                
                if pay_result["status"]:
                    message_text = t["status_code_ready_pay"].format(
                        code=sms_code, number=number, transfer_status=transfer_status, transfer_sig=transfer_sig, cost=cost_sol_display
                    )
                else:
                    message_text = t["status_code_ready_fail"].format(
                        code=sms_code, number=number, transfer_status=transfer_status
                    )
                
                try:
                    bot.edit_message_text(message_text, chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
                except telebot.apihelper.ApiTelegramException:
                    pass
                
                break

            # --- 2. İPTAL VEYA ZAMAN AŞIMI ---
            elif status_code == -1:
                reason = status_result["status_text"] 
                message_text = t["status_cancelled"].format(reason=reason)
                kb = InlineKeyboardMarkup(row_width=1)
                kb.add(InlineKeyboardButton(t["back_msg"], callback_data="main_menu_return"))
                
                try:
                    bot.edit_message_text(message_text, chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
                except telebot.apihelper.ApiTelegramException:
                    pass
                
                break

            # --- 3. KOD BEKLENİYOR (Devam) ---
            pass
            
        if thread_name in active_check_threads:
            del active_check_threads[thread_name]
        
        if time.time() - start_time >= MAX_CHECK_TIME_SECONDS and status_code == 0:
            print(f"Order {order_id} reached max check time, likely TIMEOUT.")

    thread = threading.Thread(target=check_loop, name=thread_name)
    active_check_threads[thread_name] = thread
    thread.start()

# --- TELEGRAM HANDLERLAR ---

@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    user_lang[uid] = "en" 
    
    bot.send_message(message.chat.id, TEXT["en"]["select"], reply_markup=main_menu(uid))

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    lang = get_lang(uid) 
    t = TEXT[lang]
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "open_service_menu":
        if uid not in user_wallets:
            alert_text = "Please set up your Solana wallet first." if lang == "en" else "请先设置您的 Solana 钱包。"
            bot.answer_callback_query(call.id, text=alert_text, show_alert=True)
            try: 
                 bot.edit_message_text(f"**{t['wallet_setup_title']}**\n\n{t['wallet_setup_msg']}", chat_id, message_id, reply_markup=wallet_setup_menu(uid), parse_mode="Markdown")
            except Exception: 
                 bot.send_message(chat_id, f"**{t['wallet_setup_title']}**\n\n{t['wallet_setup_msg']}", reply_markup=wallet_setup_menu(uid), parse_mode="Markdown")
            return
            
        try: bot.edit_message_text(t["service_msg"], chat_id, message_id, reply_markup=service_menu(uid))
        except Exception: bot.send_message(chat_id, t["service_msg"], reply_markup=service_menu(uid))
        return
    elif call.data == "main_menu_return":
        try: bot.edit_message_text(t["select"], chat_id, message_id, reply_markup=main_menu(uid))
        except Exception: bot.send_message(chat_id, t["select"], reply_markup=main_menu(uid))
        return
    elif call.data.startswith("locked_"):
        alert_text = "🔜 Coming Soon 🔒" if lang == "en" else "🔜 即将推出 🔒"
        bot.answer_callback_query(call.id, text=alert_text, show_alert=True)
        return
    elif call.data.startswith("select_service_"):
        service_code = call.data.split("_")[-1]
        service_name = get_service_display_name(service_code)
        try:
            loading_message = t["sms_country_select"].format(service_name=service_name)
            bot.edit_message_text(f"{loading_message.split(':')[0]}: {t['loading']}", chat_id, message_id, parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException: pass
        
        # Eğer bu çağrı, iptal menüsünden geliyorsa ve state boşsa tekrar doldur
        if uid not in user_sms_state or 'service_name' not in user_sms_state[uid]:
            user_sms_state[uid] = {"service_code": service_code, "service_name": service_name}
            
        bot.edit_message_text(
            loading_message,
            chat_id,
            message_id,
            reply_markup=country_menu(service_code, service_name, uid),
            parse_mode="Markdown"
        )
        return
    elif call.data.startswith("select_country_"):
        try:
            _, _, service_code, country_code = call.data.split("_", 3)
        except ValueError:
            bot.answer_callback_query(call.id, text="Error: Country data corrupted.", show_alert=True)
            return
            
        service_name = user_sms_state.get(uid, {}).get("service_name", get_service_display_name(service_code))
        country_name = get_country_display_name(country_code)

        try:
            loading_message = t["sms_service_select"].format(service_name=service_name, country_name=country_name)
            bot.edit_message_text(f"{loading_message.split(':')[0]}: {t['loading']}", chat_id, message_id, parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException: pass

        details = get_fivesim_service_price(service_code, country_code)
        sale_sol_price = details.get('sale_sol_price')
        stock = details.get('stock')
        
        if sale_sol_price == "N/A" or stock == 0:
             bot.answer_callback_query(call.id, text=t["api_fail_service"], show_alert=True)
             try: bot.delete_message(chat_id, message_id)
             except Exception: pass
             bot.send_message(chat_id, t["service_msg"], reply_markup=service_menu(uid))
             return
             
        user_sms_state[uid].update({
            "service_code": service_code, # Tekrar ekle
            "country_code": country_code, 
            "country_name": country_name,
            "sale_sol_price": sale_sol_price,
            "order_id": None,
            "number": None    
        })

        purchase_message = t["sms_purchase_detail"].format(
            service_name=service_name,
            country_name=country_name,
            price_sol=sale_sol_price,
            stock=stock,
            price_symbol=CURRENCY_SYMBOL
        )
        
        purchase_kb = InlineKeyboardMarkup(row_width=1)
        purchase_kb.add(InlineKeyboardButton(t["sms_purchase_button"], callback_data=f"buy_number_{service_code}_{country_code}")) 
        
        back_text = "Back" if lang == "en" else "返回"
        purchase_kb.add(InlineKeyboardButton(f"⬅️ {service_name} {back_text}", callback_data=f"select_service_{service_code}")) 
        
        bot.edit_message_text(purchase_message, chat_id, message_id, reply_markup=purchase_kb, parse_mode="Markdown")
        return
    elif call.data.startswith("buy_number_"):
        
        alert_text = "Checking balance..." if lang == "en" else "正在检查余额..."
        bot.answer_callback_query(call.id, text=alert_text)
        
        try:
            _, _, service_code, country_code = call.data.split("_", 3)
        except ValueError:
            bot.answer_callback_query(call.id, text="Error: Purchase data corrupted.", show_alert=True)
            return
        
        current_state = user_sms_state.get(uid, {})
        service_name = current_state.get("service_name", get_service_display_name(service_code))
        cost_sol = current_state.get("sale_sol_price")

        wallet_info = user_wallets.get(uid)
        
        if not wallet_info or not wallet_info.get("private_key_base58") or not cost_sol or cost_sol == "N/A":
             error_msg = "Wallet is not set up or price data is missing."
             bot.edit_message_text(t["purchase_fail"].format(error_message=error_msg), chat_id, message_id)
             return
             
        cost_sol_float = float(cost_sol)
        current_balance = get_sol_balance(wallet_info["public_key"])
        
        required_minimum_balance = cost_sol_float + SOLANA_FEE_SOL + SOLANA_ACCOUNT_MIN_RENT 
        
        if current_balance < required_minimum_balance:
            error_message = t["insufficient_balance"].format(
                required_sol=required_minimum_balance, 
                current_balance=current_balance
            )
            kb_error = InlineKeyboardMarkup(row_width=1)
            kb_error.add(InlineKeyboardButton(f"👤 {t['profile']}", callback_data="open_profile_menu"))
            
            back_text = "Back" if lang == "en" else "返回"
            kb_error.add(InlineKeyboardButton(f"⬅️ {service_name} {back_text}", callback_data=f"select_service_{service_code}"))
            
            bot.edit_message_text(error_message, chat_id, message_id, reply_markup=kb_error, parse_mode="Markdown")
            return
        
        bot.edit_message_text(t["loading"], chat_id, message_id)
        
        result = buy_fivesim_number(service_code, country_code.lower(), uid) 
        
        send_purchase_result(chat_id, message_id, result, service_name, current_state.get("country_name"), uid)
        return
    
    # GÜNCELLENDİ: İptal callback handler
    elif call.data.startswith("cancel_order_"):
        
        try:
             # order_id, service_code ve country_code'u alıyoruz
             _, _, order_id_str, service_code, country_code = call.data.split("_", 4)
             order_id = int(order_id_str)
        except ValueError:
             bot.answer_callback_query(call.id, text="Error: Order data corrupted.", show_alert=True)
             bot.edit_message_text(t["select"], chat_id, message_id, reply_markup=main_menu(uid))
             return
             
        success = cancel_fivesim_number(order_id)
        
        # Thread'i durdur
        thread_name = f"check_{order_id}"
        if thread_name in active_check_threads:
            del active_check_threads[thread_name]
            
        # Mesaj metnini oluştur
        if success:
            message_text = t["cancel_success"].format(id=order_id)
            
            # YENİ MENÜ GÖSTERİLİYOR
            new_kb = post_cancel_menu(service_code, country_code, uid)
            
            message_text += f"\n\n**{t['next_action']}**"
        else:
            # İptal başarısızsa, hata mesajını göster ve servisin ülke listesine dönme butonu ekle
            message_text = t["cancel_fail"]
            service_name = get_service_display_name(service_code)
            new_kb = InlineKeyboardMarkup(row_width=1)
            back_text = "Back" if lang == "en" else "返回"
            new_kb.add(InlineKeyboardButton(f"⬅️ {service_name} {back_text}", callback_data=f"select_service_{service_code}"))
            new_kb.add(InlineKeyboardButton(f"🏠 {t['back_msg']}", callback_data="main_menu_return"))

        # Mesajı güncelle
        bot.edit_message_text(message_text, chat_id, message_id, reply_markup=new_kb, parse_mode="Markdown")
        
        # İptal durumunda state'i temizle
        if uid in user_sms_state:
             del user_sms_state[uid]
             
        return
    elif call.data == "open_profile_menu": 
        
        if uid not in user_wallets:
            bot.edit_message_text(
                f"**{t['wallet_setup_title']}**\n\n{t['wallet_setup_msg']}", 
                chat_id, 
                message_id, 
                reply_markup=wallet_setup_menu(uid), 
                parse_mode="Markdown"
            )
            return
            
        public_key = user_wallets[uid]["public_key"]
        
        balance_float = get_sol_balance(public_key)
        balance_text = f"{balance_float:.8f} SOL" if balance_float >= 0 else t['api_fail_service'] 
        
        message_text = (
            f"**{t['wallet_title']}**\n\n"
            f"**{t['public_key_label']}:**\n"
            f"`{public_key}`\n\n"
            f"**{t['balance_label']}:** {balance_text}\n\n"
            f"_{t['note']}_" 
        )
        
        bot.edit_message_text(
            message_text, chat_id, message_id, reply_markup=wallet_details_menu(uid), parse_mode="Markdown"
        )
        return
    elif call.data == "wallet_generate":
        public_key = generate_and_save_wallet(uid)
        
        balance_float = get_sol_balance(public_key)
        balance_text = f"{balance_float:.8f} SOL" if balance_float >= 0 else t['api_fail_service'] 
        
        message_text = (
            f"**{t['wallet_title']}** ({t['wallet_generated_note']})\n\n"
            f"**{t['public_key_label']}:**\n"
            f"`{public_key}`\n\n"
            f"**{t['balance_label']}:** {balance_text}\n\n"
            f"_{t['note']}_" 
        )
        
        bot.edit_message_text(
            message_text, chat_id, message_id, reply_markup=wallet_details_menu(uid), parse_mode="Markdown"
        )
        return
    elif call.data == "wallet_export":
        if uid not in user_wallets:
            alert_text = "Error: Wallet information not found." if lang == "en" else "错误：未找到钱包信息。"
            bot.answer_callback_query(call.id, text=alert_text, show_alert=True)
            return
        
        public_key = user_wallets[uid]["public_key"]
        private_key_base58 = user_wallets[uid]["private_key_base58"]
        
        warning_text = t["key_delete_warning"].format(time=20)
        full_message = (
            f"{t['export_key_msg']}\n\n"
            f"**{t['public_key_label']}:**\n"
            f"`{public_key}`\n\n"
            f"**Private Key:**\n" 
            f"`{private_key_base58}`\n\n"
            f"_{warning_text}_"
        )
        sent_msg = bot.send_message(chat_id, full_message, parse_mode="Markdown")
        delete_message_later(sent_msg.chat.id, sent_msg.message_id, 20)
        bot.answer_callback_query(call.id, text=t["key_exported_ok"])
        return
    elif call.data == "wallet_import":
        alert_text = "Starting import..." if lang == "en" else "正在开始导入..."
        bot.answer_callback_query(call.id, text=alert_text)
        try: bot.delete_message(chat_id, message_id)
        except Exception: pass
        sent_msg = bot.send_message(chat_id, t["import_prompt"], parse_mode="Markdown")
        delete_message_later(sent_msg.chat.id, sent_msg.message_id, 60)
        bot.register_next_step_handler(sent_msg, handle_private_key_input)
        return
    elif call.data == "language":
        bot.edit_message_text(t["language_msg"], chat_id, message_id, reply_markup=language_menu())
        return
    elif call.data.startswith("lang_"):
        new_lang = call.data.split("_")[1]
        if new_lang in TEXT:
            user_lang[uid] = new_lang
        else:
            user_lang[uid] = "en" 
            new_lang = "en"
            
        nt = TEXT[new_lang] 
        bot.edit_message_text(nt["select"], chat_id, message_id, reply_markup=main_menu(uid))
        return
    elif call.data == "ignore_error" or call.data == "open_country_menu_placeholder":
        try: bot.edit_message_text(t["service_msg"], chat_id, message_id, reply_markup=service_menu(uid))
        except Exception: bot.send_message(chat_id, t["service_msg"], reply_markup=service_menu(uid))
        return
    else:
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        return

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    pass

# --- HATA AYIKLAMA (DEBUG) FONKSİYONU - Bot Başlangıcı ---
def test_fivesim_api():
    print("--- 5SIM API BAĞLANTI VE BAKIYE TESTİ BAŞLATILIYOR ---")
    
    rub_rate = get_current_usd_rub_price()
    sol_rub_rate = get_current_sol_rub_price()
    print(f"🌐 Currency Check: 1 USD = {rub_rate:.2f} RUB | 1 SOL = {sol_rub_rate:.2f} RUB")
    
    def get_fivesim_account_balance_debug():
        url = f"{FIVESIM_BASE_URL}profile" 
        try:
            response = requests.get(url, headers=FIVESIM_HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {"status": "success", "balance": float(data.get('balance', 0.0)), "currency": data.get('currency', 'RUB'), "http_status": 200, "message": "OK"} 
            else:
                error_message = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('error', 'API Server Error')
                    error_message += f" - Detail: {error_detail}"
                except:
                    error_message += " - Response unreadable."
                return {"status": "error", "message": error_message, "balance": 0.0, "currency": "N/A", "http_status": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Connection Error: {e}", "balance": 0.0, "currency": "N/A", "http_status": 0}
        except Exception as e:
            return {"status": "error", "message": f"General Error: {e}", "balance": 0.0, "currency": "N/A", "http_status": 0}

    balance_result = get_fivesim_account_balance_debug()
    http_status = balance_result["http_status"]
    
    if balance_result["status"] == "success":
        balance = balance_result["balance"]
        currency = balance_result["currency"]
        
        if currency == 'RUB':
            balance_sol = convert_rub_to_sol(balance)
        elif currency == 'USD':
            balance_rub_from_usd = balance * rub_rate
            balance_sol = convert_rub_to_sol(balance_rub_from_usd)
        else:
            balance_sol = 0.0

        print("--- 5SIM BALANCE STATUS (API Key OK) ---")
        print(f"✅ HTTP 200 Successful. Account Balance ({currency}): {balance:.2f} {currency}")
        print(f"✅ Estimated SOL Equivalent: {balance_sol:.8f} SOL")

    else:
        print("--- 5SIM BALANCE CHECK FAILED ---")
        print(f"❌ HTTP Status: {http_status}")
        print(f"❌ Error Message: {balance_result['message']}")
        if http_status == 403:
            print("\n*** ⚠️ 403 ALERT: Your Key is likely INVALID or restricted. ***")
            print("*** Please get a NEW JWT Key from 5sim.net and copy it correctly to 'FIVESIM_API_KEY'. ***")


    prices_data = get_fivesim_services()
    if prices_data:
        first_service = next(iter(prices_data.keys()), "N/A")
        if first_service != "N/A":
            first_country = next(iter(prices_data.get(first_service, {}).keys()), "N/A")
            
            if first_country != "N/A":
                details = get_fivesim_service_price(first_service, first_country)
                print(f"✅ Price Fetch Successful (Guest API): {first_service}/{first_country}")
                print(f"   Final Price (SOL, including profit): {details.get('sale_sol_price')}, Stock: {details.get('stock')}")
            else:
                 print(f"❌ Price Fetch Failed: No country found under first service ({first_service}).")
        else:
            print("❌ Price Fetch Failed: No service data received from API.")

    print("--- 5SIM API CONNECTION AND BALANCE TEST ENDED ---")


# --- BOT BAŞLATMA ---

if __name__ == '__main__':
    load_wallets() 
    test_fivesim_api() 
    print("Bot starting...")
    bot.polling(non_stop=True, interval=0)
