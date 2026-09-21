import os
import telebot
import requests
import json
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- DUMMY WEB SERVER FOR RENDER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running smoothly!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Dummy server running on port {port}")
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()
# -----------------------------------

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_KEY = os.getenv('OSINT_API_KEY')
API_BASE_URL = 'https://onrender.com'

if not BOT_TOKEN or not API_KEY:
    print("Error: TELEGRAM_BOT_TOKEN ya OSINT_API_KEY set nahi hai!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🔍 **OSINT Search Bot mein aapka swagat hai!**\n\n"
        "Mujhe koi bhi target ya phone number bhejein (jaise: `919116224238`).\n"
        "Main API se data check karke aapko result bataunga.\n\n"
        "⚡ _Commands:_ \n"
        "/start - Bot shuru karne ke liye"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_osint_search(message):
    query = message.text.strip()
    
    if query.startswith('/'):
        if query not in ['/start', '/help']:
            bot.reply_to(message, "❌ Galat command! Kripya sahi command chunein ya seedhe number bhejein.")
            return

    bot.send_chat_action(message.chat.id, 'typing')
    status_msg = bot.reply_to(message, "⏳ API se data fetch kiya ja raha hai, kripya intezar karein...")

    try:
        payload = {
            'key': API_KEY,
            'query': query
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(API_BASE_URL, params=payload, headers=headers, timeout=25)
        
        if response.status_code == 200:
            raw_text = response.text
            
            if "<html" in raw_text.lower() or "414 request-uri too large" in raw_text.lower():
                bot.send_message(message.chat.id, "❌ Server Error: API ne data ki jagah HTML error page return kiya hai. Kripya query check karein.")
                return

            try:
                json_data = response.json()
                clean_output = json.dumps(json_data, indent=4, ensure_ascii=False)
            except:
                clean_output = raw_text

            if len(clean_output) > 3000:
                filename = f"result_{query}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(clean_output)
                
                with open(filename, "rb") as doc:
                    bot.send_document(
                        message.chat.id, 
                        doc, 
                        caption=f"📋 Search Results for `{query}`\n(Data bada hone ke karan file format mein bheja gaya hai.)",
                        parse_mode='Markdown'
                    )
                
                if os.path.exists(filename):
                    os.remove(filename)
            else:
                response_text = f"✅ **Search Results for:** `{query}`\n\n```text\n{clean_output}\n```"
                bot.send_message(message.chat.id, response_text, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"❌ API Error: Server ne error code {response.status_code} diya.")
            
    except requests.exceptions.Timeout:
        bot.send_message(message.chat.id, "⏱️ API Timeout: Server respond nahi kar raha hai, kripya thodi der baad prayas karein.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Connection Error: {str(e)}")
    finally:
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except:
            pass

if __name__ == '__main__':
    print("🚀 Bot restarted successfully with URL optimization...")
    bot.infinity_polling(timeout=60, long_polling_timeout=5)
