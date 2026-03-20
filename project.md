# Application-Level Backend Projects — Incremental Approach

## Context for AI Assistants

This file is a project roadmap for a 2nd year CS student in India learning backend development with **FastAPI**. The student's problem: they kept picking big complex projects (real-time multiplayer games, distributed systems) that required too many concepts at once, so nothing ever got finished.

**The fix:** Each project below is designed as a "layered cake" — Phase 1 is dead simple (buildable in a few hours), and each subsequent phase adds exactly ONE new backend concept. The student should **deploy after every phase** so there's always a working product. When expanding any phase, teach only the concept listed for that phase — don't introduce concepts from later phases early.

**Tech stack:** FastAPI, SQLAlchemy (async), PostgreSQL, Redis, Pydantic v2. No frontend — API only. Use tools like httpie or Postman for testing.

**Rules when expanding phases:**
- Each phase should be a PR-sized chunk of work (a few hours to a day, not a week).
- The student should be able to explain every line of code they write.
- Don't over-engineer. No microservices. No Docker until deployment. No Kubernetes ever.
- Every phase must result in a working, deployable API.

---

## Project 1: URL Shortener → Analytics Platform

A URL shortener that evolves into a full link analytics service. This is the first project because it has the gentlest on-ramp — Phase 1 is literally 2 endpoints.

### Phase 1 — Basic URL Shortening
**Build:** Two endpoints. `POST /shorten` accepts a long URL, generates a short code, stores it in PostgreSQL, returns the short URL. `GET /{code}` looks up the code and returns a 307 redirect to the original URL.
**Concepts:** FastAPI route basics, Pydantic request/response models, SQLAlchemy models and sessions, async database operations, proper project structure (routers, models, schemas, database config in separate files).

### Phase 2 — User Authentication
**Build:** Add signup (`POST /auth/register`) and login (`POST /auth/login`) endpoints. Users get a JWT token. Now each shortened URL belongs to a user. Users can see their own links via `GET /links`. Unauthenticated users can still shorten URLs (anonymous links), but can't manage them later.
**Concepts:** Password hashing with bcrypt, JWT access tokens, FastAPI dependency injection for auth (`Depends(get_current_user)`), protecting routes, user-link relationships in the database.

### Phase 3 — Click Tracking
**Build:** Every time someone hits `GET /{code}`, log the click — timestamp, IP address, User-Agent header, Referer header. Store clicks in a separate `clicks` table. Don't let the logging slow down the redirect — the user should be redirected immediately.
**Concepts:** FastAPI `BackgroundTasks` for fire-and-forget work, request metadata extraction (`request.client.host`, `request.headers`), one-to-many relationships (one link → many clicks), async database writes that don't block the response.

### Phase 4 — Analytics API with Caching
**Build:** Add analytics endpoints: `GET /links/{code}/stats` returns total clicks, clicks per day (last 30 days), top 5 referrers, and top 5 user agents. These queries hit the database hard, so cache the results in Redis with a 5-minute TTL. If cache exists, return it. If not, query DB, cache it, return it.
**Concepts:** Redis basics (connect, get, set, TTL), cache-aside pattern, SQL aggregation queries (GROUP BY, COUNT, date truncation), pagination for large result sets, serializing/deserializing complex data to Redis.

### Phase 5 — Rate Limiting + API Keys
**Build:** Add a public API tier. Users can generate API keys from `POST /api-keys`. External consumers use the API key (via `X-API-Key` header) instead of JWT. Add rate limiting: free users get 10 requests/minute, API key users get 100/minute. Rate limit using a sliding window counter in Redis.
**Concepts:** API key generation and validation, sliding window rate limiting algorithm, Redis INCR + EXPIRE for counters, custom FastAPI middleware, different auth strategies (JWT vs API key) coexisting.

### Phase 6 — Link Expiry + Scheduled Cleanup
**Build:** Users can now set an expiry time when shortening a URL (optional `expires_at` field). Expired links return 410 Gone. Add a background worker that runs every hour and deletes links that expired more than 30 days ago (cleanup). Use ARQ (async Redis queue) or a simple asyncio background loop.
**Concepts:** Background task queues (ARQ or Celery), scheduled/periodic tasks, database cleanup patterns, handling time zones properly, graceful handling of expired resources (HTTP 410).

