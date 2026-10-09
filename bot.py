import os
import logging
from google import genai
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# Logging ማዘጋጀት
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# የአካባቢ ተለዋዋጮች (Environment Variables ከ Render ይወሰዳሉ)
BOT_TOKEN = os.environ.get("8640220728:AAH0-c-8mCclYsqinupY8ZpsZ8JxjdYXtHk")
GEMINI_API_KEY = os.environ.get("AQ.Ab8RN6JjYT9AN-b4KBhVHcHCy27oyG_iSpOwRpB6aOFbFztXvg")
ADMIN_CHAT_ID = os.environ.get("8613322776")  # ያንተ የቴሌግራም User ID

# Gemini Client ማዘጋጀት
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# የውይይት ደረጃዎች (States)
NAME, PHONE, ADDRESS, STATUS = range(4)

# የመጽሐፉ ሙሉ የእውቀት ማዕከል (Knowledge Base System Prompt)
SYSTEM_PROMPT = """
አንተ 'Ethio Remote job' የተባልክ የቴሌግራም ቦት ረዳት ነህ።
ስራህ ስለ ቀጥተኛ ሽያጭ (Direct Selling / Network Marketing) እና ስለ 'አልፋ' (ALFA) አለም አቀፍ ድርጅት የተዘጋጀውን መጽሐፍ መሰረት በማድረግ የተጠቃሚዎችን ጥያቄ በሙሉ በትህትና፣ በሙያዊ ብቃት እና በአማርኛ መመለስ ነው።

የመጽሐፉ ዋና ዋና ነጥቦች፦
1. ድርጅቱ፦ አልፋ (ALFA) ዋና ቢሮው አሜሪካ ሲሆን የመጀመሪያ ቅርንጫፉ በኢትዮጵያ ተከፍቷል። ወደ ሱዳን፣ ኬንያ፣ ሶማሊያ፣ እስራኤል፣ አንጎላ እና ኡጋንዳ ለመስፋፋት አቅዷል።
2. የግብይት ልዩነት፦ ባህላዊ ግብይት (አምራች -> ጅምላ -> ችርቻሮ -> ተጠቃሚ) በብዙ ደላሎችና ማስታወቂያ ወጪ ሲኖረው፤ ቀጥተኛ ሽያጭ ምርት ከአምራች በቀጥታ ወደ ተጠቃሚ ይደርሳል፣ ተጠቃሚዎች በቃላት ማስታወቂያ ኮሚሽን ያገኛሉ።
3. የአባልነት ፓኬጆች፦
   - የሎው (Yellow)፦ $110 (11% ዙር ኮሚሽን፣ ሳምንታዊ ጣሪያ $1,000)
   - ኦሬንጅ (Orange)፦ $210 (12% ዙር ኮሚሽን፣ ሳምንታዊ ጣሪያ $2,000)
   - ግሪን (Green)፦ $410 (14% ዙር ኮሚሽን፣ ሳምንታዊ ጣሪያ $4,000)
   - ጎልደን (Golden)፦ $810 (15% ዙር ኮሚሽን፣ ሳምንታዊ ጣሪያ $5,000)
4. የዙር (Cycle) አሰራር፦ በግራ 600 ነጥብ፣ በቀኝ 600 ነጥብ ሲመጣጠን 1 ዙር ይሆናል። ቀጥተኛ የማስታወቂያ ጉርሻ 16% - 19% ይሰጣል።
5. የደረጃ እድገቶች፦ CT -> MT -> TT -> NTB ($5,000 ቢሮ ድጎማ/ጉዞ) -> IBB ($10,000 ቢሮ + $15,000 መኪና) -> GEB ($20,000 ቢሮ + $25,000 መኪና) -> CA ($50,000 ቢሮ + $100,000 ዶላር) -> AL/Alpha Legend ($100,000 ቢሮ + $500,000 ዶላር ሽልማት)።
6. ምርቶች፦ የጤና መጠበቂያ፣ ኮስሞቲክስ፣ አዳዲስ ቴክኖሎጂዎች (የአየር ላይ ግሎብ)፣ የአእምሮ እና የአመራር ስልጠናዎች።
7. የመተግበሪያ አገልግሎት፦ ሲ.ኤፍ.ኤስ (CFS App) በPlay store የሚገኝ ሲሆን የደንበኞች አገልግሎትና የቅሬታ መፍቻ ነው።
8. ስልቶች፦ ማጨት (Prospecting)፣ 8ቱ የግብዣ ሂደቶች (ፍጥነት፣ ማድነቅ፣ መጋበዝ፣ "እንዲህ ባደርግልህ... ታደርጋለህ?"፣ የጊዜ ቁርጠኝነት ማግኘት፣ ስልክ መዝጋት)፣ እና ተቃውሞዎችን በአግባቡ ማስተናገድ።

ደንበኞች ስለስራው፣ ስለ ክፍያው፣ ስለ ፓኬጆች ወይም ስለ ድርጅቱ ህጋዊነት ሲጠይቁ ከዚህ መጽሐፍ መረጃ አንጻር አሳማኝ፣ አበረታች እና ግልጽ መልስ ስጥ።
"""

