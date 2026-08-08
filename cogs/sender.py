import disnake
from disnake.ext import commands

class EmbedModal(disnake.ui.Modal):
    def __init__(self, target_channel):
        self.target_channel = target_channel
        # Детальная настройка сообщения (Заголовок, Текст, Цвет)
        components = [
            disnake.ui.TextInput(
                label="Заголовок",
                placeholder="Например: 📢 Важное объявление",
                custom_id="title",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=256
            ),
            disnake.ui.TextInput(
                label="Основной текст",
                placeholder="Введите текст сообщения...",
                custom_id="desc",
                style=disnake.TextInputStyle.paragraph,
                max_length=4000
            ),
            disnake.ui.TextInput(
                label="Цвет (HEX-код, например 2b2d31)",
                placeholder="2b2d31",
                custom_id="color",
                style=disnake.TextInputStyle.short,
                required=False
            )
        ]
        super().__init__(title="Настройка сообщения", custom_id="secret_embed_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        title = inter.text_values["title"]
        desc = inter.text_values["desc"]
        color_input = inter.text_values["color"]

        # Цвет по умолчанию - современный темный
        color = 0x2b2d31 
        if color_input:
            try:
                color = int(color_input.replace("#", ""), 16)
            except ValueError:
                pass

        embed = disnake.Embed(title=title, description=desc, color=color)
        
        # Отправляем сообщение в выбранный канал
        await self.target_channel.send(embed=embed)
        await inter.response.send_message(f"✅ Сообщение успешно отправлено в {self.target_channel.mention}!", ephemeral=True)


class SenderView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.target_channel = None

    # Выпадающий список для выбора канала
    @disnake.ui.channel_select(
        placeholder="1. Выберите канал для отправки...", 
        custom_id="channel_select", 
        channel_types=[disnake.ChannelType.text, disnake.ChannelType.news]
    )
    async def select_channel(self, select: disnake.ui.ChannelSelect, inter: disnake.MessageInteraction):
        self.target_channel = select.values[0]
        await inter.response.send_message(f"Канал {self.target_channel.mention} выбран! Теперь нажми зеленую кнопку.", ephemeral=True)

    # Кнопка для открытия окна ввода текста
    @disnake.ui.button(label="2. Настроить и отправить", style=disnake.ButtonStyle.green, custom_id="btn_send", emoji="📝")
    async def create_btn(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not self.target_channel:
            return await inter.response.send_message("❌ Сначала выберите канал в меню выше!", ephemeral=True)
        
        # Открываем форму для ввода текста
        await inter.response.send_modal(modal=EmbedModal(self.target_channel))
        
        # Заметаем следы: удаляем панель управления после отправки
        await self.message.delete()


class SenderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Секретная команда на восклицательный знак
    @commands.command(name="смс")
    async def secret_send(self, ctx):
        # 1. Удаляем команду пользователя (!смс), чтобы никто не видел
        try:
            await ctx.message.delete()
        except disnake.Forbidden:
            pass

        # 2. Жесткая проверка прав (только Owner и Administrator)
        admin_role = disnake.utils.find(lambda r: "Administrator DC" in r.name, ctx.guild.roles)
        owner_role = disnake.utils.find(lambda r: "Owner DragPolit" in r.name, ctx.guild.roles)
        
        has_access = False
        if admin_role and admin_role in ctx.author.roles: has_access = True
        if owner_role and owner_role in ctx.author.roles: has_access = True
        if ctx.author.guild_permissions.administrator: has_access = True

        if not has_access:
            return await ctx.send("У вас нет доступа к этой панели.", delete_after=5)

        # 3. Отправляем панель управления
        embed = disnake.Embed(
            title="Секретная панель отправки",
            description="1. Выбери нужный канал в выпадающем списке ниже.\n2. Нажми зеленую кнопку, чтобы написать текст и выбрать цвет.",
            color=0x2b2d31
        )
        
        view = SenderView()
        view.message = await ctx.send(embed=embed, view=view)

def setup(bot):
    bot.add_cog(SenderCog(bot))
