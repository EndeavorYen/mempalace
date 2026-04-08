# Deep Interview Spec: Mempalace Multilingual Architecture

## Metadata
- Interview ID: di-mempalace-chinese-001
- Rounds: 10
- Final Ambiguity Score: 19%
- Type: brownfield
- Generated: 2026-04-08
- Threshold: 20%
- Status: PASSED

## Clarity Breakdown
| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Goal Clarity | 0.90 | 0.35 | 0.315 |
| Constraint Clarity | 0.75 | 0.25 | 0.188 |
| Success Criteria | 0.80 | 0.25 | 0.200 |
| Context Clarity | 0.70 | 0.15 | 0.105 |
| **Total Clarity** | | | **0.808** |
| **Ambiguity** | | | **19%** |

## Goal

Build a **general-purpose multilingual architecture** for Mempalace that enables language-agnostic memory storage, retrieval, entity detection, room classification, and content extraction — with **Chinese as the first non-English language** implemented. The architecture should allow adding new languages in the future without architectural changes.

### Approach
- **Modify the original Mempalace** codebase (not rewrite)
- **Selectively borrow techniques** from MemChinesePalace fork (bilingual keyword detection, configurable embedding model, Chinese particle removal rules)
- **Do not merge** the fork wholesale — it's a single-day rewrite missing many features (onboarding, entity registry, palace graph, etc.)

## Constraints
- **Bilingual coexistence**: English functionality must be fully preserved. All existing English tests must continue to pass.
- **Configurable embedding model**: Add model selection to config. Default to a multilingual model (e.g., `paraphrase-multilingual-MiniLM-L12-v2` or `BAAI/bge-m3`). Existing users can keep the original model.
- **Language detection strategy**: File-level detection as primary, with chunk-level fallback for mixed-language content.
- **Mixed content support**: Chinese-English mixed content (e.g., "小明用 Python 寫了一個元件") is the most common pattern and must be handled correctly.
- **Incremental modification**: Modify 7 existing modules, do not restructure the project or add unnecessary abstractions.
- **No new external service dependencies**: Everything runs locally, consistent with Mempalace's design philosophy.

## Non-Goals
- UI/CLI internationalization (all prompts remain English for now)
- Classical Chinese compression (文言文/Wenjian) — this is a MemChinesePalace-specific feature
- Full onboarding localization
- Supporting right-to-left languages in this iteration
- Building a plugin system for language modules

## Acceptance Criteria
- [ ] Chinese semantic search works: querying with Chinese terms returns relevant Chinese memories with reasonable similarity scores
- [ ] Chinese entity detection works: Chinese person names (e.g., 張三, 小明, 王大明) and mixed names (e.g., "Simon 說...") are correctly identified by entity_detector
- [ ] Chinese room classification works: Chinese technical discussions are classified into the correct rooms (technical, planning, decisions, etc.) — not all falling into "general"
- [ ] Chinese content extraction works: Chinese decision patterns (我們決定), preference patterns (我偏好), emotion patterns are detected by general_extractor
- [ ] Spellcheck gracefully handles Chinese: Chinese text is not erroneously "corrected" by the English spellchecker
- [ ] Dialect/stopwords support Chinese: Chinese stopwords (的, 了, 着, etc.) are properly handled
- [ ] Embedding model is configurable: Users can select embedding model in config.json, with multilingual model as default
- [ ] Language detection works: System auto-detects file language and applies appropriate rules, with chunk-level fallback for mixed content
- [ ] All existing English tests continue to pass (no regression)
- [ ] New pytest tests cover all Chinese-specific functionality

## Assumptions Exposed & Resolved
| Assumption | Challenge | Resolution |
|------------|-----------|------------|
| Only need Chinese support | Asked if general multilingual architecture is better | User chose general multilingual architecture |
| Need to rewrite like MemChinesePalace | Compared effort of rewrite vs incremental modification | Modify original, selectively borrow from fork |
| Must change embedding model | Challenged with re-embedding cost trade-off | Configurable, default to multilingual model |
| Language detection at one level only | Asked about file vs chunk level | File-level primary, chunk-level fallback |
| Chinese-only content | Asked about typical content patterns | Mixed Chinese-English is most common |
| Need Classical Chinese compression | Simplifier mode: is this necessary? | Not in scope — focus on functional correctness |

## Technical Context

### Modules to Modify (7)

| Module | Current State | Required Change |
|--------|--------------|-----------------|
| `searcher.py` | ChromaDB default embedding (all-MiniLM-L6-v2) | Add configurable embedding model, default to multilingual |
| `entity_detector.py` | English verb patterns only (e.g., `{name} said`) | Add Chinese entity patterns (Chinese name structures, Chinese verb signals like 說, 問, 認為) |
| `convo_miner.py` | English TOPIC_KEYWORDS only | Add Chinese keyword equivalents for room classification |
| `general_extractor.py` | 30-50 English regex patterns per memory type | Add Chinese equivalents (決定→decision, 偏好→preference, etc.) |
| `spellcheck.py` | Hardcoded `lang="en"` | Add language detection; skip spellcheck for non-English content |
| `dialect.py` | 250+ English stopwords | Add Chinese stopwords (的, 了, 着, 過, 把, 被, etc.) |
| `config.py` | No language/model config | Add `embedding_model` and `language` configuration options |

### New Infrastructure Needed

| Component | Purpose |
|-----------|---------|
| Language detection module | Detect content language at file and chunk level |
| Language-specific pattern files/dicts | Organize patterns by language for extensibility |
| Chinese word segmentation (optional) | Consider jieba or similar for keyword matching in Chinese |

