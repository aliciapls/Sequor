# RAG Pipeline — Document Ingestion, Retrieval, and Hallucination Controls

## Overview

The RAG (Retrieval-Augmented Generation) pipeline answers routine queries from the user's internal documents. The pipeline must work with the messy, unstructured documents that characterize the target market — WhatsApp exports, inconsistent spreadsheets, PDFs of varying quality, scanned images.

---

## Document Types Supported

| Type                | Format                               | Parsing Approach                                 | Notes                              |
| ------------------- | ------------------------------------ | ------------------------------------------------ | ---------------------------------- |
| FAQ                 | PDF, DOCX, TXT, WhatsApp chat export | Text extraction + line-item segmentation         | Each Q+A pair treated as one chunk |
| Roster              | XLSX, CSV, email attachment          | Spreadsheet parser (openpyxl) + row-level chunks | Each row = one chunk               |
| Price list          | PDF, XLSX, CSV                       | Same as roster                                   | Each item = one chunk              |
| Policy / Procedures | PDF, DOCX                            | Section-level chunking (headings as delimiters)  | Preserves hierarchical structure   |
| Informal notes      | TXT, WhatsApp export, email          | Sentence-level chunking with overlap             | Lower quality retrieval expected   |

---

## Document Ingestion Flow

### 1. Upload and Validation

- User uploads a file via the onboarding wizard
- Supported formats: PDF, DOCX, XLSX, CSV, TXT, PNG (OCR), JPG (OCR)
- Maximum file size: 25MB
- File is scanned for malware (ClamAV or equivalent) before processing
- Upload generates a `Document` record with status `pending`

### 2. Parsing

- Text extraction: PDF text via pdfminer; DOCX via python-docx; XLSX via openpyxl
- OCR for scanned documents: Tesseract or cloud OCR API (Google Vision, AWS Textract)
- If OCR is used, the extracted text is stored alongside the image for audit
- Parsing errors are logged; the document is marked `error` if >20% of pages fail

### 3. Chunking

Three chunking strategies, selected by document type:

**Line-item** (FAQ, price lists): Each Q+A pair or line item is one chunk. Preserves discrete units.

**Section-based** (policy, procedures): Chunk boundaries at H1/H2 headings. Chunks are ~500-1000 tokens.

**Sentence-overlap** (informal notes, chat exports): 3-sentence chunks with 1-sentence overlap. Lower precision but better recall on informal content.

### 4. Embedding Generation

- Embedding model: `text-embedding-3-small` (OpenAI) or equivalent (Cohere, Anthropic)
- Per-chunk: one embedding vector (1536 dimensions for ada-003 equivalent)
- Embeddings stored in pgvector (PostgreSQL extension) — vector storage alongside relational data

### 5. Indexing

- Each chunk stored with: `document_id`, `chunk_index`, `chunk_text`, `embedding_id`
- Inverted index: `keyword → chunks` for BM25 hybrid retrieval
- Hybrid retrieval: combine vector similarity (0.7 weight) + BM25 keyword match (0.3 weight)
- Index is ready when all chunks are stored and indexed; `Document.status` → `ready`

### 6. Index Age Tracking

- `Document.last_indexed_at` updated on every re-index
- Staleness threshold: configurable per document type (default: 7 days for rosters/price lists, 30 days for policies)
- Documents approaching staleness threshold (5 days before) trigger a re-index warning to the user
- Stale documents (>threshold) are flagged in retrieval — confidence badge shows "may be outdated"

---

## Retrieval Flow

### Query Processing

1. User message is received and classified
2. If classification confidence > 60% and category != `high_stakes`, RAG retrieval is triggered
3. Query is embedded (same model as documents)
4. Hybrid search: vector similarity + BM25 against tenant's document chunks

### Retrieval Confidence Scoring

Each retrieved passage is scored on two dimensions:

**Relevance score** (0-1): Vector similarity + BM25 combined score

**Answerability score** (0-1): Cross-check prompt — "Does this passage answer the user's question?" answered yes/no by the LLM

Final passage score = relevance × answerability

If answerability < 0.3, the passage is excluded even if vector similarity is high.

### Synthesis

- Retrieved passages (top 5 by score) are passed to the LLM (GPT-4o or equivalent) with the user query
- System prompt includes: "Do not add information not present in the retrieved documents. Cite each factual claim with a source. If you are uncertain, say so."
- Each factual claim in the response is tagged with a citation: `[Source: FAQ.pdf, Q3]`
- Synthesis confidence = weighted average of passage answerability scores × LLM confidence

### Hallucination Detection (Post-Synthesis)

- A second LLM call checks the final response: "Does every factual claim in this response have a citation from the retrieved documents?"
- If un-cited claims are found: response is flagged, confidence reduced, and routed to backup review
- If >50% of claims are un-cited: response is rejected, routed to backup with "RAG failed to produce verifiable answer"

---

## Document Freshness

### Triggered Re-indexing

- User manually triggers re-index from the dashboard
- Webhook: if a document is updated (file re-uploaded), auto-detect and prompt for re-index
- Scheduled: every 7 days for rosters/price lists, every 30 days for policies (configurable per document type)

### Versioning

- Each upload creates a new `Document` record; the previous version is archived
- Old chunks are not deleted immediately — retained for 7 days for debugging
- Old embeddings are dropped after 7 days

---

## Learning from Human Answers

### Purpose

