"""
Archive manager for automatically backing up WindRecorder data to Hetzner server.
"""

import json
import gzip
import logging
import paramiko
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from io import BytesIO
import sqlite3
import shutil

from .models import ArchiveStatus, AppConfig
from .windrecorder_client import WindRecorderClient
from .claude_parser import ClaudeLogParser


class ArchiveManager:
    """Manages archiving of WindRecorder and Claude data to Hetzner server."""
    
    def __init__(self, config: AppConfig):
        """Initialize archive manager with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize clients
        self.windrecorder = WindRecorderClient(config.windrecorder_db_path)
        self.claude_parser = ClaudeLogParser(config.claude_logs_path)
        
        # Ensure directories exist
        config.ensure_directories()
        
        self.last_check = datetime.now()
        self.upload_progress = 0.0
    
    def should_archive(self) -> tuple[bool, str]:
        """Check if archiving is needed based on size and age thresholds."""
        try:
            # Check database size
            size_mb = self.windrecorder.get_database_size()
            if size_mb >= self.config.max_size_mb:
                return True, f"Size threshold reached: {size_mb:.1f}MB >= {self.config.max_size_mb}MB"
            
            # Check database age
            age_days = self.windrecorder.get_database_age()
            if age_days >= self.config.max_age_days:
                return True, f"Age threshold reached: {age_days} days >= {self.config.max_age_days} days"
            
            return False, f"No archiving needed (Size: {size_mb:.1f}MB, Age: {age_days} days)"
            
        except Exception as e:
            self.logger.error(f"Error checking archive status: {e}")
            return False, f"Error checking status: {e}"
    
    def get_status(self) -> ArchiveStatus:
        """Get current archive status."""
        try:
            size_mb = self.windrecorder.get_database_size()
            age_days = self.windrecorder.get_database_age()
            
            # Estimate next archive time
            next_archive = None
            if age_days < self.config.max_age_days:
                days_until_archive = self.config.max_age_days - age_days
                next_archive = datetime.now() + timedelta(days=days_until_archive)
            
            # Count remote archives
            remote_count = 0
            try:
                remote_count = len(self.list_remote_archives())
            except Exception:
                pass  # Ignore if can't connect to remote
            
            return ArchiveStatus(
                database_size_mb=size_mb,
                database_age_days=age_days,
                next_archive_estimate=next_archive,
                remote_archives_count=remote_count,
                upload_progress=self.upload_progress
            )
            
        except Exception as e:
            self.logger.error(f"Error getting archive status: {e}")
            return ArchiveStatus(
                database_size_mb=0.0,
                database_age_days=0,
                remote_archives_count=0
            )
    
    def check_and_archive(self) -> bool:
        """Check if archiving is needed and perform it if so."""
        if not self.config.auto_archive:
            return False
        
        should_archive, reason = self.should_archive()
        self.logger.info(f"Archive check: {reason}")
        
        if should_archive:
            return self.create_and_upload_archive()
        
        return False
    
    def create_and_upload_archive(self) -> bool:
        """Create archive and upload to Hetzner server."""
        try:
            self.logger.info("Starting archive creation...")
            self.upload_progress = 0.0
            
            # Create archive file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"recall_archive_{timestamp}.json"
            archive_path = self.config.temp_dir / archive_name
            
            # Export data
            self.upload_progress = 0.1
            archive_data = self._create_archive_data()
            
            self.upload_progress = 0.3
            self._write_archive_file(archive_data, archive_path)
            
            self.upload_progress = 0.5
            
            # Compress archive
            compressed_path = self._compress_archive(archive_path)
            
            self.upload_progress = 0.7
            
            # Upload to Hetzner
            success = self._upload_to_hetzner(compressed_path)
            
            self.upload_progress = 1.0 if success else 0.0
            
            # Cleanup temporary files
            self._cleanup_temp_files([archive_path, compressed_path])
            
            if success:
                self.logger.info(f"Archive uploaded successfully: {compressed_path.name}")
                # Optionally reset/cleanup local database after successful upload
                # self._cleanup_local_data()
            else:
                self.logger.error("Archive upload failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating archive: {e}")
            self.upload_progress = 0.0
            return False
    
    def _create_archive_data(self) -> Dict[str, Any]:
        """Create archive data structure."""
        # Get WindRecorder data
        windrecorder_records = self.windrecorder.get_records_since(
            datetime.now() - timedelta(days=self.config.max_age_days * 2)
        )
        
        # Get Claude data
        claude_entries = self.claude_parser.get_entries_since(
            datetime.now() - timedelta(days=self.config.max_age_days * 2)
        )
        
        archive_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "source": "recall_app",
                "version": "1.0.0",
                "config": {
                    "max_size_mb": self.config.max_size_mb,
                    "max_age_days": self.config.max_age_days
                }
            },
            "windrecorder": {
                "records_count": len(windrecorder_records),
                "records": [record.dict() for record in windrecorder_records],
                "database_files": [str(f) for f in self.windrecorder.db_files]
            },
            "claude": {
                "entries_count": len(claude_entries),
                "entries": [entry.dict() for entry in claude_entries],
                "conversations": self.claude_parser.get_conversations()
            },
            "statistics": {
                "total_events": len(windrecorder_records) + len(claude_entries),
                "date_range": {
                    "start": min(
                        min([r.timestamp for r in windrecorder_records], default=datetime.now()),
                        min([e.timestamp for e in claude_entries], default=datetime.now())
                    ).isoformat(),
                    "end": max(
                        max([r.timestamp for r in windrecorder_records], default=datetime.now()),
                        max([e.timestamp for e in claude_entries], default=datetime.now())
                    ).isoformat()
                }
            }
        }
        
        return archive_data
    
    def _write_archive_file(self, data: Dict[str, Any], file_path: Path):
        """Write archive data to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"Archive file created: {file_path} ({file_path.stat().st_size / 1024 / 1024:.1f}MB)")
    
    def _compress_archive(self, file_path: Path) -> Path:
        """Compress archive file with gzip."""
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Calculate compression ratio
        original_size = file_path.stat().st_size
        compressed_size = compressed_path.stat().st_size
        ratio = (1 - compressed_size / original_size) * 100
        
        self.logger.info(f"Archive compressed: {compressed_size / 1024 / 1024:.1f}MB ({ratio:.1f}% reduction)")
        
        return compressed_path
    
    def _upload_to_hetzner(self, file_path: Path) -> bool:
        """Upload file to Hetzner server via SFTP."""
        if not self.config.hetzner_host or not self.config.hetzner_user:
            self.logger.warning("Hetzner configuration not set, skipping upload")
            return False
        
        try:
            # Setup SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Use SSH key authentication
            if self.config.ssh_key_path.exists():
                pkey = paramiko.RSAKey.from_private_key_file(str(self.config.ssh_key_path))
                ssh.connect(
                    self.config.hetzner_host,
                    username=self.config.hetzner_user,
                    pkey=pkey,
                    timeout=30
                )
            else:
                self.logger.error(f"SSH key not found: {self.config.ssh_key_path}")
                return False
            
            # Upload via SFTP
            sftp = ssh.open_sftp()
            
            # Ensure remote directory exists
            try:
                sftp.chdir(self.config.remote_backup_dir)
            except IOError:
                # Directory doesn't exist, try to create it
                try:
                    sftp.mkdir(self.config.remote_backup_dir)
                    sftp.chdir(self.config.remote_backup_dir)
                except Exception as e:
                    self.logger.error(f"Cannot create remote directory: {e}")
                    return False
            
            # Upload file
            remote_path = f"{self.config.remote_backup_dir}/{file_path.name}"
            sftp.put(str(file_path), remote_path)
            
            # Verify upload
            remote_stats = sftp.stat(remote_path)
            local_size = file_path.stat().st_size
            
            sftp.close()
            ssh.close()
            
            if remote_stats.st_size == local_size:
                self.logger.info(f"Upload verified: {remote_stats.st_size} bytes")
                return True
            else:
                self.logger.error(f"Upload verification failed: {remote_stats.st_size} != {local_size}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error uploading to Hetzner: {e}")
            return False
    
    def _cleanup_temp_files(self, file_paths: List[Path]):
        """Clean up temporary files."""
        for file_path in file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
                    self.logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                self.logger.warning(f"Error cleaning up {file_path}: {e}")
    
    def list_remote_archives(self) -> List[str]:
        """List available archives on Hetzner server."""
        if not self.config.hetzner_host or not self.config.hetzner_user:
            return []
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            pkey = paramiko.RSAKey.from_private_key_file(str(self.config.ssh_key_path))
            ssh.connect(
                self.config.hetzner_host,
                username=self.config.hetzner_user,
                pkey=pkey,
                timeout=30
            )
            
            sftp = ssh.open_sftp()
            files = sftp.listdir(self.config.remote_backup_dir)
            
            # Filter for archive files
            archives = [f for f in files if f.startswith('recall_archive_') and f.endswith('.json.gz')]
            archives.sort(reverse=True)  # Most recent first
            
            sftp.close()
            ssh.close()
            
            return archives
            
        except Exception as e:
            self.logger.error(f"Error listing remote archives: {e}")
            return []
    
    def download_archive(self, archive_name: str) -> Optional[Dict[str, Any]]:
        """Download and decompress archive from Hetzner."""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            pkey = paramiko.RSAKey.from_private_key_file(str(self.config.ssh_key_path))
            ssh.connect(
                self.config.hetzner_host,
                username=self.config.hetzner_user,
                pkey=pkey,
                timeout=30
            )
            
            sftp = ssh.open_sftp()
            
            # Download to memory
            remote_path = f"{self.config.remote_backup_dir}/{archive_name}"
            file_obj = BytesIO()
            sftp.getfo(remote_path, file_obj)
            file_obj.seek(0)
            
            # Decompress and parse
            with gzip.open(file_obj, 'rb') as f:
                data = json.loads(f.read().decode('utf-8'))
            
            sftp.close()
            ssh.close()
            
            self.logger.info(f"Downloaded archive: {archive_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error downloading archive {archive_name}: {e}")
            return None
    
    def force_archive(self) -> bool:
        """Force archive creation regardless of thresholds."""
        self.logger.info("Forcing archive creation...")
        return self.create_and_upload_archive()
    
    def test_connection(self) -> bool:
        """Test connection to Hetzner server."""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            pkey = paramiko.RSAKey.from_private_key_file(str(self.config.ssh_key_path))
            ssh.connect(
                self.config.hetzner_host,
                username=self.config.hetzner_user,
                pkey=pkey,
                timeout=10
            )
            
            ssh.close()
            self.logger.info("Hetzner connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Hetzner connection test failed: {e}")
            return False