import asyncio
from datetime import datetime, timedelta, time
from pytz import timezone
from config import Config
from database.database import get_db
from database.models import Group

def parse_time(time_str: str) -> time:
    """Converte string 'HH:MM' para objeto time"""
    hours, minutes = map(int, time_str.split(':'))
    return time(hour=hours, minute=minutes)

async def schedule_message(client, message, time_str: str):
    """Agenda uma mensagem para um horário específico"""
    target_time = parse_time(time_str)
    tz = timezone(Config.TIME_ZONE)
    
    while True:
        now = datetime.now(tz)
        target_datetime = datetime.combine(now.date(), target_time).astimezone(tz)
        
        if now > target_datetime:
            target_datetime = datetime.combine(
                now.date() + timedelta(days=1),
                target_time
            ).astimezone(tz)
        
        wait_seconds = (target_datetime - now).total_seconds()
        print(f"Esperando {wait_seconds} segundos para enviar a mensagem às {target_time}")
        await asyncio.sleep(wait_seconds)
        
        # Encaminha ou copia a mensagem para todos os grupos ativos
        db = next(get_db())
        groups = db.query(Group).filter(Group.is_active == True).all()
        
        # Determina o message_id e chat_id corretos
        if message.forward_from_message_id:
            source_chat_id = message.forward_from.id
            message_id = message.forward_from_message_id
        elif message.reply_to_message:
            source_chat_id = message.reply_to_message.chat.id
            message_id = message.reply_to_message.id
        else:
            source_chat_id = message.chat.id
            message_id = message.id
        
        for group in groups:
            try:
                await client.forward_messages(
                    chat_id=int(group.group_id),
                    from_chat_id=source_chat_id,
                    message_ids=message_id
                )
                print(f"Mensagem encaminhada para: {group.title}")
            except Exception as e:
                print(f"Erro ao encaminhar para {group.title}: {e}")
                try:
                    await client.copy_message(
                        chat_id=int(group.group_id),
                        from_chat_id=source_chat_id,
                        message_id=message_id
                    )
                    print(f"Mensagem copiada para: {group.title}")
                except Exception as copy_e:
                    print(f"Erro ao copiar para {group.title}: {copy_e}")