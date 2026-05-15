# Session: Setup Guide Enhancements — 2026-05-15

## Changes Made

### FAQ Accordion Fix

Removed inline `style="display:none"` from FAQ accordion bodies that was conflicting with CSS class toggling in some browsers. Accordions now properly collapse/expand.

**Files:** `src/sequor/onboarding/templates/faq.html`

### Key Phrase Suggestions — AI-Generated

Users didn't know what phrases to link. Added AI-generated suggestions that appear in the Add Mapping modal — clickable pills that auto-fill the phrase + select the document.

- New `KeyPhraseMapping` model and `KeyPhraseMappingType` enum
- New API endpoints: `GET/POST/DELETE /api/v1/portal/keyphrase/mappings`, `GET /api/v1/portal/keyphrase/suggestions`
- Suggestions generated via Ollama LLM from uploaded document names
- Suggestions filtered to exclude already-mapped phrases
- Click suggestion → auto-fills form, button becomes disabled with ✓

**Files:** `src/sequor/db/models.py`, `src/sequor/onboarding/app.py`, `src/sequor/onboarding/templates/keyphrases.html`

### Document Upload Modal

Replaced hidden upload div with proper centered modal popup.

- Full drag-and-drop with visual feedback
- Multi-file selection with individual remove buttons
- File type/size validation (PDF, DOCX, TXT, max 25MB)
- Real XHR progress bar
- New `POST /api/v1/portal/documents/upload` endpoint for auth-based uploads

**Files:** `src/sequor/onboarding/app.py`, `src/sequor/onboarding/templates/documents.html`

### Step 1 Card Clickable

"Upload your docs" card in "How Document Linking Works" section now opens upload modal when clicked.

**Files:** `src/sequor/onboarding/templates/documents.html`

### Document Upload — Graceful Ollama Fallback

Documents now upload even when Ollama is unavailable. If embedding generation fails, document is saved without embeddings and stays in "indexing" status. Processed later when Ollama is available.

**Files:** `src/sequor/ai/ingestion.py`

### Upload Error Messages

Upload failures now return specific error messages instead of generic "Upload failed" — includes hints for Ollama connectivity, timeouts, and vector processing issues.

**Files:** `src/sequor/onboarding/app.py`

## Commits Pushed

- `a769dcc` fix: remove inline display:none from FAQ accordion bodies
- `1623302` feat: key phrase suggestions — AI-generated phrase suggestions with click-to-add
- `30b16e9` feat: document upload modal with drag-and-drop
- `03533d1` feat: make step 1 "Upload your docs" card clickable
- `3b1ec4a` fix: return specific error messages on document upload failure
- `4bcece1` feat: document upload works when Ollama is unavailable

## Pending / To Do

- WhatsApp and Email credential saving from UI (channels page credentials are read-only, stored as env vars)
- Verify escalation count API is working correctly (was crashing before fix)
- Background job to reprocess "indexing" status documents when Ollama becomes available
