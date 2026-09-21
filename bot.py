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
        self.wfile.write(b"Bot is active and running!")

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
        "🔍 OSINT Search Bot mein aapka swagat hai!\n\n"
        "Mujhe koi bhi target ya phone number bhejein.\n"
        "Main API se data check karke aapko result bataunga.\n\n"
        "⚡ Commands:\n"
        "/start - Bot shuru karne ke liye"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_osint_search(message):
    query = message.text.strip()
    
    # Check agar user ne galti se galat command likhi hai
    if query.startswith('/'):
        if query not in ['/start', '/help']:
            bot.reply_to(message, "❌ Galat command! Kripya sahi command chunein ya seedhe number bhejein.")
            return

    bot.send_chat_action(message.chat.id, 'typing')
    status_msg = bot.reply_to(message, "⏳ API se data fetch kiya ja raha hai...")

    try:
        payload = {'key': API_KEY, 'query': query}
        response = requests.get(API_BASE_URL, params=payload, timeout=15)
        
        if response.status_code == 200:
            try:
                # Response ko text format mein handle karna safe rakhne ke liye
                raw_text = response.text
                
                # Agar output bohot bada hai ya complex hai, toh seedhe file mein bhejna
                if len(raw_text) > 2500:
                    filename = f"result_{query}.txt"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(raw_text)
                    
                    with open(filename, "rb") as doc:
                        bot.send_document(
                            message.chat.id, 
                            doc, 
                            caption=f"📋 Search Results for {query}\n(Data bada hone ke karan file mein bheja gaya hai.)"
                        )
                    
                    # File send karne ke baad use server se delete karna
                    if os.path.exists(filename):
                        os.remove(filename)
                else:
                    # Chota response seedhe plain text mein send karna bina kisi markdown ke
                    response_text = f"✅ Search Results for: {query}\n\n{raw_text}"
                    bot.send_message(message.chat.id, response_text)
                    
            except Exception as file_err:
                bot.send_message(message.chat.id, f"❌ Data processing mein error aaya: {str(file_err)}")
        else:
            bot.send_message(message.chat.id, f"❌ API Error: Server ne response code {response.status_code} diya.")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Connection Error: {str(e)}")
    finally:
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except:
            pass

if __name__ == '__main__':
    print("🚀 Bot running...")
    bot.infinity_polling()
