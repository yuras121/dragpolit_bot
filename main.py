import disnake
from disnake.ext import commands
import os
import config

intents = disnake.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Убрали test_guilds, теперь команды будут работать на любом сервере, куда добавлен бот
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    reload=True
)

@bot.event
async def on_ready():
    print(f"[{bot.user}] Система Dragpolit Bot успешно запущена!")
    await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name="Dragpolit.com"))

for filename in os.listdir('./cogs'):
    if filename.endswith('.py') and filename != '__init__.py':
        bot.load_extension(f'cogs.{filename[:-3]}')

if __name__ == "__main__":
    bot.run(config.BOT_TOKEN)
