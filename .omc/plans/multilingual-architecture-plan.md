# Multilingual Architecture Plan for Mempalace

## Metadata
- Plan ID: multilingual-architecture
- Created: 2026-04-08
- Revised: 2026-04-08 (iteration 2 -- Architect/Critic feedback incorporated)
- Spec: `.omc/specs/deep-interview-multilingual-support.md`
- Type: brownfield (modify existing codebase)
- Estimated Complexity: HIGH

---

## RALPLAN-DR Summary

### Principles (5)
1. **Bilingual Preservation** -- English functionality must never regress. All existing tests pass at every phase.
2. **Language-Agnostic Foundation** -- Architecture enables arbitrary language addition; Chinese is the first concrete implementation.
3. **Minimal Invasion** -- Modify 12 existing modules surgically. No project restructure, no new abstractions beyond what's needed.
4. **Local-Only** -- No external API dependencies. Language detection, segmentation, embeddings all run locally.
5. **Progressive Enhancement** -- Each phase produces a working system. No big-bang integration.

### Decision Drivers (top 3)
1. **Embedding model choice** -- Determines whether Chinese semantic search works at all. Must be multilingual, must be configurable, must not break existing palaces.
2. **Language detection accuracy** -- Drives correct routing to Chinese vs English pattern sets. False positives (treating English as Chinese) would corrupt extraction.
3. **Pattern organization** -- How Chinese patterns coexist with English patterns in each module affects maintainability and future language additions.

### Viable Options

#### Option A: Inline Patterns with Language Dispatch (RECOMMENDED)
Add Chinese patterns directly into existing modules alongside English patterns. A shared `language_detect.py` module provides detection. Each module checks language and selects the appropriate pattern set.

**Pros:**
- Minimal file count change (1 new file + 12 modified files)
- Easy to review: all patterns visible in one place per module
- No import indirection or plugin loading complexity
- Matches current codebase style (flat, explicit)

**Cons:**
- Modules grow larger (manageable: ~50-100 lines of Chinese patterns each)
- Adding a third language later means touching all modules again

#### Option B: External Pattern Files with Registry
Create `mempalace/lang/` directory with per-language pattern files (`en.py`, `zh.py`). Each module loads patterns from the registry by language code.

**Pros:**
- Clean separation of language data from logic
- Adding new languages requires only new files + registration
- Smaller individual modules

**Cons:**
- Adds structural complexity (new package, registry pattern, dynamic loading)
- Over-engineers for the current 2-language scope
- Diverges from codebase style (currently no sub-packages)
- More indirection makes debugging harder

**Decision:** Option A. The codebase is flat and explicit. Two languages don't justify a registry. If a third language is added, the inline approach can be refactored then with clear patterns to follow.

---

## Context