### Phase 7 — Real-Time Click Notifications via WebSocket
**Build:** Add a WebSocket endpoint `WS /links/{code}/live`. When a user connects, they see click events in real-time as people use their short link. Use Redis Pub/Sub — when a click is logged (Phase 3), publish it to a Redis channel. The WebSocket listener subscribes to that channel and forwards events to the connected client.
**Concepts:** FastAPI WebSocket handling, Redis Pub/Sub (PUBLISH, SUBSCRIBE), bridging async Redis subscriptions to WebSocket connections, connection lifecycle management (handling disconnects gracefully).

---

## Project 2: Pastebin Clone → Collaborative Code Sharing Platform

A text/code paste service that evolves into a collaborative platform with syntax highlighting metadata, access controls, and real-time editing. Slightly more complex than the URL shortener because it deals with larger payloads and content types.

### Phase 1 — Basic Paste Service
**Build:** `POST /pastes` accepts a text body and an optional language field (e.g., "python", "javascript"), stores it in PostgreSQL, returns a unique paste ID. `GET /pastes/{id}` returns the paste content and metadata (created_at, language). `GET /pastes/{id}/raw` returns just the raw text with `text/plain` content type. Pastes are public and anonymous by default.
**Concepts:** Handling large text payloads, content-type negotiation, generating unique IDs (nanoid/short-uuid), storing text efficiently in PostgreSQL (TEXT column type), response model customization.

### Phase 2 — User Ownership + Visibility Controls
**Build:** Add auth (same JWT approach as URL shortener). Users can create pastes that are "public", "unlisted" (accessible via link but not listed), or "private" (only the owner can view). Add `GET /users/me/pastes` to list your own pastes. Anonymous pastes are still allowed (always public).
**Concepts:** Authorization vs authentication (you can be logged in but still not allowed to view someone's private paste), enum fields in Pydantic/SQLAlchemy, query filtering based on ownership and visibility, proper 403 vs 404 responses (don't reveal that a private paste exists).

### Phase 3 — Paste Expiration + View Counting
**Build:** Users can set pastes to expire after a duration (1 hour, 1 day, 1 week, never). Add "burn after reading" mode — paste deletes itself after being viewed once. Track view count for each paste. Add a periodic cleanup job for expired pastes.
**Concepts:** Self-destructing resources, atomic database operations (read + delete in one transaction for burn-after-read), scheduled background tasks for cleanup, handling race conditions (two people trying to view a burn-after-read paste simultaneously).

