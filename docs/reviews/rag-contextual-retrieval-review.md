# RAG Review: SeismoBrain vs. Anthropic "Contextual Retrieval"

Reference: <https://www.anthropic.com/engineering/contextual-retrieval>
Scope: the code path that actually serves chat answers today (Starter tier), plus the
library modules in `packages/core` that exist but are not yet wired in.
Date: 2026-09-28 · Commit reviewed: `4e0e558`

---

## 1. TL;DR

| | Anthropic recipe | SeismoBrain (live path) | Verdict |
|---|---|---|---|
| Chunk context | LLM writes 50–100 tokens situating each chunk in its document | Fixed template `Document: {title} \| Revision: {rev} \| Section: {heading path}` | **Partial** – structural, not semantic |
| Contextual embeddings | Dense embeddings over `context + chunk` | SHA‑256 hash → 32‑dim vector; not used in retrieval | **Missing** |
| Contextual BM25 | BM25 (TF‑IDF) over `context + chunk` | BM25 over `header + chunk`, **but no IDF** | **Partial** |
| Rank fusion | Dense + BM25 fused | `weighted_rrf` exists, not called; single BM25 arm | **Missing (in live path)** |
| Reranking | Cohere/Voyage cross‑encoder, top‑150 → top‑20 | Whole-query substring count; returns input order for natural questions | **Missing (effectively a no-op)** |
| Top‑K to LLM | 20 | 20 (then 2 000‑word context budget) | **Aligned** |
| Chunk size | "a few hundred tokens" | 50 whitespace words (~65 tokens) | **Much smaller** |
| Prompt caching for context generation | Yes (~$1.02 / M doc tokens) | N/A (no LLM contextualization) | **N/A** |
| Eval metric | 1 − recall@20 across domains | recall@10 harness; release gate asserts hard-coded constants | **Partial** |

**Bottom line:** SeismoBrain adopts the *spirit* of contextual retrieval (a context header is
prepended before indexing, and BM25 sees it) but none of the three components that produced
Anthropic's measured gains (LLM‑generated context, real contextual embeddings + fusion, a
real reranker) are active in the served path. The README's "hybrid retrieval + weighted RRF +
rerank" describes the target design, not current behaviour.

Where SeismoBrain goes **beyond** the article is everything *after* retrieval — grounding,
verification, typed refusals, server-side citations, ACL design, and no‑truncation
chunking. The article doesn't cover those at all (see §4).

---

## 2. Component-by-component comparison

### 2.1 Chunk contextualization

*Anthropic:* per chunk, an LLM (Claude Haiku) is given the whole document + the chunk with the
prompt *"Please give a short succinct context to situate this chunk within the overall
document…"*; the 50–100 token answer is prepended. Prompt caching keeps the doc in cache so
cost is ~$1/M document tokens.

*SeismoBrain:* `packages/core/src/seismobrain_core/chunking.py:61` –
`build_contextual_header()` produces:

```
Document: Pump_Manual | Revision: 1 | Section: Pump_Manual / Limits
```

It's prepended in `apps/api/src/seismobrain_api/starter_ingest.py:77` and in
`packages/ingest/.../sample_load.py:100`.

Assessment:
- ✅ Right placement (prepended before indexing, so BM25 sees it).
- ✅ Deterministic, free, reproducible, zero hallucination risk — a genuine advantage in
  regulated/technical settings.
- ❌ Only resolves *which document/section*. It does not resolve the article's canonical
  failure: a chunk like "The limit was raised to 250 bar" doesn't say *what* limit or
  *which* equipment — the header won't either, unless the heading happens to.
- ❌ `revision` is hard-coded to `"1"` for every upload (`chunk_document(..., revision="1")`),
  and the title is the filename stem. For most uploads the header is `filename + filename`.
- ❌ Starter ingest passes `heading_path or (title,)`; for formats without headings (plain
  TXT, many PDFs) every chunk gets the same header, which adds no discrimination.

### 2.2 Contextual embeddings

*Anthropic:* the single biggest standalone gain (−35 % failure rate).

*SeismoBrain:* `apps/models/src/seismobrain_models/runtime.py` –
`dense_embed()` is SHA‑256 of the text spread over 32 floats. Two near-identical texts get
unrelated vectors; there is no semantic signal. The live chat path
(`apps/api/src/seismobrain_api/chat_doc_qa.py`) never calls `embed` at all. The Qdrant adapter
exists but is not wired for Starter (README acknowledges this).

