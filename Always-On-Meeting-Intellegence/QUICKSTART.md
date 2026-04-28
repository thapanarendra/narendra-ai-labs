# Quick Start Guide

Get the Always-On Meeting Intelligence Agent running in under 5 minutes!

## 1. Install Dependencies

```bash
cd Always-On-Meeting-Intellegence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your keys
nano .env  # or use any editor
```

Required API keys:
- **OPENAI_API_KEY**: Get from https://platform.openai.com/api-keys

Optional (for speaker diarization):
- **HF_TOKEN**: Get from https://huggingface.co/settings/tokens (accept pyannote model terms)

Optional (for ticket creation):
- **JIRA_URL**, **JIRA_EMAIL**, **JIRA_API_TOKEN**
- **ASANA_API_TOKEN**, **ASANA_WORKSPACE_GID**, **ASANA_PROJECT_GID**

## 3. Start the Agent

```bash
# Start listening for meetings
python -m src.main start
```

That's it! The agent will now:
- Detect when voice/meeting activity begins
- Automatically start recording
- Transcribe speech in real-time
- Generate meeting notes when the meeting ends
- Extract action items
- Save everything to a local database

## 4. Common Commands

```bash
# List recent meetings
python -m src.main list-meetings

# View a specific meeting
python -m src.main show-meeting <meeting_id>

# Ask questions about past meetings
python -m src.main query "What was decided about the API?"

# List action items
python -m src.main list-actions

# Export meeting notes
python -m src.main export <meeting_id> --format markdown

# Export action items to Jira
python -m src.main export-actions <meeting_id> --target jira
```

## 5. Configuration

Edit `config.yaml` to customize:

```yaml
# Increase sensitivity to detect softer voices
audio:
  sensitivity: 0.2  # Lower = more sensitive

# Use larger Whisper model for better accuracy
ai:
  whisper_model: "medium"  # Options: tiny, base, small, medium, large

# Generate briefer summaries
notes:
  summary_style: "brief"
```

## Troubleshooting

### No audio devices found
```bash
# List available devices
python -m src.main devices
```

### Low transcription quality
- Try a larger Whisper model (`small`, `medium`, or `large`)
- Ensure microphone quality is good
- Reduce background noise

### High CPU usage
- Use a smaller Whisper model (`tiny` or `base`)
- Enable GPU acceleration if available

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Configure Jira/Asana integration for automatic ticket creation
- Set up speaker diarization with pyannote for speaker identification
