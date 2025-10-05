from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database.database import get_db
from database.models import Group

@Client.on_message(filters.command("divulgar") & filters.user(Config.ADMINS))
async def forward_to_groups(client: Client, message: Message):
    db = next(get_db())
    groups = db.query(Group).filter(Group.is_active == True).all()
    
    for group in groups:
        try:
            await client.forward_messages(
                chat_id=int(group.group_id),
                from_chat_id=message.chat.id,
                message_ids=message.id
            )
        except Exception as e:
            print(f"Erro ao encaminhar para o grupo {group.title}: {e}")