### Current State
- ChromaDB collections use **default embedding** (ChromaDB's built-in `all-MiniLM-L6-v2`) -- English-only
- No `embedding_function` parameter is passed to any `get_collection`/`create_collection`/`get_or_create_collection` call across **all 7 consumer modules** (searcher, miner, convo_miner, mcp_server, layers, palace_graph, cli)
- All pattern matching is English regex (`\b` word boundaries, Latin character classes)
- `entity_detector.py` extracts candidates via `r"\b([A-Z][a-z]{1,19})\b"` -- only matches Latin capitalized words
- `spellcheck.py` hardcodes `Speller(lang="en")`
- `dialect.py` has English-only `_STOP_WORDS` set (~120 words) and `_extract_topics()` uses `r"[a-zA-Z][a-zA-Z_-]{2,}"` which only matches Latin characters
- `config.py` has no language or embedding model settings
- Dependencies: `chromadb>=0.5.0,<0.7`, `pyyaml>=6.0`, optional `autocorrect`

### Key Files
| File | Lines | Role | Collection Access |
|------|-------|------|-------------------|
| `mempalace/config.py` | 150 | Configuration (env > file > defaults) | -- |
| `mempalace/searcher.py` | 153 | Search via ChromaDB query | `get_collection` x2 |
| `mempalace/miner.py` | ~450 | Project file mining into palace | `get_collection`/`create_collection` + bare `get_collection` in `status()` at L650 |
| `mempalace/convo_miner.py` | 404 | Conversation mining + room detection | `get_collection`/`create_collection` |
| `mempalace/mcp_server.py` | ~400 | Primary MCP interface | `_get_collection()` called 13+ times, uses `get_or_create_collection` and `get_collection` |
| `mempalace/layers.py` | ~450 | Layer generation (L1/L2/L3) | `get_collection` x5 (lines 95, 200, 264, 320, 441) |
| `mempalace/palace_graph.py` | ~80 | Graph visualization | `_get_collection()` wrapper, `get_collection` x1 |
| `mempalace/cli.py` | ~350 | CLI entry point (repair, compress, etc.) | `get_collection` x2, `create_collection` x1, `get_or_create_collection` x1 |
| `mempalace/entity_detector.py` | 854 | Entity candidate extraction + scoring | -- |
| `mempalace/general_extractor.py` | 522 | Decision/preference/milestone/problem/emotion extraction | -- |
| `mempalace/spellcheck.py` | 270 | Spell-correction for user text | -- |
| `mempalace/dialect.py` | ~350+ | AAAK dialect compression + stopwords | -- |

### Modules Reviewed and Excluded
| File | Reason |
|------|--------|
| `mempalace/room_detector_local.py` | Uses folder-name mapping (e.g., "frontend", "backend"). Folder names are language-neutral technical terms. No language-dependent logic. |
| `mempalace/knowledge_graph.py` | Stores entity triples in SQLite. Entity names are opaque strings -- works with any charset already. No pattern matching. |
| `mempalace/entity_registry.py` | Has `COMMON_ENGLISH_WORDS` set for disambiguation but this is additive -- Chinese names won't collide with English common words. No changes needed for Chinese support. |
| `mempalace/normalize.py` | Format detection (JSON, JSONL, plain text). Uses structural markers (`>`, JSON keys), not language-dependent patterns. Already handles UTF-8. |

---

## Work Objectives

Build a general-purpose multilingual architecture with Chinese as the first non-English language, modifying 12 existing modules and adding 1 new infrastructure module. Centralize the embedding function helper in `config.py` to eliminate duplication across 7 consumer modules.

## Guardrails

### Must Have
- All 10 acceptance criteria from the spec met with pytest tests
- Every existing test passes after every phase
- Embedding model configurable via `config.json` and env var
- Language auto-detection at file and chunk level
- Chinese patterns for entity detection, room classification, content extraction
- Spellcheck bypass for non-English content
- Centralized `_get_embedding_function()` in `config.py` -- single source of truth
- All Chinese pattern lists include both simplified AND traditional variants where they differ
- Explicit `CHINESE_STOPWORDS` set defined for entity detection false-positive filtering
- CJK tokenizer pass in `dialect.py` `_extract_topics()`
- Runtime warning when `sentence-transformers` is not installed (not silent `None` return)
- Embedding model name stored in collection metadata for mismatch detection

### Must NOT Have
- Project restructuring (no new sub-packages like `mempalace/lang/`)
- UI/CLI internationalization
- Classical Chinese compression
- New external service dependencies
- Breaking changes to existing API signatures (only additive parameters)
- Duplicated `_get_embedding_function()` across modules -- must import from `config.py`

---

## Task Flow (5 Phases)

```
Phase 1: Foundation (config.py + language_detect.py)
    |
    v
Phase 2: Search Infrastructure (config.py embedding helper + ALL 7 collection consumers)
    |        searcher.py, miner.py, convo_miner.py, mcp_server.py,
    |        layers.py, palace_graph.py, cli.py
    v
Phase 3: Pattern Modules (entity_detector.py + convo_miner.py + general_extractor.py)
    |
    v
Phase 4: Guard Modules (spellcheck.py + dialect.py)
    |
    v
Phase 5: Integration Testing + Documentation
```

---

## Phase 1: Foundation -- Config + Language Detection

**Goal:** Establish configuration for embedding model and language, plus a reusable language detection module. Centralize the embedding function helper in `config.py`.

### 1.1 Modify `mempalace/config.py`

**Changes:**
- Add `embedding_model` property (default: `"paraphrase-multilingual-MiniLM-L12-v2"`)
- Add `language` property (default: `"auto"` -- auto-detect; can be set to `"en"`, `"zh"`, etc.)
- Support env var overrides: `MEMPALACE_EMBEDDING_MODEL`, `MEMPALACE_LANGUAGE`
- Add these to `init()` default config output
- Add centralized `get_embedding_function()` as a module-level function (not a method) so all consumers import from here

**Specific edits:**

After line 12 (`DEFAULT_COLLECTION_NAME`), add:
```python
DEFAULT_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_LANGUAGE = "auto"
```

Add two new properties to `MempalaceConfig` class:
```python
@property
def embedding_model(self):
    """Embedding model name for ChromaDB collections."""
    env_val = os.environ.get("MEMPALACE_EMBEDDING_MODEL")
    if env_val:
        return env_val
    return self._file_config.get("embedding_model", DEFAULT_EMBEDDING_MODEL)

@property
def language(self):
    """Language setting: 'auto', 'en', 'zh', etc."""
    env_val = os.environ.get("MEMPALACE_LANGUAGE")
    if env_val:
        return env_val
    return self._file_config.get("language", DEFAULT_LANGUAGE)
```

Add centralized embedding function helper (module-level, after class definition):
```python
import logging

_logger = logging.getLogger(__name__)

def get_embedding_function(model_name: str = None):
    """Get ChromaDB-compatible embedding function for the configured model.
    
    This is the SINGLE source of truth for embedding functions.
    All modules that access ChromaDB collections MUST import this.
    
    Returns SentenceTransformerEmbeddingFunction or None (ChromaDB default fallback).
    Logs a warning on fallback so users can diagnose missing multilingual support.
    """
    if model_name is None:
        model_name = MempalaceConfig().embedding_model
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        return SentenceTransformerEmbeddingFunction(model_name=model_name)
    except ImportError:
        _logger.warning(
            "sentence-transformers not installed. Chinese semantic search will not work. "
            "Install with: pip install 'mempalace[multilingual]'"
        )
        return None
    except Exception as e:
        _logger.warning(f"Failed to load embedding model '{model_name}': {e}. Falling back to ChromaDB default.")
        return None
```

Update `init()` method's `default_config` dict to include:
```python
"embedding_model": DEFAULT_EMBEDDING_MODEL,
"language": DEFAULT_LANGUAGE,
```

### 1.2 Create `mempalace/language_detect.py`

**New file.** Language detection module using Unicode range heuristics (no external dependency).

**Functions:**
```python
def detect_language(text: str) -> str:
    """Detect primary language of text. Returns 'zh', 'en', or 'unknown'.
    Uses Unicode range analysis: CJK Unified Ideographs (U+4E00-U+9FFF).
    """

def detect_chunk_language(text: str) -> str:
    """Chunk-level detection with lower thresholds for mixed content."""

def is_chinese(text: str) -> bool:
    """Quick check: does text contain significant Chinese characters?"""

def get_chinese_ratio(text: str) -> float:
    """Return ratio of Chinese characters to total alphabetic+CJK characters."""
```

**Implementation details:**
- Count characters in CJK Unified Ideographs range (U+4E00 to U+9FFF)
- File-level: >10% CJK characters => `"zh"`; <1% => `"en"`; between => check chunk-level
- Chunk-level: >5% CJK => `"zh"` (lower threshold for mixed content)
- No external dependencies (pure Unicode analysis)

### 1.3 Tests for Phase 1

**New file: `tests/test_language_detect.py`**
```
- test_detect_pure_english() -> "en"
- test_detect_pure_chinese() -> "zh"  
- test_detect_mixed_content() -> "zh" (mixed defaults to zh when significant CJK present)
- test_detect_english_with_chinese_names() -> handles edge case
- test_is_chinese_true/false
- test_get_chinese_ratio()
- test_empty_string()
```

**Update `tests/test_config.py`:**
```
- test_embedding_model_default() -> assert "multilingual" in model name
- test_embedding_model_env_override()
- test_language_default() -> "auto"
- test_language_env_override()
- test_init_includes_new_fields() -> verify config.json has embedding_model + language
- test_get_embedding_function_returns_ef() -> when sentence-transformers installed
- test_get_embedding_function_fallback_warns() -> when NOT installed, verify warning is logged
```

**Acceptance criteria:**
- [ ] `MempalaceConfig().embedding_model` returns `"paraphrase-multilingual-MiniLM-L12-v2"` by default
- [ ] `MempalaceConfig().language` returns `"auto"` by default
- [ ] Both can be overridden via env vars and config file
- [ ] `detect_language("这是中文内容")` returns `"zh"`
- [ ] `detect_language("This is English")` returns `"en"`
- [ ] `detect_language("小明用 Python 写了一个组件")` returns `"zh"` (mixed content)
- [ ] `get_embedding_function()` returns a `SentenceTransformerEmbeddingFunction` when sentence-transformers is installed
- [ ] `get_embedding_function()` returns `None` AND logs a warning when sentence-transformers is NOT installed
- [ ] All existing tests pass

---

## Phase 2: Search Infrastructure -- Configurable Embedding Model Across ALL Consumers

**Goal:** Make ALL ChromaDB collection access points use the centralized configurable multilingual embedding model so Chinese semantic search works. Store model metadata for mismatch detection.

**CRITICAL: There are 7 modules that access ChromaDB collections. ALL must be updated.**

### 2.1 Modify `mempalace/searcher.py`

**Changes:**
- Import `get_embedding_function` from `config.py`
- Pass `embedding_function=get_embedding_function()` to both `get_collection()` calls (lines 28, 102)

**Specific edits:**

Add import (after existing imports):
```python
from .config import get_embedding_function
```

Modify `search()` (line 28) and `search_memories()` (line 102):
```python
col = client.get_collection("mempalace_drawers", embedding_function=get_embedding_function())
```

### 2.2 Modify `mempalace/miner.py`

**Changes:**
- Import `get_embedding_function` from `config.py`
- Update `get_collection()` (line 396-402): pass embedding function to both `get_collection` and `create_collection`
- Update `status()` (line 650): pass embedding function to `get_collection`
- On `create_collection`, store model name in collection metadata for mismatch detection

```python
from .config import MempalaceConfig, get_embedding_function

def get_collection(palace_path: str):
    os.makedirs(palace_path, exist_ok=True)
    client = chromadb.PersistentClient(path=palace_path)
    ef = get_embedding_function()
    try:
        col = client.get_collection("mempalace_drawers", embedding_function=ef)
        _check_model_mismatch(col)
        return col
    except Exception:
        return client.create_collection(
            "mempalace_drawers",
            embedding_function=ef,
            metadata={"embedding_model": MempalaceConfig().embedding_model},
        )
```

In `status()` (line 650):
```python
ef = get_embedding_function()
col = client.get_collection("mempalace_drawers", embedding_function=ef)
```

### 2.3 Modify `mempalace/convo_miner.py`

**Changes to `get_collection()` (line 214-220):**
- Import `get_embedding_function` from `config.py`
- Pass embedding function to both `get_collection` and `create_collection`
- Store model name in metadata on create

```python
from .config import MempalaceConfig, get_embedding_function

def get_collection(palace_path: str):
    os.makedirs(palace_path, exist_ok=True)
    client = chromadb.PersistentClient(path=palace_path)
    ef = get_embedding_function()
    try:
        return client.get_collection("mempalace_drawers", embedding_function=ef)
    except Exception:
        return client.create_collection(
            "mempalace_drawers",
            embedding_function=ef,
            metadata={"embedding_model": MempalaceConfig().embedding_model},
        )
```

### 2.4 Modify `mempalace/mcp_server.py` (PRIMARY MCP INTERFACE -- CRITICAL)

**This is the most critical module: `_get_collection()` is called 13+ times and is the primary MCP interface for all external consumers.**

**Changes to `_get_collection()` (line 42-50):**
- Import `get_embedding_function` from `config.py`
- Pass embedding function to both `get_or_create_collection` and `get_collection`
- Store model name in metadata on create

```python
from .config import MempalaceConfig, get_embedding_function

def _get_collection(create=False):
    """Return the ChromaDB collection, or None on failure."""
    try:
        client = chromadb.PersistentClient(path=_config.palace_path)
        ef = get_embedding_function()
        if create:
            return client.get_or_create_collection(
                _config.collection_name,
                embedding_function=ef,
                metadata={"embedding_model": _config.embedding_model},
            )
        return client.get_collection(_config.collection_name, embedding_function=ef)
    except Exception:
        return None
```

**Impact:** All 13+ call sites (`_get_collection()` and `_get_collection(create=True)`) are fixed by updating this single wrapper. No other changes needed in `mcp_server.py`.

### 2.5 Modify `mempalace/layers.py`

**Changes:** 5 bare `get_collection` calls at lines 95, 200, 264, 320, 441.

- Import `get_embedding_function` from `config.py`
- Pass embedding function to all 5 `client.get_collection()` calls

```python
from .config import get_embedding_function

# At each of the 5 call sites, change:
#   col = client.get_collection("mempalace_drawers")
# to:
#   col = client.get_collection("mempalace_drawers", embedding_function=get_embedding_function())
```

### 2.6 Modify `mempalace/palace_graph.py`

**Changes to `_get_collection()` (line 24-30):**
- Import `get_embedding_function` from `config.py`
- Pass embedding function to `get_collection`

```python
from .config import get_embedding_function

def _get_collection(config=None):
    config = config or MempalaceConfig()
    try:
        client = chromadb.PersistentClient(path=config.palace_path)
        return client.get_collection(config.collection_name, embedding_function=get_embedding_function())
    except Exception:
        return None
```

### 2.7 Modify `mempalace/cli.py`

**Changes:** 4 collection access points at lines 177, 213, 253, 324.

- Import `get_embedding_function` from `config.py`
- Pass embedding function to all `get_collection`, `create_collection`, and `get_or_create_collection` calls
- On `create_collection` (line 213, repair rebuild), store model metadata

```python
from .config import MempalaceConfig, get_embedding_function

# Line 177 (repair read):
col = client.get_collection("mempalace_drawers", embedding_function=get_embedding_function())

# Line 213 (repair rebuild):
new_col = client.create_collection(
    "mempalace_drawers",
    embedding_function=get_embedding_function(),
    metadata={"embedding_model": MempalaceConfig().embedding_model},
)

# Line 253 (compress read):
col = client.get_collection("mempalace_drawers", embedding_function=get_embedding_function())

# Line 324 (compressed collection):
comp_col = client.get_or_create_collection(
    "mempalace_compressed",
    embedding_function=get_embedding_function(),
    metadata={"embedding_model": MempalaceConfig().embedding_model},
)
```

### 2.8 Add model mismatch detection helper

**Add to `mempalace/config.py` (alongside `get_embedding_function`):**

```python
def check_embedding_model_mismatch(collection) -> bool:
    """Check if collection was created with a different embedding model.
    
    Returns True if there's a mismatch (caller should log warning).
    Returns False if models match or metadata is unavailable.
    """
    try:
        col_meta = collection.metadata or {}
        stored_model = col_meta.get("embedding_model")
        if stored_model and stored_model != MempalaceConfig().embedding_model:
            _logger.warning(
                f"Embedding model mismatch: collection was created with '{stored_model}' "
                f"but current config uses '{MempalaceConfig().embedding_model}'. "
                f"Search quality may be degraded. Re-mine to fix: mempalace mine <dir>"
            )
            return True
    except Exception:
        pass
    return False
```

Call this from `miner.py:get_collection()` and `mcp_server.py:_get_collection()` after successful `get_collection`.

### 2.9 Add `sentence-transformers` as optional dependency

**Modify `pyproject.toml`:**
```toml
[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.4.0"]
spellcheck = ["autocorrect>=2.0"]
multilingual = ["sentence-transformers>=2.0"]
```

### 2.10 Tests for Phase 2

**Update `tests/test_searcher.py`:**
```
- test_chinese_semantic_search() -- seed collection with Chinese text, query in Chinese, verify results returned
- test_mixed_language_search() -- seed with mixed content, query in either language
```

**New file: `tests/test_embedding_fallback.py`:**
```
- test_get_embedding_function_fallback_logs_warning() -- mock sentence-transformers as unavailable, verify warning logged
- test_model_mismatch_detection() -- create collection with model A metadata, configure model B, verify warning
- test_no_mismatch_when_models_match() -- verify no warning when models match
- test_no_mismatch_when_no_metadata() -- verify graceful handling of old collections without metadata
```

**Update `tests/conftest.py`:**
- Add `seeded_collection_multilingual` fixture with Chinese content:
  ```python
  "认证模块使用 JWT 令牌进行会话管理。令牌在24小时后过期。",
  "数据库迁移由 Alembic 处理。我们使用 PostgreSQL 15。",
  ```

**Acceptance criteria:**
- [ ] `get_embedding_function()` lives in `config.py` -- single source of truth
- [ ] `get_embedding_function()` logs a warning (not silent) when sentence-transformers is not installed
- [ ] ALL 7 consumer modules import `get_embedding_function` from `config.py` -- no local copies
- [ ] `mcp_server.py:_get_collection()` passes embedding function (covers all 13+ call sites)
- [ ] `layers.py` all 5 `get_collection` calls pass embedding function
- [ ] `palace_graph.py:_get_collection()` passes embedding function
- [ ] `cli.py` all 4 collection access points pass embedding function
- [ ] `miner.py:status()` (line 650) passes embedding function
- [ ] New collections store `embedding_model` in metadata
- [ ] Model mismatch between config and stored metadata produces a logged warning
- [ ] Chinese query against Chinese-seeded collection returns relevant results
- [ ] English queries against English-seeded collection still work (no regression)
- [ ] All existing tests pass

---

## Phase 3: Pattern Modules -- Chinese Entity Detection, Room Classification, Content Extraction

**Goal:** Add Chinese patterns to the three content-analysis modules. All pattern lists must include both simplified and traditional Chinese variants where they differ.

### 3.1 Modify `mempalace/entity_detector.py`

**Changes:**

**a) Define `CHINESE_STOPWORDS` set (false positives -- common words starting with surname characters):**

