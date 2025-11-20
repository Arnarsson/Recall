"""
Claude conversation log parser for extracting AI chat history.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Iterator
from .models import ClaudeLogEntry, TimelineEvent


class ClaudeLogParser:
    """Parser for Claude Code conversation logs."""
    
    def __init__(self, logs_path: Optional[Path] = None):
        """Initialize parser with logs directory path."""
        if logs_path is None:
            logs_path = Path.home() / ".claude" / "projects"
        
        self.logs_path = Path(logs_path)
        self.logger = logging.getLogger(__name__)
        
        if not self.logs_path.exists():
            self.logger.warning(f"Claude logs directory not found: {self.logs_path}")
    
    def get_recent_entries(self, hours: int = 24) -> List[ClaudeLogEntry]:
        """Get recent Claude conversation entries."""
        from datetime import timedelta
        since = datetime.now() - timedelta(hours=hours)
        return self.get_entries_since(since)
    
    def get_entries_since(self, since_date: datetime) -> List[ClaudeLogEntry]:
        """Get Claude entries since a specific date."""
        entries = []
        
        if not self.logs_path.exists():
            return entries
        
        # Find all JSONL files
        jsonl_files = list(self.logs_path.glob("*.jsonl"))
        
        for jsonl_file in jsonl_files:
            try:
                file_entries = self._parse_jsonl_file(jsonl_file, since_date)
                entries.extend(file_entries)
            except Exception as e:
                self.logger.error(f"Error parsing {jsonl_file}: {e}")
        
        # Sort by timestamp
        entries.sort(key=lambda x: x.timestamp)
        return entries
    
    def _parse_jsonl_file(self, file_path: Path, since_date: datetime) -> List[ClaudeLogEntry]:
        """Parse a single JSONL file."""
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        if line.strip():  # Skip empty lines
                            entry = self._parse_jsonl_line(line.strip())
                            if entry and entry.timestamp >= since_date:
                                entries.append(entry)
                    except Exception as e:
                        self.logger.debug(f"Error parsing line {line_num} in {file_path}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
        
        return entries
    
    def _parse_jsonl_line(self, line: str) -> Optional[ClaudeLogEntry]:
        """Parse a single JSONL line into ClaudeLogEntry."""
        try:
            data = json.loads(line)
            
            # Skip non-message entries
            if data.get("type") != "user" or "message" not in data:
                return None
            
            message = data["message"]
            
            # Parse timestamp
            timestamp_str = data.get("timestamp")
            if timestamp_str:
                # Handle various timestamp formats
                try:
                    if timestamp_str.endswith('Z'):
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    # Try parsing as Unix timestamp
                    timestamp = datetime.fromtimestamp(float(timestamp_str))
            else:
                return None
            
            # Extract message content and type
            content = message.get("content", "")
            role = message.get("role", "user")
            
            # Map role to message_type
            message_type = "user" if role == "user" else "assistant"
            
            entry = ClaudeLogEntry(
                uuid=data.get("uuid", ""),
                session_id=data.get("sessionId", ""),
                timestamp=timestamp,
                message_type=message_type,
                content=content,
                cwd=data.get("cwd"),
                git_branch=data.get("gitBranch"),
                parent_uuid=data.get("parentUuid"),
                user_type=data.get("userType", "external"),
                version=data.get("version")
            )
            
            return entry
            
        except Exception as e:
            self.logger.debug(f"Error parsing JSONL line: {e}")
            return None
    
    def get_conversations(self, session_id: Optional[str] = None) -> Dict[str, List[ClaudeLogEntry]]:
        """Get conversations grouped by session ID."""
        all_entries = self.get_entries_since(datetime(2020, 1, 1))  # Get all entries
        
        conversations = {}
        for entry in all_entries:
            if session_id is None or entry.session_id == session_id:
                if entry.session_id not in conversations:
                    conversations[entry.session_id] = []
                conversations[entry.session_id].append(entry)
        
        # Sort entries within each conversation
        for session_entries in conversations.values():
            session_entries.sort(key=lambda x: x.timestamp)
        
        return conversations
    
    def to_timeline_events(self, entries: List[ClaudeLogEntry]) -> List[TimelineEvent]:
        """Convert Claude log entries to timeline events."""
        events = []
        
        for entry in entries:
            # Create title based on message type and content
            if entry.message_type == "user":
                title = "Claude Conversation (User)"
                # Use first line or first 60 chars as title
                first_line = entry.content.split('\n')[0]
                if len(first_line) > 60:
                    title = f"Asked Claude: {first_line[:57]}..."
                else:
                    title = f"Asked Claude: {first_line}"
            else:
                title = "Claude Conversation (Assistant)"
                first_line = entry.content.split('\n')[0]
                if len(first_line) > 60:
                    title = f"Claude replied: {first_line[:57]}..."
                else:
                    title = f"Claude replied: {first_line}"
            
            # Generate tags
            tags = ["claude", "ai-chat", entry.message_type]
            
            # Add context tags
            if entry.cwd:
                tags.append("coding")
            if entry.git_branch:
                tags.append("git")
            
            # Add content-based tags
            content_lower = entry.content.lower()
            if any(word in content_lower for word in ["error", "bug", "fix", "debug"]):
                tags.append("debugging")
            if any(word in content_lower for word in ["implement", "create", "build", "develop"]):
                tags.append("development")
            if any(word in content_lower for word in ["explain", "how", "what", "why"]):
                tags.append("question")
            
            event = TimelineEvent(
                timestamp=entry.timestamp,
                source="claude",
                title=title,
                text=entry.content,
                conversation_id=entry.session_id,
                message_type=entry.message_type,
                tags=tags,
                metadata={
                    "uuid": entry.uuid,
                    "session_id": entry.session_id,
                    "parent_uuid": entry.parent_uuid,
                    "cwd": entry.cwd,
                    "git_branch": entry.git_branch,
                    "user_type": entry.user_type,
                    "version": entry.version
                }
            )
            
            events.append(event)
        
        return events
    
    def search_conversations(self, query: str, limit: int = 50) -> List[ClaudeLogEntry]:
        """Search conversations by content."""
        all_entries = self.get_entries_since(datetime(2020, 1, 1))
        
        query_lower = query.lower()
        matching_entries = []
        
        for entry in all_entries:
            if query_lower in entry.content.lower():
                matching_entries.append(entry)
        
        # Sort by relevance (timestamp for now)
        matching_entries.sort(key=lambda x: x.timestamp, reverse=True)
        
        return matching_entries[:limit]
    
    def get_conversation_context(self, entry: ClaudeLogEntry, context_messages: int = 3) -> List[ClaudeLogEntry]:
        """Get conversation context around a specific entry."""
        conversations = self.get_conversations(entry.session_id)
        session_entries = conversations.get(entry.session_id, [])
        
        # Find the index of the current entry
        try:
            current_index = next(i for i, e in enumerate(session_entries) if e.uuid == entry.uuid)
        except StopIteration:
            return [entry]
        
        # Get context around the entry
        start_index = max(0, current_index - context_messages)
        end_index = min(len(session_entries), current_index + context_messages + 1)
        
        return session_entries[start_index:end_index]
    
    def export_conversations(self, output_path: Path, since_date: Optional[datetime] = None) -> int:
        """Export conversations to JSON file."""
        if since_date is None:
            since_date = datetime(2020, 1, 1)
        
        entries = self.get_entries_since(since_date)
        conversations = {}
        
        for entry in entries:
            if entry.session_id not in conversations:
                conversations[entry.session_id] = []
            conversations[entry.session_id].append(entry.dict())
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "source": "claude",
            "conversations": conversations,
            "total_entries": len(entries),
            "total_conversations": len(conversations)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return len(entries)