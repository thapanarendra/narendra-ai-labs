# Always-On Meeting Intelligence Agent

An autonomous AI-powered meeting intelligence system that captures, transcribes, analyzes, and extracts actionable insights from meetings in real-time.

## 🎯 Features

### 1. **Autonomous Audio Detection & Recording**
- Automatically detects when meetings or voice activity begins
- Records audio for future reference
- Supports system audio capture and microphone input

### 2. **Real-Time Transcription**
- Live speech-to-text using OpenAI Whisper
- High accuracy transcription with timestamp support

### 3. **Speaker Identification (Diarization)**
- Identifies and labels different speakers
- Tracks speaker statistics and participation

### 4. **AI-Powered Meeting Notes**
- Generates structured summaries
- Highlights key discussion points
- Identifies decisions made

### 5. **Automated Action Item Extraction**
- Extracts tasks, deadlines, and assignments
- Creates structured tickets automatically
- Integrates with Jira and Asana

### 6. **Post-Meeting Query Interface**
- Ask questions about past meetings
- Get instant, cited answers
- Search across meeting history

## 📁 Project Structure

```
Always-On-Meeting-Intellegence/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Main orchestrator
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── detector.py            # Audio activity detection
│   │   ├── recorder.py            # Audio recording
│   │   └── audio_utils.py         # Audio utilities
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── transcriber.py         # Speech-to-text
│   │   └── speaker_diarization.py # Speaker identification
│   ├── intelligence/
│   │   ├── __init__.py
│   │   ├── notes_generator.py     # AI meeting notes
│   │   ├── action_extractor.py    # Action item extraction
│   │   └── query_engine.py        # Meeting query interface
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── jira_integration.py    # Jira connector
│   │   └── asana_integration.py   # Asana connector
│   ├── storage/
│   │   ├── __init__.py
│   │   └── database.py            # Meeting storage
│   └── config/
│       ├── __init__.py
│       └── settings.py            # Configuration
├── data/
│   ├── recordings/                # Audio recordings
│   ├── transcripts/               # Meeting transcripts
│   └── meetings.db                # SQLite database
├── tests/
│   └── ...
├── requirements.txt
├── config.yaml
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- FFmpeg (for audio processing)
- OpenAI API key (for Whisper and GPT)

### Installation

```bash
# Clone or navigate to the project
cd Always-On-Meeting-Intellegence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure settings
cp config.yaml.example config.yaml
# Edit config.yaml with your API keys
```

### Running the Agent

```bash
# Start the always-on meeting intelligence agent
python -m src.main start

# Start with specific options
python -m src.main start --input microphone --sensitivity high

# Query past meetings
python -m src.main query "What was discussed about the API redesign?"

# View meeting history
python -m src.main list-meetings

# Export action items to Jira
python -m src.main export-actions --meeting-id <id> --target jira
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
# Audio settings
audio:
  input: "system"  # system, microphone, or both
  sensitivity: 0.3  # Voice activity detection threshold
  sample_rate: 16000

# AI settings
ai:
  openai_api_key: "your-api-key"
  model: "gpt-4o"
  whisper_model: "base"  # tiny, base, small, medium, large

# Storage
storage:
  recordings_path: "./data/recordings"
  database_path: "./data/meetings.db"

# Integrations
integrations:
  jira:
    enabled: false
    url: "https://your-domain.atlassian.net"
    api_token: ""
  asana:
    enabled: false
    api_token: ""
```

## 🔧 API Reference

### MeetingIntelligenceAgent

```python
from src.main import MeetingIntelligenceAgent

# Initialize the agent
agent = MeetingIntelligenceAgent()

# Start listening
agent.start()

# Query meetings
results = agent.query("What did John say about deadlines?")

# Get action items
actions = agent.get_action_items(meeting_id="...")

# Stop the agent
agent.stop()
```

## 📊 Meeting Data Model

```python
Meeting:
  - id: str
  - title: str
  - start_time: datetime
  - end_time: datetime
  - duration: int (seconds)
  - recording_path: str
  - transcript: List[TranscriptSegment]
  - speakers: List[Speaker]
  - summary: str
  - action_items: List[ActionItem]
  - key_points: List[str]

ActionItem:
  - id: str
  - description: str
  - assignee: str (optional)
  - deadline: datetime (optional)
  - priority: str
  - status: str
  - source_quote: str
```

## 🛠️ Development

```bash
# Run tests
pytest tests/

# Run with debug logging
python -m src.main start --debug

# Development mode (auto-reload)
python -m src.main start --dev
```

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.