```python
CHINESE_STOPWORDS = {
    # Common 2-char words that start with surname characters but are NOT names
    "王国",  # kingdom (王)
    "张开",  # open/spread (张/張)
    "李子",  # plum (李)
    "陈述",  # state/declare (陈/陳)
    "刘海",  # bangs/fringe (刘/劉)
    "黄金",  # gold (黄/黃)
    "赵钱",  # as compound phrase (赵/趙)
    "周围",  # surroundings (周)
    "周末",  # weekend (周)
    "周期",  # cycle/period (周)
    "吴语",  # Wu language (吴/吳)
    "徐徐",  # slowly (徐)
    "马上",  # immediately (马/馬)
    "马路",  # road (马/馬)
    "胡说",  # nonsense (胡)
    "胡乱",  # recklessly (胡)
    "朱红",  # vermillion (朱)
    "何况",  # let alone (何)
    "何必",  # why bother (何)
    "林立",  # stand in great numbers (林)
    "高兴",  # happy (高)
    "高度",  # height/highly (高)
    "许多",  # many (许/許)
    # Traditional variants of the above
    "張開", "陳述", "劉海", "黃金", "趙錢", "吳語", "馬上", "馬路", "許多",
}
```

**b) Add Chinese name extraction to `extract_candidates()` (line 443-463):**