# /start ሲባል ምዝገባ መጀመር
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "እንኳን ወደ *Ethio Remote job* በሰላም መጡ! 🌟\n\n"
        "ለመጀመር እባክዎ ሙሉ ስምዎን (Full Name) ይጻፉልን፡",
        parse_mode="Markdown"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text
    await update.message.reply_text("በጣም ጥሩ! አሁን ደግሞ ስልክ ቁጥርዎን (Phone Number) ያስገቡ፡")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("አድራሻዎን (Address / የሚኖሩበትን ከተማ ወይም ክፍለ ከተማ) ይጻፉልን፡")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    
    reply_keyboard = [["ተማሪ", "ሰራተኛ"], ["ሌላ"]]
    await update.message.reply_text(
        "እርስዎ ተማሪ ነዎት ወይስ ሰራተኛ?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return STATUS

async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["status"] = update.message.text
    user = update.message.from_user
    
    # ለAdmin የሚላክ መረጃ ማዘጋጀት
    admin_notification = (
        "📥 *አዲስ ተመዝጋቢ ደርሷል!*\n\n"
        f"👤 *ስም:* {context.user_data.get('full_name')}\n"
        f"📞 *ስልክ:* {context.user_data.get('phone')}\n"
        f"📍 *አድራሻ:* {context.user_data.get('address')}\n"
        f"💼 *ሁኔታ:* {context.user_data.get('status')}\n"
        f"🔗 *Telegram:* @{user.username if user.username else 'የለውም'} (ID: {user.id})"
    )
    
    # ለAdmin መላክ
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_notification,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Error sending to admin: {e}")

    await update.message.reply_text(
        "✅ መረጃዎ በተሳካ ሁኔታ ተመዝግቧል! እናመሰግናለን።\n\n"
        "አሁን ስለ ስራው፣ ስለ ድርጅቱ፣ ስለ ፓኬጆች ወይም ስለ ገቢ አሰራሩ ማንኛውንም ጥያቄ መጠየቅ ይችላሉ። ምን ማወቅ ይፈልጋሉ?",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# መደበኛ ጥያቄዎችን በGemini AI መመለስ
async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[SYSTEM_PROMPT, f"የተጠቃሚ ጥያቄ፦ {user_query}"]
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await update.message.reply_text("ይቅርታ፣ ጥያቄዎን በማስተናገድ ላይ ችግር አጋጥሟል። እባክዎ እንደገና ይሞክሩ።")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # የተጠቃሚ መረጃ መቀበያ መዋቅር
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_status)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    # ከምዝገባ ውጪ የሚጠየቁ ጥያቄዎችን በAI መመለስ
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat))

    print("Ethio Remote job ቦት መስራት ጀምሯል...")
    app.run_polling()

if __name__ == "__main__":
    main()
