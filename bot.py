import os
import telebot
import requests
import json

# Environment variables se tokens lena (GitHub par leak hone se bachane ke liye)
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
        "Mujhe koi bhi target ya phone number bhejein.\n"
        "Main API se data check karke aapko result bataunga.\n\n"
        "⚡ _Commands:_ \n"
        "/start - Bot shuru karne ke liye"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_osint_search(message):
    query = message.text.strip()
    bot.send_chat_action(message.chat.id, 'typing')
    status_msg = bot.reply_to(message, "⏳ API se data fetch kiya ja raha hai...")

    try:
        payload = {'key': API_KEY, 'query': query}
        response = requests.get(API_BASE_URL, params=payload, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                formatted_json = json.dumps(data, indent=4, ensure_ascii=False)
                
                if len(formatted_json) > 4000:
                    with open("result.txt", "w", encoding="utf-8") as f:
                        f.write(formatted_json)
                    with open("result.txt", "rb") as doc:
                        bot.send_document(message.chat.id, doc, caption="📋 Result bada hone ke karan file mein bheja gaya hai.")
                else:
                    response_text = f"✅ **Results for:** `{query}`\n\n```json\n{formatted_json}\n```"
                    bot.send_message(message.chat.id, response_text, parse_mode='Markdown')
            except json.JSONDecodeError:
                bot.send_message(message.chat.id, f"✅ **Results for:** `{query}`\n\n{response.text}")
        else:
            bot.send_message(message.chat.id, f"❌ API Error: {response.status_code}")
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
