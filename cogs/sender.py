import disnake
from disnake.ext import commands

# Тільки ви можете використовувати команду
ALLOWED_USERS = ["sakura0", "dragwayder"]

class EmbedModal(disnake.ui.Modal):
    def __init__(self, target_channel, embed_color, ping_text, panel_message, attachment: disnake.Attachment = None):
        self.target_channel = target_channel
        self.embed_color = embed_color
        self.ping_text = ping_text
        self.panel_message = panel_message
        self.attachment = attachment # Перехоплений файл
        
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
                label="Нижній текст / Footer (необов'язково)",
                placeholder="Наприклад: Адміністрація сервера",
                custom_id="footer",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=2000
            ),
            disnake.ui.TextInput(
                label="Посилання на банер (якщо немає файлу)",
                placeholder="Вставте лінк АБО залиште пустим, якщо прикріпили файл",
                custom_id="image_url",
                style=disnake.TextInputStyle.short,
                required=False
            )
        ]
        super().__init__(title="Фінальне налаштування", custom_id="secret_embed_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        # Даємо боту час подумати, якщо файл великий і довго вантажиться
        await inter.response.defer(ephemeral=True) 
        
        title = inter.text_values["title"]
        desc = inter.text_values["desc"]
        footer = inter.text_values["footer"]
        image_url_input = inter.text_values["image_url"]

        embed = disnake.Embed(description=desc, color=self.embed_color)
        if title:
            embed.title = title
        if footer:
            embed.set_footer(text=footer)

        file_to_send = None

        # НАДІЙНА ЛОГІКА КАРТИНОК:
        # Якщо був прикріплений файл - заново створюємо його для відправки
        if self.attachment:
            file_to_send = await self.attachment.to_file()
            embed.set_image(url=f"attachment://{self.attachment.filename}")
        # Якщо файлу немає, але є лінк з інтернету
        elif image_url_input:
            embed.set_image(url=image_url_input)

        # Відправляємо із захистом від помилок доступу
        try:
            if file_to_send:
                await self.target_channel.send(content=self.ping_text, embed=embed, file=file_to_send)
            else:
                await self.target_channel.send(content=self.ping_text, embed=embed)
            
            await inter.followup.send(f"✅ Успішно відправлено в {self.target_channel.mention}!", ephemeral=True)
        except disnake.Forbidden:
            await inter.followup.send(f"❌ Помилка: У бота немає прав писати в канал {self.target_channel.mention}. Перевірте налаштування каналу.", ephemeral=True)
        except Exception as e:
            await inter.followup.send(f"❌ Виникла помилка: {e}", ephemeral=True)
        
        # Прибираємо панель керування за собою
        try:
            await self.panel_message.delete()
        except:
            pass

class SenderView(disnake.ui.View):
    def __init__(self, author, attachment: disnake.Attachment = None):
        super().__init__(timeout=300)
        self.author = author
        self.target_channel = None
        self.embed_color = 0x2b2d31 
        self.ping_text = None
        self.message = None 
        self.attachment = attachment 

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
            disnake.SelectOption(label="Темний (Стандарт)", value="0x2b2d31", emoji="⬛"),
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

    @disnake.ui.button(label="4️⃣ Написати текст і Відправити", style=disnake.ButtonStyle.green, custom_id="btn_send", emoji="🚀", row=4)
    async def create_btn(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not self.target_channel:
            return await inter.response.send_message("❌ Спочатку оберіть канал у першому меню вище!", ephemeral=True)
        
        await inter.response.send_modal(modal=EmbedModal(self.target_channel, self.embed_color, self.ping_text, self.message, self.attachment))


class SenderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="смс")
    async def secret_send(self, ctx):
        if ctx.author.name not in ALLOWED_USERS:
            return 

        # Ловимо прикріплений файл, якщо він є
        attachment = None
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]

        # Видаляємо повідомлення адміністратора для скритності
        try:
            await ctx.message.delete()
        except:
            pass

        # Візуальний індикатор для зручності
        file_status = "✅ **Файл успішно прикріплено до повідомлення!**" if attachment else "⚠️ *Файл не прикріплено (можете додати лінк на банер пізніше)*"

        embed = disnake.Embed(
            title="⚙️ Секретна панель DragPolit (ФІНАЛ)",
            description=(
                f"{file_status}\n\n"
                "**Кроки для розсилки:**\n"
                "1️⃣ Обери канал.\n"
                "2️⃣ Обери колір рамки.\n"
                "3️⃣ Обери пінг (якщо потрібно).\n"
                "4️⃣ Натисни зелену кнопку, заповни текст і відправляй!\n\n"
                "🛡️ *Ця система надійно зберігає файли та перевіряє права бота.*"
            ),
            color=0x2b2d31
        )
        
        view = SenderView(ctx.author, attachment)
        view.message = await ctx.send(embed=embed, view=view)

def setup(bot):
    bot.add_cog(SenderCog(bot))