After the existing English candidate extraction, add Chinese name detection:
```python
# Chinese person names: 2-3 character sequences starting with common surnames
# Common surname characters (百家姓 top surnames, both simplified and traditional)
CHINESE_SURNAMES = set(
    "王李张張刘劉陈陳杨楊黄黃赵趙周吴吳徐孙孫马馬胡朱郭何林罗羅高梁郑鄭"
    "谢謝宋唐许許邓鄧冯馮韩韓曹曾彭萧蕭蔡潘田董袁于余叶葉蒋蔣杜苏蘇魏程"
    "吕呂丁沈任姚卢盧傅钟鍾"
)

def _extract_chinese_names(text: str) -> dict:
    """Extract Chinese person name candidates (2-4 chars starting with common surname)."""
    counts = defaultdict(int)
    surname_chars = ''.join(CHINESE_SURNAMES)
    for match in re.finditer(r'([' + surname_chars + r'][\u4e00-\u9fff]{1,3})', text):
        name = match.group(1)
        if len(name) >= 2 and name not in CHINESE_STOPWORDS:
            counts[name] += 1
    return {name: count for name, count in counts.items() if count >= 2}
```

**c) Add Chinese verb patterns for person scoring (alongside `PERSON_VERB_PATTERNS`):**

**NOTE: Every entry must include both simplified AND traditional forms where they differ.**

