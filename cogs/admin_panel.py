import disnake
from disnake.ext import commands

# Функція для перевірки повного доступу (пускає sakura0 або Owner DragPolit)
def has_full_access(inter):
    if inter.author.name.lower() == "sakura0":
        return True
    
    owner_role = disnake.utils.get(inter.guild.roles, name="Owner DragPolit")
    if owner_role and owner_role in inter.author.roles:
        return True
        
    return False

class EmbedModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Заголовок", custom_id="embed_title", style=disnake.TextInputStyle.short, max_length=256
            ),
            disnake.ui.TextInput(
                label="Основной текст", custom_id="embed_description", style=disnake.TextInputStyle.paragraph
            ),
            disnake.ui.TextInput(
                label="Цвет (HEX, например 00ff00)", custom_id="embed_color", style=disnake.TextInputStyle.short, required=False
            )
        ]
        super().__init__(title="Конструктор сообщений", custom_id="embed_builder", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        title = inter.text_values["embed_title"]
        desc = inter.text_values["embed_description"]
        color_input = inter.text_values["embed_color"]

        color = disnake.Color.blurple()
        if color_input:
            try:
                color = int(color_input.replace("#", ""), 16)
            except ValueError:
                pass 

        embed = disnake.Embed(title=title, description=desc, color=color)
        await inter.channel.send(embed=embed)
        await inter.response.send_message("Сообщение успешно отправлено!", ephemeral=True)

class AdminPanelView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Создать Embed", style=disnake.ButtonStyle.primary, custom_id="btn_create_embed", emoji="📝")
    async def create_embed(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not has_full_access(inter):
            return await inter.response.send_message("У вас нет прав для этого действия!", ephemeral=True)
        await inter.response.send_modal(modal=EmbedModal())

class AdminPanelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="panel", description="Открыть панель управления (Только Руководство)")
    async def admin_panel(self, inter: disnake.ApplicationCommandInteraction):
        if not has_full_access(inter):
            return await inter.response.send_message("Отказано в доступе.", ephemeral=True)
        
        embed = disnake.Embed(
            title="⚙️ Панель управления Dragpolit",
            description="Выберите нужное действие ниже. Все действия логируются.",
            color=0x2b2d31
        )
        await inter.response.send_message(embed=embed, view=AdminPanelView(), ephemeral=True)

def setup(bot):
    bot.add_cog(AdminPanelCog(bot))
