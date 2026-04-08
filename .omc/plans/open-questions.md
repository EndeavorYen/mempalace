# Open Questions

## multilingual-architecture - 2026-04-08
- [ ] Should existing palaces be auto-detected as "legacy embedding" and warn users to re-mine? — Affects UX for existing users upgrading
- [ ] What threshold of CJK characters should trigger "zh" detection vs "mixed"? — 5% and 10% are initial guesses, may need tuning with real data
- [ ] Should jieba be added as optional dependency in Phase 1 or deferred entirely? — Affects Chinese keyword matching accuracy for compound words
- [ ] How should the system handle Traditional vs Simplified Chinese conflicts in patterns? — Both forms are included but untested with real Traditional Chinese content
- [ ] Should `_get_embedding_function()` be a shared utility or duplicated in miner/convo_miner/searcher? — DRY vs keeping modules self-contained
- [ ] What is the model download UX? First `mempalace mine` will download ~120MB silently — Should there be a progress indicator or pre-download command?
