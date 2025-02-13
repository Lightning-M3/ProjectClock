import disnake
from disnake.ext import commands
from datetime import datetime, timezone
from typing import Optional

from timeclock.bot import TimeClockBot
from timeclock.calendar_sync import CalendarSync

class Schedule(commands.Cog):
    """إدارة جداول العمل والمواعيد"""

    def __init__(self, bot: TimeClockBot) -> None:
        self.bot = bot
        self.calendar = CalendarSync()

    @commands.slash_command(name="schedule")
    async def schedule(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @schedule.sub_command(name="sync-calendar")
    async def sync_calendar(self, inter: disnake.ApplicationCommandInteraction):
        """مزامنة جدول العمل مع تقويم Google"""
        await inter.response.defer()

        if not self.calendar.authenticate():
            await inter.edit_original_response(
                content="⚠️ يرجى إعداد مصادقة Google Calendar أولاً. راجع المشرف للحصول على المساعدة."
            )
            return

        member = await self.bot.get_members(inter.guild.id, member_id=inter.author.id)
        if not member:
            await inter.edit_original_response(
                content="❌ لم يتم العثور على سجلات دوام خاصة بك."
            )
            return

        recent_times = [time for time in member.times[-10:]]
        if not recent_times:
            await inter.edit_original_response(
                content="❌ لا توجد سجلات دوام حديثة لمزامنتها."
            )
            return

        synced_events = 0
        for time in recent_times:
            start_time = datetime.fromtimestamp(time.punch_in, tz=timezone.utc)
            if time.punch_out:
                end_time = datetime.fromtimestamp(time.punch_out, tz=timezone.utc)
                description = f"سجل الدوام - {inter.guild.name}"
                
                event_id = self.calendar.add_work_schedule(
                    start_time, end_time, description
                )
                if event_id:
                    synced_events += 1

        await inter.edit_original_response(
            content=f"✅ تمت مزامنة {synced_events} من سجلات الدوام مع تقويم Google."
        )

    @schedule.sub_command(name="view-schedule")
    async def view_schedule(
        self,
        inter: disnake.ApplicationCommandInteraction,
        days: int = commands.Param(7, ge=1, le=30)
    ):
        """عرض جدول العمل المزامن

        Parameters
        ----------
        days: :type:`int`
            عدد الأيام المراد عرضها (الحد الأقصى 30 يوم)
        """
        await inter.response.defer()

        if not self.calendar.authenticate():
            await inter.edit_original_response(
                content="⚠️ يرجى إعداد مصادقة Google Calendar أولاً. راجع المشرف للحصول على المساعدة."
            )
            return

        start_date = datetime.now(timezone.utc)
        end_date = start_date.replace(hour=23, minute=59, second=59)

        events = self.calendar.get_work_schedules(start_date, end_date)
        if not events:
            await inter.edit_original_response(
                content="ℹ️ لا توجد مواعيد عمل مجدولة للفترة المحددة."
            )
            return

        embed = disnake.Embed(
            title="📅 جدول العمل",
            description="المواعيد المزامنة مع Google Calendar",
            color=disnake.Color.blue()
        )

        for event in events:
            start = datetime.fromisoformat(event['start']['dateTime'])
            end = datetime.fromisoformat(event['end']['dateTime'])
            duration = end - start
            hours = duration.total_seconds() / 3600

            embed.add_field(
                name=f"🕒 {start.strftime('%d/%m/%Y %H:%M')}",
                value=f"المدة: {int(hours)} ساعة و {int((hours % 1) * 60)} دقيقة",
                inline=False
            )

        await inter.edit_original_response(embed=embed)

def setup(bot: TimeClockBot) -> None:
    bot.add_cog(Schedule(bot))