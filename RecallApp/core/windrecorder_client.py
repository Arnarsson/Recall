"""
WindRecorder database client for accessing screen recordings and OCR data.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models import WindRecorderRecord, TimelineEvent


class WindRecorderClient:
    """Client for accessing WindRecorder SQLite database."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize client with database path."""
        if db_path is None:
            # Default WindRecorder path
            db_path = Path.home() / "WindRecorder" / "userdata" / "db"
        
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        
        # Discover database files (excluding temporary ones)
        self.db_files = self._find_database_files()
        
        if not self.db_files:
            self.logger.warning(f"No WindRecorder databases found at {self.db_path}")
    
    def _find_database_files(self) -> List[Path]:
        """Find all WindRecorder database files."""
        if not self.db_path.exists():
            return []
        
        db_files = []
        for db_file in self.db_path.glob("*.db"):
            # Skip temporary files created during indexing
            if "_TEMP_READ" not in db_file.name:
                db_files.append(db_file)
        
        return sorted(db_files)
    
    def _get_table_schema(self, db_file: Path) -> Dict[str, List[str]]:
        """Discover table schema from database."""
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                schema[table] = columns
            
            conn.close()
            return schema
            
        except Exception as e:
            self.logger.error(f"Error reading schema from {db_file}: {e}")
            return {}
    
    def get_recent_records(self, hours: int = 24) -> List[WindRecorderRecord]:
        """Get recent WindRecorder records."""
        since = datetime.now() - timedelta(hours=hours)
        return self.get_records_since(since)
    
    def get_records_since(self, since_date: datetime) -> List[WindRecorderRecord]:
        """Get records since a specific date."""
        records = []
        
        for db_file in self.db_files:
            try:
                db_records = self._query_database(db_file, since_date)
                records.extend(db_records)
            except Exception as e:
                self.logger.error(f"Error querying {db_file}: {e}")
        
        # Sort by timestamp
        records.sort(key=lambda x: x.timestamp)
        return records
    
    def _query_database(self, db_file: Path, since_date: datetime) -> List[WindRecorderRecord]:
        """Query a specific database file."""
        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Discover schema for this database
        schema = self._get_table_schema(db_file)
        
        records = []
        
        # Try common table names and patterns
        possible_tables = [
            'recordings', 'events', 'activities', 'screenshots', 
            'ocr_data', 'window_data', 'browser_data'
        ]
        
        for table_name in schema.keys():
            if any(pt in table_name.lower() for pt in possible_tables):
                try:
                    table_records = self._query_table(cursor, table_name, schema[table_name], since_date)
                    records.extend(table_records)
                except Exception as e:
                    self.logger.debug(f"Error querying table {table_name}: {e}")
        
        conn.close()
        return records
    
    def _query_table(self, cursor, table_name: str, columns: List[str], since_date: datetime) -> List[WindRecorderRecord]:
        """Query a specific table and convert to WindRecorderRecord."""
        records = []
        
        # Find timestamp column (common names)
        timestamp_cols = ['timestamp', 'created_at', 'datetime', 'time', 'date']
        timestamp_col = None
        
        for col in timestamp_cols:
            if col in [c.lower() for c in columns]:
                timestamp_col = next(c for c in columns if c.lower() == col)
                break
        
        if not timestamp_col:
            self.logger.debug(f"No timestamp column found in {table_name}")
            return records
        
        # Build query
        query = f"SELECT * FROM {table_name} WHERE {timestamp_col} >= ?"
        
        try:
            cursor.execute(query, (since_date.isoformat(),))
            rows = cursor.fetchall()
            
            for row in rows:
                record = self._row_to_record(dict(row), timestamp_col)
                if record:
                    records.append(record)
                    
        except Exception as e:
            self.logger.debug(f"Error executing query on {table_name}: {e}")
        
        return records
    
    def _row_to_record(self, row: Dict[str, Any], timestamp_col: str) -> Optional[WindRecorderRecord]:
        """Convert database row to WindRecorderRecord."""
        try:
            # Parse timestamp
            timestamp_str = row.get(timestamp_col)
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.fromtimestamp(timestamp_str)
            
            # Map common column names
            record_data = {
                'id': row.get('id', 0),
                'timestamp': timestamp,
                'screenshot_path': self._find_value(row, ['screenshot_path', 'image_path', 'screenshot', 'image']),
                'video_path': self._find_value(row, ['video_path', 'video', 'clip_path']),
                'ocr_text': self._find_value(row, ['ocr_text', 'text', 'content', 'extracted_text']),
                'page_title': self._find_value(row, ['page_title', 'title', 'window_title']),
                'browser_url': self._find_value(row, ['browser_url', 'url', 'page_url']),
                'app_name': self._find_value(row, ['app_name', 'application', 'app', 'process_name']),
                'window_title': self._find_value(row, ['window_title', 'title', 'window_name']),
                'active_duration': self._find_value(row, ['duration', 'active_duration', 'time_active'])
            }
            
            return WindRecorderRecord(**record_data)
            
        except Exception as e:
            self.logger.debug(f"Error converting row to record: {e}")
            return None
    
    def _find_value(self, row: Dict[str, Any], possible_keys: List[str]) -> Optional[Any]:
        """Find value from row using possible key names."""
        for key in possible_keys:
            # Check exact match
            if key in row:
                return row[key]
            
            # Check case-insensitive match
            for row_key in row.keys():
                if row_key.lower() == key.lower():
                    return row[row_key]
        
        return None
    
    def to_timeline_events(self, records: List[WindRecorderRecord]) -> List[TimelineEvent]:
        """Convert WindRecorder records to timeline events."""
        events = []
        
        for record in records:
            # Create title from available data
            title = record.window_title or record.page_title or record.app_name or "Screen Activity"
            
            # Combine text from OCR and other sources
            text_parts = []
            if record.ocr_text:
                text_parts.append(record.ocr_text)
            if record.page_title and record.page_title != title:
                text_parts.append(f"Page: {record.page_title}")
            if record.browser_url:
                text_parts.append(f"URL: {record.browser_url}")
            
            text = " | ".join(text_parts) if text_parts else ""
            
            # Generate tags
            tags = ["windrecorder", "screen"]
            if record.app_name:
                tags.append(record.app_name.lower())
            if record.browser_url:
                tags.append("browser")
            if record.ocr_text:
                tags.append("ocr")
            
            event = TimelineEvent(
                timestamp=record.timestamp,
                source="windrecorder",
                title=title,
                text=text,
                screenshot_path=record.screenshot_path,
                video_path=record.video_path,
                ocr_text=record.ocr_text,
                page_title=record.page_title,
                browser_url=record.browser_url,
                duration=record.active_duration,
                tags=tags,
                metadata={
                    "app_name": record.app_name,
                    "window_title": record.window_title,
                    "record_id": record.id
                }
            )
            
            events.append(event)
        
        return events
    
    def get_database_size(self) -> float:
        """Get total size of all database files in MB."""
        total_size = 0
        
        for db_file in self.db_files:
            if db_file.exists():
                total_size += db_file.stat().st_size
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def get_database_age(self) -> int:
        """Get age of oldest database file in days."""
        if not self.db_files:
            return 0
        
        oldest_time = min(db_file.stat().st_mtime for db_file in self.db_files)
        oldest_date = datetime.fromtimestamp(oldest_time)
        age = datetime.now() - oldest_date
        
        return age.days
    
    def check_windrecorder_running(self) -> bool:
        """Check if WindRecorder is currently running."""
        import psutil
        
        for proc in psutil.process_iter(['name']):
            try:
                if 'windrecorder' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False