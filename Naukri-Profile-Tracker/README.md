# Naukri Profile Tracker Agent

An intelligent automation agent for managing your Naukri.com profile, keeping it active for recruiters, and tracking all job-related activities.

## Features

### Core Functionality
- **Auto Resume Update**: Updates your resume every 2 days to keep profile fresh and visible to recruiters
- **Recruiter Activity Tracking**: Monitors profile views, messages, and interview requests
- **Job Recommendations**: Fetches and stores recommended jobs based on your profile
- **Application Tracking**: Monitors status of all job applications
- **Profile Health Check**: Ensures profile completeness and optimization

### Notifications
- Email notifications for recruiter activities
- Daily/Weekly activity summary reports
- Alert for new matching jobs

## Project Structure

```
Naukri-Profile-Tracker/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── naukri_agent.py        # Main automation agent
│   ├── resume_manager.py      # Resume upload/update logic
│   ├── recruiter_tracker.py   # Track recruiter activities
│   ├── job_tracker.py         # Job recommendations & applications
│   ├── notifier.py            # Email/notification system
│   └── scheduler.py           # Task scheduling
├── data/
│   └── .gitkeep               # Data storage directory
├── logs/
│   └── .gitkeep               # Log files directory
├── tests/
│   ├── __init__.py
│   └── test_agent.py
├── .env.example               # Environment variables template
├── requirements.txt           # Python dependencies
├── main.py                    # Entry point
└── README.md
```

## Installation

### Prerequisites
- Python 3.10+
- Chrome/Chromium browser

### Setup

1. Clone the repository:
```bash
cd Naukri-Profile-Tracker
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Naukri credentials
```

## Configuration

Edit `.env` file with your credentials:

```env
NAUKRI_EMAIL=your_email@example.com
NAUKRI_PASSWORD=your_password
RESUME_PATH=/path/to/your/resume.pdf
NOTIFICATION_EMAIL=your_notification_email@example.com
```

## Usage

### Run Agent Manually
```bash
python main.py
```

### Run Specific Tasks
```bash
# Update resume only
python main.py --task resume-update

# Check recruiter activity
python main.py --task recruiter-check

# Get job recommendations
python main.py --task job-recommendations

# Full profile check
python main.py --task full-check
```

### Run as Scheduled Service
```bash
python main.py --daemon
```

## Scheduling

The agent runs the following tasks automatically:

| Task | Frequency | Description |
|------|-----------|-------------|
| Resume Update | Every 2 days | Re-uploads resume to refresh profile |
| Recruiter Check | Every 6 hours | Checks for new recruiter activities |
| Job Recommendations | Daily | Fetches new job recommendations |
| Profile Health | Weekly | Checks profile completeness |

## API Reference

### NaukriAgent

```python
from src.naukri_agent import NaukriAgent

agent = NaukriAgent()
agent.login()
agent.update_resume()
agent.check_recruiter_activity()
agent.get_job_recommendations()
agent.close()
```

## Security Notes

- Credentials are stored locally in `.env` file
- Never commit `.env` to version control
- Consider using a password manager or secrets vault for production
- Browser runs in headless mode by default

## Troubleshooting

### Common Issues

1. **Login Failed**: Check if credentials are correct in `.env`
2. **Resume Upload Failed**: Ensure resume path is correct and file exists
3. **Browser Not Found**: Run `playwright install chromium`
4. **Captcha Detected**: Manual intervention may be required

### Logs

Check logs in `logs/` directory for detailed information:
```bash
tail -f logs/naukri_agent.log
```

## Future Enhancements

- [ ] LinkedIn integration
- [ ] Indeed integration
- [ ] AI-powered job matching
- [ ] Auto-apply to matching jobs
- [ ] Interview scheduling assistant
- [ ] Resume optimization suggestions

## License

MIT License

## Disclaimer

This tool is for personal use only. Ensure compliance with Naukri.com's terms of service. The authors are not responsible for any account restrictions or bans resulting from automated activities.
