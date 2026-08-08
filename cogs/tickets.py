import disnake
from disnake.ext import commands
import asyncio

# Розумна перевірка для Керівництва (Мають доступ до всього)
def has_management_access(inter):
    allowed_users = ["sakura0", "dragwayder"]
    if inter.author.name.lower() in allowed_users:
        return True
        
    if isinstance(inter.author, disnake.Member):
        owner = disnake.utils.find(lambda r: "Owner DragPolit" in r.name, inter.guild.roles)
        admin = disnake.utils.find(lambda r: "Administrator" in r.name, inter.guild.roles)
        if (owner and owner in inter.author.roles) or (admin and admin in inter.author.roles):
            return True
    return False

# Розумна перевірка для Підтримки
def is_support(inter):
    # Керівництво автоматично є підтримкою
    if has_management_access(inter): 
        return True
        
    if isinstance(inter.author, disnake.Member):
        support = disnake.utils.find(lambda r: "Support Team" in r.name, inter.guild.roles)
        if support and support in inter.author.roles:
            return True
    return False


class TicketControls(disnake.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id # ID того, хто створив тікет

    # Кнопка: Закрити тікет
    @disnake.ui.button(label="🔒 Закрыть | Close", style=disnake.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        # Закрити може або сапорт/адмін, або сам творець тікета
        if not is_support(inter) and inter.author.id != self.author_id:
            return await inter.response.send_message("❌ У вас нет прав для закрытия этого тикета. / You don't have permission.", ephemeral=True)

        await inter.response.send_message("🇷🇺 Закрытие тикета... Канал будет удален через 5 секунд.\n🇬🇧 Closing ticket... Channel will be deleted in 5 seconds.")

        # Логування видалення
        audit_channel = disnake.utils.find(lambda c: "audit-logs" in c.name, inter.guild.channels)
        if audit_channel:
            log_embed = disnake.Embed(
                title="🔒 Тикет закрыт | Ticket Closed",
                description=f"**Канал / Channel:** {inter.channel.name}\n**Закрыл / Closed by:** {inter.author.mention}",
                color=disnake.Color.red(),
                timestamp=disnake.utils.utcnow()
            )
            await audit_channel.send(embed=log_embed)

        await asyncio.sleep(5)
        try:
            await inter.channel.delete()
        except:
            pass

    # Кнопка: Взяти в роботу (Тільки для персоналу)
    @disnake.ui.button(label="🙋‍♂️ Взять в работу | Claim", style=disnake.ButtonStyle.success, custom_id="claim_ticket")
    async def claim_ticket(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not is_support(inter):
            return await inter.response.send_message("❌ Только администрация может взять тикет в работу. / Only staff can claim tickets.", ephemeral=True)

        # Змінюємо вигляд кнопки
        button.disabled = True
        button.label = f"В работе: {inter.author.display_name}"
        button.style = disnake.ButtonStyle.secondary
        await inter.response.edit_message(view=self)

        # Відправляємо повідомлення про те, хто взяв тікет
        embed = disnake.Embed(
            description=f"🇷🇺 {inter.author.mention} взял(а) ваш тикет в работу. Ожидайте ответа!\n🇬🇧 {inter.author.mention} claimed your ticket. Please wait for a response!",
            color=0x00ff00
        )
        await inter.channel.send(embed=embed)


class TicketOpenView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="📩 Открыть тикет | Open Ticket", style=disnake.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        guild = inter.guild
        
        # Розумний пошук ігноруючи смайлики
        category = disnake.utils.find(lambda c: "Support Tickets" in c.name, guild.categories)
        support_role = disnake.utils.find(lambda r: "Support Team" in r.name, guild.roles)
        
        if not category or not support_role:
            return await inter.response.send_message("❌ Ошибка: Не найдена категория 'Support Tickets' или роль 'Support Team'.", ephemeral=True)

        channel_name = f"ticket-{inter.author.name}"
        
        # Захист від спаму: перевірка чи є вже відкритий тікет
        existing_channel = disnake.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            return await inter.response.send_message(f"❌ У вас уже есть открытый тикет / You already have an open ticket: {existing_channel.mention}", ephemeral=True)

        # Налаштування прав доступу до нового каналу
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            inter.author: disnake.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            support_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        }
        
        # Додаємо Керівництво до каналу, щоб вони теж бачили всі тікети
        owner_role = disnake.utils.find(lambda r: "Owner DragPolit" in r.name, guild.roles)
        admin_role = disnake.utils.find(lambda r: "Administrator" in r.name, guild.roles)
        if owner_role: overwrites[owner_role] = disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        if admin_role: overwrites[admin_role] = disnake.PermissionOverwrite(read_messages=True, send_messages=True)

        # Відкладена відповідь, щоб бот встиг створити канал без помилки тайм-ауту
        await inter.response.defer(ephemeral=True)
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        
        await inter.followup.send(f"✅ Ваш тикет создан / Ticket created: {ticket_channel.mention}", ephemeral=True)
        
        # Двомовний Embed всередині тікета
        embed = disnake.Embed(
            title="🛠️ Техническая поддержка | Support Center",
            description=(
                f"🇷🇺 Приветствуем, {inter.author.mention}!\n"
                f"Пожалуйста, детально опишите вашу проблему. Администрация ответит вам в ближайшее время.\n\n"
                f"🇬🇧 Welcome, {inter.author.mention}!\n"
                f"Please describe your issue in detail. The administration will respond to you shortly."
            ),
            color=0x2b2d31
        )
        # Тегаємо користувача і роль підтримки, щоб їм прийшло сповіщення
        await ticket_channel.send(content=f"{inter.author.mention} | {support_role.mention}", embed=embed, view=TicketControls(inter.author.id))


class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="setup_tickets", description="Установить панель тикетов (Только Руководство)")
    async def setup_tickets(self, inter: disnake.ApplicationCommandInteraction):
        if not has_management_access(inter):
            return await inter.response.send_message("❌ Отказано в доступе. / Access Denied.", ephemeral=True)
        
        # Двомовна панель відкриття тікетів
        embed = disnake.Embed(
            title="📩 Центр Поддержки | Support Center",
            description=(
                "🇷🇺 **Нужна помощь?**\n"
                "Нажмите кнопку ниже, чтобы связаться с администрацией проекта DragPolit.\n\n"
                "🇬🇧 **Need help?**\n"
                "Click the button below to contact the DragPolit administration team."
            ),
            color=0x2b2d31
        )
        # Якщо на сервері є логотип, він гарно відобразиться збоку
        if inter.guild.icon:
            embed.set_thumbnail(url=inter.guild.icon.url)

        await inter.channel.send(embed=embed, view=TicketOpenView())
        await inter.response.send_message("✅ Панель тикетов успешно установлена.", ephemeral=True)

def setup(bot):
    bot.add_cog(TicketsCog(bot))
