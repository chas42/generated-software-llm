---
# Adjudication Report: coding-tasks/python-fastAPI/CreditCardService

Verified directly against coding-tasks/python-fastAPI/CreditCardService/code/app.py (full file read, 171 lines). All cited line ranges in both handoffs were checked against the actual file and are accurate (minor ±1 line offsets in class boundaries, immaterial). No code was executed; this is a static-analysis adjudication only.

---
Consolidated Finding 1 — Unbounded phone_numbers list drives unbounded SQL query construction

IDs merged: CR-1 + FA-4 (same code, same mechanism) Static validity: confirmed Location: app.py lines 103-104 (phone_numbers: List[str] = Field(..., min_length=1), no max_length), 106-121 (dedup only, no cap), 148-162 (placeholders = ",".join(["?"] * len(phones)); conn.execute(query, (*phones, len(phones)))).

- **Performance relevance:** direct for the sub-claim that per-request CPU/memory/query-parse cost scales linearly with the client-supplied list size (directly evidenced — no size cap exists anywhere between the Pydantic model and the query execution). Conditional for the sub-claim that this can raise sqlite3.OperationalError: too many SQL variables — that depends on the SQLite build's SQLITE_LIMIT_VARIABLE_NUMBER (historically 999, 32766 since SQLite 3.32.0), which is not determinable from this file.
- **Affected resource / trigger / cleanup / bounds:** per-request CPU/memory and SQLite statement compilation; triggered by any single request with a large phone_numbers list; resource is request-scoped and fully released when the connection closes (line 56) — no leak, no persistence across requests.
- **Direct evidence vs. assumption:** Direct — absence of max_length, and the 1:1 mapping from list length to placeholder count and bound-parameter count is unambiguous in code. Assumption — the actual compiled SQLite variable limit, and whether any upstream layer (proxy/body-size limit) already constrains payload size before reaching this code.
- **Mechanism class:** transient/repeated overhead (cost is proportional to a single request's input and does not persist or accumulate after the request completes).
- **Aging relevance:** non-aging performance fault. It lacks the "persistent accumulation over long-running execution" element — each occurrence is self-contained per request, not a mechanism that worsens with process uptime.
- **Final severity:** medium (real, code-confirmed, unbounded-input surface that can cause per-request failure or degraded latency).
- **Final confidence:** medium (mechanism is directly evidenced; magnitude/crash threshold depends on environment).

---
Consolidated Finding 2 — Unbounded field length + no cleanup/retention mechanism → cumulative table/index growth

ID: CR-2 (standalone from CR/FA sets, but supplemented by my own verification of the full file for the "existing cleanup" element required by the adjudication protocol) Static validity: confirmed, and strengthened Location: app.py lines 79-92 (credit_card validated digits-only but no length bound), 94-100 (phone has no format or length constraint at all), 33-41 (associations table with credit_card TEXT NOT NULL, phone TEXT NOT NULL, UNIQUE(credit_card, phone), plus idx_assoc_phone/idx_assoc_card), 128-140 (INSERT OR IGNORE).

- **Performance relevance:** conditional, but with a stronger basis than either reviewer stated. I confirmed via full-file read that app.py defines exactly two routes (POST /associate_card, POST /retrieve_cards) and no delete/expiry/admin endpoint exists anywhere in the file — i.e., every successfully inserted (credit_card, phone) pair is permanent for the life of the database, regardless of string length. This directly satisfies the "insufficient cleanup" element that CR-2 asserted but did not explicitly verify by absence-of-endpoint.
- **Affected resource / trigger / cleanup / bounds:** the associations table and its two B-tree indexes (plus the implicit UNIQUE-constraint index on (credit_card, phone)); triggered by any repeated legitimate or adversarial associate_card call with a new unique pair; no cleanup/TTL/deletion path exists in the codebase; no upper bound on row count or per-field string length.
- **Direct evidence vs. assumption:** Direct — no max_length on either field; no DELETE/cleanup route in the file; SQLite TEXT columns do not enforce declared length regardless of type annotation. Assumption — actual growth rate under real traffic, and whether external DB maintenance (VACUUM, archival) happens outside this codebase.
- **Mechanism class:** cumulative resource retention (monotonic, unbounded growth of table/index size over the service's running lifetime, with no bounding or eviction).
- **Aging relevance:** this is the only finding among the two handoffs that satisfies all four required aging elements on direct code evidence: (1) repeatable trigger — every associate_card call with a new pair; (2) persistent accumulation — rows/index entries never expire; (3) insufficient cleanup — confirmed no deletion mechanism exists; (4) plausible degradation — growing indexed table increases insert/lookup cost (retrieve_cards's WHERE phone IN (...) GROUP BY ... HAVING scans a growing index). Classified as a static aging mechanism supported hypothesis — this is a static-analysis hypothesis about a plausible long-running degradation pattern, not an empirically confirmed one; runtime/soak testing would be needed to measure actual growth rate and latency impact.
- **Final severity:** medium (upgraded from CR-2's "low" given the confirmed total absence of any cleanup path, not just unbounded field length).
- **Final confidence:** medium (mechanism and absence-of-cleanup are directly evidenced; magnitude and time-to-materialize are unconfirmed).

---
Consolidated Finding 3 — Per-request SQLite connection open/PRAGMA/close (no pooling)

IDs merged: CR-3 + FA-2 Static validity: confirmed Location: app.py lines 47-56 (db_conn(): sqlite3.connect → PRAGMA foreign_keys=ON → yield → commit → finally: conn.close()), called fresh at line 130 and line 161.

- **Performance relevance:** direct — this is a real, unconditional per-request cost (connect + PRAGMA + close) on every call to both endpoints.
- **Affected resource / trigger / cleanup / bounds:** OS file handle / SQLite connection object, released every time via try/finally (line 56) — confirmed no leak. Triggered unconditionally by every request to either endpoint.
- **Direct evidence vs. assumption:** Direct — the connect/PRAGMA/close cycle per call site is unambiguous. Assumption — the absolute magnitude of this overhead relative to query execution time (filesystem/OS dependent), which both reviewers correctly flag as needing profiling.
- **Mechanism class:** transient/repeated overhead — a fixed, non-growing cost paid identically on request 1 and request 1,000,000.
- **Aging relevance:** non-aging performance fault. Cleanup is fully sufficient (no leak); the cost does not accumulate or worsen with process uptime — it is a constant steady-state inefficiency, not a degradation mechanism.
- **Final severity:** low (both reviewers agree; confirmed).
- **Final confidence:** high (mechanically unambiguous from the code).

---
Consolidated Finding 4 — Unhandled sqlite3.OperationalError under concurrent write-lock contention

IDs merged: CR-4 + FA-3 Static validity: confirmed Location: app.py lines 47-56 (db_conn, sqlite3.connect(DB_PATH, check_same_thread=False) line 49, no timeout= argument), 65-67 (only registered exception handler is for RequestValidationError), 128-140 (associate_card, no try/except around conn.execute).

- **Performance relevance:** conditional — manifests only when concurrent write requests exceed SQLite's default busy-timeout window. Note the 5-second default busy-timeout value is a Python sqlite3 stdlib default, not something visible in this file — this is a well-established but external assumption, correctly flagged by both reviewers.
- **Affected resource / trigger / cleanup / bounds:** the SQLite writer lock; triggered by concurrent POST /associate_card calls contending beyond the (assumed) 5s default timeout. Connection is still closed in finally regardless of outcome (no resource leak) — the gap is purely in error handling/response contract, not resource retention.
- **Direct evidence vs. assumption:** Direct — no try/except around the write, no registered handler for DB exceptions, no explicit timeout=. Assumption — actual concurrent write throughput in practice, and the specific default timeout value of the deployed Python/SQLite combination.
- **Mechanism class:** finite-resource exhaustion, transient (lock contention resolves per-transaction; no state persists across requests, no cumulative degradation with uptime).
- **Aging relevance:** non-aging performance fault (more precisely a reliability/error-contract gap with conditional performance relevance under load spikes). Missing the "persistent accumulation over long-running execution" element — this is a function of instantaneous concurrent load, not elapsed run time.
- **Final severity:** low-medium (reviewers rated med/med and med/low; the generous 5s default timeout is a meaningful mitigating factor not fully credited in either handoff).
- **Final confidence:** low-medium (core claim depends on an external stdlib default not verifiable from this file alone).

---
Consolidated Finding 5 — Synchronous def handlers performing blocking DB I/O (threadpool saturation risk)

IDs merged: CR-5 + FA-1 Static validity: confirmed for the in-file facts; framework-behavior claims are external assumptions Location: app.py line 129 (def associate_card(...)), line 148 (def retrieve_cards(...)), both performing blocking sqlite3 calls in-body with no async/await anywhere in the file (verified via full read).

- **Performance relevance:** conditional — contingent on concurrent request volume approaching FastAPI/Starlette's default AnyIO threadpool capacity (commonly ~40 workers), and on blocking I/O duration (which itself could be worsened by Finding 4's lock contention). None of this threadpool-sizing detail is present in app.py — it is framework-internal behavior, not code evidence from this file.
- **Affected resource / trigger / cleanup / bounds:** shared, framework-managed AnyIO threadpool; threads are returned after each request (framework-managed, not a leak); bounded by the framework's own default limiter.
- **Direct evidence vs. assumption:** Direct — sync def handlers with blocking calls in-body. Assumption — FastAPI/Starlette/AnyIO's actual threadpool default and behavior in the deployed version, and real concurrency levels.
- **Mechanism class:** finite-resource exhaustion (bounded capacity can saturate under load), not persistent/cumulative — resets between load periods.
- **Aging relevance:** non-aging performance fault — a static architectural throughput ceiling under concurrent load, not a mechanism that worsens with process uptime.
- **Final severity:** low-medium (reviewers split med/med vs low/low; I weight it toward low-medium given the framework-dependent nature of the core claim).
- **Final confidence:** low-medium (substantially dependent on unverified framework internals).

---
Consolidated Finding 6 — Redundant PRAGMA/commit() on the read-only retrieve_cards path

ID: CR-6 (standalone; no direct FA equivalent, though FA-2 tangentially notes PRAGMA repetition as part of connection overhead) Static validity: confirmed Location: app.py lines 51-54 (generic db_conn context manager issues PRAGMA foreign_keys=ON and conn.commit() unconditionally), line 161-162 (retrieve_cards only performs a SELECT, no mutation, yet goes through the same generic context manager).

- **Performance relevance:** direct but minor — the PRAGMA and no-op commit() calls are genuinely extraneous work on the read path, though both handoffs correctly note the absolute cost of a no-op commit/PRAGMA in SQLite is typically negligible without measurement.
- **Affected resource / trigger / cleanup / bounds:** per-request CPU/syscall overhead only, on every /retrieve_cards call; fully bounded, no accumulation.
- **Direct evidence vs. assumption:** Direct — the shared, undifferentiated db_conn() implementation unconditionally issues PRAGMA and commit for both read and write call sites. Assumption — actual latency materiality of a no-op PRAGMA/commit.
- **Mechanism class:** transient/repeated overhead, fixed and non-growing.
- **Aging relevance:** non-aging performance fault.
- **Final severity:** low (agrees with reviewer).
- **Final confidence:** medium (code fact is exact; materiality is unconfirmed and likely small).

---
Excluded from consolidation

FA-5 (missing explicit rollback() in db_conn's finally path, lines 47-56) was reviewed but excluded from the six consolidated findings: static validity is confirmed as a code fact, but per the scope constraint to consider only findings with direct or conditional performance relevance, this finding's own text frames it as a data-integrity/correctness concern ("latent correctness gap," "partial-write ambiguity"), not a performance-consequence one. Performance relevance: none. Not an aging mechanism (no resource accumulation described).

---
SELF-SOURCED — UNVALIDATED (not cross-checked by an independent reviewer; not included above)

1. Read-path query cost is coupled to Finding 2's unbounded table growth, with no pagination/LIMIT. retrieve_cards (lines 148-167) executes WHERE phone IN (...) GROUP BY credit_card HAVING COUNT(DISTINCT phone) = ? ORDER BY credit_card with no LIMIT and no bound on result-set/scan size. Since (per Finding 2) the associations table has no deletion mechanism and can only grow over the service's lifetime, this query's per-request scan/sort cost is hypothesized to increase correspondingly over long-running execution — connecting the write-side accumulation (Finding 2) to a read-side latency-degradation mechanism that neither reviewer explicitly stated. This is an unvalidated static-analysis hypothesis requiring runtime/load-profile confirmation.
2. Write-path index-maintenance amplification compounds unbounded table growth. The schema (lines 33-41) declares UNIQUE(credit_card, phone) — which SQLite implements via an automatic composite index — plus two additional explicit single-column indexes idx_assoc_phone and idx_assoc_card. idx_assoc_card substantially overlaps in purpose with the leading column of the automatic UNIQUE index, meaning each INSERT OR IGNORE (lines 131-137) maintains three B-tree structures instead of the two that appear functionally necessary. Combined with Finding 2's unbounded row growth, each insert's index-maintenance cost is hypothesized to scale with O(log n) per index across three indexes rather than two, compounding over the table's lifetime. This is an unvalidated static-analysis hypothesis requiring runtime/profiling confirmation of actual index-maintenance cost and growth trajectory.

------ APPENDIX A — Raw Phase-1 Handoff: CR-* (voltagent-qa-sec:code-reviewer)

### CR-1
- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 103-121, 148-162
- **fault and direct code evidence:** RetrieveCardsRequest.phone_numbers (line 104) is declared with min_length=1 but no max_length bound: phone_numbers: List[str] = Field(..., description="Phone numbers", min_length=1). In retrieve_cards, this unbounded list is used to build the SQL statement dynamically: placeholders = ",".join(["?"] * len(phones)) (line 150) and then WHERE phone IN ({placeholders}) ... HAVING COUNT(DISTINCT phone) = ? (lines 152-159), executed with conn.execute(query, (*phones, len(phones))) (line 162).
- **relevant execution path:** POST /retrieve_cards -> pydantic validation (dedup only, no size cap) -> retrieve_cards() -> query string built proportional to list length -> single SQLite execute with N bound parameters and a GROUP BY/HAVING scan.
- **affected state or resource:** SQLite query planner/execution cost, CPU/memory for building the placeholder string and parameter tuple, SQLite parameter-count limits (SQLITE_LIMIT_VARIABLE_NUMBER, default 999/32766 depending on build).
- **triggering conditions:** client submits phone_numbers with a very large number of unique entries (nothing in the model or handler caps list length).
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: only min_length=1 and de-duplication (lines 106-121) exist; there is no upper bound, so arbitrarily large lists reach the query-building and execution code unmodified.
- **plausible runtime consequence:** degraded response latency for large requests, increased memory/CPU per request, and for sufficiently large lists a SQLite "too many SQL variables" runtime error (unhandled, see CR-4) instead of a graceful 400.
- **severity:** med
- **confidence:** med
- **assumptions that would need runtime/profiling validation:** actual SQLite build's variable limit, presence/absence of any upstream request-size limiting (e.g., reverse proxy) not visible in this file, and observed latency/throughput under large payloads.

### CR-2
- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 79-101
- **fault and direct code evidence:** credit_card and phone fields (lines 80-81) are declared as plain str with no max_length: credit_card: str = Field(..., description="Number of the credit card") and phone: str = Field(..., description="Phone number"). Validators (lines 83-100) only normalize/reject empty or non-digit values, never bound length.
- **relevant execution path:** POST /associate_card -> AssociateCardRequest validation -> associate_card() -> INSERT OR IGNORE INTO associations (credit_card, phone) VALUES (?, ?) (lines 131-137).
- **affected state or resource:** associations table rows and the two indexes idx_assoc_phone/idx_assoc_card (lines 40-41) that index these unbounded-length TEXT columns; per-request memory for validated strings.
- **triggering conditions:** client submits arbitrarily long credit_card/phone strings (digits-only constraint still permits unbounded length for credit_card; phone has no format constraint at all).
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: normalization strips spaces/hyphens (lines 70-72) and rejects empty/non-digit credit_card, but no size cap exists anywhere in the model or handler, so the values flow unbounded into indexed columns.
- **plausible runtime consequence:** growth of index size and per-row storage disproportionate to legitimate input, increasing insert/query latency and index maintenance cost over time as such rows accumulate.
- **severity:** low
- **confidence:** med
- **assumptions that would need runtime/profiling validation:** whether any external layer restricts request body/field size; actual index growth/latency impact would need profiling under adversarial input volume.

### CR-3
- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 47-56, 130, 161
- **fault and direct code evidence:** db_conn() (lines 47-56) opens a brand-new sqlite3.connect(DB_PATH, check_same_thread=False) and issues PRAGMA foreign_keys=ON; (line 52) on every invocation, then closes the connection in finally (line 56). Both associate_card (line 130) and retrieve_cards (line 161) call with db_conn() as conn: per request, i.e., a fresh connect/PRAGMA/close cycle for every single HTTP request rather than reusing a connection or pool.
- **relevant execution path:** every POST /associate_card and POST /retrieve_cards request independently triggers sqlite3.connect -> PRAGMA execution -> query -> commit -> close.
- **affected state or resource:** OS-level file handles/sqlite connection objects, per-request syscall overhead (open/close), no shared connection or pool object at module scope.
- **triggering conditions:** any request to either endpoint; effect scales with request rate.
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: the try/finally reliably closes each connection (no leak), but there is no reuse/pooling mechanism, so the per-request connect/PRAGMA/close overhead is paid unconditionally on the hot path for both read and write endpoints.
- **plausible runtime consequence:** added latency per request from repeated connection setup/teardown and PRAGMA execution, and reduced achievable throughput under sustained load compared to a reused-connection design.
- **severity:** low
- **confidence:** high
- **assumptions that would need runtime/profiling validation:** magnitude of per-connect overhead on the deployment's filesystem/OS, and whether request volume is high enough for this overhead to be material versus query execution time itself.

### CR-4
- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 47-56, 128-140
- **fault and direct code evidence:** db_conn() performs no exception handling around conn.execute/conn.commit (lines 51-54); associate_card (lines 128-140) calls conn.execute("INSERT OR IGNORE INTO associations ...") (lines 131-137) with no try/except. The only registered exception handler in the file is validation_exception_handler for RequestValidationError (lines 65-67); there is no handler for sqlite3.OperationalError or other DB exceptions.
- **relevant execution path:** concurrent POST /associate_card requests each open independent connections (per CR-3) and attempt writes against the same WAL-mode SQLite file; if SQLite's writer lock/busy timeout is exceeded, conn.execute/conn.commit raises sqlite3.OperationalError ("database is locked"), which propagates unhandled out of the route.
- **affected state or resource:** the associations SQLite database file/WAL lock, in-flight request/response cycle for the affected requests.
- **triggering conditions:** multiple concurrent write requests contending for the single SQLite writer lock beyond the default connect timeout (5s default when no timeout argument is passed at line 49, so contention window is bounded but not eliminated); higher concurrency increases likelihood.
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: the try/finally in db_conn guarantees the connection is closed even on error, but it does not catch or translate the exception, so it surfaces to the client as an unhandled 500 rather than a controlled response; no retry logic exists.
- **plausible runtime consequence:** sporadic unhandled 500 errors (or connection errors) for /associate_card under concurrent write load, rather than deterministic success/idempotent-ignore behavior implied by the "INSERT OR IGNORE" design.
- **severity:** med
- **confidence:** med
- **assumptions that would need runtime/profiling validation:** actual concurrent write rate in production/tests, and whether observed responses under load show 500s consistent with SQLite lock contention (would require load testing to confirm reachability).

### CR-5
- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 129, 148, 130-140, 161-162
- **fault and direct code evidence:** associate_card(payload: AssociateCardRequest, response: Response) (line 129) and retrieve_cards(payload: RetrieveCardsRequest) (line 148) are both defined as synchronous def handlers (not async def), yet each performs blocking file/database I/O directly in the handler body via db_conn()/conn.execute (lines 130-140, 161-162), with no async/await or offloading indicated in this file.
- **relevant execution path:** every request to either endpoint executes blocking SQLite I/O synchronously within the handler's execution context.
- **affected state or resource:** request-handling execution context/worker capacity used to service concurrent HTTP requests to this app.
- **triggering conditions:** multiple simultaneous requests to /associate_card and/or /retrieve_cards.
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: no bounding, batching, or async I/O is implemented anywhere in this file for the DB calls; the handlers rely entirely on default framework behavior for sync endpoints, which this file does not configure or override.
- **plausible runtime consequence:** under concurrent load, blocking I/O executed synchronously in request handlers can serialize/queue requests and increase tail latency compared to true async DB access, limiting throughput scaling.
- **severity:** low
- **confidence:** low
- **assumptions that would need runtime/profiling validation:** this depends heavily on FastAPI/Starlette's threadpool-offload behavior for sync def routes (framework internals outside this file), which would need to be confirmed/profiled to determine actual throughput impact; flagged here strictly as an application-code characteristic (sync handlers doing blocking I/O) with a plausible performance consequence.

### CR-6
- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 51-54, 161-162
- **fault and direct code evidence:** db_conn() unconditionally executes conn.execute("PRAGMA foreign_keys=ON;") (line 52) and calls conn.commit() (line 54) after every with block, including in retrieve_cards (lines 161-162), which only performs a SELECT and never mutates data.
- **relevant execution path:** POST /retrieve_cards -> with db_conn() as conn: rows = conn.execute(query, ...).fetchall() -> context manager exit runs conn.commit() regardless of the read-only nature of the query.
- **affected state or resource:** SQLite connection/transaction handling for the read path.
- **triggering conditions:** every call to /retrieve_cards.
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: the context manager is generic (shared by both write and read call sites) and does not distinguish read-only usage, so it always issues a PRAGMA and a commit even when no write occurred, adding avoidable per-request overhead on the read path.
- **plausible runtime consequence:** minor additional latency per read request from redundant PRAGMA execution and commit call on a connection that made no changes.
- **severity:** low
- **confidence:** med
- **assumptions that would need runtime/profiling validation:** the actual cost of a no-op commit()/PRAGMA on this SQLite build/OS would need measurement to confirm materiality relative to overall request latency.

------ APPENDIX B — Raw Phase-1 Handoff: FA-* (voltagent-lang:fastapi-developer)

### FA-1

- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 128-140, 143-167, 47-56
- **fault and direct code evidence:** Path operations are declared with plain def rather than async def (def associate_card(payload: AssociateCardRequest, response: Response): line 129; def retrieve_cards(payload: RetrieveCardsRequest): line 148). FastAPI/Starlette dispatches sync path operations through AnyIO's bounded worker thread pool (run_in_threadpool, default capacity limiter). Each call performs blocking synchronous I/O inside db_conn() (sqlite3.connect(DB_PATH, check_same_thread=False) line 49, conn.execute(...) / conn.commit() line 54) while holding a thread-pool slot for the whole request.
- **relevant execution path:** Every incoming POST to /associate_card or /retrieve_cards is scheduled onto the shared AnyIO threadpool; the request's async task is blocked waiting for a worker thread to become free, then blocked again on synchronous SQLite calls within that thread.
- **affected state or resource:** Shared, app-wide AnyIO threadpool (bounded number of worker threads) and the ASGI event loop's ability to service concurrent requests.
- **triggering conditions:** Concurrent request volume approaching or exceeding the threadpool's default capacity (commonly 40 workers) — sustained SQLite I/O latency under WAL mode or disk contention would keep threads occupied longer, queuing subsequent requests.
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: No custom capacity limiter or async DB driver is configured; only the framework's default threadpool bound applies, which is not tuned to the blocking DB workload here, so it provides sizing but not throughput guarantees for this I/O pattern.
- **plausible runtime consequence:** Under concurrent load, request latency increases nonlinearly once threadpool saturation is reached; requests queue rather than execute, producing tail-latency spikes or timeouts even though the event loop itself remains unblocked.
- **severity:** medium
- **confidence:** medium
- **assumptions that would need runtime/profiling validation:** Actual default threadpool size in the deployed Starlette/AnyIO version, real concurrent request rate, and measured SQLite call latency under contention.

### FA-2

- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 47-56, 130, 161
- **fault and direct code evidence:** db_conn() (lines 47-56) opens a brand-new sqlite3.connect(DB_PATH, ...) and issues conn.execute("PRAGMA foreign_keys=ON;") (line 52) on every single call, then closes the connection in finally: conn.close() (line 56). Both associate_card (line 130: with db_conn() as conn:) and retrieve_cards (line 161: with db_conn() as conn:) invoke this per request — there is no persistent connection or pool reused across requests.
- **relevant execution path:** Each /associate_card and /retrieve_cards call independently opens a new OS-level file handle to db.sqlite3, runs a PRAGMA, executes the query, commits, then closes and discards the connection.
- **affected state or resource:** SQLite connection/file-descriptor lifecycle, SQLite statement cache (lost on each close), and underlying WAL/SHM sidecar files.
- **triggering conditions:** Any sustained request rate — the overhead is incurred unconditionally on every call, so it scales linearly with request volume.
- existing cleanup, lifecycle, or bounding logic, and why it isn't sufficient: The contextmanager-based db_conn() correctly closes the connection (no leak), but it provides no reuse/pooling, so connection-establishment cost (open/PRAGMA/close, WAL checkpoint bookkeeping) is paid on every request instead of amortized.
- **plausible runtime consequence:** Increased per-request latency and syscall overhead compared to a pooled/persistent-connection design; under high request rates this repeated connect/close cycle becomes a throughput ceiling independent of query complexity.
- **severity:** low
- **confidence:** medium
- **assumptions that would need runtime/profiling validation:** Measured cost of sqlite3.connect/close and PRAGMA execution on the target filesystem, and whether WAL auto-checkpoint frequency is materially affected by short-lived connections.

### FA-3

- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 27, 49, 65-67, 128-140
- **fault and direct code evidence:** init_db() sets PRAGMA journal_mode=WAL; (line 27), and db_conn() (line 49) calls sqlite3.connect(DB_PATH, check_same_thread=False) without an explicit timeout= argument, so the driver's default busy-wait (5 seconds) applies. associate_card (lines 128-140) performs an INSERT inside this connection with no try/except around it, and the only registered exception handler is @app.exception_handler(RequestValidationError) (lines 65-67) — nothing handles sqlite3.OperationalError.
- **relevant execution path:** Multiple concurrent POST /associate_card requests each open independent write connections; SQLite permits only one writer at a time even in WAL mode, so concurrent writers serialize on the database lock.
- **affected state or resource:** The single SQLite database file's write lock, and the per-request thread executing the INSERT.
- **triggering conditions:** Several /associate_card requests executing concurrently such that one writer's transaction is not released within the default busy timeout window, causing a competing connection's execute/commit to raise sqlite3.OperationalError: database is locked.
- existing cleanup, lifecycle, or bounding logic, and why it isn't sufficient: The default 5-second busy timeout provides some tolerance, but there is no retry logic and no handler for this exception class, so once the timeout is exceeded the exception propagates unhandled out of the sync path operation.
- **plausible runtime consequence:** Under write-concurrency spikes, some requests fail with an unhandled 500-level error instead of a graceful response, and the failure is opaque to the client (no explicit error contract for this case, only the RequestValidationError 400 path is defined).
- **severity:** medium
- **confidence:** low
- **assumptions that would need runtime/profiling validation:** Actual observed write-concurrency levels and whether transactions are held long enough to exceed the 5-second default busy timeout in practice.

### FA-4

- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 103-104, 148-162
- **fault and direct code evidence:** RetrieveCardsRequest.phone_numbers is declared as List[str] = Field(..., description="Phone numbers", min_length=1) (lines 103-104) with no upper bound (max_length). In retrieve_cards, placeholders = ",".join(["?"] * len(phones)) (line 150) and the query is executed as conn.execute(query, (*phones, len(phones))) (line 162), so the number of bound SQL parameters equals the (unbounded) size of the client-supplied list.
- **relevant execution path:** A POST /retrieve_cards request whose validated phone_numbers list (after dedup at lines 106-121) contains a very large number of entries flows directly into query construction and execution without any size check.
- **affected state or resource:** The SQLite query compiler's bound-parameter limit (SQLITE_LIMIT_VARIABLE_NUMBER) and per-request memory/CPU used to build and parse the dynamically sized SQL string.
- **triggering conditions:** A request with a phone_numbers list large enough to exceed the SQLite build's variable limit (commonly 999 or higher depending on version) triggers sqlite3.OperationalError: too many SQL variables; even below that limit, very large lists linearly increase query string size and parse/plan cost.
- existing cleanup, lifecycle, or bounding logic, and why it isn't sufficient: min_length=1 bounds the lower end only; deduplication (lines 112-121) reduces but does not cap the list; no max_length or explicit length check exists before query construction, and no exception handler catches the resulting OperationalError.
- **plausible runtime consequence:** For sufficiently large input lists, the endpoint raises an unhandled exception (effectively a request failure) instead of a defined error response; for large-but-under-limit lists, per-request CPU/memory cost for query construction grows without bound.
- **severity:** medium
- **confidence:** medium
- **assumptions that would need runtime/profiling validation:** The exact SQLite variable limit compiled into the deployed Python's sqlite3 module, and whether any upstream layer (e.g., request body size limit) already constrains list length before it reaches this code.

### FA-5

- **file:** coding-tasks/python-fastAPI/CreditCardService/code/app.py
- **exact line range:** 47-56
- **fault and direct code evidence:** db_conn() yields the connection inside a bare try/finally (lines 51-56) with conn.commit() placed immediately after the yield (line 54) and no except clause. If the code inside the with db_conn() as conn: block raises after a partial write (e.g., a second statement failing after a first execute succeeded, or an exception raised by SQLite itself), control jumps directly from the yield point to finally: conn.close() (line 56), skipping conn.commit() entirely with no explicit rollback() call.
- **relevant execution path:** Applies to both associate_card (line 130) and retrieve_cards (line 161) call sites whenever an exception occurs between entering the with block and its normal completion.
- **affected state or resource:** The SQLite connection's open transaction state at close time.
- **triggering conditions:** Any exception raised inside the with db_conn() as conn: body after at least one write has been staged on the connection (currently only a single INSERT OR IGNORE per request, so limited exposure today, but the pattern generalizes to any future multi-statement addition).
- existing cleanup, lifecycle, or bounding logic, and why it isn't sufficient: Connection close() implicitly discards an uncommitted transaction, so no committed corruption occurs for the current single-statement usage; however, there is no explicit rollback() in the finally path, so behavior for any future multi-statement transaction added to a handler would rely on implicit close semantics rather than an explicit guarantee.
- **plausible runtime consequence:** With the current single-INSERT usage this is low-impact, but it is a latent correctness gap: any future handler that performs multiple sequential writes within one with db_conn() block would silently rely on implicit rollback-on-close rather than a guaranteed rollback, risking partial-write ambiguity if that implicit behavior differs across SQLite/Python versions.
- **severity:** low
- **confidence:** low
- **assumptions that would need runtime/profiling validation:** Confirmation of the exact implicit-rollback-on-close behavior for the specific Python sqlite3/SQLite version in the deployment environment.

---