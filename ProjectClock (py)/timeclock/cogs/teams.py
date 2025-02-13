import csv
import json
from datetime import datetime, timezone
from io import StringIO, BytesIO
from typing import List, Optional

import disnake
from disnake.ext import commands
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from timeclock.bot import TimeClockBot
from timeclock.database.team import Team

class Teams(commands.Cog):
    """إدارة الفرق والأقسام"""

    def __init__(self, bot: TimeClockBot) -> None:
        self.bot = bot
        self.teams = {}

    @commands.slash_command(name="team")
    @commands.has_permissions(administrator=True)
    async def team(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @team.sub_command(name="create")
    async def create_team(self, inter: disnake.ApplicationCommandInteraction,
                         name: str = commands.Param(description="اسم الفريق"),
                         leader: Optional[disnake.Member] = None):
        """إنشاء فريق جديد"""
        team_id = len(self.teams) + 1
        team = Team(team_id, name, inter.guild.id, leader.id if leader else None)
        self.teams[team_id] = team

        embed = disnake.Embed(
            title="✅ تم إنشاء الفريق",
            description=f"تم إنشاء فريق {name} بنجاح",
            color=disnake.Color.green()
        )
        if leader:
            embed.add_field(name="قائد الفريق", value=leader.mention)

        await inter.response.send_message(embed=embed)

    @team.sub_command(name="add-member")
    async def add_team_member(self, inter: disnake.ApplicationCommandInteraction,
                            team_id: int = commands.Param(description="رقم الفريق"),
                            member: disnake.Member = commands.Param(description="العضو المراد إضافته")):
        """إضافة عضو إلى الفريق"""
        if team_id not in self.teams:
            await inter.response.send_message("❌ لم يتم العثور على الفريق المحدد", ephemeral=True)
            return

        team = self.teams[team_id]
        if team.add_member(member.id):
            await inter.response.send_message(f"✅ تمت إضافة {member.mention} إلى الفريق {team.name}")
        else:
            await inter.response.send_message("❌ العضو موجود بالفعل في الفريق", ephemeral=True)

    @team.sub_command(name="export")
    async def export_team_data(self, inter: disnake.ApplicationCommandInteraction,
                             team_id: Optional[int] = commands.Param(None, description="رقم الفريق (اتركه فارغاً لتصدير بيانات جميع الفرق)"),
                             format: str = commands.Param(choices=["csv", "json", "xlsx", "pdf"], description="صيغة التصدير")):
        """تصدير بيانات الحضور للفريق"""
        await inter.response.defer()

        if team_id and team_id not in self.teams:
            await inter.followup.send("❌ لم يتم العثور على الفريق المحدد", ephemeral=True)
            return

        data = []
        teams_to_export = [self.teams[team_id]] if team_id else self.teams.values()

        for team in teams_to_export:
            for member_id in team.members:
                member_data = await self.bot.get_members(inter.guild.id, member_id=member_id)
                if member_data:
                    user = inter.guild.get_member(member_id)
                    if user:
                        for time in member_data.times:
                            data.append({
                                'team_name': team.name,
                                'member_name': user.display_name,
                                'punch_in': datetime.fromtimestamp(time.punch_in, tz=timezone.utc).isoformat(),
                                'punch_out': datetime.fromtimestamp(time.punch_out, tz=timezone.utc).isoformat() if time.punch_out else None,
                                'duration': time.as_seconds() / 3600 if time.punch_out else None
                            })

        if not data:
            await inter.followup.send("❌ لا توجد بيانات للتصدير", ephemeral=True)
            return

        if format == "json":
            file_content = json.dumps(data, ensure_ascii=False, indent=2)
            file = disnake.File(StringIO(file_content), filename="attendance_data.json")
        elif format == "csv":
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=['team_name', 'member_name', 'punch_in', 'punch_out', 'duration'])
            writer.writeheader()
            writer.writerows(data)
            file = disnake.File(StringIO(output.getvalue()), filename="attendance_data.csv")
        elif format == "xlsx":
            df = pd.DataFrame(data)
            df['duration'] = df['duration'].apply(lambda x: f"{x:.2f}" if x is not None else "")
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Attendance Data', index=False)
                workbook = writer.book
                worksheet = writer.sheets['Attendance Data']
                header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                worksheet.set_column('A:E', 20)
            output.seek(0)
            file = disnake.File(output, filename="attendance_data.xlsx")
        else:  # PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            table_data = [["Team Name", "Member Name", "Punch In", "Punch Out", "Duration (Hours)"]]
            for item in data:
                table_data.append([
                    item['team_name'],
                    item['member_name'],
                    item['punch_in'],
                    item['punch_out'] or "",
                    f"{item['duration']:.2f}" if item['duration'] else ""
                ])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            doc.build(elements)
            buffer.seek(0)
            file = disnake.File(buffer, filename="attendance_data.pdf")

        await inter.followup.send("✅ تم تصدير البيانات بنجاح", file=file)

    @team.sub_command(name="list")
    async def list_teams(self, inter: disnake.ApplicationCommandInteraction):
        """عرض قائمة الفرق"""
        if not self.teams:
            await inter.response.send_message("لا توجد فرق حالياً", ephemeral=True)
            return

        embed = disnake.Embed(
            title="📋 قائمة الفرق",
            color=disnake.Color.blue()
        )

        for team in self.teams.values():
            members = [inter.guild.get_member(mid).mention for mid in team.members if inter.guild.get_member(mid)]
            leader = inter.guild.get_member(team.leader_id) if team.leader_id else None
            
            value = f"القائد: {leader.mention if leader else 'لا يوجد'}\n"
            value += f"الأعضاء: {', '.join(members) if members else 'لا يوجد'}"
            
            embed.add_field(
                name=f"{team.name} (ID: {team.id})",
                value=value,
                inline=False
            )

        await inter.response.send_message(embed=embed)

def setup(bot: TimeClockBot) -> None:
    bot.add_cog(Teams(bot))