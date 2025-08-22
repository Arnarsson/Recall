"""
Data models for the Recall application.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path


class TimelineEvent(BaseModel):
    """Unified timeline event from any source."""
    
    timestamp: datetime
    source: str = Field(..., description="Source: windrecorder, claude, chatgpt")
    title: str
    text: str
    
    # Visual content (for WindRecorder events)
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    ocr_text: Optional[str] = None
    
    # Web context
    page_title: Optional[str] = None
    browser_url: Optional[str] = None
    
    # Chat context (for AI logs)
    conversation_id: Optional[str] = None
    message_type: Optional[str] = None  # user, assistant
    
    # Metadata
    duration: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Search relevance (populated by search engine)
    relevance_score: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchResult(BaseModel):
    """Search result with context and relevance."""
    
    event: TimelineEvent
    relevance_score: float
    matched_text: str
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    visual_preview: Optional[str] = None  # Base64 encoded thumbnail


class ArchiveStatus(BaseModel):
    """Status of the archive system."""
    
    database_size_mb: float
    database_age_days: int
    last_archive: Optional[datetime] = None
    next_archive_estimate: Optional[datetime] = None
    remote_archives_count: int
    pending_upload: bool = False
    upload_progress: float = 0.0


class AppConfig(BaseModel):
    """Application configuration."""
    
    # WindRecorder settings
    windrecorder_db_path: Path = Path("~/WindRecorder/userdata/db").expanduser()
    claude_logs_path: Path = Path("~/.claude/projects").expanduser()
    
    # Archive settings
    max_size_mb: int = 5000  # 5GB
    max_age_days: int = 30
    
    # Hetzner settings
    hetzner_host: Optional[str] = None
    hetzner_user: Optional[str] = None
    ssh_key_path: Path = Path("~/.ssh/id_rsa").expanduser()
    remote_backup_dir: str = "/var/backups/windrecorder"
    
    # Local settings
    app_data_dir: Path = Path("~/Library/Application Support/Recall").expanduser()
    chroma_db_path: Path = app_data_dir / "chroma_db"
    temp_dir: Path = app_data_dir / "temp"
    
    # UI settings
    search_limit: int = 50
    timeline_hours: int = 24
    notification_enabled: bool = True
    auto_archive: bool = True
    
    # Search settings
    embedding_model: str = "all-MiniLM-L6-v2"
    search_threshold: float = 0.3
    
    class Config:
        json_encoders = {
            Path: lambda v: str(v)
        }
    
    def ensure_directories(self):
        """Create necessary directories."""
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_db_path.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


class WindRecorderRecord(BaseModel):
    """Raw record from WindRecorder database."""
    
    id: int
    timestamp: datetime
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    ocr_text: Optional[str] = None
    page_title: Optional[str] = None
    browser_url: Optional[str] = None
    app_name: Optional[str] = None
    window_title: Optional[str] = None
    active_duration: Optional[float] = None


class ClaudeLogEntry(BaseModel):
    """Parsed Claude conversation log entry."""
    
    uuid: str
    session_id: str
    timestamp: datetime
    message_type: str  # "user" or "assistant" 
    content: str
    cwd: Optional[str] = None
    git_branch: Optional[str] = None
    
    # Metadata from JSONL
    parent_uuid: Optional[str] = None
    user_type: str = "external"
    version: Optional[str] = None