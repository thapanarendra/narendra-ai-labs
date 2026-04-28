# Always-On Meeting Intelligence Agent

## Agent Description

An autonomous AI agent that ensures your presence is felt in every discussion, even when you're not physically present. This agent continuously monitors for voice activity and automatically captures, transcribes, analyzes, and extracts actionable insights from meetings in real-time.

## Core Capabilities

### 1. Autonomous Notetaking
- **Voice Activity Detection**: Automatically detects when meetings or conversations begin
- **Continuous Recording**: Records audio for reference without manual intervention
- **Real-time Transcription**: Live speech-to-text using OpenAI Whisper
- **Speaker Identification**: Uses pyannote.audio for speaker diarization

### 2. Intelligent Analysis
- **Meeting Summaries**: Generates structured summaries with key points and decisions
- **Speaker Attribution**: Tracks who said what throughout the meeting
- **Language Detection**: Automatically identifies the spoken language

### 3. Action Item Extraction
- **Automatic Detection**: Identifies tasks, commitments, and follow-ups from discussion
- **Assignment Recognition**: Detects who is responsible for each action
- **Deadline Parsing**: Extracts due dates from natural language
- **Priority Assessment**: Determines urgency based on context

### 4. Post-Meeting Intelligence
- **Semantic Search**: Query past meetings using natural language
- **Cited Answers**: Get answers with specific references to when/who said something
- **Cross-Meeting Insights**: Find patterns and information across multiple meetings

### 5. Integration Capabilities
- **Jira Integration**: Automatically create issues from action items
- **Asana Integration**: Push tasks directly to Asana projects
- **Export Options**: Markdown, JSON, or plain text exports

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Meeting Intelligence Agent                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Audio     │───▶│ Transcription│───▶│   AI Intelligence   │ │
│  │  Detection  │    │   Engine    │    │   (Notes/Actions)   │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                  │                      │              │
│         ▼                  ▼                      ▼              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Recorder   │    │  Speaker    │    │   Query Engine      │ │
│  │             │    │ Diarization │    │   (Search/Q&A)      │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                  │                      │              │
│         └──────────────────┼──────────────────────┘              │
│                            ▼                                      │
│                    ┌─────────────┐                               │
│                    │  Database   │                               │
│                    │  Storage    │                               │
│                    └─────────────┘                               │
│                            │                                      │
│              ┌─────────────┼─────────────┐                       │
│              ▼             ▼             ▼                       │
│        ┌─────────┐   ┌─────────┐   ┌─────────┐                  │
│        │  Jira   │   │  Asana  │   │ Export  │                  │
│        └─────────┘   └─────────┘   └─────────┘                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Behaviors

### Autonomous Mode
When started, the agent operates autonomously:
1. Continuously monitors audio input for voice activity
2. When voice is detected for sufficient duration, begins recording
3. Transcribes audio in real-time
4. When silence persists, ends the meeting session
5. Processes transcript to generate notes and extract actions
6. Stores everything in database and vector store
7. Optionally creates tickets in Jira/Asana

### Interactive Mode
Users can interact with the agent via CLI:
- Query past meetings with natural language questions
- View meeting summaries and transcripts
- List and manage action items
- Export data in various formats
- Configure agent settings

## Required APIs

| API | Purpose | Required |
|-----|---------|----------|
| OpenAI | Whisper transcription, GPT analysis | Yes |
| Hugging Face | Speaker diarization (pyannote) | No (falls back to simple) |
| Jira | Issue creation | No |
| Asana | Task creation | No |

## Privacy & Security

- All data is stored locally by default
- Audio recordings are saved to configurable path
- API keys stored in environment variables
- No data sent to external services except configured APIs

## Performance Considerations

- **CPU**: Transcription can be CPU-intensive; GPU recommended for large models
- **Memory**: Larger Whisper models require more RAM
- **Storage**: Audio recordings can consume significant disk space
- **Network**: Minimal bandwidth needed (only for API calls)

## Extending the Agent

The agent is designed to be extensible:
- Add new integrations by implementing the integration interface
- Customize transcription with different speech-to-text providers
- Extend action extraction with domain-specific patterns
- Build custom query interfaces on top of the search engine
