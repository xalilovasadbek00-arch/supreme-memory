import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    BufferedInputFile
)
from config import BOT_TOKEN, CHANNEL_ID, CHANNEL_URL
import database as db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Bosh menyu tugmalari
def main_menu():
    kb = [
        [KeyboardButton(text="👥 Do'stlarni taklif qilish (Bonus)")],
        [KeyboardButton(text="🧬 Murakkab Masalalar Yechimi (PDF)")],
        [KeyboardButton(text="🎓 Intensiv Kursga Yozilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Obunani tekshirish tugmasi (Inline)
def sub_check_keyboard():
    kb = [
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Obunani tekshiruvchi yordamchi funksiya
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return False

# /start buyrug'i
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    user_name = message.from_user.full_name
    db.add_user(message.from_user.id, user_name, referrer_id)
    
    if await is_subscribed(message.from_user.id):
        await message.answer(
            f"Salom, {user_name}!\n"
            f"Biologiya Milliy Sertifikat botiga xush kelibsiz! Bo'limni tanlang:",
            reply_markup=main_menu()
        )
    else:
        await message.answer(
            "Botdan foydalanish va materiallarni olish uchun avval rasmiy biologiya kanalimizga obuna bo'ling:",
            reply_markup=sub_check_keyboard()
        )

# Obunani tekshirish (Callback)
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer("Rahmat! Obuna tasdiqlandi. Bo'limni tanlang:", reply_markup=main_menu())
    else:
        await callback.answer("Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

# Referal bo'limi
@dp.message(F.text == "👥 Do'stlarni taklif qilish (Bonus)")
async def referal_handler(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        return await message.answer("Avval kanalga obuna bo'ling:", reply_markup=sub_check_keyboard())

    user_id = message.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    invites = db.get_invites(user_id)
    
    text = (
        f"<b>Sizning shaxsiy referal havolangiz:</b>\n<code>{ref_link}</code>\n\n"
        f"Siz taklif qilgan do'stlar soni: <b>{invites} ta</b>\n\n"
        f"<i>3 ta do'stingizni taklif qiling va Milliy sertifikatga tushadigan murakkab masalalar to'plamini bepul oling!</i>"
    )
    await message.answer(text, parse_mode="HTML")

# Masalalar bo'limi va Yangi Sifatli Masalalar Yuborish
@dp.message(F.text == "🧬 Murakkab Masalalar Yechimi (PDF)")
async def tasks_handler(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        return await message.answer("Avval kanalga obuna bo'ling:", reply_markup=sub_check_keyboard())

    user_id = message.from_user.id
    invites = db.get_invites(user_id)

    if invites >= 3:
        masalalar_text = (
            "🧬 <b>Biologiya Milliy Sertifikat — Murakkab Masalalar To'plami (MS-6)</b>\n\n"

            "<b>41-masala.</b>\n"
            "Nuqtalar o‘rniga mos keluvchi to‘g‘ri javob varianti berilgan javobni aniqlang.\n"
            "<i>Taqqoslanayotgan genotipik va fenotipik sinflar soni mos ravishda genotip shakllarining kombinatsiyasi bo‘yicha ... bo‘ladi.</i>\n\n"
            "A) AaBbCc x AaBbCc da 3/2 ga teng\n"
            "B) AaBbCc x AABBCC da 1/2 ga teng\n"
            "C) AaBb x aabb da 2 ga teng\n"
            "D) AaBb x AaBb da 4/3 ga teng\n\n"

            "<b>42-masala.</b>\n"
            "Otasining qon guruhi va rezuvi noma’lum bo‘lgan ayolning (qon guruhi fenotipi bo‘yicha dominant va retsessiv genlar soni teng, gomozigota va geterozigota genlar soni teng) onasining va erining qon guruhi gomozigota retsessiv. Ushbu oilada tug‘ilishi mumkin bo‘lgan bolalarning necha foizi rezus musbat gomozigota bo‘lishi mumkin?\n"
            "<i>(Genlar birikmagan, birikish guruhi hosil qilmaydi va krossingover kuzatilmaydi)</i>\n\n"
            "A) 0%\n"
            "B) 25%\n"
            "C) 50%\n"
            "D) 75%\n\n"

            "<b>43-masala.</b>\n"
            "DNK fragmentidagi timin va sitozin nukleotidlari orasidagi vodorod bog‘lar soni 1800 ga teng. Shu DNK molekulasining bitta zanjirida guanin nukleotidlari soni 250 ga va ikkinchi zanjirida sitozin nukleotidlari soni 350 ga teng. Ushbu DNK fragmentidagi timin nukleotidlari sonini toping.\n\n"
            "A) 200\n"
            "B) 300\n"
            "C) 400\n"
            "D) 500\n"
        )
        
        await message.answer("🎉 Tabriklaymiz! Siz 3 ta do'stingizni taklif qildingiz. Mana siz so'ragan haqiqiy Milliy Sertifikat masalalari:")
        await message.answer(masalalar_text, parse_mode="HTML")
        
        # Fayl ko'rinishida yuborish
        file_bytes = masalalar_text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "").encode("utf-8")
        doc_file = BufferedInputFile(file_bytes, filename="Milliy_Sertifikat_MS6_Masalalar.txt")
        await message.answer_document(doc_file, caption="📄 Masalalarning fayl ko'rinishi")
    else:
        await message.answer(
            f"🔒 Ushbu materialni yuklab olish uchun kamida <b>3 ta</b> do'stingizni taklif qilishingiz kerak.\n\n"
            f"Siz hozirgacha <b>{invites} ta</b> do'st taklif qildingiz. Yana <b>{3 - invites} ta</b> taklif qiling!",
            parse_mode="HTML"
        )

# Kursga yozilish
@dp.message(F.text == "🎓 Intensiv Kursga Yozilish")
async def course_handler(message: types.Message):
    await message.answer(
        "<b>Biologiya Milliy Sertifikat (A / A+) Intensiv Kursi</b>\n\n"
        "• Chuqurlashtirilgan nazariya va DTM/Sertifikat masalalari\n"
        "• Har haftalik timerli sinov testlari\n"
        "• Xatolar ustida shaxsiy tahlil\n\n"
        "Kursga yozilish uchun adminga murojaat qiling: @admin_username",
        parse_mode="HTML"
    )

async def main():
    db.init_db()
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())