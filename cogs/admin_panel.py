import disnake
from disnake.ext import commands

# Наш надійний захист: пускає тільки своїх
def has_full_access(inter):
    allowed_users = ["sakura0", "dragwayder"]
    if inter.author.name.lower() in allowed_users:
        return True
    
    if isinstance(inter.author, disnake.Member):
        owner_role = disnake.utils.find(lambda r: "Owner DragPolit" in r.name, inter.guild.roles)
        admin_role = disnake.utils.find(lambda r: "Administrator" in r.name, inter.guild.roles)
        
        if owner_role and owner_role in inter.author.roles:
            return True
        if admin_role and admin_role in inter.author.roles:
            return True
            
    return False

class ServerCheckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="check", description="Повна детальна перевірка та статистика сервера")
    async def server_check(self, inter: disnake.ApplicationCommandInteraction):
        if not has_full_access(inter):
            return await inter.response.send_message("❌ Відмовлено в доступі. Команда тільки для Керівництва.", ephemeral=True)
        
        # Даємо боту час на збір даних, якщо сервер великий
        await inter.response.defer()
        
        guild = inter.guild
        
        # --- ЗБІР ДАНИХ ---
        # 1. Учасники (рахуємо окремо людей і ботів)
        total_members = guild.member_count
        bots = sum(1 for member in guild.members if member.bot)
        humans = total_members - bots
        
        # 2. Канали
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        total_channels = text_channels + voice_channels
        
        # 3. Інше
        roles_count = len(guild.roles)
        boosts = guild.premium_subscription_count
        tier = guild.premium_tier
        
        # Динамічний час у форматі Discord (покаже, наприклад, "3 роки тому")
        created_time = f"<t:{int(guild.created_at.timestamp())}:R>"

        # --- СТВОРЕННЯ КРАСИВОГО ЗВІТУ ---
        embed = disnake.Embed(
            title=f"📊 Детальний аудит сервера: {guild.name}",
            description="Звіт про поточний стан екосистеми DragPolit.",
            color=0x2b2d31,
            timestamp=disnake.utils.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.add_field(name="👑 Власник", value=f"{guild.owner.mention}", inline=True)
        embed.add_field(name="🆔 ID Сервера", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="📅 Створено", value=created_time, inline=True)
        
        embed.add_field(
            name=f"👥 Громадяни ({total_members})", 
            value=f"👤 Люди: **{humans}**\n🤖 Боти: **{bots}**", 
            inline=True
        )
        
        embed.add_field(
            name=f"📁 Інфраструктура ({total_channels})", 
            value=f"💬 Текстові: **{text_channels}**\n🔊 Голосові: **{voice_channels}**\n🗂️ Категорії: **{categories}**", 
            inline=True
        )
        
        embed.add_field(
            name="🛡️ Додатково", 
            value=f"🎭 Кількість ролей: **{roles_count}**\n🚀 Бусти: **{boosts}** (Рівень {tier})", 
            inline=True
        )
        
        embed.set_footer(
            text=f"Перевірку ініціював: {inter.author.name}", 
            icon_url=inter.author.display_avatar.url if inter.author.display_avatar else None
        )
        
        await inter.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(ServerCheckCog(bot))
