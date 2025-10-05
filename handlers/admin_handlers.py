import asyncio
from pytz import timezone
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database.database import get_db
from database.models import Group, User, Message as MsgModel
from utils.scheduler import schedule_message
from utils.helpers import parse_time_input
from pyrogram.enums import ChatType

# Filtro para verificar se o usuário é admin
admin_filter = filters.user(Config.ADMINS)

@Client.on_message(filters.command("add_grupo") & admin_filter)
async def add_group(client: Client, message: Message):
    db = next(get_db())

    print(f"Tipo do chat: {message.chat.type}")

    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
        print("Chat é grupo, supergrupo ou canal")
        group_id = str(message.chat.id)  # Faltava definir!
        group_title = message.chat.title or "Sem título"
        print(f"Título do grupo/canal: {group_title}")
        print(f"ID do grupo/canal: {group_id}")

    elif message.chat.type == ChatType.PRIVATE:
        print("Chat é privado")
        try:
            group_id = message.text.split()[1]
            print(f"ID do grupo/canal recebido: {group_id}")
        except IndexError:
            await message.reply("Por favor, informe o ID do grupo ou canal. Exemplo:\n/add_grupo -1001234567890")
            return

        try:
            print(f"Tentando obter informações do chat com id: {group_id}")
            chat = await client.get_chat(group_id)
            group_title = chat.title or "Sem título"
            print(f"Título obtido do grupo/canal: {group_title}")
        except Exception as e:
            print(f"Erro ao obter informações do grupo/canal: {e}")
            await message.reply(f"Erro ao obter informações do grupo/canal: {e}")
            return

    else:
        print("Comando usado em chat inválido (não grupo/canal ou PV com ID)")
        await message.reply("Este comando só pode ser usado em grupos, canais ou PV com ID.")
        return

    # Verifica se o grupo já existe no banco de dados
    existing_group = db.query(Group).filter(Group.group_id == group_id).first()

    if existing_group:
        await message.reply(f"ℹ️ O grupo/canal '{group_title}' já está cadastrado.")
    else:
        new_group = Group(group_id=group_id, title=group_title)
        db.add(new_group)
        db.commit()
        await message.reply(
            f"✅ Grupo/canal adicionado com sucesso!\n\n📛 Nome: {group_title}\n🆔 ID: {group_id}"
        )
     
@Client.on_message(filters.command("add_divulgacao") & admin_filter)
async def add_message(client: Client, message: Message):
    db = next(get_db())

    target_message = message.reply_to_message
    if not target_message:
        await message.reply("Responda à mensagem que deseja divulgar.")
        return

    try:
        args = message.text.split(" ", 2)
        if len(args) < 3:
            await message.reply("Uso: /add_divulgacao <horários> <dias>. Ex: /add_divulgacao 12:00,18:00 3")
            return

        times_input = args[1]
        days_input = int(args[2])
        times = parse_time_input(times_input)

        if not times:
            await message.reply("Formato de horários inválido. Use: HH:MM,HH:MM")
            return

        new_message = MsgModel(
            message_id=str(target_message.id),
            chat_id=str(target_message.chat.id),
            schedule_times=times_input,
            is_active=True
        )
        db.add(new_message)
        db.commit()

        for day_offset in range(days_input):
            for time_str in times:
                asyncio.create_task(
                    schedule_message(client, target_message, time_str, message.from_user.id, day_offset)
                )

        await message.reply(f"✅ Mensagem agendada para {len(times)} horário(s), por {days_input} dia(s).")

    except Exception as e:
        await message.reply(f"Erro ao agendar mensagem: {e}")


async def schedule_message(client: Client, message: Message, time_str: str, user_id: int, delay_days: int):
    tz = timezone(Config.TIME_ZONE)
    try:
        target_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        print(f"Horário inválido: {time_str}")
        return

    now = datetime.now(tz)
    target_date = now.date() + timedelta(days=delay_days)
    target_datetime = datetime.combine(target_date, target_time)
    target_datetime = tz.localize(target_datetime)

    wait_seconds = (target_datetime - now).total_seconds()
    if wait_seconds < 0:
        print(f"Horário {time_str} de {delay_days} dias já passou. Ignorando.")
        return

    print(f"Aguardando {wait_seconds:.0f}s para enviar {message.id} às {time_str} (em {delay_days} dia[s])")
    await asyncio.sleep(wait_seconds)

    db = next(get_db())
    groups = db.query(Group).filter(Group.is_active == True).all()

    success_count = 0
    for group in groups:
        try:
            await client.forward_messages(
                chat_id=int(group.group_id),
                from_chat_id=message.chat.id,
                message_ids=message.id
            )
            success_count += 1
        except Exception as e:
            print(f"Erro ao enviar para {group.group_id}: {e}")

    try:
        await client.send_message(
            chat_id=user_id,
            text=f"✅ Mensagem enviada para {success_count} grupo(s) às {time_str} (dia +{delay_days})"
        )
    except Exception as e:
        print(f"Erro ao notificar admin: {e}")

