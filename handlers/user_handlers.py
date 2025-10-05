from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database.database import get_db
from database.models import User

async def unauthorized_start(client: Client, message: Message):
    await message.reply("""
    ⚠️ Você não está autorizado a usar este bot.
    Entre em contato com um administrador para obter acesso.
    """)

async def authorized_start(client: Client, message: Message):
    db = next(get_db())
    user = db.query(User).filter(User.user_id == str(message.from_user.id)).first()
    
    if user and user.is_authorized:
        await message.reply("""
        👋 Bem-vindo ao Bot de Divulgação!
        
        **Comandos disponíveis:**
        /start - Mostra esta mensagem
        /help - Mostra os comandos disponíveis
        
        Entre em contato com um administrador para mais funcionalidades.
        """)
    else:
        await unauthorized_start(client, message)

user_handler = filters.command(["start", "help"]) & ~filters.user(Config.ADMINS)