### Phase 4 — Paste Versioning (Edit History)
**Build:** Allow paste owners to update their pastes via `PUT /pastes/{id}`. Store every version. Add `GET /pastes/{id}/versions` to list all versions and `GET /pastes/{id}/versions/{version_number}` to view a specific version. Show a simple diff between any two versions (use Python's `difflib`).
**Concepts:** Versioning strategies in databases (version table with foreign key to paste), generating text diffs, immutable history (versions can't be deleted individually), handling large version histories with pagination.

### Phase 5 — Forking + Collections
**Build:** Any user can "fork" a public/unlisted paste — creates a copy under their account with a reference to the original. Add collections — a user can group their pastes into named collections (like GitHub gists). `GET /collections/{id}` returns all pastes in a collection.
**Concepts:** Self-referential relationships (paste forked_from paste), many-to-many relationships (pastes ↔ collections), database query optimization (avoid N+1 queries when loading a collection with all its pastes), eager loading with SQLAlchemy.

### Phase 6 — Full-Text Search with Caching
**Build:** Add `GET /pastes/search?q=keyword` that searches across all public paste contents. Use PostgreSQL full-text search (tsvector/tsquery) instead of LIKE queries. Cache frequent search results in Redis.
**Concepts:** PostgreSQL full-text search (to_tsvector, to_tsquery, GIN indexes), search ranking and relevance, caching search results with smart invalidation (new pastes should eventually appear in results).

### Phase 7 — Real-Time Collaborative Editing
**Build:** Add a WebSocket endpoint for a paste. Multiple users can connect and send edits. Use operational transform (simplified) or last-write-wins for conflict resolution. Broadcast changes to all connected clients via Redis Pub/Sub.
**Concepts:** WebSocket rooms (multiple clients on one paste), basic conflict resolution strategies, Redis Pub/Sub for broadcasting, operational transform basics (or CRDTs if ambitious), managing connection state.

---

## Project 3: File Upload Service → Processing Pipeline

A file upload API that evolves into an image/document processing pipeline. This project teaches you to handle binary data, background processing, and working with external services — things that text-based APIs don't cover.

### Phase 1 — Basic File Upload + Download
**Build:** `POST /files/upload` accepts a file via multipart form upload, saves it to local disk (a configurable upload directory), stores metadata in PostgreSQL (filename, size, mime type, upload timestamp, storage path), returns a file ID. `GET /files/{id}` returns the file metadata. `GET /files/{id}/download` streams the file back to the client. Limit upload size to 10MB.
**Concepts:** FastAPI `UploadFile` handling, multipart form data, streaming file responses (`StreamingResponse` or `FileResponse`), file system operations, MIME type detection, request size limits.

### Phase 2 — User Auth + File Ownership
**Build:** Add auth. Files belong to users. Users can list their files (`GET /users/me/files`), delete their files (`DELETE /files/{id}`). Add a storage quota — each user gets 100MB total. Check quota before accepting uploads.
**Concepts:** File ownership and access control, quota management (tracking cumulative file sizes per user), proper file deletion (delete from disk AND database), handling partial failures (what if DB delete succeeds but file delete fails?).

### Phase 3 — Image Thumbnail Generation
**Build:** When an image file is uploaded (JPEG, PNG, WebP), automatically generate a thumbnail (200x200) in the background. Store the thumbnail path in the database. Add `GET /files/{id}/thumbnail` to retrieve it. Non-image files don't get thumbnails and this endpoint returns 404.
**Concepts:** Background task processing with a task queue (ARQ), image processing with Pillow, handling different content types differently, async workers that process files after the upload response is sent.

### Phase 4 — S3-Compatible Storage
**Build:** Replace local disk storage with S3-compatible object storage (use MinIO locally for development, or any S3 API). Generate pre-signed URLs for downloads instead of streaming through your API. Add a storage backend abstraction so you can swap between local and S3.
**Concepts:** S3 API (boto3/aioboto3), pre-signed URLs, storage abstraction layer (strategy pattern), separating storage concerns from business logic, environment-based configuration for different storage backends.

### Phase 5 — Virus Scanning + File Validation
**Build:** Before making a file available, run it through ClamAV (open source antivirus) in the background. Files start in "processing" status, move to "clean" or "quarantined". Only "clean" files can be downloaded. Also add content-type validation — don't trust the client's content-type header, detect it server-side.
**Concepts:** Integrating with external services/processes, file processing pipelines (upload → scan → available), status state machines, content-type detection with `python-magic`, security considerations for file uploads.

### Phase 6 — Resumable Uploads (tus protocol)
**Build:** Implement the tus resumable upload protocol (simplified version). Client can upload a file in chunks. If the connection drops, they can resume from where they left off. Track upload progress in Redis (which chunks have been received). Assemble chunks into the final file when all parts arrive.
**Concepts:** Chunked file uploads, the tus protocol basics, tracking partial upload state in Redis, assembling file chunks, handling concurrent chunk uploads, cleanup of abandoned partial uploads.

### Phase 7 — Document Processing Pipeline
**Build:** Add a processing pipeline — when certain file types are uploaded, automatically extract metadata. For images: EXIF data, dimensions, color palette. For PDFs: page count, text extraction. Queue these as background jobs. Add `GET /files/{id}/metadata` that returns the extracted data.
**Concepts:** Background job chaining (upload → scan → process → ready), handling different processors for different file types (strategy/registry pattern), extracting metadata from binary files, pipeline architecture.

---

## Project 4: Webhook Relay Service → Event Delivery Platform

A service that receives webhooks from external services and reliably forwards them to your applications. This is a less common project which makes it stand out — and it covers retry logic, delivery guarantees, and event-driven architecture which are critical backend concepts.

### Phase 1 — Basic Webhook Receiver + Forwarding
**Build:** Users register a "target URL" via `POST /endpoints` (e.g., their local dev server). The service generates a unique webhook URL for them. When any HTTP request hits that webhook URL (`POST /webhooks/{endpoint_id}`), the service captures the full request (headers, body, method) and immediately forwards it to the target URL. Store every received webhook in PostgreSQL for history. `GET /endpoints/{id}/deliveries` lists all received webhooks.
**Concepts:** Capturing raw HTTP requests (headers, body, query params), making outbound HTTP requests with httpx, storing request/response data, async HTTP forwarding.

### Phase 2 — Delivery Status + Retry Logic
**Build:** Track the delivery status of each forwarded webhook: "pending", "delivered" (2xx response from target), or "failed" (non-2xx or timeout). For failed deliveries, retry up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s). Use a background task queue (ARQ) for retries. Add `GET /endpoints/{id}/deliveries/{delivery_id}` to see delivery attempts and their status.
**Concepts:** Retry patterns with exponential backoff, background job scheduling with delays, idempotency considerations (what if the target received it but responded slowly?), tracking delivery attempts, timeout handling.

### Phase 3 — Webhook Signature Verification
**Build:** Add HMAC signature verification. When a user creates an endpoint, they get a signing secret. When forwarding webhooks to their target, include a signature header (`X-Webhook-Signature`) computed as HMAC-SHA256 of the request body with their secret. Also support verifying incoming webhooks — users can configure their endpoint to only accept webhooks signed by a specific provider (e.g., Stripe, GitHub).
**Concepts:** HMAC signatures, webhook security best practices, signature computation and verification, timing-safe string comparison (prevent timing attacks), configurable security policies.

### Phase 4 — Filtering + Transformations
**Build:** Let users define filters on their endpoints — only forward webhooks that match certain criteria (e.g., body contains a specific field, a header has a specific value). Simple JSONPath-like matching is enough (e.g., `body.event == "payment.completed"`). Also let users define simple transformations — remap fields before forwarding (e.g., rename `body.data.id` to `body.payment_id`).
**Concepts:** JSONPath or JMESPath for querying JSON, rule engine basics, request transformation, validating user-defined rules/expressions, separating filtering logic from delivery logic.

### Phase 5 — Rate Limiting + Queueing
**Build:** Add rate limiting per endpoint — users configure max deliveries per minute for their target (to avoid overwhelming their server). If webhooks arrive faster than the rate limit, queue them in Redis and deliver them at the configured rate. Add `GET /endpoints/{id}/queue` to see queued deliveries.
**Concepts:** Token bucket or leaky bucket rate limiting, Redis-based queuing (LPUSH/BRPOP), backpressure handling, ordered delivery guarantees (deliver in the order received), queue depth monitoring.

### Phase 6 — Multi-Endpoint Fan-Out + Event Log
**Build:** Allow one webhook source to fan out to multiple target endpoints. Create "channels" — a channel has one inbound webhook URL but can forward to multiple endpoints. Each endpoint can have its own filters and rate limits. Add a searchable event log — `GET /events?channel_id=X&status=failed&from=2024-01-01` with full filtering and pagination.
**Concepts:** Fan-out pattern, many-to-many relationships (channels ↔ endpoints), concurrent HTTP requests (forward to all targets simultaneously with asyncio.gather), complex query building with filters, efficient pagination with cursor-based pagination.

### Phase 7 — Real-Time Dashboard via WebSocket
**Build:** Add a WebSocket endpoint `WS /endpoints/{id}/live` that streams delivery events in real-time. When a webhook is received, processed, or fails — push the event to connected WebSocket clients. Use Redis Pub/Sub for the event broadcasting. This lets users monitor their webhook flow live.
**Concepts:** WebSocket event streaming, Redis Pub/Sub integration, real-time monitoring patterns, connection management, event serialization for live feeds.

---

## General Rules for All Projects

1. **Deploy after every phase.** Use Railway, Render, or Fly.io free tier. A deployed project is 10x more valuable than a local one.
2. **Write a README at every phase.** Document what the API does, how to run it, and what endpoints exist. This is what interviewers read.
3. **Use proper project structure from Phase 1.** Separate routers, models, schemas, services, and config into different files/folders. Don't dump everything in `main.py`.
4. **Write at least basic tests for each phase.** Use `pytest` + `httpx.AsyncClient` for testing FastAPI. Even 5 tests per phase is enough.
5. **Each phase is a Git branch or PR.** Keep the history clean so you can show progression.
6. **Don't skip phases.** The whole point is incremental learning. If you skip Phase 3 and jump to Phase 5, you'll end up in the same "too many new concepts at once" trap.
7. **When asking AI to expand a phase:** Copy the phase description and tell the AI your current project state (what phases you've completed). The phase descriptions above are designed to be self-contained enough for any AI to expand into step-by-step implementation instructions.
