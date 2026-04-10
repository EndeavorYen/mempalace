"""
test_session_checkpoint.py — Tests for session checkpoint/restore/list tools.

Tests the session state management tools that enable token-efficient
save→clear→restore cycles. Uses isolated HOME from conftest.py.
"""

import time

from pathlib import Path

from mempalace import mcp_server
from mempalace.mcp_server import (
    _slugify_project,
    _get_state_path,
    tool_session_checkpoint,
    tool_session_restore,
    tool_session_list,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir):
    """Patch mcp_server globals to use test fixtures with isolated sessions dir."""
    monkeypatch.setattr(mcp_server, "_config", config)
    monkeypatch.setattr(mcp_server, "_kg", kg)
    # Isolate _SESSIONS_DIR per test to prevent cross-test leakage
    isolated_sessions = Path(tmp_dir) / "sessions"
    monkeypatch.setattr(mcp_server, "_SESSIONS_DIR", isolated_sessions)


# ── Slugify ──────────────────────────────────────────────────────────────


class TestSlugify:
    def test_basic(self):
        assert _slugify_project("My Project") == "my-project"

    def test_special_chars(self):
        assert _slugify_project("foo@bar!baz") == "foo-bar-baz"

    def test_already_slug(self):
        assert _slugify_project("mempalace") == "mempalace"

    def test_uppercase(self):
        assert _slugify_project("MemPalace") == "mempalace"

    def test_leading_trailing_hyphens(self):
        assert _slugify_project("  --hello--  ") == "hello"


# ── Session Checkpoint ───────────────────────────────────────────────────


