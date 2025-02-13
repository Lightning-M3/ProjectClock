import disnake
from disnake.ext import commands
from datetime import time
from typing import Optional

from timeclock.bot import TimeClockBot
from timeclock.database.config import GuildConfig

class WorkHours(commands.Cog):
    """إدارة ساعات العمل المطلوبة"""

    def __init__(self, bot: TimeClockBot) -> None:
        self.bot = bot
        self.guild_configs = {}

    def get_guild_config(self, guild_id: int) -> GuildConfig:
        if guild_id not in self.guild_configs:
            self.guild_configs[guild_id] = GuildConfig(guild_id)
        return self.guild_configs[guild_id]

    @commands.slash_command(name="workhours")
    @commands.has_permissions(administrator=True)
    async def workhours(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @workhours.sub_command(name="set")
    async def set_hours(self, inter: disnake.ApplicationCommandInteraction,
                       day: int = commands.Param(description="اليوم (0-6، حيث 0 هو الإثنين)", ge=0, le=6),
                       start_hour: int = commands.Param(description="ساعة البدء (0-23)", ge=0, le=23),
                       start_minute: int = commands.Param(description="دقيقة البدء (0-59)", ge=0, le=59),
                       end_hour: int = commands.Param(description="ساعة الانتهاء (0-23)", ge=0, le=23),
                       end_minute: int = commands.Param(description="دقيقة الانتهاء (0-59)", ge=0, le=59)):
        """تعيين ساعات العمل ليوم محدد"""
        config = self.get_guild_config(inter.guild.id)
        
        start = time(hour=start_hour, minute=start_minute)
        end = time(hour=end_hour, minute=end_minute)
        
        if config.set_work_hours(day, start, end):
            days = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
            await inter.response.send_message(
                f"✅ تم تعيين ساعات العمل ليوم {days[day]}:\n"
                f"من الساعة {start.strftime('%H:%M')} إلى {end.strftime('%H:%M')}"
            )
        else:
            await inter.response.send_message("❌ حدث خطأ أثناء تعيين ساعات العمل.")

    @workhours.sub_command(name="clear")
    async def clear_hours(self, inter: disnake.ApplicationCommandInteraction,
                         day: Optional[int] = commands.Param(None, description="اليوم (0-6، حيث 0 هو الإثنين)، اتركه فارغًا لمسح جميع الأيام", ge=0, le=6)):
        """مسح ساعات العمل ليوم محدد أو لجميع الأيام"""
        config = self.get_guild_config(inter.guild.id)
        
        if config.clear_work_hours(day):
            if day is None:
                await inter.response.send_message("✅ تم مسح ساعات العمل لجميع الأيام.")
            else:
                days = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
                await inter.response.send_message(f"✅ تم مسح ساعات العمل ليوم {days[day]}.")
        else:
            await inter.response.send_message("❌ حدث خطأ أثناء مسح ساعات العمل.")

    @workhours.sub_command(name="view")
    async def view_hours(self, inter: disnake.ApplicationCommandInteraction):
        """عرض ساعات العمل المعينة لكل يوم"""
        config = self.get_guild_config(inter.guild.id)
        days = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        
        embed = disnake.Embed(
            title="⏰ ساعات العمل المطلوبة",
            color=disnake.Color.blue()
        )
        
        for day_num, day_name in enumerate(days):
            hours = config.get_work_hours(day_num)
            if hours:
                start, end = hours
                embed.add_field(
                    name=day_name,
                    value=f"من {start.strftime('%H:%M')} إلى {end.strftime('%H:%M')}",
                    inline=False
                )
            else:
                embed.add_field(
                    name=day_name,
                    value="لم يتم تعيين ساعات عمل",
                    inline=False
                )
        
        await inter.response.send_message(embed=embed)

def setup(bot: TimeClockBot) -> None:
    bot.add_cog(WorkHours(bot))