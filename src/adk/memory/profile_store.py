"""Profile store implementations for user preference persistence.

This module provides an abstract interface and multiple implementations:
- ProfileStoreInterface: Abstract base class defining the contract
- ProfileStoreMemory: In-memory implementation for testing
- ProfileStoreSQLite: SQLite implementation for local development
- get_profile_store(): Factory function based on PROFILE_STORE env var

The factory pattern allows switching between implementations without code changes.
"""

import json
import os
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional


class ProfileStoreInterface(ABC):
    """Abstract interface for user profile storage.
    
    Defines the contract that all profile store implementations must follow.
    This allows swapping between in-memory, SQLite, and Firestore implementations
    without changing business logic code.
    """
    
    @abstractmethod
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Retrieve a user profile by ID.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User profile dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def create_profile(
        self,
        user_id: str,
        preferred_tags: Optional[Dict[str, int]] = None,
        language: str = "en",
        saved_event_ids: Optional[List[str]] = None,
    ) -> Dict:
        """Create a new user profile.
        
        Args:
            user_id: Unique user identifier
            preferred_tags: Tag weights dictionary {tag: weight (1-5)}
            language: User's preferred language (en/es)
            saved_event_ids: List of saved event IDs
            
        Returns:
            Created profile dictionary
        """
        pass
    
    @abstractmethod
    def update_profile(
        self,
        user_id: str,
        preferred_tags: Optional[Dict[str, int]] = None,
        saved_event_ids: Optional[List[str]] = None,
        language: Optional[str] = None,
    ) -> Dict:
        """Update an existing user profile.
        
        Args:
            user_id: Unique user identifier
            preferred_tags: Updated tag weights (merges with existing)
            saved_event_ids: Updated saved events (replaces existing)
            language: Updated language preference
            
        Returns:
            Updated profile dictionary
        """
        pass
    
    @abstractmethod
    def delete_profile(self, user_id: str) -> bool:
        """Delete a user profile.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    def update_tag_weights(
        self,
        user_id: str,
        tag_deltas: Dict[str, float],
    ) -> Dict:
        """Update tag weights by applying deltas.
        
        Weights are clamped to the range [1.0, 5.0].
        
        Args:
            user_id: Unique user identifier
            tag_deltas: Dictionary of {tag: delta_weight}
            
        Returns:
            Updated profile dictionary
        """
        pass
    
    @abstractmethod
    def add_saved_event(self, user_id: str, event_id: str) -> Dict:
        """Add an event to user's saved events.
        
        Args:
            user_id: Unique user identifier
            event_id: Event ID to save
            
        Returns:
            Updated profile dictionary
        """
        pass
    
    @abstractmethod
    def remove_saved_event(self, user_id: str, event_id: str) -> Dict:
        """Remove an event from user's saved events.
        
        Args:
            user_id: Unique user identifier
            event_id: Event ID to remove
            
        Returns:
            Updated profile dictionary
        """
        pass
    
    @abstractmethod
    def list_all_profiles(self, limit: int = 100) -> List[Dict]:
        """List all user profiles (for admin/debugging).
        
        Args:
            limit: Maximum number of profiles to return
            
        Returns:
            List of profile dictionaries
        """
        pass
    
    @abstractmethod
    def clear_all_profiles(self) -> int:
        """Delete all profiles (for testing/cleanup).
        
        WARNING: This is destructive and should only be used in
        development/testing environments.
        
        Returns:
            Number of profiles deleted
        """
        pass


class ProfileStoreMemory(ProfileStoreInterface):
    """In-memory profile store implementation.
    
    Stores profiles in a Python dictionary. Data is lost when process terminates.
    Ideal for unit testing and development scenarios where persistence is not needed.
    """
    
    def __init__(self):
        """Initialize in-memory storage."""
        self._profiles: Dict[str, Dict] = {}
    
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Retrieve profile from memory."""
        return self._profiles.get(user_id)
    
    def create_profile(
        self,
        user_id: str,
        preferred_tags: Optional[Dict[str, int]] = None,
        language: str = "en",
        saved_event_ids: Optional[List[str]] = None,
    ) -> Dict:
        """Create new profile in memory."""
        profile = {
            "user_id": user_id,
            "preferred_tags": preferred_tags or {},
            "saved_event_ids": saved_event_ids or [],
            "language": language,
            "last_interaction_ts": datetime.now(UTC).isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._profiles[user_id] = profile
        return profile
    
    def update_profile(
        self,
        user_id: str,
        preferred_tags: Optional[Dict[str, int]] = None,
        saved_event_ids: Optional[List[str]] = None,
        language: Optional[str] = None,
    ) -> Dict:
        """Update profile in memory."""
        # Get or create profile
        if user_id not in self._profiles:
            return self.create_profile(
                user_id=user_id,
                preferred_tags=preferred_tags or {},
                language=language or "en",
                saved_event_ids=saved_event_ids or [],
            )
        
        profile = self._profiles[user_id]
        
        # Update fields
        if preferred_tags is not None:
            profile["preferred_tags"].update(preferred_tags)
        if saved_event_ids is not None:
            profile["saved_event_ids"] = saved_event_ids
        if language is not None:
            profile["language"] = language
        
        profile["last_interaction_ts"] = datetime.now(UTC).isoformat()
        return profile
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete profile from memory."""
        if user_id in self._profiles:
            del self._profiles[user_id]
            return True
        return False
    
    def update_tag_weights(
        self,
        user_id: str,
        tag_deltas: Dict[str, float],
    ) -> Dict:
        """Update tag weights with clamping."""
        profile = self.get_profile(user_id)
        
        if not profile:
            # Create new profile with initial weights
            initial_tags = {
                tag: max(1, min(5, int(3 + delta)))
                for tag, delta in tag_deltas.items()
            }
            return self.create_profile(user_id=user_id, preferred_tags=initial_tags)
        
        # Update existing weights
        current_tags = profile.get("preferred_tags", {})
        
        for tag, delta in tag_deltas.items():
            current_weight = current_tags.get(tag, 3)  # Default weight: 3
            new_weight = max(1, min(5, int(current_weight + delta)))
            current_tags[tag] = new_weight
        
        return self.update_profile(user_id=user_id, preferred_tags=current_tags)
    
    def add_saved_event(self, user_id: str, event_id: str) -> Dict:
        """Add event to saved list."""
        profile = self.get_profile(user_id)
        
        if not profile:
            return self.create_profile(user_id=user_id, saved_event_ids=[event_id])
        
        saved_events = profile.get("saved_event_ids", [])
        if event_id not in saved_events:
            saved_events.append(event_id)
        
        return self.update_profile(user_id=user_id, saved_event_ids=saved_events)
    
    def remove_saved_event(self, user_id: str, event_id: str) -> Dict:
        """Remove event from saved list."""
        profile = self.get_profile(user_id)
        
        if not profile:
            return None
        
        saved_events = profile.get("saved_event_ids", [])
        if event_id in saved_events:
            saved_events.remove(event_id)
        
        return self.update_profile(user_id=user_id, saved_event_ids=saved_events)
    
    def list_all_profiles(self, limit: int = 100) -> List[Dict]:
        """List all profiles from memory."""
        return list(self._profiles.values())[:limit]
    
    def clear_all_profiles(self) -> int:
        """Clear all profiles from memory."""
        count = len(self._profiles)
        self._profiles.clear()
        return count


class ProfileStoreSQLite(ProfileStoreInterface):
    """SQLite-based profile store implementation.
    
    Stores profiles in a SQLite database file. Data persists across process restarts.
    Ideal for local development where you want persistence without external services.
    
    Schema:
        user_profiles table with columns:
        - user_id (TEXT PRIMARY KEY)
        - preferred_tags (TEXT, JSON-encoded)
        - saved_event_ids (TEXT, JSON-encoded)
        - language (TEXT)
        - last_interaction_ts (TEXT, ISO format)
        - created_at (TEXT, ISO format)
    """
    
    def __init__(self, db_path: str = "data/profiles.db"):
        """Initialize SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self._create_tables()
    
    def _create_tables(self):
        """Create user_profiles table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                preferred_tags TEXT,
                saved_event_ids TEXT,
                language TEXT,
                last_interaction_ts TEXT,
                created_at TEXT
            )
        """)
        self.conn.commit()
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert SQLite row to profile dictionary."""
        return {
            "user_id": row["user_id"],
            "preferred_tags": json.loads(row["preferred_tags"]),
            "saved_event_ids": json.loads(row["saved_event_ids"]),
            "language": row["language"],
            "last_interaction_ts": row["last_interaction_ts"],
            "created_at": row["created_at"],
        }
    
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Retrieve profile from SQLite."""
        cursor = self.conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def create_profile(
        self,
        user_id: str,
        preferred_tags: Optional[Dict[str, int]] = None,
        language: str = "en",
        saved_event_ids: Optional[List[str]] = None,
    ) -> Dict:
        """Create new profile in SQLite."""
        now = datetime.now(UTC).isoformat()
        profile = {
            "user_id": user_id,
            "preferred_tags": preferred_tags or {},
            "saved_event_ids": saved_event_ids or [],
            "language": language,
            "last_interaction_ts": now,
            "created_at": now,
        }
        
        self.conn.execute(
            """
            INSERT INTO user_profiles 
            (user_id, preferred_tags, saved_event_ids, language, last_interaction_ts, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                json.dumps(profile["preferred_tags"]),
                json.dumps(profile["saved_event_ids"]),
                language,
                now,
                now,
            )
        )
        self.conn.commit()
        return profile
    
    def update_profile(
        self,
        user_id: str,
        preferred_tags: Optional[Dict[str, int]] = None,
        saved_event_ids: Optional[List[str]] = None,
        language: Optional[str] = None,
    ) -> Dict:
        """Update profile in SQLite."""
        # Get existing profile
        existing = self.get_profile(user_id)
        
        if not existing:
            return self.create_profile(
                user_id=user_id,
                preferred_tags=preferred_tags or {},
                language=language or "en",
                saved_event_ids=saved_event_ids or [],
            )
        
        # Merge updates
        if preferred_tags is not None:
            existing["preferred_tags"].update(preferred_tags)
        if saved_event_ids is not None:
            existing["saved_event_ids"] = saved_event_ids
        if language is not None:
            existing["language"] = language
        
        existing["last_interaction_ts"] = datetime.now(UTC).isoformat()
        
        # Update database
        self.conn.execute(
            """
            UPDATE user_profiles
            SET preferred_tags = ?,
                saved_event_ids = ?,
                language = ?,
                last_interaction_ts = ?
            WHERE user_id = ?
            """,
            (
                json.dumps(existing["preferred_tags"]),
                json.dumps(existing["saved_event_ids"]),
                existing["language"],
                existing["last_interaction_ts"],
                user_id,
            )
        )
        self.conn.commit()
        return existing
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete profile from SQLite."""
        cursor = self.conn.execute(
            "DELETE FROM user_profiles WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_tag_weights(
        self,
        user_id: str,
        tag_deltas: Dict[str, float],
    ) -> Dict:
        """Update tag weights with clamping."""
        profile = self.get_profile(user_id)
        
        if not profile:
            # Create new profile with initial weights
            initial_tags = {
                tag: max(1, min(5, int(3 + delta)))
                for tag, delta in tag_deltas.items()
            }
            return self.create_profile(user_id=user_id, preferred_tags=initial_tags)
        
        # Update existing weights
        current_tags = profile.get("preferred_tags", {})
        
        for tag, delta in tag_deltas.items():
            current_weight = current_tags.get(tag, 3)  # Default weight: 3
            new_weight = max(1, min(5, int(current_weight + delta)))
            current_tags[tag] = new_weight
        
        return self.update_profile(user_id=user_id, preferred_tags=current_tags)
    
    def add_saved_event(self, user_id: str, event_id: str) -> Dict:
        """Add event to saved list."""
        profile = self.get_profile(user_id)
        
        if not profile:
            return self.create_profile(user_id=user_id, saved_event_ids=[event_id])
        
        saved_events = profile.get("saved_event_ids", [])
        if event_id not in saved_events:
            saved_events.append(event_id)
        
        return self.update_profile(user_id=user_id, saved_event_ids=saved_events)
    
    def remove_saved_event(self, user_id: str, event_id: str) -> Dict:
        """Remove event from saved list."""
        profile = self.get_profile(user_id)
        
        if not profile:
            return None
        
        saved_events = profile.get("saved_event_ids", [])
        if event_id in saved_events:
            saved_events.remove(event_id)
        
        return self.update_profile(user_id=user_id, saved_event_ids=saved_events)
    
    def list_all_profiles(self, limit: int = 100) -> List[Dict]:
        """List all profiles from SQLite."""
        cursor = self.conn.execute(
            "SELECT * FROM user_profiles LIMIT ?",
            (limit,)
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def clear_all_profiles(self) -> int:
        """Clear all profiles from SQLite."""
        cursor = self.conn.execute("DELETE FROM user_profiles")
        self.conn.commit()
        return cursor.rowcount
    
    def close(self):
        """Close database connection."""
        self.conn.close()


def get_profile_store(store_type: Optional[str] = None) -> ProfileStoreInterface:
    """Factory function to get profile store implementation.
    
    Determines which implementation to use based on environment variable
    PROFILE_STORE or the store_type parameter.
    
    Args:
        store_type: Override store type ("memory", "sqlite", "firestore")
                   If None, reads from PROFILE_STORE env var (default: "sqlite")
    
    Returns:
        ProfileStoreInterface implementation
    
    Examples:
        >>> # Use default (SQLite)
        >>> store = get_profile_store()
        
        >>> # Use in-memory for testing
        >>> store = get_profile_store("memory")
        
        >>> # Use environment variable
        >>> os.environ["PROFILE_STORE"] = "memory"
        >>> store = get_profile_store()
    """
    if store_type is None:
        store_type = os.getenv("PROFILE_STORE", "sqlite").lower()
    
    if store_type == "memory":
        return ProfileStoreMemory()
    elif store_type == "sqlite":
        db_path = os.getenv("SQLITE_DB_PATH", "data/profiles.db")
        return ProfileStoreSQLite(db_path)
    elif store_type == "firestore":
        # Placeholder for Day 10 implementation
        raise NotImplementedError(
            "Firestore adapter will be implemented in Day 10. "
            "Use 'memory' or 'sqlite' for now."
        )
    else:
        raise ValueError(
            f"Unknown store type: {store_type}. "
            f"Valid options: 'memory', 'sqlite', 'firestore'"
        )
