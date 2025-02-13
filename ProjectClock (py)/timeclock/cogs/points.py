import disnake
from disnake.ext import commands
from datetime import datetime, timedelta, timezone

from timeclock.bot import TimeClockBot
from timeclock.database.points import Points

class PointSystem(commands.Cog):
    """نظام النقاط والمكافآت"""

    def __init__(self, bot: TimeClockBot) -> None:
        self.bot = bot

    @commands.slash_command(name="points")
    async def points(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @points.sub_command(name="view")
    async def view_points(self, inter: disnake.ApplicationCommandInteraction,
                         member: disnake.Member = None):
        """عرض نقاط العضو"""
        target = member or inter.author
        points = await self.bot.db.get_points(target.id, inter.guild.id)

        embed = disnake.Embed(
            title="🏆 نقاط العضو",
            color=disnake.Color.gold()
        )
        embed.set_author(
            name=target.display_name,
            icon_url=target.display_avatar.url if target.display_avatar else None
        )

        if points:
            embed.description = f"**مجموع النقاط:** {points.points}"
            if points.last_weekly_check:
                embed.add_field(
                    name="آخر تحقق من الحضور الأسبوعي",
                    value=disnake.utils.format_dt(points.last_weekly_check, 'R'),
                    inline=False
                )
        else:
            embed.description = "لا توجد نقاط مسجلة بعد"

        await inter.response.send_message(embed=embed)

    @points.sub_command(name="leaderboard")
    async def points_leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        """عرض قائمة المتصدرين"""
        await inter.response.defer()

        leaderboard = await self.bot.db.get_points_leaderboard(inter.guild.id)
        if not leaderboard:
            await inter.followup.send("لا توجد نقاط مسجلة بعد", ephemeral=True)
            return

        embed = disnake.Embed(
            title="🏆 قائمة المتصدرين",
            color=disnake.Color.gold()
        )

        description = ""
        for i, (member_id, points) in enumerate(leaderboard[:10], 1):
            member = inter.guild.get_member(member_id)
            if member:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                description += f"{medal} {member.mention}: **{points}** نقطة\n"

        embed.description = description
        await inter.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        """Check for point awards when member status changes"""
        if not before.bot and before.status != after.status:
            member_data = await self.bot.get_members(after.guild.id, member_id=after.id)
            if not member_data:
                return

            # Check for overtime points
            if member_data.on_duty:
                latest_time = member_data.times[-1]
                punch_in = datetime.fromtimestamp(latest_time.punch_in, tz=timezone.utc)
                duration = datetime.now(timezone.utc) - punch_in
                hours_worked = duration.total_seconds() / 3600

                points = Points.award_overtime_points(hours_worked, 8)  # Assuming 8 hours is standard
                if points > 0:
                    await self.bot.db.add_points(after.id, after.guild.id, points)

            # Check for weekly attendance
            today = datetime.now(timezone.utc)
            if today.weekday() == 6:  # Sunday, end of week
                week_times = [time for time in member_data.times if 
                             (today - datetime.fromtimestamp(time.punch_in, tz=timezone.utc)).days <= 7]
                attendance_days = len(set(datetime.fromtimestamp(time.punch_in, tz=timezone.utc).date()
                                      for time in week_times))

                points = Points.award_weekly_attendance(attendance_days, 5)  # Assuming 5 working days
                if points > 0:
                    await self.bot.db.add_points(after.id, after.guild.id, points)

def setup(bot: TimeClockBot) -> None:
    bot.add_cog(PointSystem(bot))