"""Tests for profile store implementations.

Tests all three implementations (Memory, SQLite, and interface contract) with:
- Basic CRUD operations
- Tag weight updates with clamping
- Saved events management
- Persistence validation (SQLite only)
- Edge cases and error handling
"""

import os
import tempfile
from pathlib import Path

import pytest

from adk.memory.profile_store import (
    ProfileStoreInterface,
    ProfileStoreMemory,
    ProfileStoreSQLite,
    get_profile_store,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def memory_store():
    """Create a fresh in-memory profile store."""
    return ProfileStoreMemory()


@pytest.fixture
def sqlite_store():
    """Create a temporary SQLite profile store."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    store = ProfileStoreSQLite(db_path)
    yield store
    
    # Cleanup
    store.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture(params=["memory", "sqlite"])
def any_store(request):
    """Parametrized fixture to test all implementations."""
    if request.param == "memory":
        yield ProfileStoreMemory()
    else:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        store = ProfileStoreSQLite(db_path)
        yield store
        store.close()
        Path(db_path).unlink(missing_ok=True)


# ============================================================================
# Interface Contract Tests (run against all implementations)
# ============================================================================

class TestProfileStoreContract:
    """Test that all implementations follow the interface contract."""
    
    def test_create_profile(self, any_store: ProfileStoreInterface):
        """Test creating a new profile."""
        profile = any_store.create_profile(
            user_id="user123",
            preferred_tags={"modern": 4, "sculpture": 3},
            language="es",
            saved_event_ids=["evt_001"],
        )
        
        assert profile["user_id"] == "user123"
        assert profile["preferred_tags"] == {"modern": 4, "sculpture": 3}
        assert profile["language"] == "es"
        assert profile["saved_event_ids"] == ["evt_001"]
        assert "created_at" in profile
        assert "last_interaction_ts" in profile
    
    def test_get_profile_exists(self, any_store: ProfileStoreInterface):
        """Test retrieving an existing profile."""
        any_store.create_profile("user456", preferred_tags={"digital": 5})
        
        profile = any_store.get_profile("user456")
        
        assert profile is not None
        assert profile["user_id"] == "user456"
        assert profile["preferred_tags"] == {"digital": 5}
    
    def test_get_profile_not_exists(self, any_store: ProfileStoreInterface):
        """Test retrieving a non-existent profile."""
        profile = any_store.get_profile("nonexistent")
        assert profile is None
    
    def test_update_profile_existing(self, any_store: ProfileStoreInterface):
        """Test updating an existing profile."""
        any_store.create_profile("user789", preferred_tags={"painting": 3})
        
        updated = any_store.update_profile(
            "user789",
            preferred_tags={"photography": 4},
            language="en",
        )
        
        assert updated["preferred_tags"]["painting"] == 3  # Preserved
        assert updated["preferred_tags"]["photography"] == 4  # Added
        assert updated["language"] == "en"
    
    def test_update_profile_creates_if_not_exists(self, any_store: ProfileStoreInterface):
        """Test that update creates profile if it doesn't exist."""
        profile = any_store.update_profile(
            "newuser",
            preferred_tags={"abstract": 5},
        )
        
        assert profile["user_id"] == "newuser"
        assert profile["preferred_tags"] == {"abstract": 5}
    
    def test_delete_profile(self, any_store: ProfileStoreInterface):
        """Test deleting a profile."""
        any_store.create_profile("user_delete", preferred_tags={})
        
        result = any_store.delete_profile("user_delete")
        assert result is True
        
        profile = any_store.get_profile("user_delete")
        assert profile is None
    
    def test_delete_nonexistent_profile(self, any_store: ProfileStoreInterface):
        """Test deleting a non-existent profile."""
        result = any_store.delete_profile("nonexistent")
        assert result is False
    
    def test_update_tag_weights_new_user(self, any_store: ProfileStoreInterface):
        """Test updating tag weights for a new user."""
        profile = any_store.update_tag_weights(
            "newuser",
            {"modern": 1, "digital": -1},  # Deltas from default weight 3
        )
        
        assert profile["preferred_tags"]["modern"] == 4  # 3 + 1
        assert profile["preferred_tags"]["digital"] == 2  # 3 - 1
    
    def test_update_tag_weights_existing_user(self, any_store: ProfileStoreInterface):
        """Test updating tag weights for an existing user."""
        any_store.create_profile("user_weights", preferred_tags={"sculpture": 3})
        
        profile = any_store.update_tag_weights(
            "user_weights",
            {"sculpture": 2, "installation": 1},  # Deltas
        )
        
        assert profile["preferred_tags"]["sculpture"] == 5  # 3 + 2
        assert profile["preferred_tags"]["installation"] == 4  # 3 + 1
    
    def test_tag_weight_clamping_min(self, any_store: ProfileStoreInterface):
        """Test that tag weights are clamped to minimum of 1."""
        any_store.create_profile("user_min", preferred_tags={"modern": 2})
        
        profile = any_store.update_tag_weights("user_min", {"modern": -5})
        
        assert profile["preferred_tags"]["modern"] == 1  # Clamped to min
    
    def test_tag_weight_clamping_max(self, any_store: ProfileStoreInterface):
        """Test that tag weights are clamped to maximum of 5."""
        any_store.create_profile("user_max", preferred_tags={"digital": 4})
        
        profile = any_store.update_tag_weights("user_max", {"digital": 5})
        
        assert profile["preferred_tags"]["digital"] == 5  # Clamped to max
    
    def test_add_saved_event_new_user(self, any_store: ProfileStoreInterface):
        """Test adding saved event for a new user."""
        profile = any_store.add_saved_event("newuser", "evt_001")
        
        assert "evt_001" in profile["saved_event_ids"]
    
    def test_add_saved_event_existing_user(self, any_store: ProfileStoreInterface):
        """Test adding saved event for an existing user."""
        any_store.create_profile("user_save", saved_event_ids=["evt_001"])
        
        profile = any_store.add_saved_event("user_save", "evt_002")
        
        assert profile["saved_event_ids"] == ["evt_001", "evt_002"]
    
    def test_add_saved_event_duplicate(self, any_store: ProfileStoreInterface):
        """Test adding duplicate saved event."""
        any_store.create_profile("user_dup", saved_event_ids=["evt_001"])
        
        profile = any_store.add_saved_event("user_dup", "evt_001")
        
        # Should not create duplicate
        assert profile["saved_event_ids"].count("evt_001") == 1
    
    def test_remove_saved_event(self, any_store: ProfileStoreInterface):
        """Test removing saved event."""
        any_store.create_profile("user_remove", saved_event_ids=["evt_001", "evt_002"])
        
        profile = any_store.remove_saved_event("user_remove", "evt_001")
        
        assert "evt_001" not in profile["saved_event_ids"]
        assert "evt_002" in profile["saved_event_ids"]
    
    def test_remove_saved_event_not_exists(self, any_store: ProfileStoreInterface):
        """Test removing non-existent saved event."""
        any_store.create_profile("user_remove", saved_event_ids=["evt_001"])
        
        profile = any_store.remove_saved_event("user_remove", "evt_999")
        
        # Should not raise error
        assert profile["saved_event_ids"] == ["evt_001"]
    
    def test_list_all_profiles(self, any_store: ProfileStoreInterface):
        """Test listing all profiles."""
        any_store.create_profile("user1", preferred_tags={})
        any_store.create_profile("user2", preferred_tags={})
        any_store.create_profile("user3", preferred_tags={})
        
        profiles = any_store.list_all_profiles()
        
        assert len(profiles) == 3
        user_ids = {p["user_id"] for p in profiles}
        assert user_ids == {"user1", "user2", "user3"}
    
    def test_list_all_profiles_limit(self, any_store: ProfileStoreInterface):
        """Test listing profiles with limit."""
        for i in range(5):
            any_store.create_profile(f"user{i}", preferred_tags={})
        
        profiles = any_store.list_all_profiles(limit=3)
        
        assert len(profiles) <= 3
    
    def test_clear_all_profiles(self, any_store: ProfileStoreInterface):
        """Test clearing all profiles."""
        any_store.create_profile("user1", preferred_tags={})
        any_store.create_profile("user2", preferred_tags={})
        
        count = any_store.clear_all_profiles()
        
        assert count == 2
        assert len(any_store.list_all_profiles()) == 0


# ============================================================================
# SQLite-Specific Tests
# ============================================================================

class TestProfileStoreSQLite:
    """Tests specific to SQLite implementation."""
    
    def test_persistence_across_instances(self):
        """Test that data persists when creating new store instance."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        try:
            # Create profile with first instance
            store1 = ProfileStoreSQLite(db_path)
            store1.create_profile("user_persist", preferred_tags={"modern": 5})
            store1.close()
            
            # Retrieve with second instance
            store2 = ProfileStoreSQLite(db_path)
            profile = store2.get_profile("user_persist")
            store2.close()
            
            assert profile is not None
            assert profile["user_id"] == "user_persist"
            assert profile["preferred_tags"] == {"modern": 5}
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    def test_creates_db_directory(self):
        """Test that database directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "subdir" / "profiles.db"
            
            store = ProfileStoreSQLite(str(db_path))
            
            assert db_path.exists()
            store.close()
    
    def test_json_encoding_decoding(self, sqlite_store: ProfileStoreSQLite):
        """Test that complex data structures are properly JSON encoded/decoded."""
        profile = sqlite_store.create_profile(
            "user_json",
            preferred_tags={"modern": 5, "sculpture": 3, "digital": 4},
            saved_event_ids=["evt_001", "evt_002", "evt_003"],
        )
        
        retrieved = sqlite_store.get_profile("user_json")
        
        assert retrieved["preferred_tags"] == profile["preferred_tags"]
        assert retrieved["saved_event_ids"] == profile["saved_event_ids"]


# ============================================================================
# Memory-Specific Tests
# ============================================================================

class TestProfileStoreMemory:
    """Tests specific to in-memory implementation."""
    
    def test_no_persistence(self):
        """Test that data is lost when store is destroyed."""
        store1 = ProfileStoreMemory()
        store1.create_profile("user_temp", preferred_tags={"modern": 5})
        
        # Create new instance
        store2 = ProfileStoreMemory()
        profile = store2.get_profile("user_temp")
        
        assert profile is None  # Data not persisted


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestGetProfileStore:
    """Test the factory function."""
    
    def test_get_memory_store(self):
        """Test getting memory store."""
        store = get_profile_store("memory")
        assert isinstance(store, ProfileStoreMemory)
    
    def test_get_sqlite_store(self):
        """Test getting SQLite store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["SQLITE_DB_PATH"] = str(Path(tmpdir) / "test.db")
            store = get_profile_store("sqlite")
            
            assert isinstance(store, ProfileStoreSQLite)
            store.close()
    
    def test_default_is_sqlite(self):
        """Test that default store type is SQLite."""
        # Clear env var to test default
        old_val = os.environ.pop("PROFILE_STORE", None)
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.environ["SQLITE_DB_PATH"] = str(Path(tmpdir) / "default.db")
                store = get_profile_store()
                
                assert isinstance(store, ProfileStoreSQLite)
                store.close()
        finally:
            if old_val:
                os.environ["PROFILE_STORE"] = old_val
    
    def test_env_var_override(self):
        """Test that PROFILE_STORE env var is respected."""
        os.environ["PROFILE_STORE"] = "memory"
        
        try:
            store = get_profile_store()
            assert isinstance(store, ProfileStoreMemory)
        finally:
            os.environ.pop("PROFILE_STORE", None)
    
    def test_firestore_not_implemented(self):
        """Test that Firestore raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Day 10"):
            get_profile_store("firestore")
    
    def test_invalid_store_type(self):
        """Test that invalid store type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown store type"):
            get_profile_store("invalid")


# ============================================================================
# Integration Tests
# ============================================================================

class TestProfileStoreIntegration:
    """Integration tests simulating real usage patterns."""
    
    def test_user_journey_recommendations(self, any_store: ProfileStoreInterface):
        """Test a typical user journey with recommendations."""
        # User signs up
        profile = any_store.create_profile("alice", language="en")
        assert profile["preferred_tags"] == {}
        
        # User views modern art event, system increases weight
        profile = any_store.update_tag_weights("alice", {"modern": 1})
        assert profile["preferred_tags"]["modern"] == 4  # 3 + 1
        
        # User saves event
        profile = any_store.add_saved_event("alice", "evt_001")
        assert "evt_001" in profile["saved_event_ids"]
        
        # User views more modern art, weight increases
        profile = any_store.update_tag_weights("alice", {"modern": 1})
        assert profile["preferred_tags"]["modern"] == 5  # Clamped at max
        
        # User also likes sculpture
        profile = any_store.update_tag_weights("alice", {"sculpture": 2})
        assert profile["preferred_tags"]["sculpture"] == 5  # 3 + 2
        assert profile["preferred_tags"]["modern"] == 5  # Still 5
    
    def test_multiple_users_isolation(self, any_store: ProfileStoreInterface):
        """Test that multiple users' data is properly isolated."""
        any_store.create_profile("bob", preferred_tags={"digital": 5})
        any_store.create_profile("charlie", preferred_tags={"painting": 3})
        
        bob_profile = any_store.get_profile("bob")
        charlie_profile = any_store.get_profile("charlie")
        
        assert bob_profile["preferred_tags"] == {"digital": 5}
        assert charlie_profile["preferred_tags"] == {"painting": 3}
        
        # Update one shouldn't affect the other
        any_store.update_tag_weights("bob", {"sculpture": 1})
        charlie_check = any_store.get_profile("charlie")
        
        assert "sculpture" not in charlie_check["preferred_tags"]
