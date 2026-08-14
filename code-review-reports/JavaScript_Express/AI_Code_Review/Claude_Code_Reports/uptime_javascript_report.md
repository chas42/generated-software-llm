# 1. Performance-Engineer Final Consolidated Report (verbatim)

# Verification Report: project-bolt-uptime `src/server.js`

Verified against actual file content (92 lines total) at:
`coding-task-shared/javascript/project-bolt-uptime/project-bolt-uptime/project/src/server.js`

Line-citation corrections noted inline where reviewer citations were slightly off. All 12 raw findings (6 CR-*, 6 NS-*) were checked; they collapse into 8 distinct claims, consolidated below into 6 findings, prioritized by performance/aging relevance.

---

## Finding 1 — Unindexed `token` column + unbounded table growth (full-table-scan degradation)
- **Merged from:** CR-2, NS-5
- **Static validity:** Confirmed
- **Standalone/merged:** Merged (same root defect, two independent write-ups)
- **Code evidence (direct):** Schema at lines 24-30 declares only `serviceId TEXT PRIMARY KEY` (line 26); no `CREATE INDEX` on `token` anywhere in the file. `/services` query (lines 72-76, inside call spanning 72-85) filters `WHERE token = ?`. Heartbeat's conflict-resolution clause (line 47) also filters `WHERE token = ?`. No `DELETE` statement exists anywhere in the file — confirmed by full-file read.
- **Performance relevance:** Direct
- **Affected resource:** SQLite query execution time per `/services` call and per heartbeat conflict check; occupies the request-handling path each call.
- **Triggering conditions:** Every `/services` POST and every `/heartbeat` conflict check; degrades as distinct `serviceId` rows accumulate (since `serviceId` is PRIMARY KEY, only new distinct services add rows — but nothing ever removes stale/inactive ones).
- **Existing cleanup/bounding:** None — no index, no TTL/prune job, no row cap.
- **Mechanism class:** Cumulative resource retention (unbounded table growth) driving transient/repeated per-query overhead (full scan cost).
- **Aging relevance:** Static aging mechanism supported (qualified) — satisfies repeatable trigger (every request), persistent accumulation (rows never deleted), insufficient bounding (no index/TTL), and plausible progressive degradation over long-running deployment as service count grows. Requires runtime confirmation of actual growth rate/cardinality in production to establish materiality.
- **Assumption dependency:** Production row-count growth trajectory and query frequency — not verifiable from static code alone.
- **Final severity/confidence:** Medium / Medium (code evidence for the defect itself is high-confidence; magnitude of runtime impact remains an environment-dependent assumption).

---

## Finding 2 — Unbounded result set / no LIMIT on `/services` per token
- **Source:** CR-6
- **Static validity:** Confirmed
- **Standalone/merged:** Standalone (distinct symptom from Finding 1, though same underlying growth root cause)
- **Code evidence (direct):** `db.all(...)` (lines 72-85) has no `LIMIT`; schema (lines 24-30) has no `UNIQUE` constraint on `token` (line 27: `token TEXT NOT NULL` only), so arbitrarily many `serviceId` rows can share one token; heartbeat UPSERT (lines 41-48) enforces no cap on services-per-token at insert time.
- **Performance relevance:** Direct (conditional on token cardinality)
- **Affected resource:** Node heap buffering of full result set before `res.json(rows)`; outbound payload size.
- **Triggering conditions:** A token with many registered services; grows only if new `serviceId`s keep registering under that token and are never pruned.
- **Existing cleanup/bounding:** None — no LIMIT, no per-token cap, no pagination.
- **Mechanism class:** Cumulative resource retention → transient overhead scaling with retained data volume (larger response construction/serialization per request as data accumulates).
- **Aging relevance:** Conditionally plausible aging mechanism — same four criteria as Finding 1 are structurally present (repeatable trigger, accumulation, no bound, plausible degradation), but materializes only if a single token's service count grows large, which is workload-pattern dependent and unconfirmed statically.
- **Assumption dependency:** Typical/max services-per-token in real usage — unknown from code.
- **Final severity/confidence:** Low-Medium / Medium.

