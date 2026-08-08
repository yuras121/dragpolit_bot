import disnake
from disnake.ext import commands

# Тільки ці два користувачі можуть використовувати команду
ALLOWED_USERS = ["sakura0", "dragwayder"]

class EmbedModal(disnake.ui.Modal):
    def __init__(self, target_channel, embed_color, ping_text, panel_message, attachment_url):
        self.target_channel = target_channel
        self.embed_color = embed_color
        self.ping_text = ping_text
        self.panel_message = panel_message
        self.attachment_url = attachment_url # Збережений файл
        
        components = [
            disnake.ui.TextInput(
                label="Заголовок (необов'язково)",
                placeholder="Наприклад: 📢 Важливе оголошення DragPolit",
                custom_id="title",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=256
            ),
            disnake.ui.TextInput(
                label="Основний текст",
                placeholder="Введіть текст повідомлення...",
                custom_id="desc",
                style=disnake.TextInputStyle.paragraph,
                max_length=4000
            ),
            disnake.ui.TextInput(
                label="Посилання на банер (необов'язково)",
                placeholder="Встав лінк АБО просто прикріпи файл до команди !смс",
                custom_id="image_url",
                style=disnake.TextInputStyle.short,
                required=False
            )
        ]
        super().__init__(title="Написання повідомлення", custom_id="secret_embed_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        title = inter.text_values["title"]
        desc = inter.text_values["desc"]
        image_url_input = inter.text_values["image_url"]

        embed = disnake.Embed(description=desc, color=self.embed_color)
        if title:
            embed.title = title

        # Розумна логіка банера: якщо дали лінк - беремо його. Якщо лінка немає, але був файл - беремо файл!
        final_image = image_url_input if image_url_input else self.attachment_url
        if final_image:
            embed.set_image(url=final_image)

        # Відправляємо повідомлення в обраний канал
        await self.target_channel.send(content=self.ping_text, embed=embed)
        await inter.response.send_message(f"✅ Успішно відправлено в {self.target_channel.mention}!", ephemeral=True)
        
        # Прибираємо за собою
        try:
            await self.panel_message.delete()
        except:
            pass

class SenderView(disnake.ui.View):
    def __init__(self, author, attachment_url):
        super().__init__(timeout=300)
        self.author = author
        self.target_channel = None
        self.embed_color = 0x2b2d31 
        self.ping_text = None
        self.message = None 
        self.attachment_url = attachment_url # Передаємо збережений файл

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author != self.author:
            await inter.response.send_message("Це не ваша панель!", ephemeral=True)
            return False
        return True

    @disnake.ui.channel_select(
        placeholder="1️⃣ Оберіть канал для відправки...", 
        custom_id="select_channel", 
        channel_types=[disnake.ChannelType.text, disnake.ChannelType.news]
    )
    async def select_channel(self, select: disnake.ui.ChannelSelect, inter: disnake.MessageInteraction):
        self.target_channel = select.values[0]
        await inter.response.defer()

    @disnake.ui.string_select(
        placeholder="2️⃣ Оберіть колір рамки...",
        options=[
            disnake.SelectOption(label="Темний (Стандартний)", value="0x2b2d31", emoji="⬛"),
            disnake.SelectOption(label="Червоний (DragPolit)", value="0xff0000", emoji="🟥"),
            disnake.SelectOption(label="Зелений (Успіх/Оновлення)", value="0x00ff00", emoji="🟩"),
            disnake.SelectOption(label="Синій (Інформація)", value="0x0000ff", emoji="🟦"),
            disnake.SelectOption(label="Жовтий (Увага!)", value="0xffff00", emoji="🟨")
        ],
        custom_id="select_color"
    )
    async def select_color(self, select: disnake.ui.StringSelect, inter: disnake.MessageInteraction):
        self.embed_color = int(select.values[0], 16)
        await inter.response.defer()

    @disnake.ui.string_select(
        placeholder="3️⃣ Чи потрібен пінг?",
        options=[
            disnake.SelectOption(label="Без пінгу", value="none", emoji="🔕"),
            disnake.SelectOption(label="Пінгувати @everyone", value="@everyone", emoji="🔔"),
            disnake.SelectOption(label="Пінгувати @here", value="@here", emoji="📢")
        ],
        custom_id="select_ping"
    )
    async def select_ping(self, select: disnake.ui.StringSelect, inter: disnake.MessageInteraction):
        val = select.values[0]
        self.ping_text = None if val == "none" else val
        await inter.response.defer()

    @disnake.ui.button(label="4️⃣ Написати текст і Відправити", style=disnake.ButtonStyle.green, custom_id="btn_send", emoji="📝", row=4)
    async def create_btn(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not self.target_channel:
            return await inter.response.send_message("❌ Спочатку оберіть канал у першому меню вище!", ephemeral=True)
        
        await inter.response.send_modal(modal=EmbedModal(self.target_channel, self.embed_color, self.ping_text, self.message, self.attachment_url))


class SenderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="смс")
    async def secret_send(self, ctx):
        # ХАК: Перевіряємо, чи прикріпив адмін файл до команди !смс
        attachment_url = None
        if ctx.message.attachments:
            attachment_url = ctx.message.attachments[0].url

        try:
            await ctx.message.delete()
        except:
            pass

        if ctx.author.name not in ALLOWED_USERS:
            return 

        embed = disnake.Embed(
            title="⚙️ Секретна панель розсилки DragPolit",
            description=(
                "**Як відправити повідомлення:**\n"
                "1️⃣ Обери канал для відправки.\n"
                "2️⃣ Обери колір рамки.\n"
                "3️⃣ Обери пінг (якщо потрібно).\n"
                "4️⃣ Натисни зелену кнопку, впиши текст і відправляй!\n\n"
                "🖼️ *Лайфхак: щоб відправити файл замість лінка, просто прикріпи картинку з ПК/телефону до команди `!смс`!*"
            ),
            color=0x2b2d31
        )
        
        view = SenderView(ctx.author, attachment_url)
        view.message = await ctx.send(embed=embed, view=view)

def setup(bot):
    bot.add_cog(SenderCog(bot))
