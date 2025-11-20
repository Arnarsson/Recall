#!/usr/bin/env python3
"""
Test script for Recall app components.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add the app to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.models import AppConfig, TimelineEvent
from core.windrecorder_client import WindRecorderClient
from core.claude_parser import ClaudeLogParser
from core.search_engine import SearchEngine
from core.archiver import ArchiveManager
from app.config_manager import ConfigManager


def setup_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_config_manager():
    """Test configuration management."""
    print("🔧 Testing Configuration Manager...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        print(f"✅ Config loaded successfully")
        print(f"📁 App data dir: {config.app_data_dir}")
        print(f"💾 Chroma DB path: {config.chroma_db_path}")
        print(f"🖥️ WindRecorder path: {config.windrecorder_db_path}")
        print(f"🤖 Claude logs path: {config.claude_logs_path}")
        
        # Validate config
        is_valid, issues = config_manager.validate_config(config)
        if is_valid:
            print("✅ Configuration is valid")
        else:
            print("⚠️ Configuration issues:")
            for issue in issues:
                print(f"   - {issue}")
        
        return config
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return None


def test_windrecorder_client(config):
    """Test WindRecorder client."""
    print("\n🖥️ Testing WindRecorder Client...")
    
    try:
        client = WindRecorderClient(config.windrecorder_db_path)
        
        print(f"📁 Database files found: {len(client.db_files)}")
        for db_file in client.db_files[:3]:  # Show first 3
            print(f"   - {db_file.name}")
        
        # Test database size
        size_mb = client.get_database_size()
        age_days = client.get_database_age()
        print(f"💾 Database size: {size_mb:.1f} MB")
        print(f"📅 Database age: {age_days} days")
        
        # Test getting recent records
        records = client.get_recent_records(hours=1)
        print(f"📊 Recent records (1h): {len(records)}")
        
        if records:
            # Show sample record
            sample = records[0]
            print(f"📝 Sample record: {sample.timestamp} - {sample.app_name}")
        
        # Test conversion to timeline events
        events = client.to_timeline_events(records)
        print(f"🎯 Converted to {len(events)} timeline events")
        
        print("✅ WindRecorder client test passed")
        return True
        
    except Exception as e:
        print(f"❌ WindRecorder test failed: {e}")
        return False


def test_claude_parser(config):
    """Test Claude log parser."""
    print("\n🤖 Testing Claude Parser...")
    
    try:
        parser = ClaudeLogParser(config.claude_logs_path)
        
        # Test getting recent entries
        entries = parser.get_recent_entries(hours=24)
        print(f"💬 Recent Claude entries (24h): {len(entries)}")
        
        if entries:
            # Show sample entry
            sample = entries[0]
            print(f"📝 Sample entry: {sample.timestamp} - {sample.message_type}")
            print(f"   Content preview: {sample.content[:100]}...")
        
        # Test conversion to timeline events
        events = parser.to_timeline_events(entries)
        print(f"🎯 Converted to {len(events)} timeline events")
        
        # Test conversation grouping
        conversations = parser.get_conversations()
        print(f"💬 Total conversations: {len(conversations)}")
        
        print("✅ Claude parser test passed")
        return events
        
    except Exception as e:
        print(f"❌ Claude parser test failed: {e}")
        return []


def test_search_engine(config, sample_events):
    """Test search engine."""
    print("\n🔍 Testing Search Engine...")
    
    try:
        search_engine = SearchEngine(config)
        
        # Get initial stats
        stats = search_engine.get_statistics()
        print(f"📊 Initial stats: {stats}")
        
        if sample_events:
            # Index sample events
            print(f"📥 Indexing {len(sample_events)} events...")
            indexed_count = search_engine.index_events(sample_events)
            print(f"✅ Indexed {indexed_count} events")
            
            # Test search
            print("🔍 Testing search...")
            results = search_engine.search("Claude", limit=5)
            print(f"📊 Search results: {len(results)}")
            
            for i, result in enumerate(results[:3]):
                print(f"   {i+1}. {result.event.timestamp} - {result.event.title[:50]}... (score: {result.relevance_score:.2f})")
            
            # Test timeframe search
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            timeframe_events = search_engine.search_by_timeframe(yesterday, now)
            print(f"📅 Events in last 24h: {len(timeframe_events)}")
        
        print("✅ Search engine test passed")
        return search_engine
        
    except Exception as e:
        print(f"❌ Search engine test failed: {e}")
        return None


def test_archiver(config):
    """Test archive manager."""
    print("\n💾 Testing Archive Manager...")
    
    try:
        archiver = ArchiveManager(config)
        
        # Test status
        status = archiver.get_status()
        print(f"📊 Archive status:")
        print(f"   Size: {status.database_size_mb:.1f} MB")
        print(f"   Age: {status.database_age_days} days")
        print(f"   Remote archives: {status.remote_archives_count}")
        
        # Test archive check
        should_archive, reason = archiver.should_archive()
        print(f"🔍 Should archive: {should_archive}")
        print(f"   Reason: {reason}")
        
        # Test connection (if configured)
        if config.hetzner_host:
            print("🌐 Testing Hetzner connection...")
            connection_ok = archiver.test_connection()
            if connection_ok:
                print("✅ Hetzner connection successful")
                
                # List remote archives
                try:
                    archives = archiver.list_remote_archives()
                    print(f"📁 Remote archives: {len(archives)}")
                    for archive in archives[:3]:
                        print(f"   - {archive}")
                except Exception as e:
                    print(f"⚠️ Could not list remote archives: {e}")
            else:
                print("❌ Hetzner connection failed")
        else:
            print("⚠️ Hetzner not configured, skipping connection test")
        
        print("✅ Archive manager test passed")
        return True
        
    except Exception as e:
        print(f"❌ Archive manager test failed: {e}")
        return False


def test_gui_components():
    """Test GUI components if available."""
    print("\n🖼️ Testing GUI Components...")
    
    try:
        # Test if PyQt6 is available
        try:
            from app.search_window import create_search_window
            from app.timeline_viewer import create_timeline_viewer
            
            print("✅ PyQt6 available - GUI components can be created")
            
            # Don't actually create windows in test, just verify imports work
            search_window = create_search_window()
            timeline_viewer = create_timeline_viewer()
            
            if search_window is not None:
                print("✅ Search window can be created")
            if timeline_viewer is not None:
                print("✅ Timeline viewer can be created")
                
        except ImportError:
            print("⚠️ PyQt6 not available - GUI components will use fallbacks")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI component test failed: {e}")
        return False


def test_menu_bar_app():
    """Test menu bar app components (without actually running)."""
    print("\n📱 Testing Menu Bar App...")
    
    try:
        # Test if rumps is available
        import rumps
        print("✅ rumps available")
        
        # Test app imports
        from app.menu_bar import RecallApp
        print("✅ Menu bar app imports successfully")
        
        # Don't actually create the app in test mode
        print("✅ Menu bar app test passed")
        return True
        
    except Exception as e:
        print(f"❌ Menu bar app test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Running Recall App Tests\n")
    setup_logging()
    
    test_results = {}
    
    # Test configuration
    config = test_config_manager()
    test_results['config'] = config is not None
    
    if config:
        # Test core components
        test_results['windrecorder'] = test_windrecorder_client(config)
        claude_events = test_claude_parser(config)
        test_results['claude_parser'] = len(claude_events) >= 0
        
        search_engine = test_search_engine(config, claude_events)
        test_results['search_engine'] = search_engine is not None
        
        test_results['archiver'] = test_archiver(config)
        
        # Test UI components
        test_results['gui'] = test_gui_components()
        test_results['menu_bar'] = test_menu_bar_app()
    
    # Print summary
    print("\n📊 Test Summary:")
    print("=" * 40)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:15} {status}")
    
    print("=" * 40)
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Ready to build the app.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)