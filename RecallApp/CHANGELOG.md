# Changelog

All notable changes to the Recall app will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-08-22

### Added
- Initial release of Recall memory search application
- Native macOS menu bar integration with rumps
- WindRecorder database integration with automatic schema discovery
- Claude conversation log parser for JSONL format
- Semantic search engine using ChromaDB and sentence transformers
- Automatic archiving to Hetzner server when size/age thresholds reached
- SFTP upload with SSH key authentication and compression
- PyQt6-based search window with advanced filtering
- Timeline viewer for chronological browsing of activities
- Configuration management with environment variable support
- Background task scheduling for automatic maintenance
- Native macOS notifications for sync status
- Dark mode support and Retina display optimization

### Core Features
- **Menu Bar App**: Always accessible from macOS menu bar with 🧠 icon
- **Quick Search**: Instant search across all timeline data
- **Visual Context**: Screenshot and video references from WindRecorder
- **AI Integration**: Parse and search Claude/ChatGPT conversations
- **Smart Archiving**: Automatic backup when database reaches 5GB or 30 days
- **Secure Upload**: Encrypted SFTP transfer to Hetzner with verification
- **Timeline View**: Browse activities chronologically with filtering
- **Configuration**: Easy setup via environment variables or GUI

### Technical Details
- **Dependencies**: rumps, ChromaDB, sentence-transformers, paramiko, PyQt6
- **Database**: SQLite (WindRecorder) + ChromaDB (search index)
- **Packaging**: py2app for native .app bundle creation
- **Requirements**: macOS 11.0+, Python 3.9+
- **Architecture**: Modular design with core/, app/, and resource separation

### Security
- SSH key authentication for server access
- Local data processing (no cloud dependencies)
- Code-signed application bundle
- Sandboxed execution environment

### Performance
- Background indexing with 5-minute status updates
- Efficient vector search with cosine similarity
- Compressed archives (80-90% size reduction)
- Lazy loading of GUI components

### Known Limitations
- Requires WindRecorder to be installed and running
- PyQt6 optional (GUI falls back to basic alerts)
- Hetzner server configuration required for archiving
- Single-user application (no multi-user support)

## [Unreleased]

### Planned Features
- [ ] Spotlight integration for system-wide search
- [ ] Apple Shortcuts integration
- [ ] Touch Bar support for MacBook Pro
- [ ] ChatGPT log integration (when API available)
- [ ] Real-time indexing of new WindRecorder data
- [ ] Timeline visualization with charts
- [ ] Export to various formats (PDF, HTML, etc.)
- [ ] Multi-language OCR support
- [ ] Advanced filtering by activity type
- [ ] Integration with calendar apps

### Future Enhancements
- [ ] Migration to Qdrant for production scale
- [ ] Web interface for remote access
- [ ] Mobile companion app
- [ ] Team collaboration features
- [ ] AI-powered auto-tagging
- [ ] Voice transcription integration
- [ ] Git repository integration
- [ ] Slack/Discord chat integration

## Development Notes

### Build Process
1. Run `./test_app.py` to verify all components
2. Execute `./build.sh` to create .app bundle
3. Test on multiple macOS versions
4. Create DMG installer with `create-dmg`

### Architecture Decisions
- **rumps over PyObjC**: Simpler menu bar integration
- **ChromaDB over alternatives**: Better Python integration and performance
- **py2app over PyInstaller**: Native macOS bundle support
- **Modular design**: Easier testing and maintenance
- **Configuration flexibility**: Support multiple deployment scenarios

### Testing Strategy
- Unit tests for each core component
- Integration tests for data flow
- Manual testing on macOS 11, 12, 13, 14
- Performance testing with large datasets
- Security audit of network communications

### Release Process
1. Update version numbers in setup.py and plist
2. Run full test suite
3. Build and test .app bundle
4. Create release notes
5. Tag release in git
6. Distribute via GitHub releases