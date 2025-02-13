import disnake
from disnake.ext import commands
from datetime import datetime, timedelta
from typing import Optional, List

from timeclock.bot import TimeClockBot
from timeclock.database.config import GuildConfig

class Leave(commands.Cog):
    """إدارة الإجازات والأذونات"""

    def __init__(self, bot: TimeClockBot) -> None:
        self.bot = bot
        self.guild_configs = {}

    def get_guild_config(self, guild_id: int) -> GuildConfig:
        if guild_id not in self.guild_configs:
            self.guild_configs[guild_id] = GuildConfig(guild_id)
        return self.guild_configs[guild_id]

    @commands.slash_command(name="leave")
    async def leave(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @leave.sub_command(name="request")
    async def request_leave(self, inter: disnake.ApplicationCommandInteraction,
                          start_date: str = commands.Param(description="تاريخ بداية الإجازة (YYYY-MM-DD)"),
                          days: int = commands.Param(description="عدد أيام الإجازة", ge=1, le=30),
                          reason: str = commands.Param(description="سبب الإجازة")):
        """تقديم طلب إجازة"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = start + timedelta(days=days)

            embed = disnake.Embed(
                title="طلب إجازة جديد",
                color=disnake.Color.blue()
            )
            embed.add_field(name="العضو", value=inter.author.mention, inline=False)
            embed.add_field(name="تاريخ البداية", value=start.strftime("%d/%m/%Y"), inline=True)
            embed.add_field(name="تاريخ النهاية", value=end.strftime("%d/%m/%Y"), inline=True)
            embed.add_field(name="عدد الأيام", value=str(days), inline=True)
            embed.add_field(name="السبب", value=reason, inline=False)

            # Send to moderators/admins
            for channel in inter.guild.text_channels:
                if channel.permissions_for(inter.guild.me).send_messages:
                    if "admin" in channel.name.lower() or "mod" in channel.name.lower():
                        await channel.send(embed=embed)
                        break

            await inter.response.send_message("✅ تم إرسال طلب الإجازة بنجاح، سيتم إبلاغك بالرد قريباً.")

        except ValueError:
            await inter.response.send_message("❌ صيغة التاريخ غير صحيحة. الرجاء استخدام الصيغة YYYY-MM-DD")

    @leave.sub_command(name="approve")
    @commands.has_permissions(administrator=True)
    async def approve_leave(self, inter: disnake.ApplicationCommandInteraction,
                          member: disnake.Member,
                          start_date: str,
                          days: int = commands.Param(ge=1, le=30)):
        """الموافقة على طلب إجازة"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = start + timedelta(days=days)

            embed = disnake.Embed(
                title="تمت الموافقة على طلب الإجازة",
                color=disnake.Color.green()
            )
            embed.add_field(name="العضو", value=member.mention, inline=False)
            embed.add_field(name="تاريخ البداية", value=start.strftime("%d/%m/%Y"), inline=True)
            embed.add_field(name="تاريخ النهاية", value=end.strftime("%d/%m/%Y"), inline=True)
            embed.add_field(name="عدد الأيام", value=str(days), inline=True)
            embed.add_field(name="تمت الموافقة من قبل", value=inter.author.mention, inline=False)

            await inter.response.send_message(embed=embed)
            try:
                await member.send(embed=embed)
            except:
                pass

        except ValueError:
            await inter.response.send_message("❌ صيغة التاريخ غير صحيحة. الرجاء استخدام الصيغة YYYY-MM-DD")

    @leave.sub_command(name="deny")
    @commands.has_permissions(administrator=True)
    async def deny_leave(self, inter: disnake.ApplicationCommandInteraction,
                        member: disnake.Member,
                        reason: str = commands.Param(description="سبب الرفض")):
        """رفض طلب إجازة"""
        embed = disnake.Embed(
            title="تم رفض طلب الإجازة",
            color=disnake.Color.red()
        )
        embed.add_field(name="العضو", value=member.mention, inline=False)
        embed.add_field(name="سبب الرفض", value=reason, inline=False)
        embed.add_field(name="تم الرفض من قبل", value=inter.author.mention, inline=False)

        await inter.response.send_message(embed=embed)
        try:
            await member.send(embed=embed)
        except:
            pass

    @leave.sub_command(name="balance")
    async def leave_balance(self, inter: disnake.ApplicationCommandInteraction,
                          member: Optional[disnake.Member] = None):
        """عرض رصيد الإجازات المتبقي"""
        target = member or inter.author
        
        # This is a placeholder. In a real implementation, you'd fetch this from a database
        annual_leave = 30  # Example: 30 days per year
        used_leave = 10    # Example: 10 days used
        
        embed = disnake.Embed(
            title="رصيد الإجازات",
            color=disnake.Color.blue()
        )
        embed.add_field(name="العضو", value=target.mention, inline=False)
        embed.add_field(name="الرصيد السنوي", value=f"{annual_leave} يوم", inline=True)
        embed.add_field(name="الإجازات المستخدمة", value=f"{used_leave} يوم", inline=True)
        embed.add_field(name="الرصيد المتبقي", value=f"{annual_leave - used_leave} يوم", inline=True)
        
        await inter.response.send_message(embed=embed)

def setup(bot: TimeClockBot) -> None:
    bot.add_cog(Leave(bot))