@Client.on_message(filters.command("enviar_agora") & admin_filter)
async def enviar_agora(client: Client, message: Message):
    db = next(get_db())

    target_message = message.reply_to_message
    if not target_message:
        await message.reply("Você precisa responder a uma mensagem cadastrada para enviar.")
        return

    # Busca a mensagem no banco
    msg = db.query(MsgModel).filter(
        MsgModel.message_id == str(target_message.id),
        MsgModel.chat_id == str(target_message.chat.id)
    ).first()

    if not msg:
        await message.reply("Mensagem não encontrada no banco de dados.")
        return

    # Pega todos os grupos cadastrados
    groups = db.query(Group).all()

    success = 0
    failed = 0

    for group in groups:
        try:
            await client.forward_messages(
                chat_id=int(group.group_id),
                from_chat_id=int(msg.chat_id),
                message_ids=int(msg.message_id)
            )
            success += 1
        except Exception as e:
            print(f"Erro ao enviar para {group.group_id}: {e}")
            failed += 1

    await message.reply(
        f"✅ Envio concluído!\n\n"
        f"Total de grupos: {len(groups)}\n"
        f"Enviados com sucesso: {success}\n"
        f"Falharam: {failed}"
    )       
      
@Client.on_message(filters.command("add_user") & admin_filter)
async def add_user(client: Client, message: Message):
    db = next(get_db())

    try:
        user_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply("Uso: /add_user <ID do usuário>")
        return

    user = await client.get_users(user_id)

    existing_user = db.query(User).filter(User.user_id == str(user.id)).first()

    if existing_user:
        existing_user.is_authorized = True
        db.commit()
        await message.reply(f"Usuário {user.first_name} já estava cadastrado e foi autorizado.")
    else:
        new_user = User(
            user_id=str(user.id),
            username=user.username or "",
            is_authorized=True
        )
        db.add(new_user)
        db.commit()
        await message.reply(f"Usuário {user.first_name} adicionado e autorizado com sucesso!")

@Client.on_message(filters.command("remove_grupo") & admin_filter)
async def remove_group(client: Client, message: Message):
    db = next(get_db())

    try:
        group_id = message.text.split()[1]
    except IndexError:
        await message.reply("Uso: /remove_grupo <ID do grupo ou canal>")
        return

    group = db.query(Group).filter(Group.group_id == group_id).first()

    if group:
        db.delete(group)
        db.commit()
        await message.reply(f"{group.title} removido com sucesso!")
    else:
        await message.reply("Grupo ou canal não encontrado.")

@Client.on_message(filters.command("remove_user") & admin_filter)
async def remove_user(client: Client, message: Message):
    db = next(get_db())

    try:
        user_id = message.text.split()[1]
    except IndexError:
        await message.reply("Uso: /remove_user <ID do usuário>")
        return

    user = db.query(User).filter(User.user_id == user_id).first()

    if user:
        db.delete(user)
        db.commit()
        await message.reply(f"Usuário {user.username or user.user_id} removido com sucesso!")
    else:
        await message.reply("Usuário não encontrado.")
        
@Client.on_message(filters.command("testa") & admin_filter)
async def testa_envio(client: Client, message: Message):
    db = next(get_db())

    target_message = message.reply_to_message
    if not target_message:
        await message.reply("Responda à mensagem que deseja testar o envio.")
        return

    groups = db.query(Group).filter(Group.is_active == True).all()

    success = []
    failed = []

    for group in groups:
        try:
            await client.forward_messages(
                chat_id=int(group.group_id),
                from_chat_id=target_message.chat.id,
                message_ids=target_message.id
            )
            success.append(group.title)
        except Exception as e:
            print(f"Erro ao enviar para {group.group_id}: {e}")
            failed.append(group.title or group.group_id)

    response = "✅ **Teste de envio concluído!**\n\n"
    response += f"**Sucesso ({len(success)}):**\n" + "\n".join(f"• {title}" for title in success) + "\n\n"
    response += f"**Falha ({len(failed)}):**\n" + ("\n".join(f"• {title}" for title in failed) if failed else "• Nenhum")

    await message.reply(response)        

@Client.on_message(filters.command("admin") & admin_filter)
async def admin_commands(client: Client, message: Message):
    commands = """
**Comandos Administrativos:**
/add_grupo - Adiciona um grupo ou canal para divulgação
    • No grupo ou canal: apenas envie o comando
    • No PV: /add_grupo <ID> <Título>
/add_divulgacao <horários> - Adiciona uma mensagem para divulgação (responder ou encaminhar)
/add_user <ID> - Adiciona um usuário autorizado
/remove_grupo <ID> - Remove um grupo ou canal
/remove_user <ID> - Remove um usuário

**Formato de horários:**
HH:MM, HH:MM, HH:MM (ex: 18:10, 19:00, 20:30)
"""
    await message.reply(commands)