### Reference: MemChinesePalace Fork Techniques to Borrow
- **Bilingual keyword detection**: Both "決定" and "decided" trigger decision type (from `miner.py`)
- **Chinese particle removal**: Rule-based removal of 的, 了, 着, etc. (from `compressor.py`)
- **Configurable embedding model**: SentenceTransformer with external model selection (from `searcher.py`)
- **Status markers in Chinese**: [定] confirmed, [疑] uncertain, etc. (reference only)

## Ontology (Key Entities)

| Entity | Type | Fields | Relationships |
|--------|------|--------|---------------|
| Mempalace | core system | modules[], config, palace_path | contains all other entities |
| Multilingual Architecture | core design | language_detection, module_loading, pattern_files | enables Language Module |
| Language Module | core design | language_code, patterns, keywords, stopwords | loaded by Multilingual Architecture |
| Language Detection | infrastructure | file_level, chunk_fallback, auto_detect | feeds into Language Module selection |
| Semantic Search | feature | embedding_model, query, results, similarity | uses Embedding Model Config |
| Entity Detection | feature | patterns, person_signals, project_signals | uses Language Module patterns |
| Room Classification | feature | topic_keywords, scoring | uses Language Module keywords |
| Content Extraction | feature | decision_patterns, preference_patterns, emotion_patterns | uses Language Module patterns |
| Embedding Model Config | configuration | model_name, configurable, default_multilingual | used by Semantic Search |
| Chinese Content | data | mixed_content, pure_chinese, entity_names | processed by all features |
| Mixed Content Pattern | data pattern | chinese_text, english_terms, entity_mixing | most common input format |
| Tokenization | processing | chunk_size, overlap, segmentation | may need Chinese word segmentation |
| Stopwords | processing | english_list, chinese_list, per_language | used by dialect.py |
| Pytest Tests | validation | chinese_entity_tests, search_tests, room_tests | validates all acceptance criteria |

## Ontology Convergence

| Round | Entity Count | New | Changed | Stable | Stability Ratio |
|-------|-------------|-----|---------|--------|----------------|
| 1 | 8 | 8 | - | - | N/A |
| 2 | 9 | 1 | 0 | 8 | 89% |
| 3 | 10 | 1 | 0 | 9 | 90% |
| 4 | 11 | 1 | 0 | 10 | 91% |
| 5 | 12 | 1 | 0 | 11 | 92% |
| 8 | 13 | 2 | 1 | 10 | 85% |
| 9 | 14 | 1 | 0 | 13 | 93% |
| 10 | 14 | 0 | 0 | 14 | 100% |

## Interview Transcript
<details>
<summary>Full Q&A (10 rounds)</summary>

### Round 1
**Q:** 你的目標是「讓 Mempalace 更好地支援中文」——這涵蓋的範圍很廣。你心中最核心的改善目標是什麼？
**A:** 功能面：中文內容的儲存與檢索
**Ambiguity:** 71% (Goal: 0.50, Constraints: 0.10, Criteria: 0.10, Context: 0.40)

### Round 2
**Q:** Mempalace 目前是純英文系統。你希望改造後的系統是「雙語並存」還是「中文優先」？
**A:** 雙語並存
**Ambiguity:** 60% (Goal: 0.55, Constraints: 0.45, Criteria: 0.10, Context: 0.45)

### Round 3
**Q:** 假設你把一段中文對話餵入 Mempalace，到後來搜尋時能正確找到。你覺得「成功」的標準是什麼？
**A:** 以上全部都要（搜尋 + 實體辨識 + 房間分類）
**Ambiguity:** 42% (Goal: 0.70, Constraints: 0.50, Criteria: 0.55, Context: 0.50)

### Round 4 (Contrarian Mode)
**Q:** 如果要讓中文語義搜尋有效，幾乎一定要換成多語言 embedding 模型。你接受這個 trade-off 嗎？
**A:** 可配置，預設多語言模型
**Ambiguity:** 36% (Goal: 0.75, Constraints: 0.65, Criteria: 0.55, Context: 0.55)

### Round 5
**Q:** 當你說「中文實體能被正確辨識」時，你心中的中文實體長什麼樣子？
**A:** 兩種都有，但中英混合更常見
**Ambiguity:** 29% (Goal: 0.80, Constraints: 0.70, Criteria: 0.65, Context: 0.60)

### Round 6 (Simplifier Mode)
**Q:** 最小可行的第一步應該是什麼？這些額外模組的中文支援是必要的嗎？
**A:** 我全部都要，但你認為我需要像 MemChinesePalace 重寫, 還是基於誰的架構修改比較容易達成目標?
**Resolution:** 基於原始 Mempalace 修改，選擇性借鑑 fork 技術
**Ambiguity:** ~25%

### Round 7
**Q:** 綜合前面的討論，確認七個模組的範圍正確嗎？
**A:** 如果支援多語言有什麼問題? 有辦法做到任意語言支援嗎?
**Resolution:** 擴展為通用多語言架構

### Round 8 (Scope Pivot)
**Q:** 你想要「通用多語言架構 + 中文作為第一個非英文語言」嗎？
**A:** 通用多語言架構
**Ambiguity:** 35% (scope expansion caused increase)

### Round 9 (Ontologist Mode)
**Q:** 語言偵測應該在哪個層級發生？
**A:** 檔案層級為主，chunk 層級 fallback
**Ambiguity:** 27%

### Round 10
**Q:** 怎麼驗證「成功」？
**A:** pytest 測試就足夠
**Ambiguity:** 19% ✅

</details>