```python
CHINESE_PERSON_VERB_PATTERNS = [
    r"{name}说",      # said (simplified)
    r"{name}說",      # said (traditional)
    r"{name}问",      # asked (simplified)
    r"{name}問",      # asked (traditional)
    r"{name}认为",    # thinks (simplified)
    r"{name}認為",    # thinks (traditional)
    r"{name}觉得",    # feels (simplified)
    r"{name}覺得",    # feels (traditional)
    r"{name}告诉",    # told (simplified)
    r"{name}告訴",    # told (traditional)
    r"{name}回答",    # replied (same in both)
    r"{name}笑了",    # laughed (same in both)
    r"{name}决定",    # decided (simplified)
    r"{name}決定",    # decided (traditional)
    r"{name}喜欢",    # likes (simplified)
    r"{name}喜歡",    # likes (traditional)
    r"{name}讨厌",    # hates (simplified)
    r"{name}討厭",    # hates (traditional)
]
```

**d) Add Chinese dialogue patterns (both simplified and traditional):**
```python
CHINESE_DIALOGUE_PATTERNS = [
    r"^{name}[：:]",     # Speaker: (Chinese + ASCII colon)
    r"^【{name}】",      # [Speaker] (Chinese brackets)
    r"「{name}」",       # Chinese quotes with name
    r""{name}"",         # Chinese double quotes
]
```

**e) Modify `extract_candidates()` to call `_extract_chinese_names()` and merge results.**

**f) Modify `score_entity()` to also check Chinese verb/dialogue patterns when the name contains CJK characters.**

### 3.2 Modify `mempalace/convo_miner.py`

**Changes to `TOPIC_KEYWORDS` dict (line 129-193) and `detect_convo_room()` (line 196-206):**

Add Chinese keyword equivalents for each room. **Every keyword with a simplified/traditional difference includes BOTH forms:**

```python
TOPIC_KEYWORDS_ZH = {
    "technical": [
        "代码", "代碼", "程式", "函数", "函數", "错误", "錯誤",
        "接口", "数据库", "資料庫", "服务器", "伺服器", "部署",
        "测试", "測試", "调试", "調試", "重构", "重構",
    ],
    "architecture": [
        "架构", "架構", "设计", "設計", "模式", "结构", "結構",
        "模块", "模組", "组件", "元件", "服务", "服務",
    ],
    "planning": [
        "计划", "計畫", "路线图", "路線圖", "里程碑", "截止日期",
        "优先级", "優先級", "冲刺", "衝刺", "需求", "规格", "規格",
    ],
    "decisions": [
        "决定", "決定", "选择", "選擇", "切换", "切換",
        "迁移", "遷移", "替换", "替換", "权衡", "權衡",
        "方案", "策略",
    ],
    "problems": [
        "问题", "問題", "故障", "崩溃", "崩潰", "卡住",
        "修复", "修復", "解决", "解決", "变通", "變通", "bug",
    ],
}
```

Modify `detect_convo_room()` to merge scores from both `TOPIC_KEYWORDS` and `TOPIC_KEYWORDS_ZH`:
```python
def detect_convo_room(content: str) -> str:
    content_lower = content[:3000].lower()
    scores = {}
    # Score against English keywords
    for room, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            scores[room] = scores.get(room, 0) + score
    # Score against Chinese keywords (no .lower() needed for CJK)
    content_snippet = content[:3000]
    for room, keywords in TOPIC_KEYWORDS_ZH.items():
        score = sum(1 for kw in keywords if kw in content_snippet)
        if score > 0:
            scores[room] = scores.get(room, 0) + score
    if scores:
        return max(scores, key=scores.get)
    return "general"
```

### 3.3 Modify `mempalace/general_extractor.py`

**Changes:** Add Chinese marker patterns for each of the 5 memory types. **All entries include simplified AND traditional variants.**

**a) Add Chinese marker sets (after the English ones, ~line 162):**

```python
CHINESE_DECISION_MARKERS = [
    r"我们决定", r"我們決定", r"选择了", r"選擇了", r"用.*代替", r"而不是",
    r"权衡", r"權衡", r"利弊", r"方案", r"策略", r"架构", r"架構",
    r"框架", r"配置为", r"配置為", r"设为", r"設為", r"因为", r"因為",
]

CHINESE_PREFERENCE_MARKERS = [
    r"我偏好", r"我喜欢", r"我喜歡", r"总是用", r"總是用",
    r"总是使用", r"總是使用", r"永远不要", r"永遠不要",
    r"千万不要", r"千萬不要", r"我的习惯", r"我的習慣",
    r"我的风格", r"我的風格", r"用.*而不用",
    r"风格", r"風格", r"惯例", r"慣例",
]

CHINESE_MILESTONE_MARKERS = [
    r"成功了", r"搞定了", r"终于", r"終於", r"突破", r"第一次",
    r"发现了", r"發現了", r"原来是", r"原來是", r"关键是", r"關鍵是",
    r"实现了", r"實現了", r"上线了", r"上線了",
    r"发布", r"發布", r"部署了", r"版本",
]

CHINESE_PROBLEM_MARKERS = [
    r"错误", r"錯誤", r"崩溃", r"崩潰", r"失败", r"失敗",
    r"不工作", r"有问题", r"有問題", r"根本原因",
    r"修复", r"修復", r"解决方案", r"解決方案",
    r"变通方法", r"變通方法", r"bug",
]

CHINESE_EMOTION_MARKERS = [
    r"爱", r"愛", r"害怕", r"骄傲", r"驕傲", r"开心", r"開心",
    r"难过", r"難過", r"想念", r"感恩", r"生气", r"生氣",
    r"担心", r"擔心", r"孤独", r"孤獨", r"美丽", r"美麗",
    r"我觉得", r"我覺得", r"我不能", r"我希望", r"我需要",
]

ALL_MARKERS_ZH = {
    "decision": CHINESE_DECISION_MARKERS,
    "preference": CHINESE_PREFERENCE_MARKERS,
    "milestone": CHINESE_MILESTONE_MARKERS,
    "problem": CHINESE_PROBLEM_MARKERS,
    "emotional": CHINESE_EMOTION_MARKERS,
}
```

