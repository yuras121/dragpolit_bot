import disnake
from disnake.ext import commands
import asyncio

class TicketControls(disnake.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id # Запам'ятовуємо, хто створив тікет

    # Кнопка: Закрити тікет
    @disnake.ui.button(label="🔒 Закрыть | Close", style=disnake.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        # Перевірка: чи має людина права модератора (галочка "Керування повідомленнями")
        is_staff = inter.channel.permissions_for(inter.author).manage_messages or inter.channel.permissions_for(inter.author).manage_channels
        
        # Закрити може або модератор, або сам гравець
        if inter.author.id != self.author_id and not is_staff:
            return await inter.response.send_message("❌ У вас нет прав для закрытия этого тикета. / You don't have permission.", ephemeral=True)

        await inter.response.send_message("🇷🇺 Закрытие тикета... Канал будет удален через 5 секунд.\n🇬🇧 Closing ticket... Channel will be deleted in 5 seconds.")

        # Відправляємо лог у канал audit-logs (якщо він є)
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

    # Кнопка: Взяти в роботу
    @disnake.ui.button(label="🙋‍♂️ Взять в работу | Claim", style=disnake.ButtonStyle.success, custom_id="claim_ticket")
    async def claim_ticket(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        # Беремо в роботу тільки якщо є права модератора (налаштовані тобою галочки)
        is_staff = inter.channel.permissions_for(inter.author).manage_messages or inter.channel.permissions_for(inter.author).manage_channels
        
        if not is_staff:
            return await inter.response.send_message("❌ Только администрация может взять тикет в работу. / Only staff can claim tickets.", ephemeral=True)

        # Блокуємо кнопку і показуємо, хто взяв тікет
        button.disabled = True
        button.label = f"В работе: {inter.author.display_name}"
        button.style = disnake.ButtonStyle.secondary
        await inter.response.edit_message(view=self)

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
        
        # Шукаємо категорію. Права доступу братимуться саме з неї!
        category = disnake.utils.find(lambda c: "Support Tickets" in c.name, guild.categories)
        if not category:
            return await inter.response.send_message("❌ Ошибка: Создайте категорию с названием 'Support Tickets'.", ephemeral=True)

        channel_name = f"ticket-{inter.author.name}"
        
        # Захист від створення купи тікетів одним гравцем
        if disnake.utils.get(guild.text_channels, name=channel_name):
            return await inter.response.send_message(f"❌ У вас уже есть открытый тикет / You already have an open ticket.", ephemeral=True)

        await inter.response.defer(ephemeral=True)

        # СТВОРЕННЯ КАНАЛУ (Бот автоматично копіює всі твої галочки з категорії і просто додає туди гравця)
        ticket_channel = await category.create_text_channel(
            name=channel_name,
            overwrites={
                inter.author: disnake.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
            }
        )
        
        await inter.followup.send(f"✅ Ваш тикет создан / Ticket created: {ticket_channel.mention}", ephemeral=True)
        
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
        await ticket_channel.send(content=f"{inter.author.mention}", embed=embed, view=TicketControls(inter.author.id))


class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Встановити панель може тільки людина з правами Адміністратора сервера (вбудована галочка Discord)
    @commands.slash_command(name="setup_tickets", description="Установить панель тикетов", default_member_permissions=disnake.Permissions(administrator=True))
    async def setup_tickets(self, inter: disnake.ApplicationCommandInteraction):
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
        
        if inter.guild.icon:
            embed.set_thumbnail(url=inter.guild.icon.url)

        await inter.channel.send(embed=embed, view=TicketOpenView())
        await inter.response.send_message("✅ Панель тикетов успешно установлена.", ephemeral=True)

def setup(bot):
    bot.add_cog(TicketsCog(bot))
