import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict

from timeclock import log
from timeclock.bot import TimeClockBot
from timeclock.database import Member, Time

logger = log.get_logger(__name__)


class Reports(commands.Cog):
    """معالجة تقارير الحضور"""

    def __init__(self, bot: TimeClockBot) -> None:
        self.bot = bot
        self.guild_settings = None  # Will store guild-specific settings including work hours
        try:
            self.daily_report.start()
            self.weekly_report.start()
            self.monthly_report.start()
            self.overtime_check.start()
            logger.info("Successfully started all report tasks")
        except Exception as e:
            logger.error(f"Failed to start report tasks: {str(e)}")
        self.standard_hours = 8  # Standard work hours per day

    def cog_unload(self):
        self.daily_report.cancel()
        self.weekly_report.cancel()
        self.monthly_report.cancel()
        self.overtime_check.cancel()

    @tasks.loop(time=datetime.time(hour=21, tzinfo=timezone.utc))
    async def daily_report(self):
        """Send daily attendance report at 9:00 PM UTC"""
        await self._generate_report(1, "يومي")

    @tasks.loop(time=datetime.time(hour=23, minute=59, tzinfo=timezone.utc))
    async def weekly_report(self):
        """Send weekly attendance report at 11:59 PM UTC on Saturdays"""
        if datetime.now(timezone.utc).weekday() == 5:  # Saturday
            await self._generate_report(7, "أسبوعي")

    @tasks.loop(time=datetime.time(hour=23, minute=59, tzinfo=timezone.utc))
    async def monthly_report(self):
        """Send monthly attendance report at 11:59 PM UTC on the last day of the month"""
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        if tomorrow.day == 1:  # Last day of the month
            await self._generate_report(30, "شهري")

    @tasks.loop(minutes=30)
    async def overtime_check(self):
        """Check for overtime and insufficient hours every 30 minutes"""
        now = datetime.now(timezone.utc)
        for guild in self.bot.guilds:
            try:
                members = await self.bot.get_members(guild.id)
                if not members:
                    continue

                channel = next(
                    (ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages),
                    None
                )
                if not channel:
                    continue

                for member in members:
                    if member.on_duty:
                        latest_time = member.times[-1]
                        punch_in = datetime.fromtimestamp(latest_time.punch_in, tz=timezone.utc)
                        duration = now - punch_in
                        hours = duration.total_seconds() / 3600

                        if hours >= self.standard_hours + 2:  # 2 hours overtime
                            user = guild.get_member(member.id)
                            if user:
                                embed = disnake.Embed(
                                    title="تنبيه ساعات العمل الإضافية",
                                    description=f"⚠️ {user.mention} لديك {int(hours - self.standard_hours)} ساعات عمل إضافية اليوم",
                                    color=disnake.Color.orange()
                                )
                                await channel.send(embed=embed)

            except Exception as e:
                logger.error(f"Error checking overtime for guild {guild.id}: {str(e)}")

    async def _generate_report(self, days: int, report_type: str):
        """Generate and send attendance report for the specified number of days"""
        logger.info(f"Generating {report_type} attendance report")

        for guild in self.bot.guilds:
            try:
                members = await self.bot.get_members(guild.id)
                if not members:
                    continue

                channel = next(
                    (ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages),
                    None
                )
                if not channel:
                    logger.warning(f"No suitable channel found in guild {guild.name} ({guild.id})")
                    continue

                # Generate main report embeds
                embeds = await self.create_report_embed(guild, members, days, report_type)
                
                # Add points statistics
                points_embed = await self.create_points_statistics(guild, days)
                if points_embed:
                    await channel.send(embed=points_embed)
                
                # Send report embeds in chunks to respect Discord's limit
                for i in range(0, len(embeds), 10):  # Discord allows max 10 embeds per message
                    chunk = embeds[i:i + 10]
                    await channel.send(embeds=chunk)
                    
                logger.info(f"{report_type.capitalize()} report sent to guild {guild.name} ({guild.id})")
                    
            except Exception as e:
                logger.error(f"Error generating {report_type} report for guild {guild.id}: {str(e)}")

    async def create_points_statistics(self, guild: disnake.Guild, days: int) -> Optional[disnake.Embed]:
        """Create an embed containing points statistics for the specified period"""
        try:
            # Get points leaderboard
            leaderboard = await self.bot.db.get_points_leaderboard(guild.id)
            if not leaderboard:
                return None

            embed = disnake.Embed(
                title=f"📊 إحصائيات النقاط - آخر {days} يوم",
                color=disnake.Color.gold()
            )

            # Top point earners
            description = "🏆 المتصدرون في النقاط:\n"
            for i, (member_id, points) in enumerate(leaderboard[:5], 1):
                member = guild.get_member(member_id)
                if member:
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    description += f"{medal} {member.mention}: **{points}** نقطة\n"

            embed.description = description

            # Calculate period statistics
            total_points = sum(points for _, points in leaderboard)
            avg_points = total_points / len(leaderboard) if leaderboard else 0

            embed.add_field(
                name="📈 إحصائيات عامة",
                value=f"إجمالي النقاط: **{total_points}**\n" \
                      f"متوسط النقاط: **{avg_points:.1f}**\n" \
                      f"عدد المشاركين: **{len(leaderboard)}**",
                inline=False
            )

            return embed
        except Exception as e:
            logger.error(f"Error generating points statistics for guild {guild.id}: {str(e)}")
            return None
    async def create_report_embed(self, guild: disnake.Guild, members: List[Member], days: int, report_type: str) -> List[disnake.Embed]:
        """Create a list of embeds containing the attendance report for the specified period"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        embeds = []
        current_embed = disnake.Embed(
            title=f"تقرير الحضور {report_type} - {start_date.strftime('%d/%m/%Y')} إلى {end_date.strftime('%d/%m/%Y')}",
            color=disnake.Color.blue()
        )

        total_hours = 0
        total_members = 0
        details = []
        attendance_stats = self._calculate_attendance_stats(members, start_date, end_date)

        for member in members:
            member_times = []
            daily_total = timedelta()

            for time in member.times:
                punch_in = datetime.fromtimestamp(time.punch_in, tz=timezone.utc)
                if start_date <= punch_in <= end_date:
                    punch_out = datetime.fromtimestamp(time.punch_out, tz=timezone.utc) if time.punch_out else None
                    if punch_out:
                        duration = punch_out - punch_in
                        daily_total += duration
                        hours = duration.total_seconds() / 3600
                        minutes = (hours % 1) * 60
                        member_times.append(
                            f"دخول: {punch_in.strftime('%I:%M %p')} - "
                            f"خروج: {punch_out.strftime('%I:%M %p')} "
                            f"({int(hours)} ساعة و {int(minutes)} دقيقة)"
                        )

            if member_times:
                total_members += 1
                user = guild.get_member(member.id)
                if user:
                    member_details = [f"**{user.display_name}**"]
                    member_details.extend([f"• {time}" for time in member_times])
                    total_hours_member = daily_total.total_seconds() / 3600
                    total_minutes_member = (total_hours_member % 1) * 60
                    member_details.append(f"المجموع: {int(total_hours_member)} ساعة و {int(total_minutes_member)} دقيقة\n")
                    
                    # Check if adding this member's details would exceed Discord's character limit
                    potential_description = "\n".join(details + member_details)
                    if len(potential_description) > 4096:  # Discord's embed description limit
                        # Finalize current embed
                        current_embed.description = "\n".join(details)
                        embeds.append(current_embed)
                        
                        # Create new embed
                        current_embed = disnake.Embed(
                            title=f"تقرير الحضور {report_type} (تابع)",
                            color=disnake.Color.blue()
                        )
                        details = member_details
                    else:
                        details.extend(member_details)
                    
                    total_hours += daily_total.total_seconds() / 3600

        if details:  # Add the last set of details
            avg_hours_per_member = total_hours / total_members
            current_embed.description = "\n".join(details)
            
            # Add statistical analysis
            stats_text = f"📊 **إحصائيات الحضور**\n"
            stats_text += f"• متوسط ساعات العمل اليومية: {attendance_stats['avg_daily_hours']:.1f} ساعة\n"
            stats_text += f"• نسبة الالتزام بساعات العمل: {attendance_stats['compliance_rate']:.0%}\n"
            stats_text += f"• عدد ساعات العمل الإضافية: {attendance_stats['total_overtime']:.1f} ساعة\n"
            stats_text += f"• معدل الحضور: {attendance_stats['attendance_rate']:.0%}\n\n"
            
            current_embed.add_field(name="التحليل الإحصائي", value=stats_text, inline=False)
            
            total_minutes = (total_hours % 1) * 60
            footer_text = f"مجموع الساعات: {int(total_hours)} ساعة و {int(total_minutes)} دقيقة\n"
            footer_text += f"متوسط الساعات لكل عضو: {int(avg_hours_per_member)} ساعة و {int((avg_hours_per_member % 1) * 60)} دقيقة"
            current_embed.set_footer(text=footer_text)
            embeds.append(current_embed)
        else:
            current_embed.description = f"لا توجد سجلات حضور خلال الفترة المحددة."
            embeds.append(current_embed)

        return embeds

    def _calculate_attendance_stats(self, members: List[Member], start_date: datetime, end_date: datetime) -> Dict:
        """Calculate attendance statistics for the given period"""
        total_hours = 0
        total_days = (end_date - start_date).days + 1
        total_expected_hours = 0
        attendance_days = set()
        overtime_hours = 0

        for member in members:
            member_days = set()
            for time in member.times:
                punch_in = datetime.fromtimestamp(time.punch_in, tz=timezone.utc)
                if start_date <= punch_in <= end_date:
                    punch_out = datetime.fromtimestamp(time.punch_out, tz=timezone.utc) if time.punch_out else None
                    if punch_out:
                        duration = punch_out - punch_in
                        hours = duration.total_seconds() / 3600
                        total_hours += hours
                        member_days.add(punch_in.date())
                        
                        # Calculate overtime based on configured work hours
                        if self.guild_settings:
                            work_hours = self.guild_settings.get_work_hours(punch_in.weekday())
                            if work_hours:
                                start_time, end_time = work_hours
                                expected_hours = (end_time.hour + end_time.minute/60) - (start_time.hour + start_time.minute/60)
                                if hours > expected_hours:
                                    overtime_hours += hours - expected_hours
                                total_expected_hours += expected_hours

            attendance_days.update(member_days)

        return {
            'avg_daily_hours': total_hours / max(len(attendance_days), 1),
            'compliance_rate': min(total_hours / total_expected_hours if total_expected_hours > 0 else 1, 1),
            'total_overtime': overtime_hours,
            'attendance_rate': len(attendance_days) / total_days if total_days > 0 else 0
        }

    @overtime_check.before_loop
    @daily_report.before_loop
    @weekly_report.before_loop
    @monthly_report.before_loop
    async def before_report(self):
        await self.bot.wait_until_ready()


def setup(bot: TimeClockBot) -> None:
    bot.add_cog(Reports(bot))