Most SMEs in the target market do not have clean, structured internal documents. The learning loop removes the document dependency — the product gets smarter through usage, not through upfront document preparation.

### How It Works

Every time a human resolves an escalation by replying to the escalation email:

1. The human's reply is captured along with the original client query
2. The system creates a new knowledge chunk: `{question: client_query, answer: human_reply}`
3. The chunk is embedded and indexed alongside uploaded documents
4. Future queries matching this topic can be answered by the AI using the learned answer

### Quality Controls

- Only answers from confirmed escalation resolutions are learned (not drafts, not partial replies)
- The learned answer is attributed to the human who provided it, with a timestamp
- If a later human answer contradicts an earlier one, the more recent answer takes precedence
- Learned answers are marked with source type `human_answer` (distinct from `document_upload`)
- The account owner can review learned answers via a weekly digest and flag incorrect ones for removal

### Knowledge Base Composition Over Time

| Time After Activation | Knowledge Source          | Expected Coverage                        |
| --------------------- | ------------------------- | ---------------------------------------- |
| Day 0 (no documents)  | None                      | 0% auto-resolved; all escalated to human |
| Week 1                | Human answers from week 1 | 10-20% of common queries auto-resolved   |
| Month 1               | Human answers + 1 month   | 30-40% auto-resolved; most FAQs covered  |
| Month 3               | Human answers + docs      | 50-60% auto-resolved; broad coverage     |
| Month 6+              | Mature knowledge base     | 60-70% auto-resolved; stable coverage    |

### Document Cleanup Service (Optional Accelerator)

For firms that want to accelerate the learning curve, the document cleanup service prepares their existing documents into RAG-ready format. This is a paid one-time service (S$300-500) that front-loads knowledge into the system. It is optional — firms can rely entirely on the learning loop if they prefer.

---

## Multi-Document Scenarios

### Conflicting Information

If two documents contain conflicting information on the same query:

- Both passages are retrieved
- The synthesis notes the conflict: "I found information in two sources that differ. [Source A] says X. [Source B] says Y. A human review is recommended."
- The query is routed to backup for resolution — not auto-sent

### No Relevant Documents Found

- RAG returns empty result (top passage score below threshold)
- Response generated: "I don't have information about this in the available documents. Your enquiry has been forwarded to [backup name] for review."
- This is NOT an error — it is an expected outcome for out-of-scope queries

---

## Access Control

- RAG retrieval is scoped to the tenant's own documents only
- Cross-tenant document access is impossible by architecture (separate schemas)
- Users can only query documents they have uploaded
- Audit trail records which document chunks were retrieved for each query

---

## Performance Targets

| Metric                                 | Target                      |
| -------------------------------------- | --------------------------- |
| Document indexing (per page)           | < 2 seconds                 |
| Retrieval latency (P95)                | < 800ms                     |
| Synthesis latency (P95)                | < 3 seconds                 |
| Chunking accuracy (correct boundaries) | > 95%                       |
| Hallucination rate (uncited claims)    | < 5% on benchmark           |
| Answerability detection accuracy       | > 85% on synthetic test set |

---

## Pre-Build Validation: RAG on Real SME Documents

Technical feasibility depends on proving RAG works on the target market's actual documents — not synthetic test data, not clean PDFs from ideal conditions, but the actual messy documents SMEs have. This must be validated before the build decision is confirmed.

### Validation Protocol

**Step 1: Document audit (5–10 real businesses)**

Before writing any code, collect real documents from 5–10 professional services firms (accountants, consultants):

- Actual FAQs (as they exist — often in WhatsApp exports, email threads, or inconsistent formats)
- Actual price lists (spreadsheets with merged cells, inconsistent columns, notes in the margins)
- Actual rosters (team lists, contact sheets, sometimes just WhatsApp group membership)
- Actual policies (handbooks that are PDFs of scanned documents, not text-searchable)

**Step 2: Manual retrieval test**

For each document set, have a human manually answer 50 queries using only the documents:

- Which queries can be answered from the documents at all?
- Which queries require interpretation vs. direct retrieval?
- What percentage of queries a business would realistically ask are answerable from their own documents?

This gives a ground-truth answerability rate — not what the model can do in theory, but what the documents actually support.

**Step 3: RAG benchmark on real documents**

Run the RAG pipeline on the collected documents and test set of queries. Measure:

- Retrieval accuracy: Is the right document chunk retrieved?
- Synthesis accuracy: Does the answer stay within the retrieved content?
- Hallucination rate: Does the model make claims not supported by the retrieved content?
- False positive rate: Does the system claim to have an answer when the documents don't support one?

**Step 4: Decision gate**

Build only proceeds if:

- Answerability rate from real documents is >70% (70% of realistic queries can be answered from documents)
- Hallucination rate on real documents is <10%
- False positive rate (answering when documents don't support it) is <15%

If any threshold fails, the document cleanup service becomes more critical — it solves the document quality problem that caused the failure. Build proceeds with the understanding that document preparation is a required part of onboarding.

### Why This Gate Matters

RAG on clean academic documents works at 95%+ accuracy. RAG on SME document mess — WhatsApp exports, inconsistent spreadsheets, scanned PDFs — is a different problem. The benchmark must be run on the actual target market's documents, not proxy data. Skipping this step is the most common reason AI document products fail at launch.

This validation is not a research project. It is a 2–3 week effort across 5–10 businesses. It produces a pass/fail decision on the core technical assumption.