**b) Modify `extract_memories()` (line 363) to also score against Chinese markers:**

In the scoring loop (line 385-389), add:
```python
# Also score against Chinese markers
for mem_type, markers in ALL_MARKERS_ZH.items():
    score, _ = _score_markers(prose, markers)
    if score > 0:
        scores[mem_type] = scores.get(mem_type, 0) + score
```

**c) Add Chinese positive/negative words to sentiment analysis (both simplified and traditional):**
```python
POSITIVE_WORDS_ZH = {
    "开心", "開心", "快乐", "快樂", "成功", "突破",
    "解决", "解決", "完成", "喜欢", "喜歡", "爱", "愛",
    "感恩", "骄傲", "驕傲",
}
NEGATIVE_WORDS_ZH = {
    "错误", "錯誤", "崩溃", "崩潰", "失败", "失敗",
    "问题", "問題", "故障", "糟糕", "困难", "困難",
    "卡住", "恐慌",
}
```

Update `_get_sentiment()` to check both English and Chinese word sets.

### 3.4 Tests for Phase 3

**New file: `tests/test_entity_detector_chinese.py`**
```
- test_extract_chinese_names() -- "张三说了很多话，张三还提到了项目" -> detects 张三
- test_chinese_stopwords_filtered() -- "王国很大" does NOT detect 王国 as a name
- test_chinese_person_verb_signals() -- "小明说" scores as person
- test_traditional_chinese_verb_signals() -- "小明說" also scores as person
- test_mixed_name_detection() -- "Simon 说了..." detected
- test_chinese_dialogue_pattern() -- "小明：你好" scores dialogue signal
- test_english_detection_unchanged() -- existing English patterns still work
```

**New file: `tests/test_convo_miner_chinese.py`**
```
- test_chinese_technical_room() -- content with "代码" "调试" -> room "technical"
- test_traditional_chinese_technical_room() -- content with "代碼" "調試" -> room "technical"
- test_chinese_decisions_room() -- content with "决定" "选择" -> room "decisions"
- test_chinese_problems_room() -- content with "错误" "崩溃" -> room "problems"
- test_mixed_content_room() -- Chinese + English keywords score together
- test_english_room_detection_unchanged() -- existing behavior preserved
```

**New file: `tests/test_general_extractor_chinese.py`**
```
- test_chinese_decision_extraction() -- "我们决定用 GraphQL" -> decision memory
- test_traditional_decision_extraction() -- "我們決定用 GraphQL" -> decision memory
- test_chinese_preference_extraction() -- "我偏好函数式风格" -> preference memory
- test_chinese_milestone_extraction() -- "终于成功了" -> milestone memory
- test_chinese_problem_extraction() -- "这个 bug 导致崩溃" -> problem memory
- test_chinese_emotion_extraction() -- "我真的很开心" -> emotional memory
- test_english_extraction_unchanged() -- existing English patterns still work
```

**Acceptance criteria:**
- [ ] Chinese names (张三, 小明, 王大明) are detected by `extract_candidates()`
- [ ] `CHINESE_STOPWORDS` set has 15+ entries and filters false positives (王国, 马上, etc.)
- [ ] Stopwords include both simplified and traditional variants
- [ ] Chinese person verb patterns fire correctly in `score_entity()` for BOTH simplified AND traditional
- [ ] Chinese technical content classifies to "technical" room
- [ ] Chinese decision/planning/problem content classifies to correct rooms
- [ ] Chinese decision/preference/milestone/problem/emotion markers fire in `extract_memories()`
- [ ] Traditional Chinese variants fire alongside simplified variants in ALL pattern lists
- [ ] All existing English tests pass unchanged

---

## Phase 4: Guard Modules -- Spellcheck + Dialect

**Goal:** Ensure spellcheck skips Chinese text and dialect handles Chinese stopwords and CJK tokenization.

### 4.1 Modify `mempalace/spellcheck.py`

**Changes:**

**a) Import language detection (after line 4):**
```python
from .language_detect import is_chinese
```

**b) Add Chinese character skip to `_should_skip()` (line 88-107):**

Add early return for tokens containing CJK characters:
```python
# Skip Chinese/CJK characters entirely
if any('\u4e00' <= c <= '\u9fff' for c in token):
    return True
```

**c) Modify `spellcheck_user_text()` (line 161-212):**

Add early return for predominantly Chinese text:
```python
def spellcheck_user_text(text: str, known_names: Optional[set] = None) -> str:
    # Skip spellcheck entirely for Chinese-dominant text
    if is_chinese(text):
        return text
    # ... rest of existing logic
```

### 4.2 Modify `mempalace/dialect.py`

**Changes to `_STOP_WORDS` set (line 161-295), `_extract_topics()` (line 436), and `_EMOTION_SIGNALS` / `_FLAG_SIGNALS`:**

**a) Add Chinese stopwords set (after `_STOP_WORDS`):**
```python
_STOP_WORDS_ZH = {
    "的", "了", "着", "过", "過", "把", "被", "和", "与", "與",
    "或", "但", "而", "在", "从", "從", "到", "对", "對",
    "向", "为", "為", "以", "就", "也", "都", "又",
    "不", "没", "沒", "很", "太", "最", "更", "还", "還",
    "再", "已", "正", "这", "這", "那", "哪",
    "什么", "什麼", "怎么", "怎麼", "如何", "为什么", "為什麼",
    "我", "你", "他", "她", "它", "我们", "我們", "你们", "你們",
    "他们", "他們", "是", "有", "会", "會", "能", "可以",
    "要", "想", "得", "个", "個", "些", "种", "種",
    "只", "次", "件", "上", "下", "里", "裡", "中",
    "前", "后", "後", "左", "右",
}
```

