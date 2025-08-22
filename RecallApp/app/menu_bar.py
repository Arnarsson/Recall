"""
Main menu bar application for Recall using rumps.
"""

import rumps
import threading
import schedule
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add the parent directory to the path so we can import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import AppConfig
from core.windrecorder_client import WindRecorderClient
from core.claude_parser import ClaudeLogParser
from core.search_engine import SearchEngine
from core.archiver import ArchiveManager


class RecallApp(rumps.App):
    """Main menu bar application for Recall."""
    
    def __init__(self):
        super(RecallApp, self).__init__("Recall", icon="🧠")
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize core components
        self.windrecorder = WindRecorderClient(self.config.windrecorder_db_path)
        self.claude_parser = ClaudeLogParser(self.config.claude_logs_path)
        self.search_engine = SearchEngine(self.config)
        self.archiver = ArchiveManager(self.config)
        
        # App state
        self.last_sync = datetime.now()
        self.is_syncing = False
        self.last_index_update = datetime.now()
        
        # Setup menu
        self.setup_menu()
        
        # Start background tasks
        self.start_background_tasks()
        
        self.logger.info("Recall app initialized")
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path.home() / "Library" / "Application Support" / "Recall" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "recall.log"),
                logging.StreamHandler()
            ]
        )
    
    def load_config(self) -> AppConfig:
        """Load application configuration."""
        config_path = Path.home() / "Library" / "Application Support" / "Recall" / "config.json"
        
        # Create default config if it doesn't exist
        if not config_path.exists():
            config = AppConfig()
            config.ensure_directories()
            
            # Save default config
            with open(config_path, 'w') as f:
                f.write(config.json(indent=2))
            
            return config
        
        try:
            with open(config_path, 'r') as f:
                config_data = f.read()
            return AppConfig.parse_raw(config_data)
        except Exception as e:
            self.logger.error(f"Error loading config, using defaults: {e}")
            return AppConfig()
    
    def setup_menu(self):
        """Setup the menu bar menu."""
        self.menu = [
            "🔍 Quick Search...",
            None,  # Separator
            "📊 Timeline View",
            "📁 Recent Activities",
            None,
            "💾 Archive Status",
            "🔄 Sync Now",
            "📈 Statistics",
            None,
            rumps.MenuItem("⚙️ Preferences...", key="comma"),
            None,
            "🔧 Test Connection",
            "📂 Open Data Folder",
        ]
    
    @rumps.clicked("🔍 Quick Search...")
    def quick_search(self, _):
        """Open quick search dialog."""
        response = rumps.Window(
            title="Search Memory",
            message="What are you looking for?",
            default_text="",
            ok="Search",
            cancel="Cancel",
            dimensions=(400, 24)
        ).run()
        
        if response.clicked:
            self.perform_search(response.text)
    
    def perform_search(self, query: str):
        """Perform search and show results."""
        try:
            results = self.search_engine.search(query, limit=10)
            
            if not results:
                rumps.alert("No Results", f"No matching activities found for '{query}'.")
                return
            
            # Format results for display
            formatted_results = []
            for result in results:
                event = result.event
                time_str = event.timestamp.strftime("%m/%d %H:%M")
                score = f"({result.relevance_score:.2f})"
                title = event.title[:60] + ("..." if len(event.title) > 60 else "")
                formatted_results.append(f"{time_str} {score}: {title}")
            
            result_text = "\n\n".join(formatted_results)
            
            # Show detailed search window if available
            try:
                from app.search_window import SearchWindow
                search_window = SearchWindow(query, results)
                search_window.show()
            except ImportError:
                # Fallback to simple alert
                rumps.alert(
                    f"Search Results for '{query}'",
                    result_text,
                    ok="OK"
                )
            
        except Exception as e:
            self.logger.error(f"Error performing search: {e}")
            rumps.alert("Search Error", f"Error searching: {e}")
    
    @rumps.clicked("📊 Timeline View")
    def timeline_view(self, _):
        """Open timeline view."""
        try:
            from app.timeline_viewer import TimelineViewer
            viewer = TimelineViewer(self.search_engine)
            viewer.show()
        except ImportError:
            # Fallback to recent events
            self.recent_activities(None)
    
    @rumps.clicked("📁 Recent Activities")
    def recent_activities(self, _):
        """Show recent activities."""
        try:
            events = self.search_engine.get_recent_events(hours=4)
            
            if not events:
                rumps.alert("No Recent Activities", "No activities found in the last 4 hours.")
                return
            
            formatted_events = []
            for event in events[-10:]:  # Last 10 events
                time_str = event.timestamp.strftime("%H:%M")
                title = event.title[:50] + ("..." if len(event.title) > 50 else "")
                source_icon = "🖥️" if event.source == "windrecorder" else "🤖"
                formatted_events.append(f"{time_str} {source_icon} {title}")
            
            rumps.alert(
                "Recent Activities (Last 4 Hours)",
                "\n".join(formatted_events),
                ok="OK"
            )
            
        except Exception as e:
            self.logger.error(f"Error getting recent activities: {e}")
            rumps.alert("Error", f"Error getting recent activities: {e}")
    
    @rumps.clicked("💾 Archive Status")
    def archive_status(self, _):
        """Show archive status."""
        try:
            status = self.archiver.get_status()
            
            # Format next archive time
            next_archive = "Not scheduled"
            if status.next_archive_estimate:
                next_archive = status.next_archive_estimate.strftime("%m/%d at %H:%M")
            
            # Format progress
            progress = ""
            if status.upload_progress > 0:
                progress = f"\nUpload Progress: {status.upload_progress * 100:.0f}%"
            
            message = (
                f"Database Size: {status.database_size_mb:.1f} MB\n"
                f"Database Age: {status.database_age_days} days\n"
                f"Next Archive: {next_archive}\n"
                f"Remote Archives: {status.remote_archives_count}"
                f"{progress}"
            )
            
            rumps.alert("Archive Status", message, ok="OK")
            
        except Exception as e:
            self.logger.error(f"Error getting archive status: {e}")
            rumps.alert("Error", f"Error getting archive status: {e}")
    
    @rumps.clicked("🔄 Sync Now")
    def sync_now(self, sender):
        """Manually trigger sync."""
        if self.is_syncing:
            rumps.alert("Sync in Progress", "A sync is already in progress.")
            return
        
        original_title = sender.title
        sender.title = "🔄 Syncing..."
        
        def sync_task():
            try:
                self.is_syncing = True
                
                # Index recent data
                self.update_search_index()
                
                # Check for archiving
                archived = self.archiver.check_and_archive()
                
                self.last_sync = datetime.now()
                self.is_syncing = False
                
                # Update menu
                sender.title = original_title
                
                # Show notification
                if archived:
                    rumps.notification(
                        "Recall",
                        "Sync Complete",
                        f"Data archived and synced at {self.last_sync.strftime('%H:%M')}"
                    )
                else:
                    rumps.notification(
                        "Recall",
                        "Sync Complete",
                        f"Data indexed at {self.last_sync.strftime('%H:%M')}"
                    )
                
            except Exception as e:
                self.logger.error(f"Error during sync: {e}")
                self.is_syncing = False
                sender.title = original_title
                rumps.alert("Sync Error", f"Error during sync: {e}")
        
        threading.Thread(target=sync_task, daemon=True).start()
    
    @rumps.clicked("📈 Statistics")
    def show_statistics(self, _):
        """Show app statistics."""
        try:
            stats = self.search_engine.get_statistics()
            
            # WindRecorder status
            wr_running = "Yes" if self.windrecorder.check_windrecorder_running() else "No"
            
            message = (
                f"Total Events: {stats.get('total_events', 0)}\n"
                f"Sources: {stats.get('sources', {})}\n"
                f"Recent (24h): {stats.get('recent_events_24h', 0)}\n\n"
                f"WindRecorder Running: {wr_running}\n"
                f"Last Sync: {self.last_sync.strftime('%H:%M')}\n"
                f"Embedding Model: {stats.get('embedding_model', 'N/A')}"
            )
            
            rumps.alert("Statistics", message, ok="OK")
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            rumps.alert("Error", f"Error getting statistics: {e}")
    
    @rumps.clicked("⚙️ Preferences...")
    def preferences(self, _):
        """Open preferences window."""
        try:
            from app.settings import PreferencesWindow
            prefs = PreferencesWindow(self.config)
            prefs.show()
        except ImportError:
            # Fallback to basic alert
            rumps.alert(
                "Preferences",
                f"Config file: {Path.home() / 'Library' / 'Application Support' / 'Recall' / 'config.json'}",
                ok="OK"
            )
    
    @rumps.clicked("🔧 Test Connection")
    def test_connection(self, _):
        """Test Hetzner connection."""
        def test_task():
            success = self.archiver.test_connection()
            if success:
                rumps.notification("Recall", "Connection Test", "Hetzner connection successful!")
            else:
                rumps.alert("Connection Test", "Failed to connect to Hetzner server.")
        
        threading.Thread(target=test_task, daemon=True).start()
    
    @rumps.clicked("📂 Open Data Folder")
    def open_data_folder(self, _):
        """Open the app data folder in Finder."""
        import subprocess
        data_dir = self.config.app_data_dir
        subprocess.call(["open", str(data_dir)])
    
    @rumps.timer(300)  # Every 5 minutes
    def update_status(self, _):
        """Update menu bar icon based on status."""
        try:
            # Check if archiving is needed
            needs_archive, _ = self.archiver.should_archive()
            
            if self.is_syncing:
                self.icon = "⚡"  # Lightning when syncing
            elif needs_archive:
                self.icon = "🔴"  # Red dot when archive needed
            else:
                self.icon = "🧠"  # Normal brain icon
                
            # Update search index periodically
            if datetime.now() - self.last_index_update > timedelta(minutes=30):
                threading.Thread(target=self.update_search_index, daemon=True).start()
                self.last_index_update = datetime.now()
                
        except Exception as e:
            self.logger.error(f"Error in status update: {e}")
    
    def update_search_index(self):
        """Update the search index with recent data."""
        try:
            # Get recent WindRecorder data
            wr_records = self.windrecorder.get_recent_records(hours=24)
            wr_events = self.windrecorder.to_timeline_events(wr_records)
            
            # Get recent Claude data
            claude_entries = self.claude_parser.get_recent_entries(hours=24)
            claude_events = self.claude_parser.to_timeline_events(claude_entries)
            
            # Combine and index
            all_events = wr_events + claude_events
            
            if all_events:
                indexed_count = self.search_engine.index_events(all_events)
                self.logger.info(f"Indexed {indexed_count} recent events")
            
        except Exception as e:
            self.logger.error(f"Error updating search index: {e}")
    
    def start_background_tasks(self):
        """Start background task scheduler."""
        # Schedule periodic archive checks
        schedule.every(6).hours.do(self.archiver.check_and_archive)
        
        # Schedule index updates
        schedule.every(30).minutes.do(self.update_search_index)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                threading.Event().wait(60)  # Check every minute
        
        threading.Thread(target=run_scheduler, daemon=True).start()
        self.logger.info("Background scheduler started")


def main():
    """Main entry point for the application."""
    try:
        app = RecallApp()
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()