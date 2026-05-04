"""
Configuration management for Naukri Profile Tracker.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Naukri Credentials
    naukri_email: str = Field(..., description="Naukri.com login email")
    naukri_password: SecretStr = Field(..., description="Naukri.com login password")
    
    # Resume Configuration
    resume_path: Path = Field(
        default=Path("./resume.pdf"),
        description="Path to your resume file"
    )
    
    # Notification Settings
    notification_enabled: bool = Field(default=True)
    notification_email: Optional[str] = Field(default=None)
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_username: Optional[str] = Field(default=None)
    smtp_password: Optional[SecretStr] = Field(default=None)
    
    # Agent Configuration
    headless_mode: bool = Field(
        default=True,
        description="Run browser in headless mode"
    )
    update_frequency_days: int = Field(
        default=2,
        description="Resume update frequency in days"
    )
    recruiter_check_hours: int = Field(
        default=6,
        description="Recruiter activity check frequency in hours"
    )
    log_level: str = Field(default="INFO")
    
    # Database
    database_path: Path = Field(
        default=Path("./data/naukri_tracker.db"),
        description="SQLite database path"
    )
    
    # Browser state persistence
    browser_state_path: Path = Field(
        default=Path("./browser_state"),
        description="Path to store browser session state"
    )
    
    @property
    def logs_dir(self) -> Path:
        """Get logs directory path."""
        return Path("./logs")
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return Path("./data")
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.browser_state_path.mkdir(parents=True, exist_ok=True)


class NaukriURLs:
    """Naukri.com URL endpoints."""
    
    BASE = "https://www.naukri.com"
    LOGIN = f"{BASE}/nlogin/login"
    HOME = f"{BASE}/mnjuser/homepage"
    PROFILE = f"{BASE}/mnjuser/profile"
    RESUME = f"{BASE}/mnjuser/profile?id=uploadResume"
    RECRUITER_ACTIVITY = f"{BASE}/mnjuser/recruiteractivity"
    JOB_RECOMMENDATIONS = f"{BASE}/mnjuser/recommendedjobs"
    APPLICATIONS = f"{BASE}/mnjuser/appliedjobs"
    MESSAGES = f"{BASE}/mnjuser/inbox"
    PROFILE_PERFORMANCE = f"{BASE}/mnjuser/profile-performance"
    UPDATE_HEADLINE = f"{BASE}/mnjuser/profile?id=resumeHeadline"


# Global settings instance
def get_settings() -> Settings:
    """Get settings instance, loading from .env file."""
    return Settings()


# Naukri page selectors - CSS/XPath selectors for various elements
class NaukriSelectors:
    """CSS/XPath selectors for Naukri.com elements."""
    
    # Login Page
    LOGIN_EMAIL_INPUT = 'input[placeholder*="Email"]'
    LOGIN_PASSWORD_INPUT = 'input[placeholder*="Password"], input[type="password"]'
    LOGIN_SUBMIT_BUTTON = 'button[type="submit"], button:has-text("Login")'
    LOGIN_ERROR_MESSAGE = '.error-msg, .login-error'
    
    # Dashboard
    PROFILE_COMPLETION = '.profile-completion, .profileCompleteness'
    USER_NAME = '.nI-gNb-sb__main, .user-name'
    
    # Resume Upload
    RESUME_UPLOAD_SECTION = '#lazyResumeHead, .resumeUploadWrap'
    RESUME_UPLOAD_INPUT = 'input[type="file"][accept*="pdf"]'
    RESUME_UPLOAD_BUTTON = 'input[type="file"], .upload-btn'
    RESUME_UPDATE_SUCCESS = '.update-success, .success-message'
    RESUME_HEADLINE_EDIT = '.resumeHeadline .edit, #resumeHeadlineEdit'
    RESUME_HEADLINE_INPUT = 'textarea#resumeHeadlineTxt, .headline-textarea'
    RESUME_HEADLINE_SAVE = '.resumeHeadline button[type="submit"], #resumeHeadlineSave'
    
    # Recruiter Activity
    RECRUITER_VIEW_COUNT = '.recruiter-views, .profileViews'
    RECRUITER_VIEW_LIST = '.recruiter-view-item, .viewItem'
    RECRUITER_MESSAGE_COUNT = '.inbox-count, .messageCount'
    RECRUITER_MESSAGES = '.inbox-item, .messageItem'
    INTERVIEW_REQUESTS = '.interview-request, .interviewItem'
    
    # Job Recommendations
    JOB_CARDS = '.jobTuple, .job-card'
    JOB_TITLE = '.title, .job-title'
    JOB_COMPANY = '.company-name, .companyName'
    JOB_LOCATION = '.location, .loc'
    JOB_SALARY = '.salary, .sal'
    JOB_EXPERIENCE = '.experience, .exp'
    JOB_APPLY_BUTTON = '.apply-btn, button:has-text("Apply")'
    
    # Applications
    APPLICATION_ITEMS = '.applied-job, .applicationItem'
    APPLICATION_STATUS = '.application-status, .status'
    APPLICATION_DATE = '.applied-date, .date'
    
    # Profile
    PROFILE_VIEWS_STAT = '.profile-views, .viewsCount'
    SEARCH_APPEARANCES = '.search-appearances, .searchAppearances'
    RECRUITER_ACTIONS = '.recruiter-actions, .recruiterActions'
    
    # Navigation
    PROFILE_MENU = '.nI-gNb-sb, .profile-menu'
    LOGOUT_BUTTON = 'a:has-text("Logout"), .logout-btn'


# Activity types for tracking
class ActivityType:
    """Types of activities tracked by the agent."""
    
    RESUME_UPDATE = "resume_update"
    PROFILE_VIEW = "profile_view"
    RECRUITER_MESSAGE = "recruiter_message"
    JOB_APPLICATION = "job_application"
    INTERVIEW_REQUEST = "interview_request"
    LOGIN = "login"
    JOB_RECOMMENDATION = "job_recommendation"