### 2.3 Contextual BM25

*Anthropic:* standard BM25 with IDF over `context + chunk`.

*SeismoBrain:* `apps/api/src/seismobrain_api/search_index.py:207-219`:

```python
bm25_score = sum(bm25_tf(tf=counts[term], doc_len=doc_len, params=params) for term in query_terms if term in counts)
```

`bm25_tf` (`sparse_bm25_text.py:356`) is the TF-saturation half only — docstring says "IDF from
Qdrant", but Starter has no Qdrant. Consequences:
- A query term that appears in every chunk (e.g. a title word that is repeated in *every*
  header) scores the same as a rare, discriminative term. The contextual header, which is
  supposed to help, actively flattens scores within a document.
- `avg_len` is pinned at 100 while real chunks are ~60–70 words + header, so length
  normalisation is skewed.
- Candidate prefilter is substring-based (`token in hay.casefold()`), so `log` matches
  `catalog`, `pump` matches `pumpjack`.

### 2.4 Hybrid fusion

`packages/core/src/seismobrain_core/fusion.py::weighted_rrf` is correct and tested, as are
`sparse_ident.py` (identifier arm), `fused_pool.py`, `diversity.py`, `dual_query.py`,
`glossary_sparse_expand.py`. **None are called from the chat path.** Live retrieval is a
single BM25-without-IDF arm.

### 2.5 Reranking

*Anthropic:* top‑150 → cross-encoder → top‑20; takes the combined result from −49 % to −67 %.

*SeismoBrain:* `runtime.py::rerank` scores `doc.count(whole_query) + (whole_query in doc)`.
For any natural-language question this is 0 for every doc, so the order is returned unchanged.
Verified:

```
rerank("what is the pump pressure limit?", docs) -> [0, 1, 2]   # identity
```

Additionally the pool is cut to 20 *before* rerank (`chat_doc_qa.py:88`), so even a real
reranker could only reorder, not recover — Anthropic reranks 150.

### 2.6 Chunk size & parents

- Children: 50 whitespace words (`child_max_tokens=50`). Anthropic: a few hundred tokens.
  Very small chunks mean less self-contained content per chunk — which *increases* the need for
  good contextualization, not decreases it.
- Parents: built but never indexed or used for expansion in the Starter path
  (`context_expansion.expand_within_section` is unused). Parent text is also silently capped
  to the first ~200 words (`chunking.py:224-231`), which contradicts the module's "no silent
  truncation" contract (60 short sentences → parent keeps 198 of 540 words; `truncations`
  still reports 0).

### 2.7 Evaluation

- Harness computes recall@10 by query-type/collection/difficulty — good slicing, close to the
  article's 1 − recall@20.
- `eval/runner/src/seismobrain_eval/cli.py:108-130`: the `--release-gate` block asserts on
  constants it just defined (`gates["G3"]["recall@10"] = 0.92; assert >= 0.90`). It cannot
  fail and measures nothing.
- No ablation run comparing header on/off, BM25 vs. hybrid, rerank on/off — the exact
  experiments that justify each stage in the article.

---

## 3. Correctness / security findings discovered during the review

| # | Severity | Location | Issue |
|---|---|---|---|
| F1 | **High (security)** | `routes/conversations.py:204-209` → `search_index.py:_scoped` → `chat_doc_qa.py:122` | Chat retrieval scope comes from the client-supplied `body.scope.collections` and is never intersected with `collection_access.can_read_collection` / `list_collections`. Omitting `scope` gives `collection_ids=None`, and `_scoped` then returns **every chunk in the index**. The post-retrieval `guard` is a no-op. A user can therefore retrieve (and get cited answers from) collections they have no grant for. This contradicts README "Retrieval fails closed when this filter is absent." |
| F2 | Medium | `chat_doc_qa.py:147-163` vs `context_builder.py:39-50` | Citation labels are precomputed over *all* ranked items, but `build_context` `continue`s past an over-budget item and labels the next one with the freed number. If any item is dropped mid-list, every later `E#` maps to the wrong document/page. Reproduced: items `[a(1500w), b(600w), c(10w)]` → context `E2 = c`, citation_meta `E2 = b`. Realistic when PDF text lacks sentence punctuation (a whole page becomes one "sentence", kept whole by `_pack_sentences`). |
| F3 | Low | `chunking.py:224-231` | Parent chunk silently truncated despite `truncations = 0`. |
| F4 | Low | `search_index.py:204` | Substring prefilter (see 2.3). |
| F5 | Low | `eval/.../cli.py:108-130` | Release gate is tautological. |

