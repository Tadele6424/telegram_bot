import telebot
import requests
import feedparser
from telebot import types
from typing import Dict, Any

# ------------------ CONFIG ------------------
TELEGRAM_API_KEY = "8218128591:AAEAhSAHGBp9vBklKphnx15_ijdJEAFdyXM"
OPENROUTER_API_KEY = "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"
ADMIN_ID = 6970602498
PRIVACY_POLICY_URL = "https://telegra.ph/TadeleBot-Privacy-Policy-07-25"

bot = telebot.TeleBot(TELEGRAM_API_KEY)

# ------------------ USER MEMORY ------------------
user_registry = set()  # Track all private users
group_registry = set() # Track all groups the bot is in
user_memory = {}       # Store conversation history for context

# ------------------ OPENROUTER AI ------------------
def call_openrouter(messages: list) -> str:
    """
    messages: List of {"role": "user/assistant", "content": "..."} for conversation context
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15
        )
        if response.status_code == 200 and response.json().get("choices"):
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenRouter API Error: {e}")
    return "⚠️ AI is unavailable. Please try again later."

def is_amharic(text: str) -> bool:
    return any('\u1200' <= c <= '\u137F' for c in text)

# ------------------ COMMANDS ------------------
@bot.message_handler(commands=['start'])
def start_command(message):
    # Track user
    user_registry.add(message.chat.id)
    # Notify admin
    bot.send_message(ADMIN_ID, f"📥 New user started the bot: @{message.from_user.username} ({message.from_user.id})")

    # Buttons
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("💬 AI Chat", callback_data="chat"),
        types.InlineKeyboardButton("🆘 Help", callback_data="help"),
        types.InlineKeyboardButton("📢 Feedback", callback_data="feedback"),
        types.InlineKeyboardButton("💡 Motivate Me", callback_data="motivate"),
        types.InlineKeyboardButton("😂 Tell Me a Joke", callback_data="joke"),
        types.InlineKeyboardButton("📰 Tech News", callback_data="news"),
        types.InlineKeyboardButton("🔒 Privacy Policy", callback_data="privacy")
    ]
    markup.add(*buttons)

    welcome_msg = f"""
🌟 Welcome to SmartBot! 🌟

I can:
- Chat in English/Amharic
- Give motivational quotes
- Tell jokes
- Share tech news

🔒 Privacy Policy: {PRIVACY_POLICY_URL}
"""
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_msg = f"""
🆘 Help Guide:

/start - Main Menu
/help - This help
/motivate - AI Motivation
/joke - AI Joke
/news - Tech News
/feedback - Send Feedback
/about - Info about bot
/privacy - Privacy Policy
"""
    bot.reply_to(message, help_msg)

@bot.message_handler(commands=['about'])
def about_command(message):
    about_msg = f"""
🤖 SmartBot
Developer: Tadele Endale
Features: AI Chat, Motivation, Jokes, Tech News
Updated: 2025
Privacy: {PRIVACY_POLICY_URL}
"""
    bot.send_message(message.chat.id, about_msg)

@bot.message_handler(commands=['privacy'])
def privacy_command(message):
    msg = f"🔒 Privacy Policy: {PRIVACY_POLICY_URL}"
    bot.send_message(message.chat.id, msg)

# ------------------ AI FEATURES ------------------
def handle_ai_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')

    # Maintain conversation context
    if message.chat.id not in user_memory:
        user_memory[message.chat.id] = []
    language = "Amharic" if is_amharic(message.text) else "English"
    user_memory[message.chat.id].append({"role": "user", "content": message.text})
    # Get AI response
    reply = call_openrouter(user_memory[message.chat.id])
    # Save AI response
    user_memory[message.chat.id].append({"role": "assistant", "content": reply})
    bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=['motivate'])
def send_motivation(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if message.chat.id not in user_memory:
        user_memory[message.chat.id] = []
    user_memory[message.chat.id].append({"role": "user", "content": "Give me a short motivational quote"})
    reply = call_openrouter(user_memory[message.chat.id])
    user_memory[message.chat.id].append({"role": "assistant", "content": reply})
    bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=['joke'])
def send_joke(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if message.chat.id not in user_memory:
        user_memory[message.chat.id] = []
    user_memory[message.chat.id].append({"role": "user", "content": "Tell me a short funny clean joke"})
    reply = call_openrouter(user_memory[message.chat.id])
    user_memory[message.chat.id].append({"role": "assistant", "content": reply})
    bot.send_message(message.chat.id, reply)

# ------------------ FEEDBACK ------------------
@bot.message_handler(commands=['feedback'])
def feedback_command(message):
    msg = bot.send_message(message.chat.id, "📢 Send your feedback:")
    bot.register_next_step_handler(msg, process_feedback)

def process_feedback(message):
    feedback_msg = f"📢 Feedback from @{message.from_user.username}:\n{message.text}"
    bot.send_message(ADMIN_ID, feedback_msg)
    bot.reply_to(message, "✅ Feedback sent. Thank you!")

# ------------------ TECH NEWS ------------------
@bot.message_handler(commands=['news'])
def news_command(message):
    feed = feedparser.parse("https://www.theverge.com/rss/index.xml")
    if not feed.entries:
        bot.reply_to(message, "⚠️ Could not fetch news.")
        return
    news_items = [f"• {e.title}\n🔗 {e.link}" for e in feed.entries[:3]]
    bot.send_message(message.chat.id, "📰 Latest Tech News:\n\n" + "\n\n".join(news_items))

# ------------------ BUTTON CALLBACKS ------------------
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    if call.data == "chat":
        msg = bot.send_message(call.message.chat.id, "💬 What do you want to chat about?")
        bot.register_next_step_handler(msg, handle_ai_chat)
    elif call.data == "help":
        help_command(call.message)
    elif call.data == "feedback":
        feedback_command(call.message)
    elif call.data == "motivate":
        send_motivation(call.message)
    elif call.data == "joke":
        send_joke(call.message)
    elif call.data == "news":
        news_command(call.message)
    elif call.data == "privacy":
        privacy_command(call.message)

# ------------------ FORWARD ALL + AI CHAT ------------------
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Track new group chat
    if message.new_chat_members:
        group_registry.add(message.chat.id)
        for new_user in message.new_chat_members:
            bot.send_message(ADMIN_ID, f"📥 New user added to group '{message.chat.title}': @{new_user.username} ({new_user.id})")

    # Forward all messages to admin
    if not message.text.startswith('/'):
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        handle_ai_chat(message)

# ------------------ ADMIN BROADCAST ------------------
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID)
def admin_broadcast(message):
    # Send to all private users
    for user_id in user_registry:
        try:
            bot.send_message(user_id, f"📢 ADMIN MESSAGE:\n{message.text}")
        except:
            continue
    # Send to all groups
    for group_id in group_registry:
        try:
            bot.send_message(group_id, f"📢 ADMIN MESSAGE:\n{message.text}")
        except:
            continue

# ------------------ RUN BOT ------------------
if __name__ == '__main__':
    print("🤖 SmartBot is running...")
    bot.infinity_polling()