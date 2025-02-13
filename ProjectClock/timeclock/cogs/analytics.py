import disnake
from disnake.ext import commands
from datetime import datetime, timezone

from timeclock.bot import TimeClockBot
from timeclock.analytics import PatternAnalyzer
from timeclock import log

logger = log.get_logger(__name__)

class Analytics(commands.Cog):
    """تحليلات الحضور والانصراف"""

    def __init__(self, bot: TimeClockBot) -> None:
        self.bot = bot
        self.analyzer = PatternAnalyzer()

    @commands.slash_command(name="analyze-attendance")
    async def analyze_attendance(self, inter: disnake.GuildCommandInteraction) -> None:
        """تحليل أنماط الحضور والانصراف"""
        await inter.response.defer()

        try:
            member = await self.bot.get_members(inter.guild.id, member_id=inter.author.id)
            if not member:
                await inter.edit_original_response(content="لم يتم العثور على سجلات حضور خاصة بك.")
                return

            pattern = self.analyzer.analyze_member(member)
            if not pattern:
                await inter.edit_original_response(content="لا يوجد سجلات كافية للتحليل. يرجى المحاولة لاحقاً.")
                return
        except Exception as e:
            error_msg = f"Error analyzing attendance for user {inter.author.id}: {str(e)}"
            logger.error(error_msg)
            
            if isinstance(e, ValueError):
                await inter.edit_original_response(content="خطأ في تنسيق البيانات. يرجى المحاولة لاحقاً.")
            elif isinstance(e, TimeoutError):
                await inter.edit_original_response(content="انتهت مهلة تحليل البيانات. يرجى المحاولة لاحقاً.")
            else:
                await inter.edit_original_response(content="حدث خطأ أثناء تحليل البيانات. يرجى المحاولة لاحقاً.")
            return

        embed = disnake.Embed(
            title="تحليل أنماط الحضور والانصراف",
            color=disnake.Color.blue()
        )

        # Add average times with more detailed formatting
        embed.add_field(
            name="متوسط وقت الحضور",
            value=f"🕒 {pattern.average_start_time.strftime('%I:%M %p')}",
            inline=True
        )
        embed.add_field(
            name="متوسط وقت الانصراف",
            value=f"🕕 {pattern.average_end_time.strftime('%I:%M %p')}",
            inline=True
        )

        # Add duration and consistency with improved visualization
        hours = pattern.average_duration.total_seconds() / 3600
        embed.add_field(
            name="متوسط مدة العمل",
            value=f"⏱️ {hours:.1f} ساعة",
            inline=True
        )

        # Add consistency score with visual indicator
        consistency_percent = pattern.consistency_score * 100
        consistency_bar = '█' * int(consistency_percent / 10) + '░' * (10 - int(consistency_percent / 10))
        embed.add_field(
            name="مستوى الانتظام",
            value=f"{consistency_bar} {consistency_percent:.0f}%",
            inline=True
        )

        # Add active days with improved formatting
        days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        active_days = [days_ar[day] for day in pattern.days_active]
        embed.add_field(
            name="📅 أيام العمل",
            value="، ".join(active_days) or "لا يوجد",
            inline=False
        )

        # Add break patterns with improved visualization
        if pattern.break_patterns:
            breaks = []
            for start, end in pattern.break_patterns:
                duration = (end - start).total_seconds() / 60
                breaks.append(
                    f"☕ {start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')} "
                    f"({int(duration)} دقيقة)"
                )
            embed.add_field(
                name="فترات الراحة المعتادة",
                value="\n".join(breaks),
                inline=False
            )

        # Add recommendations based on patterns with more detailed analysis
        recommendations = []
        if pattern.consistency_score < 0.7:
            recommendations.append("💡 يمكن تحسين مستوى الانتظام في مواعيد الحضور والانصراف")
            if pattern.average_start_time.hour > 9:
                recommendations.append("⏰ يُفضل الحضور في وقت مبكر أكثر (قبل الساعة 9:00 صباحاً)")
        if not pattern.break_patterns:
            recommendations.append("💡 لم يتم رصد فترات راحة منتظمة")
            recommendations.append("☕ يُنصح بأخذ فترات راحة منتظمة لتحسين الإنتاجية")
        elif len(pattern.break_patterns) > 3:
            recommendations.append("⚠️ عدد فترات الراحة أكثر من المعتاد")
        if len(pattern.days_active) < 5:
            recommendations.append("📅 عدد أيام العمل أقل من المعتاد (أقل من 5 أيام)")
        
        # Add work-life balance score
        if pattern.average_duration.total_seconds() / 3600 > 10:
            recommendations.append("⚖️ ساعات العمل طويلة - يُنصح بتحسين التوازن بين العمل والحياة")

        if recommendations:
            embed.add_field(
                name="التوصيات والملاحظات",
                value="\n".join(recommendations),
                inline=False
            )
            
        # Add productivity score based on consistency and breaks
        productivity_score = (
            pattern.consistency_score * 0.6 +
            (1 if pattern.break_patterns else 0) * 0.2 +
            (min(len(pattern.days_active) / 5, 1)) * 0.2
        ) * 100
        
        embed.add_field(
            name="مؤشر الإنتاجية",
            value=f"{'🟢' if productivity_score >= 80 else '🟡' if productivity_score >= 60 else '🔴'} {productivity_score:.0f}%",
            inline=True
        )

        await inter.edit_original_response(embed=embed)


def setup(bot: TimeClockBot) -> None:
    bot.add_cog(Analytics(bot))