---

## 4. Where SeismoBrain is *better* than the article

The article is scoped to retrieval recall only. SeismoBrain adds a full answer-safety layer the
article doesn't address:

1. **Evidence-ID grounding + server-rendered citations** – the model emits `[E3]`, the server
   maps to title/section/page (`citation_renderer.py`). The model can't fabricate provenance.
2. **Sentence-level verification** with balanced/strict modes (`sentence_verifier.py`,
   `grounding_balanced.py`, `grounding_strict.py`) and a **numeric guard** (`numeric_guard.py`)
   – important for engineering docs where numbers matter.
3. **Typed refusals** (`no_evidence`, `insufficient_evidence`, `out_of_scope`, …) plus an
   answerability gate before generation, with privacy-safe refusal diagnostics.
4. **Structure-aware chunking**: procedure steps never split and keep their warnings; tables
   chunked by row groups with repeated headers + a summary chunk; sentence-boundary packing with
   comma fallback. The article uses naive fixed chunks.
5. **Identifier-aware sparse arm** (`sparse_ident.py`) for error codes / part numbers — a
   stronger answer to the article's "exact match" motivation for BM25 — once wired in.
6. **Deterministic context header** – reproducible, auditable, zero LLM cost/latency at ingest,
   no hallucinated context. For air-gapped deployments this is a real advantage.
7. **Operational rigour**: versioned chunker (`CHUNKER_VERSION`), pinned BM25 params per index
   version, embedding cache/reuse, version activation after consistency checks, prompt-injection
   defense, egress policy.

---

## 5. Recommendations (ordered by expected impact / effort)

1. **Fix F1 now** – in the chat route, compute
   `allowed = collection_access.list_collections(user_id)`; use
   `requested ∩ allowed` (or `allowed` when no scope given); refuse with `no_evidence` when
   empty. Make `_scoped` fail closed on `None`. Make the `guard` in `chat_doc_qa` re-check each
   hit's document against the metadata store as the README describes.
2. **Fix F2** – derive `citation_meta` from `ctx.blocks` *after* `build_context` (move the
   labelling inside `run_doc_qa`, or have `build_context` return the mapping).
3. **Add IDF to Starter BM25** – compute `df` per term over the scoped hits (or maintain it at
   index time) and multiply `bm25_tf` by `log(1 + (N − df + 0.5)/(df + 0.5))`. Tiny change, large
   effect, and it makes the context header helpful instead of flattening.
4. **Optional LLM contextualization at ingest** (the article's core idea), behind a flag so
   air-gapped/Starter keeps the deterministic header:
   - prompt = the article's prompt, whole document in a cached system block (Anthropic
     `cache_control`), one call per chunk with a small model;
   - store as `Chunk.context_summary`, index `header + context_summary + text`;
   - bump `CHUNKER_VERSION`; exclude the generated context from citable text so verification
     still runs against source text only.
5. **Wire the hybrid path** already built: real embedding model (via `apps/models` /
   Qdrant adapter) + `sparse_ident` + `weighted_rrf`.
6. **Real reranker** – a cross-encoder (e.g. bge-reranker / Cohere / Voyage) in
   `apps/models`, and rerank a larger pool (100–150) down to 20.
7. **Bigger children** – try 200–400 tokens with the header, keep parents for expansion, and
   use `expand_within_section` in context building.
8. **Make eval real** – run recall@20 (and @10) on `golden-v1` for each ablation (header off/on,
   +IDF, +dense, +RRF, +rerank, +LLM context) and gate releases on *measured* numbers.

---

## 6. Verdict

- **Aligned with the article?** Conceptually yes (context is prepended before indexing, top‑20
  to the LLM), but in implementation only ~1.5 of the article's 4 levers are present, and the
  most impactful ones (LLM context, embeddings + fusion, reranker) are not active. Expected
  retrieval quality today is below the article's *baseline*, not its improved numbers.
- **Better than the article?** Yes, on everything downstream of retrieval (grounding,
  verification, refusals, citations, ACL design, structured chunking). These are the parts
  that are hard to retrofit; the retrieval gaps are comparatively easy to close because the
  modules already exist.
