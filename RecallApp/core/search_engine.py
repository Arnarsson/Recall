"""
Unified search engine using ChromaDB for semantic search across timeline events.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from .models import TimelineEvent, SearchResult, AppConfig


class SearchEngine:
    """Semantic search engine for timeline events using ChromaDB."""
    
    def __init__(self, config: AppConfig):
        """Initialize search engine with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        config.ensure_directories()
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=str(config.chroma_db_path))
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.embedding_model
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="timeline_events",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        
        self.logger.info(f"Search engine initialized with {self.collection.count()} events")
    
    def index_events(self, events: List[TimelineEvent]) -> int:
        """Index timeline events in ChromaDB."""
        if not events:
            return 0
        
        # Prepare data for indexing
        documents = []
        metadatas = []
        ids = []
        
        for event in events:
            # Create searchable document by combining title and text
            doc_parts = [event.title]
            
            if event.text:
                doc_parts.append(event.text)
            
            if event.ocr_text and event.ocr_text != event.text:
                doc_parts.append(event.ocr_text)
            
            if event.page_title and event.page_title != event.title:
                doc_parts.append(event.page_title)
            
            if event.browser_url:
                doc_parts.append(event.browser_url)
            
            document = " | ".join(doc_parts)
            documents.append(document)
            
            # Create metadata
            metadata = {
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "title": event.title[:500],  # Limit length
                "tags": ",".join(event.tags),
                "has_visual": bool(event.screenshot_path or event.video_path),
            }
            
            # Add optional fields
            if event.browser_url:
                metadata["url"] = event.browser_url[:500]
            if event.conversation_id:
                metadata["conversation_id"] = event.conversation_id
            if event.message_type:
                metadata["message_type"] = event.message_type
            if event.duration:
                metadata["duration"] = str(event.duration)
            
            metadatas.append(metadata)
            
            # Create unique ID
            event_id = f"{event.source}_{event.timestamp.isoformat()}_{hash(event.title)}"
            ids.append(event_id)
        
        try:
            # Index in ChromaDB (use upsert to handle duplicates)
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Indexed {len(events)} events")
            return len(events)
            
        except Exception as e:
            self.logger.error(f"Error indexing events: {e}")
            return 0
    
    def search(
        self, 
        query: str, 
        limit: int = None,
        source_filter: Optional[str] = None,
        date_range: Optional[tuple] = None,
        tags_filter: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Search timeline events with semantic similarity."""
        if limit is None:
            limit = self.config.search_limit
        
        # Build where clause for filtering
        where_clause = {}
        
        if source_filter:
            where_clause["source"] = source_filter
        
        if date_range:
            start_date, end_date = date_range
            where_clause["timestamp"] = {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        
        if tags_filter:
            # Check if any of the specified tags are in the tags field
            for tag in tags_filter:
                where_clause["tags"] = {"$contains": tag}
        
        try:
            # Perform semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Convert to SearchResult objects
            search_results = []
            
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i] if results["distances"] else [0.0]
                    
                    # Convert distance to relevance score (1.0 - distance for cosine similarity)
                    relevance_score = max(0.0, 1.0 - distance[0])
                    
                    # Skip results below threshold
                    if relevance_score < self.config.search_threshold:
                        continue
                    
                    # Reconstruct TimelineEvent from metadata
                    event = self._metadata_to_event(metadata, doc)
                    event.relevance_score = relevance_score
                    
                    # Find matched text (simple keyword highlighting for now)
                    matched_text = self._find_matched_text(doc, query)
                    
                    search_result = SearchResult(
                        event=event,
                        relevance_score=relevance_score,
                        matched_text=matched_text
                    )
                    
                    search_results.append(search_result)
            
            # Sort by relevance score
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            self.logger.info(f"Search for '{query}' returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error searching: {e}")
            return []
    
    def search_by_timeframe(
        self, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = None
    ) -> List[TimelineEvent]:
        """Search events within a specific timeframe."""
        if limit is None:
            limit = self.config.search_limit
        
        where_clause = {
            "timestamp": {
                "$gte": start_time.isoformat(),
                "$lte": end_time.isoformat()
            }
        }
        
        try:
            results = self.collection.get(
                where=where_clause,
                limit=limit
            )
            
            events = []
            if results["metadatas"]:
                for i, metadata in enumerate(results["metadatas"]):
                    doc = results["documents"][i] if results["documents"] else ""
                    event = self._metadata_to_event(metadata, doc)
                    events.append(event)
            
            # Sort by timestamp
            events.sort(key=lambda x: x.timestamp)
            
            return events
            
        except Exception as e:
            self.logger.error(f"Error searching by timeframe: {e}")
            return []
    
    def get_recent_events(self, hours: int = 24) -> List[TimelineEvent]:
        """Get recent events from the index."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        return self.search_by_timeframe(start_time, end_time)
    
    def _metadata_to_event(self, metadata: Dict[str, Any], document: str) -> TimelineEvent:
        """Convert metadata back to TimelineEvent."""
        # Parse timestamp
        timestamp = datetime.fromisoformat(metadata["timestamp"])
        
        # Parse tags
        tags = metadata.get("tags", "").split(",") if metadata.get("tags") else []
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        # Extract text from document (remove title part)
        title = metadata.get("title", "")
        text_parts = document.split(" | ")
        text = " | ".join(text_parts[1:]) if len(text_parts) > 1 else ""
        
        event = TimelineEvent(
            timestamp=timestamp,
            source=metadata["source"],
            title=title,
            text=text,
            tags=tags,
            browser_url=metadata.get("url"),
            conversation_id=metadata.get("conversation_id"),
            message_type=metadata.get("message_type"),
            duration=float(metadata["duration"]) if metadata.get("duration") else None,
            metadata=metadata
        )
        
        return event
    
    def _find_matched_text(self, document: str, query: str, context_chars: int = 100) -> str:
        """Find and highlight matched text in document."""
        query_words = query.lower().split()
        document_lower = document.lower()
        
        # Find first matching word
        for word in query_words:
            if word in document_lower:
                match_index = document_lower.find(word)
                
                # Extract context around the match
                start = max(0, match_index - context_chars)
                end = min(len(document), match_index + len(word) + context_chars)
                
                context = document[start:end]
                
                # Add ellipsis if we're not at the beginning/end
                if start > 0:
                    context = "..." + context
                if end < len(document):
                    context = context + "..."
                
                return context
        
        # If no exact word match, return first part of document
        return document[:context_chars * 2] + ("..." if len(document) > context_chars * 2 else "")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        try:
            total_events = self.collection.count()
            
            # Get events by source
            sources = {}
            for source in ["windrecorder", "claude", "chatgpt"]:
                count = len(self.collection.get(where={"source": source})["ids"])
                if count > 0:
                    sources[source] = count
            
            # Get recent activity (last 24 hours)
            recent_events = self.get_recent_events(24)
            
            return {
                "total_events": total_events,
                "sources": sources,
                "recent_events_24h": len(recent_events),
                "database_path": str(self.config.chroma_db_path),
                "embedding_model": self.config.embedding_model
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}
    
    def clear_index(self) -> bool:
        """Clear all events from the index."""
        try:
            # Delete and recreate collection
            self.client.delete_collection("timeline_events")
            self.collection = self.client.create_collection(
                name="timeline_events",
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            
            self.logger.info("Search index cleared")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing index: {e}")
            return False