class TestSessionCheckpoint:
    def test_writes_state_file(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        result = tool_session_checkpoint(
            project="test-project",
            current_task="Implement feature X",
            progress="- [x] Step 1\n- [ ] Step 2",
            decisions="Chose embedding over regex",
            memory_triggers="embedding vs regex",
            next_steps="Run benchmarks",
        )

        assert result["success"] is True
        assert result["state_written"] is True
        assert result["project"] == "test-project"

        # Verify state.md exists and has correct content
        state_path = _get_state_path("test-project")
        assert state_path.exists()
        content = state_path.read_text()
        assert "Implement feature X" in content
        assert "Step 1" in content
        assert "embedding vs regex" in content
        assert "Run benchmarks" in content

    def test_writes_diary_entry_with_importance(
        self, monkeypatch, config, palace_path, kg, tmp_dir, collection
    ):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        result = tool_session_checkpoint(
            project="test-project",
            current_task="Build auth system",
            progress="- [x] Design\n- [ ] Implement",
        )

        assert result["diary_written"] is True

        # Verify diary entry in ChromaDB has importance=8
        results = collection.get(
            where={"$and": [{"wing": "wing_sessions"}, {"room": "checkpoints"}]},
            include=["documents", "metadatas"],
        )
        assert len(results["ids"]) >= 1
        meta = results["metadatas"][0]
        assert meta["importance"] == 8
        assert meta["topic"] == "session_checkpoint"
        assert meta["project"] == "test-project"
        assert "CHECKPOINT:test-project" in results["documents"][0]

    def test_overwrites_existing_state(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        tool_session_checkpoint(
            project="overwrite-test",
            current_task="Task v1",
            progress="v1 progress",
        )
        tool_session_checkpoint(
            project="overwrite-test",
            current_task="Task v2",
            progress="v2 progress",
        )

        state_path = _get_state_path("overwrite-test")
        content = state_path.read_text()
        assert "Task v2" in content
        assert "Task v1" not in content

    def test_per_project_isolation(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        tool_session_checkpoint(project="alpha", current_task="Alpha task", progress="alpha")
        tool_session_checkpoint(project="beta", current_task="Beta task", progress="beta")

        alpha_content = _get_state_path("alpha").read_text()
        beta_content = _get_state_path("beta").read_text()
        assert "Alpha task" in alpha_content
        assert "Beta task" in beta_content
        assert "Beta task" not in alpha_content

    def test_project_name_slugified(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        result = tool_session_checkpoint(
            project="My Cool Project",
            current_task="test",
            progress="test",
        )
        assert result["project"] == "my-cool-project"
        assert _get_state_path("My Cool Project").exists()

    def test_optional_fields_omitted(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        result = tool_session_checkpoint(
            project="minimal",
            current_task="Just a task",
            progress="- [ ] Do it",
        )
        assert result["success"] is True
        content = _get_state_path("minimal").read_text()
        assert "Just a task" in content
        assert "## Key Decisions" not in content
        assert "## Memory Triggers" not in content

    def test_token_estimate_reasonable(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        result = tool_session_checkpoint(
            project="tokens",
            current_task="test task",
            progress="- [x] done",
        )
        # Token estimate should be positive and reasonable
        assert result["token_estimate"] > 0
        assert result["token_estimate"] < 1000


# ── Session Restore ──────────────────────────────────────────────────────


class TestSessionRestore:
    def test_restore_existing(self, monkeypatch, config, palace_path, kg, tmp_dir, collection):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        tool_session_checkpoint(
            project="restore-test",
            current_task="My task",
            progress="- [x] Done\n- [ ] Todo",
            memory_triggers="- auth decisions\n- database choice",
        )

        result = tool_session_restore(project="restore-test")

        assert result["has_state"] is True
        assert result["project"] == "restore-test"
        assert "My task" in result["state"]
        assert len(result["memory_triggers"]) == 2
        assert "auth decisions" in result["memory_triggers"]
        assert result["token_estimate"] > 0

    def test_restore_no_state_graceful(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        result = tool_session_restore(project="nonexistent")
        assert result["has_state"] is False

    def test_restore_no_projects_graceful(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        result = tool_session_restore(project=None)
        assert result["has_state"] is False
        assert result["projects"] == []

    def test_restore_latest_project(
        self, monkeypatch, config, palace_path, kg, tmp_dir, collection
    ):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        tool_session_checkpoint(project="older", current_task="old", progress="old")
        time.sleep(0.1)  # ensure mtime differs
        tool_session_checkpoint(project="newer", current_task="new", progress="new")

        result = tool_session_restore(project=None)
        assert result["has_state"] is True
        assert result["project"] == "newer"

    def test_restore_includes_wake_up(
        self, monkeypatch, config, palace_path, kg, tmp_dir, collection
    ):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        tool_session_checkpoint(project="wake", current_task="test", progress="test")
        result = tool_session_restore(project="wake")

        # wake_up should be a string (may be empty if no identity.txt)
        assert isinstance(result["wake_up"], str)

    def test_restore_includes_recent_checkpoints(
        self, monkeypatch, config, palace_path, kg, tmp_dir, collection
    ):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        # Create multiple checkpoints
        for i in range(5):
            tool_session_checkpoint(
                project=f"multi-{i}",
                current_task=f"Task {i}",
                progress=f"Progress {i}",
            )

        result = tool_session_restore(project="multi-4")
        # Should return at most 3 recent checkpoints
        assert len(result["recent_checkpoints"]) <= 3


# ── Session List ─────────────────────────────────────────────────────────


class TestSessionList:
    def test_empty_list(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        result = tool_session_list()
        assert result["count"] == 0
        assert result["projects"] == []

    def test_lists_projects(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        tool_session_checkpoint(project="proj-a", current_task="a", progress="a")
        tool_session_checkpoint(project="proj-b", current_task="b", progress="b")

        result = tool_session_list()
        assert result["count"] == 2
        names = [p["project"] for p in result["projects"]]
        assert "proj-a" in names
        assert "proj-b" in names

    def test_sorted_by_recency(self, monkeypatch, config, palace_path, kg, tmp_dir):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        tool_session_checkpoint(project="first", current_task="1", progress="1")
        time.sleep(0.1)
        tool_session_checkpoint(project="second", current_task="2", progress="2")

        result = tool_session_list()
        assert result["projects"][0]["project"] == "second"


# ── Integration: Full Cycle ──────────────────────────────────────────────


class TestFullCycle:
    def test_checkpoint_restore_roundtrip(
        self, monkeypatch, config, palace_path, kg, tmp_dir, collection
    ):
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        # Save
        tool_session_checkpoint(
            project="roundtrip",
            current_task="Implement embedding classifier",
            progress="- [x] Data prep\n- [x] Model selection\n- [ ] Integration",
            decisions="Chose MiniLM over BERT for speed",
            memory_triggers="- embedding model comparison\n- MiniLM benchmarks",
            next_steps="Integrate with miner.py",
        )

        # Restore
        result = tool_session_restore(project="roundtrip")

        assert result["has_state"] is True
        assert "Implement embedding classifier" in result["state"]
        assert "MiniLM over BERT" in result["state"]
        assert len(result["memory_triggers"]) == 2
        assert "embedding model comparison" in result["memory_triggers"]
        assert result["token_estimate"] > 0

    def test_checkpoint_diary_has_importance_8(
        self, monkeypatch, config, palace_path, kg, tmp_dir, collection
    ):
        """Verify importance=8 lands in ChromaDB metadata for L1 scoring."""
        _patch_mcp(monkeypatch, config, palace_path, kg, tmp_dir)

        tool_session_checkpoint(
            project="importance-test",
            current_task="Test importance",
            progress="testing",
        )

        # Query ChromaDB directly
        results = collection.get(
            where={"$and": [{"wing": "wing_sessions"}, {"room": "checkpoints"}]},
            include=["metadatas"],
        )

        found = False
        for meta in results["metadatas"]:
            if meta.get("project") == "importance-test":
                assert meta["importance"] == 8
                found = True
        assert found, "Checkpoint diary entry not found in ChromaDB"