**b) Add CJK tokenizer pass to `_extract_topics()` (line 436):**

The current regex `r"[a-zA-Z][a-zA-Z_-]{2,}"` only matches Latin characters. Add a CJK extraction pass:

```python
def _extract_topics(self, text: str, max_topics: int = 3) -> List[str]:
    """Extract key topic words from plain text."""
    # Tokenize: Latin alphanumeric words
    words = re.findall(r"[a-zA-Z][a-zA-Z_-]{2,}", text)
    
    # CJK tokenizer: extract CJK bigrams+ (2+ consecutive CJK characters)
    cjk_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    
    # Count frequency, skip stop words
    freq = {}
    for w in words:
        w_lower = w.lower()
        if w_lower in _STOP_WORDS:
            continue
        freq[w_lower] = freq.get(w_lower, 0) + 1
    
    # Count CJK word frequency, skip Chinese stop words
    for w in cjk_words:
        if w in _STOP_WORDS_ZH:
            continue
        freq[w] = freq.get(w, 0) + 1
    
    # Return top N by frequency
    sorted_words = sorted(freq, key=freq.get, reverse=True)
    return sorted_words[:max_topics]
```

**c) Add Chinese emotion signals to `_EMOTION_SIGNALS` dict (both simplified and traditional):**
```python
# Chinese emotion signals
_EMOTION_SIGNALS.update({
    "开心": "joy", "開心": "joy", "快乐": "joy", "快樂": "joy", "高兴": "joy", "高興": "joy",
    "害怕": "fear", "恐惧": "fear", "恐懼": "fear",
    "爱": "love", "愛": "love", "喜欢": "love", "喜歡": "love",
    "生气": "rage", "生氣": "rage", "愤怒": "rage", "憤怒": "rage",
    "难过": "grief", "難過": "grief", "悲伤": "grief", "悲傷": "grief",
    "担心": "anx", "擔心": "anx", "焦虑": "anx", "焦慮": "anx",
    "感恩": "grat", "感谢": "grat", "感謝": "grat",
    "好奇": "curious",
    "惊讶": "surprise", "驚訝": "surprise",
    "骄傲": "convict", "驕傲": "convict",
    "决定": "determ", "決定": "determ",
})
```

**d) Add Chinese flag signals to `_FLAG_SIGNALS` dict (both simplified and traditional):**
```python
_FLAG_SIGNALS.update({
    "决定": "DECISION", "決定": "DECISION",
    "选择": "DECISION", "選擇": "DECISION",
    "切换": "DECISION", "切換": "DECISION",
    "创建": "ORIGIN", "創建": "ORIGIN",
    "创立": "ORIGIN", "創立": "ORIGIN",
    "成立": "ORIGIN",
    "核心": "CORE", "基本": "CORE",
    "原则": "CORE", "原則": "CORE",
    "转折点": "PIVOT", "轉折點": "PIVOT",
    "突破": "PIVOT", "顿悟": "PIVOT", "頓悟": "PIVOT",
    "架构": "TECHNICAL", "架構": "TECHNICAL",
    "数据库": "TECHNICAL", "資料庫": "TECHNICAL",
    "部署": "TECHNICAL",
})
```

### 4.3 Tests for Phase 4

**New file: `tests/test_spellcheck_chinese.py`**
```
- test_chinese_text_skipped() -- "这是中文内容" returns unchanged
- test_mixed_text_english_parts_corrected() -- English typos in mixed text get corrected
- test_chinese_token_skipped() -- individual Chinese tokens not modified
- test_english_spellcheck_unchanged() -- existing English behavior preserved
```

**Update `tests/test_dialect.py`:**
```
- test_chinese_stopwords_filtered() -- Chinese stopwords removed from topics
- test_cjk_topics_extracted() -- "数据库架构设计很重要" extracts CJK topic words
- test_mixed_language_topics() -- text with both English and Chinese extracts topics from both
- test_chinese_emotion_detection() -- "我很开心" detects joy
- test_traditional_chinese_emotion_detection() -- "我很開心" detects joy
- test_chinese_flag_detection() -- "我们决定" detects DECISION flag
- test_english_behavior_unchanged() -- all existing tests still pass
```

**Acceptance criteria:**
- [ ] `spellcheck_user_text("这是中文内容")` returns the text unchanged
- [ ] `spellcheck_user_text("我很开心 and also hapy")` corrects "hapy" but leaves Chinese alone
- [ ] Chinese stopwords are filtered from dialect topic extraction
- [ ] `_extract_topics()` extracts CJK bigrams from Chinese text (not just Latin words)
- [ ] `_STOP_WORDS_ZH` includes both simplified and traditional variants
- [ ] Chinese emotion/flag signals are detected by Dialect (both simplified and traditional)
- [ ] All existing English tests pass

---

## Phase 5: Integration Testing + Documentation

**Goal:** End-to-end validation of the complete multilingual pipeline.

### 5.1 Integration test

**New file: `tests/test_multilingual_integration.py`**
```
- test_full_chinese_pipeline():
    1. Create a temp directory with Chinese conversation files
    2. Mine them with convo_miner (exchange mode + general mode)
    3. Verify room classification is correct (not all "general")
    4. Search with Chinese queries, verify results returned
    5. Verify entity detection finds Chinese names

- test_mixed_content_pipeline():
    1. Content with both English and Chinese
    2. Verify both languages' patterns fire
    3. Search works in both languages

- test_english_regression():
    1. Run the exact same operations as existing tests
    2. Verify identical behavior with multilingual model

- test_mcp_server_chinese_search():
    1. Use mcp_server._get_collection(create=True) to create a collection
    2. Seed with Chinese content
    3. Query via mcp_server search tools
    4. Verify results returned (validates the critical MCP path)
```

### 5.2 Update `pyproject.toml` keywords

Add `"multilingual"`, `"chinese"`, `"i18n"` to keywords list.

### 5.3 Optional: Add jieba for word segmentation

**Decision: defer.** The pattern-matching approach (direct substring/regex matching for Chinese keywords) works for the defined patterns without word segmentation. Jieba can be added later if keyword matching accuracy needs improvement.