---

## Finding 3 — No busy-timeout/WAL/serialize configuration on shared `db` connection
- **Merged from:** CR-1, NS-4
- **Static validity:** Confirmed (code fact) / Qualified (runtime consequence)
- **Standalone/merged:** Merged
- **Code evidence (direct):** `db` opened at line 16 with no subsequent `db.configure('busyTimeout', ...)`, no `PRAGMA journal_mode=WAL`, and no `db.serialize()` call anywhere in the file. `/heartbeat`'s write (lines 41-48) and `/services`'s read (lines 72-85) both execute against this single connection.
- **Performance relevance:** Conditional (depends on concurrent request rate and node-sqlite3 5.1.7's default internal scheduling, neither of which is determinable from source alone)
- **Affected resource:** SQLite file-lock acquisition path for concurrent writers; error path lines 50-53.
- **Triggering conditions:** Two or more concurrent `/heartbeat` POSTs, or a write overlapping a `/services` read.
- **Existing cleanup/bounding:** None — a lock conflict returns immediately as `err` → generic 500, no retry/backoff.
- **Mechanism class:** Transient/repeated overhead (intermittent contention failures) — does not accumulate state; each occurrence is independent of process uptime.
- **Aging relevance:** Non-aging performance fault. Fails the "persistent accumulation / progressive exhaustion" criterion — contention severity does not systematically worsen purely with process age (only with concurrent load at the moment of request), so it cannot be classified as a supported aging mechanism on its own. It could conditionally worsen in combination with Finding 1 (larger table → longer per-write duration → larger contention window), but that compound effect is speculative and unconfirmed.
- **Assumption dependency:** node-sqlite3's default serialized-vs-parallel scheduling for a single `Database` handle (both reviewers correctly flagged this as needing runtime verification).
- **Final severity/confidence:** Medium / Low-Medium (downgraded from reviewers' "High/Medium" and "Med/Med" because the core scheduling-mode assumption remains unconfirmed and the mechanism is not aging-relevant).

---

## Finding 4 — `app.listen()` not gated on DB-open/table-creation completion (startup race)
- **Merged from:** CR-3, NS-1
- **Static validity:** Confirmed
- **Standalone/merged:** Merged
- **Code evidence (direct):** `new sqlite3.Database(dbPath, (err) => {...})` (line 16) is asynchronous; `app.listen(PORT, ...)` is at lines 90-92 (reviewers cited 89-92, which includes the `PORT` const declaration at line 89 — the actual `.listen()` call itself is line 90). No `await`/promise/flag links the two. `process.exit(1)` (line 19) is nested only inside the open-callback's error branch.
- **Performance relevance:** None to minimal — this is a one-time startup-ordering/correctness issue, not a sustained throughput/latency degradation.
- **Affected resource:** Requests arriving in the narrow startup window; `services` table existence.
- **Triggering conditions:** First run against a missing DB file, slow disk I/O at boot, or requests arriving in the brief window before the open callback completes.
- **Existing cleanup/bounding:** None — no readiness gate.
- **Mechanism class:** No performance impact under steady-state; at most a one-time startup correctness/reliability fault (transient error window, not degradation).
- **Aging relevance:** Unrelated to performance aging — occurs only at process start, does not recur or accumulate during long-running execution, and cannot degrade progressively over uptime.
- **Assumption dependency:** Whether node-sqlite3 queues statements issued on the same handle in call order before the open callback fires (both reviewers flagged this as unconfirmed).
- **Final severity/confidence:** Low (for performance purposes) / Medium — real as a startup-race code fact, but out of scope for aging/performance conclusions.

---

## Finding 5 — No graceful shutdown handling / `db.close()` never called
- **Merged from:** CR-5, NS-3
- **Static validity:** Confirmed
- **Standalone/merged:** Merged
- **Code evidence (direct):** Full-file read confirms no `process.on('SIGINT'|'SIGTERM', ...)` and no `db.close()` call anywhere in the 92 lines.
- **Performance relevance:** Conditional/minor — relates to clean resource release at process termination, not to steady-state throughput/latency.
- **Affected resource:** SQLite file handle/lock at process exit; in-flight requests at termination time.
- **Triggering conditions:** Any restart/redeploy/container-stop signal while requests are in flight.
- **Existing cleanup/bounding:** None.
- **Mechanism class:** No performance impact during normal operation; at most a one-time abrupt-termination effect, not an accumulating condition.
- **Aging relevance:** Unrelated to performance aging — this is a single-connection process that is not reopened/leaked repeatedly during runtime; the absence of a shutdown hook is a termination-event concern, not a source of progressive in-process degradation.
- **Assumption dependency:** Actual restart/redeploy cadence and whether requests are commonly in-flight at shutdown — unconfirmable statically.
- **Final severity/confidence:** Low / Medium.

---

## Finding 6 — No `'error'` event listener registered on `db`
- **Source:** NS-2
- **Static validity:** Confirmed
- **Standalone/merged:** Standalone
- **Code evidence (direct):** `db` (line 16) is an `EventEmitter`-based instance; only the open-callback (`err` param, lines 17-20) and per-query callbacks (lines 50-53, 78-81) handle errors. No `db.on('error', ...)` exists anywhere in the file.
- **Performance relevance:** Conditional — if triggered, causes total process termination rather than degraded performance; this is a discrete crash event, not a performance-degradation mechanism.
- **Affected resource:** Entire Node process / event loop, if an `'error'` event is emitted with no listener (Node's default EventEmitter behavior is to throw).
- **Triggering conditions:** A native sqlite3 driver-level async error emitted outside a query callback's `err` path (e.g., I/O fault, corrupted file).
- **Existing cleanup/bounding:** None.
- **Mechanism class:** No performance impact / not applicable to gradual degradation — this is a finite-resource/fault-driven abrupt failure (binary crash-or-not), not cumulative overhead.
- **Aging relevance:** Unrelated to performance aging — lacks the "progressive degradation" and "accumulation" elements entirely; it is an instantaneous catastrophic-failure risk, not a slow-decay pattern.
- **Assumption dependency:** Whether sqlite3@5.1.7's native binding ever actually emits `'error'` on the `Database` object under real fault conditions in this deployment (vs. always routing through query callbacks) — unconfirmed, requires fault-injection testing.
- **Final severity/confidence:** Medium (impact-if-triggered) / Low (likelihood of triggering path is unverified).

---

## Findings verified but excluded from the top-6 (no meaningful performance/aging relevance)

- **CR-4** (missing callback on `CREATE TABLE`, lines 24-30): Confirmed by code inspection — the `db.run` call for `CREATE TABLE IF NOT EXISTS services` genuinely has no third-argument callback, unlike the other two `db.*` calls in the file. However this is purely a diagnosability/error-visibility gap (silent failure of schema creation), with no performance or aging implication. Performance relevance: none.
- **NS-6** (no type validation on `serviceId`/`token`, lines 34-48): Confirmed — only a truthiness check (line 37) exists, no `typeof` guard. This is a data-integrity/robustness concern (potential synchronous throw or silent coercion), not a performance or aging mechanism. Performance relevance: none.

---

## SELF-SOURCED — UNVALIDATED (not cross-checked, not part of consolidated findings)

1. `app.use(express.json())` (line 10) is configured with no body-size `limit` option. Any client can submit arbitrarily large JSON payloads to `/heartbeat` or `/services`, consuming memory per request during parsing. This is a per-request transient overhead concern rather than a confirmed accumulation pattern, and has not been cross-checked against runtime behavior or Express/body-parser defaults for this version.
2. No explicit server-level timeout/keep-alive tuning is applied to the value returned by `app.listen()` (lines 90-92). Depending on Node/Express defaults in the deployed version, this could theoretically allow slow or idle client connections to hold sockets longer than intended under sustained traffic. This is speculative, environment/version-dependent, and not confirmed from source alone.

---

## Summary

Of the two-reviewer set, the strongest candidate for a genuine software-aging hypothesis (repeatable trigger + persistent accumulation + insufficient bounding + plausible long-running degradation) is the **unindexed `token` column combined with unbounded, never-pruned table growth** (Finding 1), with a related unbounded-result-set variant (Finding 2). Both require runtime/load data (row-count growth trajectory, per-token cardinality) to move from "statically plausible" to "empirically confirmed." The remaining findings (Findings 3-6) are real, verifiable code-level facts, but on inspection either represent transient/one-time conditions (startup race, shutdown handling, crash-on-error) that do not meet the accumulation/progressive-degradation criteria required for an aging classification, or are concurrency-dependent transient overhead not tied to process uptime. None of the findings should be read as confirming actual software aging in this service — all require runtime instrumentation (load testing, long-duration soak testing, query-plan analysis) to validate.

---

# 2. Appendix — Raw Phase-1 Handoffs (unedited)

## Appendix A: CR-* (general code-reviewer)

# Code Review Findings — coding-task-shared/javascript/project-bolt-uptime/project-bolt-uptime/project/src/server.js

CR-1
- ID/file/lines: CR-1, `src/server.js`, lines 16-31 (DB init) interacting with lines 34-62 (`/heartbeat` handler)
- Fault and evidence: `const db = new sqlite3.Database(dbPath, (err) => {...})` (line 16) is created with no `db.configure('busyTimeout', ...)` call, no `PRAGMA journal_mode=WAL;`, and no `db.serialize()` wrapping. The `/heartbeat` route (lines 41-48) issues an `INSERT ... ON CONFLICT ... DO UPDATE` write against the same single `db` connection for every incoming request, with node-sqlite3's default (non-serialized) scheduling.
- Execution path: Multiple concurrent POST `/heartbeat` requests arrive on the Node event loop → each independently calls `db.run(...)` on the shared module-level `db` object → statements are dispatched to SQLite without an explicit serialize boundary or busy-wait configuration.
- Affected state/resource: the single SQLite file `uptime_db` and its write lock; the shared `db` connection object.
- Triggering conditions: two or more heartbeat POSTs (or a heartbeat POST overlapping a `/services` read) processed close together in time, which is the expected steady-state load for an uptime-monitoring service receiving frequent pings from many monitored services.
- Existing cleanup/bounding logic: none — no `busyTimeout`, no WAL mode, no `serialize()`. This is insufficient because SQLite allows only one writer at a time under rollback-journal mode, and without a busy timeout, a lock conflict fails immediately rather than waiting/retrying.
- Plausible runtime consequence: intermittent `SQLITE_BUSY: database is locked` errors surfaced as 500s to legitimate concurrent heartbeat callers, causing missed/duplicated heartbeat registrations under realistic concurrent load.
- Severity: high; Confidence: medium (depends on node-sqlite3's default parallel-vs-serialized scheduling behavior and actual concurrency level, which needs runtime confirmation).
- Assumptions needing validation: actual concurrent request rate in production; node-sqlite3 5.1.7's default execution mode (serialized vs. parallel) when `serialize()` is never called.

CR-2
- ID/file/lines: CR-2, `src/server.js`, lines 24-30 (schema) and lines 72-85 (`/services` query)
- Fault and evidence: table schema only declares `serviceId TEXT PRIMARY KEY` (line 26) — `token` has no index. The `/services` handler executes `SELECT serviceId, lastNotification FROM services WHERE token = ?` (lines 73-75) filtering purely on the unindexed `token` column.
- Execution path: every POST `/services` request triggers this query.
- Affected state/resource: SQLite `services` table scan cost; CPU/I-O per request.
- Triggering conditions: table row count grows (many monitored services registered over time); becomes worse as usage scales.
- Existing cleanup/bounding logic: none — no secondary index on `token`, no query plan hint.
- Plausible runtime consequence: query cost grows linearly (full table scan) with total service count, increasing latency of every `/services` call and blocking the single-threaded event loop / SQLite connection for longer per request as data grows.
- Severity: medium (low impact at small scale, high impact at scale); Confidence: high (directly observable from schema and query).
- Assumptions needing validation: expected row-count growth trajectory and query frequency in production to confirm scan cost becomes material.

CR-3
- ID/file/lines: CR-3, `src/server.js`, lines 16-31 vs. lines 89-92
- Fault and evidence: DB open + `CREATE TABLE IF NOT EXISTS` (lines 16-30) is asynchronous and its completion is never awaited/gated; `app.listen(PORT, ...)` (lines 89-92) executes unconditionally immediately after, independent of whether the `db` open callback has fired or succeeded. On failure, `process.exit(1)` (line 19) runs only inside the async error callback, after the server may already be accepting connections.
- Execution path: process start → `new sqlite3.Database(...)` returns immediately (async open in progress) → synchronous top-level code continues to `app.listen()` → server begins accepting HTTP connections concurrently with (or before) DB open/table-creation completing.
- Affected state/resource: the `db` connection object; incoming HTTP connections/sockets accepted during the startup race window.
- Triggering conditions: requests arriving in the brief window between process start and DB-open callback completion, or a DB-open failure (e.g., file lock, permissions) occurring after the listener is already live.
- Existing cleanup/bounding logic: none — `app.listen` is not nested inside/dependent on the DB open callback's success path.
- Plausible runtime consequence: requests handled during the startup race could be processed against a not-yet-ready connection or hit errors immediately preceding an abrupt `process.exit(1)`, terminating in-flight connections/responses without a clean response.
- Severity: medium; Confidence: medium (node-sqlite3 may internally queue operations issued on the same `db` handle in call order, which would mitigate part of this — behavior needs runtime verification).
- Assumptions needing validation: whether node-sqlite3 queues statements issued before the open callback fires in strict call order (mitigating factor) versus dropping/erroring them.

CR-4
- ID/file/lines: CR-4, `src/server.js`, lines 24-30
- Fault and evidence: `db.run(\`CREATE TABLE IF NOT EXISTS services (...)\`)` is called with no callback argument at all, unlike the `/heartbeat` (line 49, `function(err) {...}`) and `/services` (line 77, `(err, rows) => {...}`) handlers which do check `err`.
- Execution path: DB open succeeds → `CREATE TABLE` executes → if it fails (e.g., disk full, permission denied, corrupted file), the error is silently discarded (no callback to observe `err`).
- Affected state/resource: the `services` table existence/schema state.
- Triggering conditions: any environment where table creation can fail (restricted filesystem permissions, disk space exhaustion, corrupt DB file reused from a prior run).
- Existing cleanup/bounding logic: none — contrast with the other two `db.*` calls in the file, which do check `err`; this one has no equivalent safeguard, so failures here are undetectable from logs.
- Plausible runtime consequence: every subsequent `/heartbeat` and `/services` request fails against a table that silently never got created, each returning a generic "Internal server error" (lines 51-52, 78-80) with no diagnostic trail pointing to the root cause (missing table), making the failure mode confusing/hard to correlate at runtime.
- Severity: medium; Confidence: high (directly observable omission of the callback parameter compared to sibling calls in the same file).
- Assumptions needing validation: whether the deployment environment can realistically produce a `CREATE TABLE` failure (e.g., read-only filesystem, disk pressure) that would exercise this gap.

CR-5
- ID/file/lines: CR-5, `src/server.js`, whole file (no matching lines exist for shutdown handling; see structural absence relative to lines 16-31 db open and 89-92 listen)
- Fault and evidence: there is no `process.on('SIGINT', ...)`/`process.on('SIGTERM', ...)` handler and no call to `db.close(...)` anywhere in the file; the `db` handle opened at line 16 is never explicitly released.
- Execution path: process receives a termination signal (deploy restart, container stop, crash-recovery kill) while requests may be in-flight or queued against `db`.
- Affected state/resource: the SQLite file handle/lock (`uptime_db`), and any queued/in-progress statements on `db`.
- Triggering conditions: any process restart/redeploy/orchestrator-issued termination while the service is under load.
- Existing cleanup/bounding logic: none — no shutdown hook exists to flush queued statements or close the connection cleanly before process exit.
- Plausible runtime consequence: abrupt process termination while `db` has pending writes can leave the connection/file handle in an unclean state (relying entirely on SQLite's own crash-recovery/journal mechanisms rather than an orderly close), and in-flight requests receive no response (socket dropped) rather than a clean shutdown.
- Severity: low-medium; Confidence: high (absence is directly verifiable by inspection of the whole file).
- Assumptions needing validation: actual deployment/restart cadence and whether requests are commonly in-flight at shutdown time; SQLite's practical resilience to this specific process under the target OS/filesystem.

CR-6
- ID/file/lines: CR-6, `src/server.js`, lines 72-85 (query) and lines 24-30 (schema)
- Fault and evidence: `db.all(\`SELECT serviceId, lastNotification FROM services WHERE token = ?\`, [token], (err, rows) => { ... res.status(200).json(rows); })` (lines 72-85) has no `LIMIT`/pagination, and the schema (lines 24-30) does not enforce `token` uniqueness (only `serviceId` is `PRIMARY KEY`), so an arbitrary number of `serviceId` rows can share one `token` value.
- Execution path: POST `/services` with a `token` that matches many rows → `db.all` buffers the entire result set in memory → the full array is serialized into a single JSON HTTP response.
- Affected state/resource: Node process heap (buffering all matched rows before sending), and outbound response payload size.
- Triggering conditions: a token associated with a large number of registered services (no cap enforced anywhere on how many `serviceId`s can register under one token).
- Existing cleanup/bounding logic: none — no `LIMIT`, no streaming, no cap on services-per-token at insert time (the heartbeat UPSERT at lines 41-61 does not restrict how many distinct `serviceId`s can be inserted with the same `token`).
- Plausible runtime consequence: as services-per-token grows, `/services` response time and memory usage grow unbounded, degrading throughput and potentially causing large-payload latency/memory pressure under load.
- Severity: low-medium; Confidence: medium (depends on real-world token-to-service cardinality, which needs profiling/usage-pattern data).
- Assumptions needing validation: typical/maximum number of services expected to share a single token in production usage.

## Appendix B: NS-* (node-specialist)

# Code Review Findings — project-bolt-uptime

**File reviewed:** `coding-task-shared/javascript/project-bolt-uptime/project-bolt-uptime/project/src/server.js`

---

**NS-1**
- **File / lines:** `src/server.js`, lines 9, 16-31, 90-92
- **Fault / evidence:** `app.listen(PORT, ...)` (line 90) is invoked unconditionally at module top-level scope, completely independent of the async `sqlite3.Database` open callback (lines 16-31) that performs `CREATE TABLE IF NOT EXISTS services` (line 24). There is no `await`, promise, or flag gating server start on DB/schema readiness.
- **Execution path:** Module load → `new sqlite3.Database(dbPath, cb)` schedules async open on libuv → synchronously continues to route registration → `app.listen()` binds and starts accepting connections immediately, before `cb` (and its nested `db.run(CREATE TABLE...)`) has necessarily completed.
- **Affected state/resource:** SQLite file handle / `services` table schema; incoming HTTP requests hitting `/heartbeat` and `/services` routes.
- **Triggering conditions:** First run against a fresh/missing `uptime_db` file (schema must be created), slow disk I/O, or any request arriving in the small window between process start and the open callback + CREATE TABLE completing.
- **Existing cleanup/lifecycle logic:** None — there is no readiness gate; `db` is a bare module-level reference used directly by route handlers with no "is ready" check.
- **Plausible runtime consequence:** Requests processed in that window run `db.run`/`db.all` against a table that may not yet exist, producing `SQLITE_ERROR: no such table: services` and 500 responses, or (depending on node-sqlite3 internal command queuing) silently queuing until CREATE TABLE finishes, masking the ordering dependency as coincidental correctness that could break under different timing/hardware.
- **Severity/confidence:** High / High
- **Assumptions needing validation:** Whether node-sqlite3's internal per-connection command queue happens to serialize `CREATE TABLE` ahead of subsequently issued `db.run` calls in practice (this would need runtime/profiling confirmation on the exact sqlite3@5.1.7 build behavior); actual reproducibility depends on disk latency and OS scheduling on first boot.

---

**NS-2**
- **File / lines:** `src/server.js`, line 16 (whole file has no `.on('error', ...)` registration on `db`)
- **Fault / evidence:** `const db = new sqlite3.Database(dbPath, (err) => {...})` (line 16) creates an `EventEmitter`-based `Database` instance. The only error handling present is the constructor callback's `err` parameter (lines 17-20) and per-query callbacks (lines 50-53, 78-81). No listener is ever attached for the instance's `'error'` event.
- **Execution path:** Any internal/native sqlite3 driver error emitted asynchronously outside of a query callback's `err` argument (e.g., driver-level I/O fault, corrupted file, native binding error) is emitted via `db.emit('error', ...)`.
- **Affected state/resource:** Whole Node.js process (all in-flight requests, event loop).
- **Triggering conditions:** Any async 'error' event emitted on `db` with zero listeners registered.
- **Existing cleanup/lifecycle logic:** None. Node's default `EventEmitter` behavior when an `'error'` event fires with no listeners is to throw the error, which is uncaught at that call site.
- **Plausible runtime consequence:** Uncaught exception terminates the entire Node.js process (default Node behavior for unhandled `'error'` events), causing a full outage rather than a contained per-request failure.
- **Severity/confidence:** Med / Med
- **Assumptions needing validation:** Whether sqlite3@5.1.7's native binding actually emits `'error'` on the `Database` object under real fault conditions in this deployment (vs. always routing errors through query callbacks) — this needs runtime/fault-injection confirmation.

---

**NS-3**
- **File / lines:** `src/server.js`, entire file (no shutdown handling); relevant context lines 16-31, 89-92
- **Fault / evidence:** No `process.on('SIGINT'/'SIGTERM', ...)` handler exists anywhere in the file, and `db.close()` is never called. The `db` handle opened at line 16 lives for the entire process lifetime with no explicit teardown path.
- **Execution path:** Process receives termination signal (container stop, `pm2 restart`, `Ctrl+C`, orchestrator rolling deploy) → Node's default behavior for SIGTERM/SIGINT with no handlers is immediate process exit, bypassing any pending SQLite writes.
- **Affected state/resource:** SQLite connection/file handle, any query queued or mid-flight at shutdown time (e.g., a `db.run` heartbeat INSERT in progress).
- **Triggering conditions:** Any restart/redeploy/orchestrated shutdown while requests are in flight.
- **Existing cleanup/lifecycle logic:** None present; contrast with typical Express service pattern of closing DB/HTTP server on signal before exit.
- **Plausible runtime consequence:** Abrupt termination mid-write can leave the SQLite file in a transient locked/journal state on next start (though SQLite's rollback journal generally recovers), and any in-flight client requests receive connection resets rather than clean responses; in clustered/rolling-restart deployments this compounds request loss during every deploy cycle.
- **Severity/confidence:** Med / High
- **Assumptions needing validation:** Actual deployment/orchestration model (whether restarts are frequent) would need to be confirmed to assess real-world frequency of this code path being hit.

---

**NS-4**
- **File / lines:** `src/server.js`, lines 41-48 (write path) and 72-85 (read path)
- **Fault / evidence:** No `PRAGMA busy_timeout` (or `db.configure('busyTimeout', ...)`) is set anywhere before issuing queries. The `INSERT ... ON CONFLICT DO UPDATE` (lines 42-47) is a write against a single SQLite file with default locking behavior (busy timeout = 0 unless configured).
- **Execution path:** Two or more concurrent `/heartbeat` POSTs (or a `/heartbeat` write overlapping a `/services` read) attempt to acquire the SQLite write lock simultaneously through the single shared `db` connection.
- **Affected state/resource:** SQLite database file lock; `db.run` callback's `err` path (lines 49-53).
- **Triggering conditions:** Any concurrent request load hitting `/heartbeat` (multiple monitored services reporting heartbeats around the same time).
- **Existing cleanup/lifecycle logic:** Only a generic `console.error` + 500 response on `err` (lines 50-53) — no retry, no busy-timeout configuration, no backoff.
- **Plausible runtime consequence:** Under concurrent write load, requests fail intermittently with `SQLITE_BUSY: database is locked` surfaced as 500 errors to legitimate heartbeat submissions, rather than being transparently retried/queued.
- **Severity/confidence:** Med / Med
- **Assumptions needing validation:** Actual concurrency level of heartbeat traffic in production and whether node-sqlite3's default internal serialization for a single `Database` object happens to prevent true concurrent file-lock contention in practice — needs load-test/profiling confirmation.

---

**NS-5**
- **File / lines:** `src/server.js`, lines 26 (schema), 72-76 (query)
- **Fault / evidence:** The `services` table (lines 25-29) only indexes `serviceId` (PRIMARY KEY). The `/services` endpoint's `SELECT serviceId, lastNotification FROM services WHERE token = ?` (lines 73-76) and the `ON CONFLICT ... WHERE token = ?` clause in `/heartbeat` (line 47) both filter/match on `token`, a column with no index. There is also no deletion/retention logic anywhere in the file, so the table only ever grows (rows are inserted or updated, never removed).
- **Execution path:** Every `/services` POST and every `/heartbeat` conflict-resolution UPDATE performs a scan predicated on the unindexed `token` column.
- **Affected state/resource:** SQLite query execution cost, event loop (query time occupies the libuv thread pool slot / blocks the response for that request).
- **Triggering conditions:** Table row count growing over the service's operational lifetime (more monitored services/tokens registered over time), since nothing ever prunes `services` rows.
- **Existing cleanup/lifecycle logic:** None — no index on `token`, no TTL/prune job, no cap on table size.
- **Plausible runtime consequence:** Query latency for `/services` and the heartbeat conflict-check degrades roughly linearly (full table scan) as the number of distinct services grows, increasing per-request latency and worker-thread-pool occupancy under sustained growth, with no bound in place.
- **Severity/confidence:** Med / High (code evidence: absence of `CREATE INDEX` and absence of any DELETE statement in the entire file, confirmed by inspection)
- **Assumptions needing validation:** Actual expected table cardinality in production (small deployments may never notice); would need query-plan (`EXPLAIN QUERY PLAN`) and load-scale data to quantify impact.

---

**NS-6**
- **File / lines:** `src/server.js`, lines 34-48
- **Fault / evidence:** `const { serviceId, token } = req.body;` (line 35) is only validated with a truthiness check (`if (!serviceId || !token)`, line 37) — no type check (e.g., `typeof === 'string'`) before binding both values directly as SQL parameters into `db.run(...)` (lines 41-48). A JSON body can supply `serviceId`/`token` as an object, array, or number instead of a string.
- **Execution path:** Malformed request body (e.g., `{"serviceId": {}, "token": {}}`) passes the falsy check (an object/array is truthy) and is forwarded straight into the parameterized query bind call.
- **Affected state/resource:** Request-handling call stack for `/heartbeat`; underlying native sqlite3 parameter-binding routine.
- **Triggering conditions:** Any client (or upstream proxy/misbehaving monitored service) sending a JSON body with non-string `serviceId`/`token` fields.
- **Existing cleanup/lifecycle logic:** None — no `typeof` or schema validation layer (e.g., Zod/Joi) is present anywhere in the file; the only guard is the line-37 truthiness check.
- **Plausible runtime consequence:** Depending on how the native sqlite3 binding handles non-primitive bind parameters, this can either throw synchronously within the route handler's call frame (before reaching the `err`-first callback path at lines 49-53) or silently coerce the value (e.g., via `toString()`/`JSON` stringification) producing corrupted `serviceId`/`token` data persisted to the database — either an unhandled-exception-driven 500 or silent data corruption.
- **Severity/confidence:** Low-Med / Low
- **Assumptions needing validation:** Exact parameter-binding behavior of sqlite3@5.1.7's native binding for non-primitive JS values would need to be confirmed at runtime (this determines whether the consequence is a synchronous throw vs. silent coercion).
