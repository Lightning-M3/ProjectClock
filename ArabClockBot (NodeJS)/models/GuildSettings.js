const mongoose = require('mongoose');

const guildSettingsSchema = new mongoose.Schema({
    guildId: {
        type: String,
        required: true,
        unique: true
    },
    attendanceRoleId: {
        type: String,
        required: true
    },
    welcomeChannelId: {
        type: String,
        required: true
    },
    logsChannelId: {
        type: String,
        required: true
    },
    setupComplete: {
        type: Boolean,
        default: false
    },
    prefix: {
        type: String,
        default: '/'
    },
    language: {
        type: String,
        default: 'ar'
    },
    timezone: {
        type: String,
        default: 'Asia/Riyadh'
    },
    features: {
        tickets: {
            enabled: { type: Boolean, default: false },
            categoryId: String,
            logChannelId: String
        },
        welcome: {
            enabled: { type: Boolean, default: false },
            message: String,
            channelId: String
        },
        apply: {
            enabled: { type: Boolean, default: false },
            channelId: String,
            logChannelId: String,
            staffRoleId: String
        },
        attendance: {
            enabled: { type: Boolean, default: false },
            roleId: String,
            channelId: String,
            schedule: {
                start: String,
                end: String,
                timezone: String
            }
        }
    }
}, {
    timestamps: true
});

// إضافة الفهارس لتحسين الأداء
guildSettingsSchema.index({ guildId: 1 });

const GuildSettings = mongoose.model('GuildSettings', guildSettingsSchema);

module.exports = GuildSettings;
