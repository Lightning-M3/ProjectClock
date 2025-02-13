const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const Attendance = require('../models/Attendance'); // تأكد من مسار النموذج
const logger = require('../utils/logger'); // تأكد من مسار السجل

module.exports = {
    data: new SlashCommandBuilder()
        .setName('open-sessions')
        .setDescription('عرض الأشخاص الذين لديهم جلسات حضور مفتوحة ولم يسجلوا انصرافهم بعد.'),
    async execute(interaction) {
        await interaction.deferReply({ ephemeral: true });

        const guildId = interaction.guild.id;
        const attendanceRole = interaction.guild.roles.cache.find(role => role.name === 'مسجل حضوره'); // الحصول على رتبة "مسجل حضوره"

        try {
            // البحث عن جميع سجلات الحضور المفتوحة
            const attendanceRecords = await Attendance.find({
                guildId: guildId,
                'sessions.checkOut': { $exists: false } // تحقق من وجود جلسات مفتوحة
            });

            if (!attendanceRecords || attendanceRecords.length === 0) {
                return await interaction.followUp({
                    content: '❌ لا توجد جلسات حضور مفتوحة حاليًا.',
                    ephemeral: true
                });
            }

            // إعداد قائمة المستخدمين الذين لديهم جلسات مفتوحة
            const openSessions = new Set(); // استخدام Set لمنع التكرار
            attendanceRecords.forEach(record => {
                const user = interaction.guild.members.cache.get(record.userId);
                if (user && user.roles.cache.has(attendanceRole.id)) { // تحقق من أن المستخدم لديه رتبة "مسجل حضوره"
                    openSessions.add(user.user.tag); // إضافة اسم المستخدم إلى Set
                }
            });

            // إعداد الرسالة
            const embed = new EmbedBuilder()
                .setTitle('🕒 الجلسات المفتوحة')
                .setDescription('الأشخاص الذين لديهم جلسات حضور مفتوحة ولم يسجلوا انصرافهم بعد:')
                .addFields({ name: 'الأعضاء', value: openSessions.size > 0 ? Array.from(openSessions).join('\n') : 'لا يوجد أعضاء' })
                .setColor(0x00ff00)
                .setTimestamp();

            await interaction.followUp({ embeds: [embed], ephemeral: true });

        } catch (error) {
            logger.error('Error in open-sessions command:', error);
            await interaction.followUp({
                content: 'حدث خطأ أثناء محاولة عرض الجلسات المفتوحة.',
                ephemeral: true
            });
        }
    }
}; 