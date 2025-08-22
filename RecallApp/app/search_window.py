"""
Enhanced search window using PyQt6 for detailed search interface.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QPixmap, QIcon
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import SearchResult, TimelineEvent
from core.search_engine import SearchEngine


class SearchThread(QThread):
    """Background thread for performing searches."""
    
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, search_engine: SearchEngine, query: str, filters: dict = None):
        super().__init__()
        self.search_engine = search_engine
        self.query = query
        self.filters = filters or {}
    
    def run(self):
        """Perform search in background thread."""
        try:
            results = self.search_engine.search(
                self.query,
                limit=self.filters.get('limit', 50),
                source_filter=self.filters.get('source'),
                date_range=self.filters.get('date_range'),
                tags_filter=self.filters.get('tags')
            )
            self.results_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))


class SearchWindow(QMainWindow):
    """Enhanced search window with filters and detailed results."""
    
    def __init__(self, initial_query: str = "", initial_results: List[SearchResult] = None):
        super().__init__()
        
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 not available for SearchWindow")
        
        self.search_engine = None  # Will be set by caller
        self.current_results = initial_results or []
        
        self.setWindowTitle("Recall - Search Memory")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # Setup UI
        self.setup_ui()
        
        # Set initial query if provided
        if initial_query:
            self.search_input.setText(initial_query)
        
        # Display initial results if provided
        if initial_results:
            self.display_results(initial_results)
    
    def set_search_engine(self, search_engine: SearchEngine):
        """Set the search engine instance."""
        self.search_engine = search_engine
    
    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Search section
        search_layout = self.create_search_section()
        layout.addLayout(search_layout)
        
        # Filters section
        filters_layout = self.create_filters_section()
        layout.addLayout(filters_layout)
        
        # Results section
        results_layout = self.create_results_section()
        layout.addLayout(results_layout, 1)  # Take remaining space
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def create_search_section(self) -> QHBoxLayout:
        """Create the search input section."""
        layout = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search your memory timeline...")
        self.search_input.setFont(QFont("SF Pro", 14))
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.setFont(QFont("SF Pro", 14))
        self.search_button.clicked.connect(self.perform_search)
        self.search_button.setFixedWidth(100)
        layout.addWidget(self.search_button)
        
        return layout
    
    def create_filters_section(self) -> QHBoxLayout:
        """Create the filters section."""
        layout = QHBoxLayout()
        
        # Source filter
        layout.addWidget(QLabel("Source:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["All", "WindRecorder", "Claude", "ChatGPT"])
        layout.addWidget(self.source_combo)
        
        # Date range filter
        layout.addWidget(QLabel("Date:"))
        self.date_combo = QComboBox()
        self.date_combo.addItems([
            "All Time", "Last Hour", "Last 24 Hours", 
            "Last Week", "Last Month", "Custom..."
        ])
        layout.addWidget(self.date_combo)
        
        # Tags filter
        layout.addWidget(QLabel("Tags:"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g., coding, debugging")
        layout.addWidget(self.tags_input)
        
        # Add stretch to push everything left
        layout.addStretch()
        
        # Clear filters button
        clear_button = QPushButton("Clear Filters")
        clear_button.clicked.connect(self.clear_filters)
        layout.addWidget(clear_button)
        
        return layout
    
    def create_results_section(self) -> QVBoxLayout:
        """Create the results display section."""
        layout = QVBoxLayout()
        
        # Results header
        header_layout = QHBoxLayout()
        self.results_label = QLabel("Search Results")
        self.results_label.setFont(QFont("SF Pro", 16, QFont.Weight.Bold))
        header_layout.addWidget(self.results_label)
        
        header_layout.addStretch()
        
        # Sort options
        header_layout.addWidget(QLabel("Sort by:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Relevance", "Date (Newest)", "Date (Oldest)", "Source"])
        self.sort_combo.currentTextChanged.connect(self.sort_results)
        header_layout.addWidget(self.sort_combo)
        
        layout.addLayout(header_layout)
        
        # Splitter for results list and detail view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_result_detail)
        self.results_list.setMinimumWidth(400)
        splitter.addWidget(self.results_list)
        
        # Detail view
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        
        self.detail_title = QLabel("Select a result to view details")
        self.detail_title.setFont(QFont("SF Pro", 14, QFont.Weight.Bold))
        self.detail_title.setWordWrap(True)
        detail_layout.addWidget(self.detail_title)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(QFont("SF Mono", 12))
        detail_layout.addWidget(self.detail_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.open_visual_button = QPushButton("View Screenshot")
        self.open_visual_button.clicked.connect(self.open_visual_content)
        self.open_visual_button.setEnabled(False)
        button_layout.addWidget(self.open_visual_button)
        
        self.copy_button = QPushButton("Copy Content")
        self.copy_button.clicked.connect(self.copy_content)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        
        button_layout.addStretch()
        detail_layout.addLayout(button_layout)
        
        splitter.addWidget(detail_widget)
        splitter.setSizes([400, 600])  # 40% list, 60% detail
        
        layout.addWidget(splitter)
        
        return layout
    
    def perform_search(self):
        """Perform search with current query and filters."""
        query = self.search_input.text().strip()
        if not query:
            return
        
        if not self.search_engine:
            self.status_bar.showMessage("Error: Search engine not available")
            return
        
        # Disable search while running
        self.search_button.setEnabled(False)
        self.search_button.setText("Searching...")
        self.status_bar.showMessage("Searching...")
        
        # Build filters
        filters = self.get_current_filters()
        
        # Start search thread
        self.search_thread = SearchThread(self.search_engine, query, filters)
        self.search_thread.results_ready.connect(self.display_results)
        self.search_thread.error_occurred.connect(self.show_error)
        self.search_thread.finished.connect(self.search_finished)
        self.search_thread.start()
    
    def get_current_filters(self) -> dict:
        """Get current filter settings."""
        filters = {}
        
        # Source filter
        source = self.source_combo.currentText()
        if source != "All":
            filters['source'] = source.lower()
        
        # Date filter
        date_filter = self.date_combo.currentText()
        if date_filter != "All Time":
            now = datetime.now()
            if date_filter == "Last Hour":
                filters['date_range'] = (now - timedelta(hours=1), now)
            elif date_filter == "Last 24 Hours":
                filters['date_range'] = (now - timedelta(days=1), now)
            elif date_filter == "Last Week":
                filters['date_range'] = (now - timedelta(weeks=1), now)
            elif date_filter == "Last Month":
                filters['date_range'] = (now - timedelta(days=30), now)
        
        # Tags filter
        tags_text = self.tags_input.text().strip()
        if tags_text:
            filters['tags'] = [tag.strip() for tag in tags_text.split(',')]
        
        return filters
    
    def display_results(self, results: List[SearchResult]):
        """Display search results in the list."""
        self.current_results = results
        self.results_list.clear()
        
        if not results:
            self.results_label.setText("No Results Found")
            self.status_bar.showMessage("No results found")
            return
        
        self.results_label.setText(f"Search Results ({len(results)} found)")
        
        for result in results:
            event = result.event
            
            # Format list item
            time_str = event.timestamp.strftime("%m/%d %H:%M")
            score_str = f"({result.relevance_score:.2f})"
            source_icon = "🖥️" if event.source == "windrecorder" else "🤖"
            title = event.title[:80] + ("..." if len(event.title) > 80 else "")
            
            item_text = f"{time_str} {score_str} {source_icon} {title}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, result)
            self.results_list.addItem(item)
        
        self.status_bar.showMessage(f"Found {len(results)} results")
        
        # Auto-select first result
        if results:
            self.results_list.setCurrentRow(0)
            self.show_result_detail(self.results_list.item(0))
    
    def show_result_detail(self, item):
        """Show detailed view of selected result."""
        if not item:
            return
        
        result: SearchResult = item.data(Qt.ItemDataRole.UserRole)
        event = result.event
        
        # Update detail view
        self.detail_title.setText(event.title)
        
        # Format detail text
        detail_parts = [
            f"📅 {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"📊 Source: {event.source.title()}",
            f"🎯 Relevance: {result.relevance_score:.2f}",
        ]
        
        if event.tags:
            detail_parts.append(f"🏷️ Tags: {', '.join(event.tags)}")
        
        if event.browser_url:
            detail_parts.append(f"🌐 URL: {event.browser_url}")
        
        if event.conversation_id:
            detail_parts.append(f"💬 Conversation: {event.conversation_id[:8]}...")
        
        detail_parts.append("\n📝 Content:")
        detail_parts.append(event.text)
        
        if event.ocr_text and event.ocr_text != event.text:
            detail_parts.append("\n👁️ OCR Text:")
            detail_parts.append(event.ocr_text)
        
        self.detail_text.setText("\n".join(detail_parts))
        
        # Enable/disable action buttons
        self.copy_button.setEnabled(True)
        self.open_visual_button.setEnabled(
            bool(event.screenshot_path or event.video_path)
        )
        
        # Store current result for actions
        self.current_result = result
    
    def sort_results(self, sort_type: str):
        """Sort current results by specified criteria."""
        if not self.current_results:
            return
        
        if sort_type == "Relevance":
            self.current_results.sort(key=lambda x: x.relevance_score, reverse=True)
        elif sort_type == "Date (Newest)":
            self.current_results.sort(key=lambda x: x.event.timestamp, reverse=True)
        elif sort_type == "Date (Oldest)":
            self.current_results.sort(key=lambda x: x.event.timestamp)
        elif sort_type == "Source":
            self.current_results.sort(key=lambda x: x.event.source)
        
        self.display_results(self.current_results)
    
    def clear_filters(self):
        """Clear all filter settings."""
        self.source_combo.setCurrentIndex(0)
        self.date_combo.setCurrentIndex(0)
        self.tags_input.clear()
    
    def open_visual_content(self):
        """Open visual content (screenshot/video) in default application."""
        if not hasattr(self, 'current_result'):
            return
        
        event = self.current_result.event
        path_to_open = event.screenshot_path or event.video_path
        
        if path_to_open and Path(path_to_open).exists():
            import subprocess
            subprocess.call(["open", path_to_open])
        else:
            QMessageBox.information(self, "Not Available", "Visual content not found or not available.")
    
    def copy_content(self):
        """Copy event content to clipboard."""
        if not hasattr(self, 'current_result'):
            return
        
        content = self.current_result.event.text
        if content:
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            self.status_bar.showMessage("Content copied to clipboard", 2000)
    
    def show_error(self, error_message: str):
        """Show error message."""
        QMessageBox.critical(self, "Search Error", f"Error performing search:\n{error_message}")
        self.status_bar.showMessage(f"Error: {error_message}")
    
    def search_finished(self):
        """Re-enable search button after search completes."""
        self.search_button.setEnabled(True)
        self.search_button.setText("Search")


def create_search_window(query: str = "", results: List[SearchResult] = None) -> Optional[SearchWindow]:
    """Create search window if PyQt6 is available."""
    if not PYQT_AVAILABLE:
        return None
    
    window = SearchWindow(query, results)
    return window


if __name__ == "__main__":
    # Test the search window
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        window = SearchWindow("test query")
        window.show()
        sys.exit(app.exec())
    else:
        print("PyQt6 not available - cannot run search window")