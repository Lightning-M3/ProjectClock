# Tawqeet (توقيت)

A Discord bot for managing attendance and work hours with comprehensive Arabic support. Tawqeet helps organizations track employee attendance, manage work schedules, and generate detailed reports.

## Features

- 🕒 Simple clock in/out system with a button click
- 📊 Detailed attendance reports (daily, weekly, monthly)
- 📅 Work hours management and scheduling
- 📈 Analytics and attendance patterns
- 🔄 Google Calendar integration
- 👥 Team management
- ⭐ Points system for attendance
- 📝 Leave management
- 🌐 Full Arabic language support

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```
   or
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables in a `.env` file:
   ```env
   DISCORD_TOKEN=your_bot_token
   MONGODB_URI=your_mongodb_uri
   ```
4. Run the bot:
   ```bash
   python main.py
   ```

## Commands

### Admin Commands
- `/config` - Configure bot settings
- `/workhours` - Manage work hours
- `/reports` - View attendance reports

### User Commands
- `/timesheet` - View your attendance records
- `/analyze-attendance` - View your attendance patterns
- `/schedule` - Manage your work schedule

### Team Management
- `/team` - Team management commands
- `/leave` - Manage leave requests

## Support

If you need help or want to report issues, please open an issue in the GitHub repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

