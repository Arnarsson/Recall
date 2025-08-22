"""
Configuration manager for loading settings from environment and config files.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from core.models import AppConfig


class ConfigManager:
    """Manages application configuration from multiple sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.home() / "Library" / "Application Support" / "Recall"
        self.config_file = self.config_dir / "config.json"
        
        # Load environment variables
        self.load_env_files()
    
    def load_env_files(self):
        """Load environment variables from .env files."""
        # Check for .env files in various locations
        env_locations = [
            Path.cwd() / ".env",  # Current directory
            self.config_dir / ".env",  # App config directory
            Path.home() / ".recall.env",  # Home directory
        ]
        
        for env_path in env_locations:
            if env_path.exists():
                load_dotenv(env_path)
                self.logger.info(f"Loaded environment from {env_path}")
    
    def load_config(self) -> AppConfig:
        """Load configuration from files and environment variables."""
        # Start with default configuration
        config_data = {}
        
        # Load from JSON config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                self.logger.info(f"Loaded config from {self.config_file}")
            except Exception as e:
                self.logger.error(f"Error loading config file: {e}")
        
        # Override with environment variables
        env_overrides = self.get_env_overrides()
        config_data.update(env_overrides)
        
        # Create AppConfig instance
        try:
            config = AppConfig(**config_data)
        except Exception as e:
            self.logger.warning(f"Error parsing config, using defaults: {e}")
            config = AppConfig()
        
        # Ensure directories exist
        config.ensure_directories()
        
        return config
    
    def get_env_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables."""
        overrides = {}
        
        # Map environment variables to config fields
        env_mappings = {
            # WindRecorder settings
            'WINDRECORDER_DB_PATH': ('windrecorder_db_path', Path),
            'CLAUDE_LOG_PATH': ('claude_logs_path', Path),
            
            # Archive settings
            'MAX_SIZE_MB': ('max_size_mb', int),
            'MAX_AGE_DAYS': ('max_age_days', int),
            
            # Hetzner settings
            'HETZNER_HOST': ('hetzner_host', str),
            'HETZNER_USER': ('hetzner_user', str),
            'SSH_KEY_PATH': ('ssh_key_path', Path),
            'REMOTE_BACKUP_DIR': ('remote_backup_dir', str),
            
            # Local settings
            'APP_DATA_DIR': ('app_data_dir', Path),
            'CHROMA_DB_PATH': ('chroma_db_path', Path),
            
            # Search settings
            'EMBEDDING_MODEL': ('embedding_model', str),
            'SEARCH_THRESHOLD': ('search_threshold', float),
            'SEARCH_LIMIT': ('search_limit', int),
            
            # UI settings
            'NOTIFICATION_ENABLED': ('notification_enabled', bool),
            'AUTO_ARCHIVE': ('auto_archive', bool),
            'TIMELINE_HOURS': ('timeline_hours', int),
        }
        
        for env_var, (config_key, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # Convert value to appropriate type
                    if value_type == bool:
                        parsed_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == Path:
                        parsed_value = Path(env_value).expanduser()
                    else:
                        parsed_value = value_type(env_value)
                    
                    overrides[config_key] = parsed_value
                    self.logger.debug(f"Environment override: {config_key} = {parsed_value}")
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Invalid environment value for {env_var}: {env_value} ({e})")
        
        return overrides
    
    def save_config(self, config: AppConfig):
        """Save configuration to JSON file."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert config to dict for JSON serialization
            config_dict = config.dict()
            
            # Convert Path objects to strings
            for key, value in config_dict.items():
                if isinstance(value, Path):
                    config_dict[key] = str(value)
            
            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            self.logger.info(f"Config saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def get_config_file_path(self) -> Path:
        """Get path to configuration file."""
        return self.config_file
    
    def reset_config(self) -> AppConfig:
        """Reset configuration to defaults."""
        try:
            if self.config_file.exists():
                # Backup existing config
                backup_path = self.config_file.with_suffix('.json.backup')
                self.config_file.rename(backup_path)
                self.logger.info(f"Backed up config to {backup_path}")
            
            # Create default config
            default_config = AppConfig()
            self.save_config(default_config)
            
            return default_config
            
        except Exception as e:
            self.logger.error(f"Error resetting config: {e}")
            return AppConfig()
    
    def validate_config(self, config: AppConfig) -> tuple[bool, list[str]]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Check WindRecorder path
        if not config.windrecorder_db_path.parent.exists():
            issues.append(f"WindRecorder directory not found: {config.windrecorder_db_path.parent}")
        
        # Check Claude logs path
        if not config.claude_logs_path.exists():
            issues.append(f"Claude logs directory not found: {config.claude_logs_path}")
        
        # Check SSH key for Hetzner
        if config.hetzner_host and not config.ssh_key_path.exists():
            issues.append(f"SSH key not found: {config.ssh_key_path}")
        
        # Check reasonable values
        if config.max_size_mb <= 0:
            issues.append("Max size must be positive")
        
        if config.max_age_days <= 0:
            issues.append("Max age must be positive")
        
        if not (0.0 <= config.search_threshold <= 1.0):
            issues.append("Search threshold must be between 0.0 and 1.0")
        
        return len(issues) == 0, issues
    
    def get_config_summary(self, config: AppConfig) -> str:
        """Get a human-readable summary of the current configuration."""
        summary_parts = [
            f"WindRecorder: {config.windrecorder_db_path}",
            f"Claude Logs: {config.claude_logs_path}",
            f"Archive Limits: {config.max_size_mb}MB / {config.max_age_days} days",
            f"Data Directory: {config.app_data_dir}",
        ]
        
        if config.hetzner_host:
            summary_parts.append(f"Hetzner: {config.hetzner_user}@{config.hetzner_host}")
        else:
            summary_parts.append("Hetzner: Not configured")
        
        summary_parts.extend([
            f"Search: {config.embedding_model} (threshold: {config.search_threshold})",
            f"Auto Archive: {'Enabled' if config.auto_archive else 'Disabled'}",
            f"Notifications: {'Enabled' if config.notification_enabled else 'Disabled'}"
        ])
        
        return "\n".join(summary_parts)