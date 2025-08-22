"""
Timeline viewer for browsing activity chronologically.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QDate, QDateTime
    from PyQt6.QtGui import QFont, QPixmap, QIcon
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import TimelineEvent
from core.search_engine import SearchEngine


class TimelineThread(QThread):
    """Background thread for loading timeline events."""
    
    events_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, search_engine: SearchEngine, start_time: datetime, end_time: datetime):
        super().__init__()
        self.search_engine = search_engine
        self.start_time = start_time
        self.end_time = end_time
    
    def run(self):
        """Load timeline events in background."""
        try:
            events = self.search_engine.search_by_timeframe(
                self.start_time, 
                self.end_time,
                limit=1000
            )
            self.events_ready.emit(events)
        except Exception as e:
            self.error_occurred.emit(str(e))


class TimelineViewer(QMainWindow):
    """Timeline viewer for browsing activity chronologically."""
    
    def __init__(self, search_engine: SearchEngine = None):
        super().__init__()
        
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 not available for TimelineViewer")
        
        self.search_engine = search_engine
        self.current_events = []
        
        self.setWindowTitle("Recall - Timeline Viewer")
        self.setGeometry(150, 150, 1200, 800)
        self.setMinimumSize(1000, 600)
        
        # Setup UI
        self.setup_ui()
        
        # Load today's timeline by default
        self.load_today()
    
    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Controls section
        controls_layout = self.create_controls_section()
        layout.addLayout(controls_layout)
        
        # Timeline section
        timeline_layout = self.create_timeline_section()
        layout.addLayout(timeline_layout, 1)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def create_controls_section(self) -> QVBoxLayout:
        """Create the timeline controls section."""
        layout = QVBoxLayout()
        
        # Date selection row
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("Date Range:"))
        
        # Start date
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("to"))
        
        # End date
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        
        # Load button
        load_button = QPushButton("Load Timeline")
        load_button.clicked.connect(self.load_timeline)
        date_layout.addWidget(load_button)
        
        date_layout.addStretch()
        
        # Quick selection buttons
        quick_layout = QHBoxLayout()
        
        today_button = QPushButton("Today")
        today_button.clicked.connect(self.load_today)
        quick_layout.addWidget(today_button)
        
        yesterday_button = QPushButton("Yesterday")
        yesterday_button.clicked.connect(self.load_yesterday)
        quick_layout.addWidget(yesterday_button)
        
        week_button = QPushButton("This Week")
        week_button.clicked.connect(self.load_week)
        quick_layout.addWidget(week_button)
        
        quick_layout.addStretch()
        
        layout.addLayout(date_layout)
        layout.addLayout(quick_layout)
        
        # Filters row
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Source:"))
        self.source_filter = QComboBox()
        self.source_filter.addItems(["All", "WindRecorder", "Claude", "ChatGPT"])
        self.source_filter.currentTextChanged.connect(self.filter_timeline)
        filters_layout.addWidget(self.source_filter)
        
        filters_layout.addWidget(QLabel("Activity:"))
        self.activity_filter = QComboBox()
        self.activity_filter.addItems(["All", "Coding", "Browsing", "AI Chat", "Other"])
        self.activity_filter.currentTextChanged.connect(self.filter_timeline)
        filters_layout.addWidget(self.activity_filter)
        
        filters_layout.addStretch()
        
        # Export button
        export_button = QPushButton("Export Timeline")
        export_button.clicked.connect(self.export_timeline)
        filters_layout.addWidget(export_button)
        
        layout.addLayout(filters_layout)
        
        return layout
    
    def create_timeline_section(self) -> QVBoxLayout:
        """Create the timeline display section."""
        layout = QVBoxLayout()
        
        # Timeline header
        header_layout = QHBoxLayout()
        self.timeline_title = QLabel("Timeline")
        self.timeline_title.setFont(QFont("SF Pro", 16, QFont.Weight.Bold))
        header_layout.addWidget(self.timeline_title)
        
        header_layout.addStretch()
        
        self.event_count_label = QLabel("0 events")
        header_layout.addWidget(self.event_count_label)
        
        layout.addLayout(header_layout)
        
        # Timeline view (using tree widget for hierarchical display)
        self.timeline_tree = QTreeWidget()
        self.timeline_tree.setHeaderLabels(["Time", "Activity", "Source", "Duration"])
        self.timeline_tree.setRootIsDecorated(True)
        self.timeline_tree.setAlternatingRowColors(True)
        self.timeline_tree.itemClicked.connect(self.show_event_detail)
        
        # Set column widths
        self.timeline_tree.setColumnWidth(0, 120)  # Time
        self.timeline_tree.setColumnWidth(1, 400)  # Activity
        self.timeline_tree.setColumnWidth(2, 120)  # Source
        self.timeline_tree.setColumnWidth(3, 80)   # Duration
        
        layout.addWidget(self.timeline_tree)
        
        # Detail view
        detail_group = QGroupBox("Event Details")
        detail_layout = QVBoxLayout(detail_group)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        self.detail_text.setFont(QFont("SF Mono", 11))
        detail_layout.addWidget(self.detail_text)
        
        layout.addWidget(detail_group)
        
        return layout
    
    def load_timeline(self):
        """Load timeline for selected date range."""
        if not self.search_engine:
            self.status_bar.showMessage("Error: Search engine not available")
            return
        
        # Get date range
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        
        # Convert to datetime
        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date, datetime.max.time())
        
        # Start loading
        self.status_bar.showMessage("Loading timeline...")
        self.timeline_tree.clear()
        
        # Load in background
        self.timeline_thread = TimelineThread(self.search_engine, start_time, end_time)
        self.timeline_thread.events_ready.connect(self.display_timeline)
        self.timeline_thread.error_occurred.connect(self.show_error)
        self.timeline_thread.start()
    
    def load_today(self):
        """Load today's timeline."""
        today = QDate.currentDate()
        self.start_date.setDate(today)
        self.end_date.setDate(today)
        self.load_timeline()
    
    def load_yesterday(self):
        """Load yesterday's timeline."""
        yesterday = QDate.currentDate().addDays(-1)
        self.start_date.setDate(yesterday)
        self.end_date.setDate(yesterday)
        self.load_timeline()
    
    def load_week(self):
        """Load this week's timeline."""
        today = QDate.currentDate()
        week_start = today.addDays(-today.dayOfWeek() + 1)  # Monday
        self.start_date.setDate(week_start)
        self.end_date.setDate(today)
        self.load_timeline()
    
    def display_timeline(self, events: List[TimelineEvent]):
        """Display timeline events in the tree widget."""
        self.current_events = events
        self.timeline_tree.clear()
        
        if not events:
            self.timeline_title.setText("Timeline - No Events")
            self.event_count_label.setText("0 events")
            self.status_bar.showMessage("No events found for selected period")
            return
        
        # Update header
        start_date = min(event.timestamp for event in events).strftime("%m/%d")
        end_date = max(event.timestamp for event in events).strftime("%m/%d")
        date_range = start_date if start_date == end_date else f"{start_date} - {end_date}"
        
        self.timeline_title.setText(f"Timeline - {date_range}")
        self.event_count_label.setText(f"{len(events)} events")
        
        # Group events by hour
        events_by_hour = {}
        for event in events:
            hour_key = event.timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in events_by_hour:
                events_by_hour[hour_key] = []
            events_by_hour[hour_key].append(event)
        
        # Create tree structure
        for hour_key in sorted(events_by_hour.keys()):
            hour_events = events_by_hour[hour_key]
            
            # Create hour group
            hour_time = datetime.strptime(hour_key, "%Y-%m-%d %H:%M")
            hour_text = hour_time.strftime("%H:00")
            hour_item = QTreeWidgetItem([
                hour_text,
                f"{len(hour_events)} activities",
                "Mixed" if len(set(e.source for e in hour_events)) > 1 else hour_events[0].source.title(),
                f"{len(hour_events)} events"
            ])
            
            # Style hour items
            font = hour_item.font(0)
            font.setBold(True)
            for col in range(4):
                hour_item.setFont(col, font)
            
            self.timeline_tree.addTopLevelItem(hour_item)
            
            # Add individual events
            for event in sorted(hour_events, key=lambda x: x.timestamp):
                self.add_event_item(hour_item, event)
            
            # Expand hour groups with few events
            if len(hour_events) <= 10:
                hour_item.setExpanded(True)
        
        self.apply_current_filters()
        self.status_bar.showMessage(f"Loaded {len(events)} events")
    
    def add_event_item(self, parent_item: QTreeWidgetItem, event: TimelineEvent):
        """Add an individual event to the timeline tree."""
        time_str = event.timestamp.strftime("%H:%M:%S")
        
        # Format activity title
        title = event.title[:60] + ("..." if len(event.title) > 60 else "")
        
        # Source icon and text
        source_icons = {
            "windrecorder": "🖥️",
            "claude": "🤖",
            "chatgpt": "💬"
        }
        source_text = f"{source_icons.get(event.source, '📄')} {event.source.title()}"
        
        # Duration text
        duration_text = ""
        if event.duration:
            if event.duration < 60:
                duration_text = f"{event.duration:.0f}s"
            else:
                duration_text = f"{event.duration/60:.1f}m"
        
        event_item = QTreeWidgetItem([time_str, title, source_text, duration_text])
        event_item.setData(0, Qt.ItemDataRole.UserRole, event)
        
        # Color coding by source
        if event.source == "windrecorder":
            event_item.setBackground(0, Qt.GlobalColor.lightGray)
        elif event.source == "claude":
            event_item.setBackground(0, Qt.GlobalColor.lightBlue)
        
        parent_item.addChild(event_item)
    
    def show_event_detail(self, item: QTreeWidgetItem, column: int):
        """Show detailed information for selected event."""
        event = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(event, TimelineEvent):
            self.detail_text.clear()
            return
        
        # Format detail information
        details = [
            f"🕐 {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"📊 Source: {event.source.title()}",
            f"📝 Title: {event.title}",
        ]
        
        if event.tags:
            details.append(f"🏷️ Tags: {', '.join(event.tags)}")
        
        if event.browser_url:
            details.append(f"🌐 URL: {event.browser_url}")
        
        if event.duration:
            details.append(f"⏱️ Duration: {event.duration:.1f} seconds")
        
        if event.conversation_id:
            details.append(f"💬 Conversation: {event.conversation_id}")
        
        details.append("\n📄 Content:")
        details.append(event.text)
        
        if event.ocr_text and event.ocr_text != event.text:
            details.append("\n👁️ OCR Text:")
            details.append(event.ocr_text)
        
        self.detail_text.setText("\n".join(details))
    
    def filter_timeline(self):
        """Apply current filter settings to timeline."""
        if not hasattr(self, 'current_events'):
            return
        
        self.apply_current_filters()
    
    def apply_current_filters(self):
        """Apply current filter settings to visible items."""
        source_filter = self.source_filter.currentText()
        activity_filter = self.activity_filter.currentText()
        
        visible_count = 0
        
        # Iterate through all top-level items (hours)
        for i in range(self.timeline_tree.topLevelItemCount()):
            hour_item = self.timeline_tree.topLevelItem(i)
            hour_visible_count = 0
            
            # Check each event in the hour
            for j in range(hour_item.childCount()):
                event_item = hour_item.child(j)
                event = event_item.data(0, Qt.ItemDataRole.UserRole)
                
                if isinstance(event, TimelineEvent):
                    visible = self.event_matches_filters(event, source_filter, activity_filter)
                    event_item.setHidden(not visible)
                    
                    if visible:
                        hour_visible_count += 1
                        visible_count += 1
            
            # Hide hour group if no visible events
            hour_item.setHidden(hour_visible_count == 0)
            
            # Update hour group text
            if hour_visible_count > 0:
                hour_time = hour_item.text(0)
                hour_item.setText(1, f"{hour_visible_count} activities")
        
        # Update count label
        if visible_count != len(self.current_events):
            self.event_count_label.setText(f"{visible_count} of {len(self.current_events)} events")
        else:
            self.event_count_label.setText(f"{len(self.current_events)} events")
    
    def event_matches_filters(self, event: TimelineEvent, source_filter: str, activity_filter: str) -> bool:
        """Check if event matches current filters."""
        # Source filter
        if source_filter != "All" and event.source.lower() != source_filter.lower():
            return False
        
        # Activity filter
        if activity_filter != "All":
            activity_tags = {
                "Coding": ["coding", "git", "debug", "development"],
                "Browsing": ["browser", "url", "web"],
                "AI Chat": ["claude", "ai-chat", "chatgpt"],
                "Other": []
            }
            
            if activity_filter in activity_tags:
                required_tags = activity_tags[activity_filter]
                if required_tags and not any(tag in event.tags for tag in required_tags):
                    return False
        
        return True
    
    def export_timeline(self):
        """Export current timeline to file."""
        if not self.current_events:
            QMessageBox.information(self, "No Data", "No timeline data to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Timeline",
            f"timeline_{datetime.now().strftime('%Y%m%d')}.txt",
            "Text Files (*.txt);;CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.export_json(file_path)
                elif file_path.endswith('.csv'):
                    self.export_csv(file_path)
                else:
                    self.export_text(file_path)
                
                QMessageBox.information(self, "Export Complete", f"Timeline exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export timeline:\n{e}")
    
    def export_text(self, file_path: str):
        """Export timeline as text file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Timeline Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            for event in sorted(self.current_events, key=lambda x: x.timestamp):
                f.write(f"{event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {event.source.upper()}\n")
                f.write(f"Title: {event.title}\n")
                if event.text:
                    f.write(f"Content: {event.text[:200]}...\n")
                f.write("-" * 40 + "\n")
    
    def export_csv(self, file_path: str):
        """Export timeline as CSV file."""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Source', 'Title', 'Content', 'Tags', 'URL'])
            
            for event in sorted(self.current_events, key=lambda x: x.timestamp):
                writer.writerow([
                    event.timestamp.isoformat(),
                    event.source,
                    event.title,
                    event.text[:500],  # Limit content length
                    ','.join(event.tags),
                    event.browser_url or ''
                ])
    
    def export_json(self, file_path: str):
        """Export timeline as JSON file."""
        import json
        
        data = {
            'export_date': datetime.now().isoformat(),
            'events': [event.dict() for event in self.current_events]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def show_error(self, error_message: str):
        """Show error message."""
        QMessageBox.critical(self, "Timeline Error", f"Error loading timeline:\n{error_message}")
        self.status_bar.showMessage(f"Error: {error_message}")


def create_timeline_viewer(search_engine: SearchEngine = None) -> Optional[TimelineViewer]:
    """Create timeline viewer if PyQt6 is available."""
    if not PYQT_AVAILABLE:
        return None
    
    viewer = TimelineViewer(search_engine)
    return viewer


if __name__ == "__main__":
    # Test the timeline viewer
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        viewer = TimelineViewer()
        viewer.show()
        sys.exit(app.exec())
    else:
        print("PyQt6 not available - cannot run timeline viewer")