If needed later, add to `pyproject.toml`:
```toml
chinese = ["jieba>=0.42"]
```

**Acceptance criteria:**
- [ ] Full pipeline test passes: mine Chinese content -> search Chinese queries -> get results
- [ ] Mixed content test passes: both languages work in single palace
- [ ] English regression test passes: identical behavior to before
- [ ] MCP server path test passes: Chinese search through MCP interface works
- [ ] All 10 acceptance criteria from the spec are covered by tests

---

## Risk Areas and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Existing palaces use default embedding model** | HIGH | `get_embedding_function()` gracefully falls back to `None` (ChromaDB default) with a logged warning when sentence-transformers not installed. Existing palaces continue to work. New palaces use multilingual model. |
| **Re-embedding required for existing palaces** | HIGH | Model mismatch detection warns users. Document that existing palaces need re-mining (`mempalace mine`) to use multilingual search. Do NOT auto-re-embed -- it's destructive. |
| **Silent fallback hides broken Chinese search** | HIGH | `get_embedding_function()` logs explicit warning on fallback. Model mismatch detection logs warning when stored model differs from config. |
| **Embedding function duplication across modules** | HIGH | Centralized in `config.py`. All 7 consumer modules import from there. No local copies allowed. |
| **`\b` word boundaries don't work for Chinese** | MEDIUM | Chinese patterns use character-level regex without `\b`. Chinese has no word boundaries -- patterns match substrings directly. |
| **Chinese regex patterns may over-match** | MEDIUM | Use specific multi-character patterns (e.g., "我们决定" not just "决") and test with real Chinese text. `CHINESE_STOPWORDS` filters false positive names. |
| **`_extract_topics()` misses CJK text entirely** | MEDIUM | Added CJK tokenizer pass (`[\u4e00-\u9fff]{2,}`) alongside Latin tokenizer. Both feed into the same frequency counter. |
| **Simplified/Traditional inconsistency** | MEDIUM | Systematic audit: every pattern entry with a simplified/traditional variant must include both forms. Tests verify both forms fire. |
| **sentence-transformers download on first use** | LOW | Model downloads on first use (~120MB). Document this. `get_embedding_function()` gives clear error message on failure. |
| **Test isolation with different embedding models** | LOW | Tests can mock `get_embedding_function()` or use ChromaDB default. Integration tests should use the actual multilingual model. |

---

## Files Changed Summary

| File | Action | Phase |
|------|--------|-------|
| `mempalace/config.py` | MODIFY | 1, 2 |
| `mempalace/language_detect.py` | CREATE | 1 |
| `mempalace/searcher.py` | MODIFY | 2 |
| `mempalace/miner.py` | MODIFY | 2 |
| `mempalace/convo_miner.py` | MODIFY | 2, 3 |
| `mempalace/mcp_server.py` | MODIFY | 2 |
| `mempalace/layers.py` | MODIFY | 2 |
| `mempalace/palace_graph.py` | MODIFY | 2 |
| `mempalace/cli.py` | MODIFY | 2 |
| `mempalace/entity_detector.py` | MODIFY | 3 |
| `mempalace/general_extractor.py` | MODIFY | 3 |
| `mempalace/spellcheck.py` | MODIFY | 4 |
| `mempalace/dialect.py` | MODIFY | 4 |
| `pyproject.toml` | MODIFY | 2, 5 |
| `tests/test_language_detect.py` | CREATE | 1 |
| `tests/test_config.py` | MODIFY | 1 |
| `tests/test_embedding_fallback.py` | CREATE | 2 |
| `tests/test_searcher.py` | MODIFY | 2 |
| `tests/conftest.py` | MODIFY | 2 |
| `tests/test_entity_detector_chinese.py` | CREATE | 3 |
| `tests/test_convo_miner_chinese.py` | CREATE | 3 |
| `tests/test_general_extractor_chinese.py` | CREATE | 3 |
| `tests/test_spellcheck_chinese.py` | CREATE | 4 |
| `tests/test_dialect.py` | MODIFY | 4 |
| `tests/test_multilingual_integration.py` | CREATE | 5 |

**Total: 12 modified source files, 6 new test files, 1 new module, 1 new test file for embeddings**

**Modules reviewed and explicitly excluded:** `room_detector_local.py`, `knowledge_graph.py`, `entity_registry.py`, `normalize.py` (see Context section for rationale).

---

## ADR: Architectural Decision Record

**Decision:** Inline language patterns with shared language detection module (Option A). Centralized embedding function in `config.py`.

**Drivers:**
1. Codebase is flat, explicit, no sub-packages -- stay consistent
2. Only 2 languages (English + Chinese) don't justify a registry
3. Each module must be self-contained and readable
4. 7 modules access ChromaDB collections -- embedding function MUST be centralized to prevent divergence

**Alternatives Considered:**
- Option B (external pattern files with registry) -- rejected as over-engineering for 2 languages
- MemChinesePalace fork merge -- rejected because fork is missing 6+ features and is a rewrite
- Per-module `_get_embedding_function()` -- rejected because 7+ copies would inevitably diverge

**Why Chosen:** Minimum structural change, maximum readability, consistent with existing codebase style. Patterns are visible inline where they're used. Single `get_embedding_function()` in `config.py` eliminates divergence risk across 7 consumer modules.

**Consequences:**
- Adding a 3rd language means touching all 12 modules again (acceptable -- each touch is small)
- Modules grow by ~50-100 lines each (manageable)
- Future refactor to registry pattern is straightforward if needed
- All 7 ChromaDB consumer modules gain an import dependency on `config.get_embedding_function`
- Model metadata in collections enables mismatch detection but requires re-mining to populate for existing palaces
- `_extract_topics()` now handles both Latin and CJK text, slightly increasing complexity of that method

**Follow-ups:**
- Document migration path for existing palaces (re-mine needed)
- Consider jieba integration if keyword matching accuracy is insufficient
- Monitor embedding model download size impact on first-time users
- Consider adding `COMMON_CHINESE_WORDS` to `entity_registry.py` for disambiguation (analogous to `COMMON_ENGLISH_WORDS`) if Chinese name false positives become an issue beyond what `CHINESE_STOPWORDS` covers
