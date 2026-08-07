import disnake
from disnake.ext import commands
import asyncio

# Функція для перевірки повного доступу
def has_full_access(inter):
    if inter.author.name.lower() == "sakura0":
        return True
        
    owner_role = disnake.utils.get(inter.guild.roles, name="Owner DragPolit")
    if owner_role and owner_role in inter.author.roles:
        return True
        
    return False

class TicketControls(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Закрыть тикет", style=disnake.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def close_ticket(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        support_role = disnake.utils.get(inter.guild.roles, name="Support Team")
        
        # Закрити може підтримка АБО той, у кого є повний доступ (sakura0 / Owner)
        is_support = support_role and support_role in inter.author.roles
        if not is_support and not has_full_access(inter):
            return await inter.response.send_message("Только поддержка или руководство может закрыть тикет.", ephemeral=True)
        
        await inter.response.send_message("Закрытие тикета... Канал будет удален через 5 секунд.")
        
        audit_channel = disnake.utils.get(inter.guild.channels, name="audit-logs")
        if audit_channel:
            log_embed = disnake.Embed(
                title="Тикет закрыт",
                description=f"**Канал:** {inter.channel.name}\n**Закрыл:** {inter.author.mention}",
                color=disnake.Color.red()
            )
            await audit_channel.send(embed=log_embed)

        await asyncio.sleep(5)
        await inter.channel.delete()

class TicketOpenView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Open Ticket", style=disnake.ButtonStyle.blurple, custom_id="open_ticket", emoji="📩")
    async def open_ticket(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        guild = inter.guild
        
        category = disnake.utils.get(guild.categories, name="Support Tickets")
        support_role = disnake.utils.get(guild.roles, name="Support Team")
        
        if not category or not support_role:
            return await inter.response.send_message("Ошибка: Не найдена категория 'Support Tickets' или роль 'Support Team'.", ephemeral=True)

        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            inter.author: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            support_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel_name = f"ticket-{inter.author.name}"
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        
        await inter.response.send_message(f"Ваш тикет создан: {ticket_channel.mention}", ephemeral=True)
        
        embed = disnake.Embed(
            title="Техническая поддержка",
            description=f"Приветствуем, {inter.author.mention}! Опишите вашу проблему, и администрация ответит вам в ближайшее время.",
            color=0x2b2d31
        )
        await ticket_channel.send(f"{support_role.mention}", embed=embed, view=TicketControls())

class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="setup_tickets", description="Установить панель тикетов (Только Руководство)")
    async def setup_tickets(self, inter: disnake.ApplicationCommandInteraction):
        if not has_full_access(inter):
            return await inter.response.send_message("Отказано в доступе.", ephemeral=True)
        
        embed = disnake.Embed(
            title="Вітаємо в #📩 • create-ticket!",
            description="**SUPPORT CENTER**\nClick the button below to open a private ticket with our Administration.",
            color=0x2b2d31
        )
        await inter.channel.send(embed=embed, view=TicketOpenView())
        await inter.response.send_message("Панель тикетов успешно установлена.", ephemeral=True)

def setup(bot):
    bot.add_cog(TicketsCog(bot))
