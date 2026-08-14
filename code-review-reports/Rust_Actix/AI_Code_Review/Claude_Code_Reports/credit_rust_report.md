---
# 1. Performance-Engineer's Final Consolidated Report (verbatim)

Static-Analysis Adjudication Report: Credit_Card main.rs (Rust)

Verified directly against coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs (142 lines) and Cargo.toml. All line numbers below reflect the actual file as read, with any reviewer line-number discrepancies flagged explicitly.

---
## Finding A — RwLock poison propagation on .unwrap() (merged: CR-1 + RE-2)

- **static validity:** confirmed (code fact) / qualified (runtime consequence)
- **direct code evidence:** data.storage.write().unwrap() (line 69), data.storage.read().unwe: RwLock<HashMap<String, HashSet<String>>> (line 34, use std::sync::RwLock; line 4). Nounwrap_or_else, into_inner(), or clear_poison() anywhere in the 142-line file — confirmed by full read.
- **affected resource:** the single RwLock in the shared Arc-backed AppState (via web::Data,line 135).
- **triggering condition:** a panic while a guard is held (lines 69–75 for write, 90–120 for read — see self-sourced note below). Critical sections contain only infallible HashMap/HashSet operations (entry, or_insert_with, insert, get, retain); no realistic panic source is visible in this file
- **existing cleanup/bounding:** none.
- **evidence vs. assumption:** the .unwrap()-without-poison-recovery pattern is a direct codroduces a "permanent full-service outage" is a runtime/framework consequence contingent on a panic actually occurring — which, per the code visible here, has no in-file trigger under normal operation.
- **mechanism class:** does not cleanly fit the aging taxonomy — it is a binary, single-evenrmanently poisoned), not progressive accumulation.
- **aging relevance:** unsupported as an aging mechanism — fails the "repeatable trigger during normal long-running operation" and "progressive accumulation" criteria (a panic is an exceptional, not routine, event; poisoning is instantaneous, not gradual). It is better characterized as a latent software aging.
- **final severity:** low (down from CR-1's med / RE-2's high) — no in-file panic source exists; degrades to purely theoretical (OOM/allocator failure) without further evidence.
- **final confidence:** med (code pattern itself is unambiguous; real-world reachability is

---
## Finding B — Unbounded growth of HashMap<String, HashSet<String>> (merged: CR-2 + RE-3)

- **static validity:** confirmed
- **direct code evidence:** storage: RwLock<HashMap<String, HashSet<String>>> (line 34), popne).or_insert_with(HashSet::new).insert(card); (lines 72–74). Full-file read confirms noeviction, TTL, capacity cap, or pruning logic exists anywhere; the map is constructed once in main (line 128) and never cleared.
- **affected resource:** process heap memory backing AppState.storage, held for the lifetime
- **triggering condition:** repeated POST /associate_card calls with distinct phone/card values — a normal, repeatable production workload pattern (not exceptional).
- **existing cleanup/bounding:** none whatsoever — confirmed by exhaustive read of the file.
- **evidence vs. assumption:** growth mechanism itself is fully evidenced in code; only the rate/eventual severity (production request volume, key uniqueness, process restart cadence) is workload/environment-dependent.
- **mechanism class:** cumulative resource retention.
- **aging relevance:** static aging mechanism supported (as a hypothesis) — satisfies all foble trigger (routine API calls), persistent accumulation (map/sets never shrink),insufficient bounding (none present), plausible degradation under long-running execution (monotonic heap growth toward OOM). Requires runtime/profiling confirmation of actual growth rate.
- **final severity:** med
- **final confidence:** high

---
## Finding C — Synchronous RwLock contention across async handlers (merged: CR-3 + RE-1)

- **static validity:** qualified
- **direct code evidence:** std::sync::RwLock (not tokio::sync::RwLock) is acquired synchronously inside async fn associate_card (line 69, exclusive) and async fn retrieve_cards (line 90, shared) — this is a verifiable code fact (blocking primitive used in an async context). A single global lockth handlers (line 34); no sharding or per-key locking exists.
- **affected resource:** AppState.storage, contended across all requests sharing the same Arc<AppState>.
- **triggering condition:** concurrent overlap between an associate_card writer and any othe
- **existing cleanup/bounding:** none — no spawn_blocking, tokio::sync::RwLock, or explicit early drop(map).
- **evidence vs. assumption:** the use of a blocking std::sync::RwLock inside async handlerss specific mechanism — that this stalls an actix-web worker's entire task executor,blocking unrelated concurrent requests on the same OS thread — depends on actix-web's internal worker/runtime threading model (version- and configuration-dependent), which cannot be confirmed from this source file alone; RE-1 itself flags this as an open assumption.
- **mechanism class:** transient/repeated overhead per contention event, standalone. Becomes progressively worse only in combination with Finding B: as stored per-phone HashSets grow unboundedly, the read lock's hold duration in retrieve_cards (which clones/scans sets while holding the guard) lengthe, extending the contention window.
- **aging relevance:** non-aging performance fault standalone (a fixed-cost concurrency behavior, not accumulating on its own); conditionally plausible aging mechanism only as a compounding effect of Finding B's growth.
- **final severity:** low (reconciling CR-3's "low" and RE-1's "med" — the underlying framework-blocking claim is unconfirmed and the lock sections are short under current data volumes)
- **final confidence:** low-med (mechanism direction is plausible but magnitude and worker-bependent assumptions, not verifiable from this file)

---
## Finding D — O(k·n) per-request intersection cost, no input-size bound (merged: CR-4 + RE-4)

- **static validity:** confirmed
- **direct code evidence:** result_set = cards.clone(); (line 99) clones the first phone's etain(|card| cards.contains(card)); (line 102) scans per subsequent phone.req.phone_numbers: Vec<String> (line 16) has no length cap in code — only an empty-list check (line 84). The read lock (line 90) spans this entire loop.
- **affected resource:** transient CPU/heap allocations per request, and read-lock hold dura
- **triggering condition:** requests with multiple phone_numbers and/or phones mapping to large card sets — a routine, repeatable workload pattern (not exceptional), scaling with legitimate or adversarial input size.
- **existing cleanup/bounding:** none beyond the empty-list check; no cap on list length or set size; only a possible (unconfirmed, not visible in this file/Cargo.toml) implicit actix-web default JSON payload-size limit, since no web::JsonConfig override exists.
- **evidence vs. assumption:** the algorithmic cost structure and absence of caps are direct code facts. Real-world impact depends on actual traffic's phone_numbers.len() distribution and per-phone set sizes (workload-dependent, unconfirmed).
- **mechanism class:** transient/repeated overhead — cost is paid fresh each request and does not itself accumulate state. However, per-request cost trends upward over the server's lifetime if Finding B's set-size growth is realized (larger n per phone over time), which both original findings noted as a compounding relationship.
- **aging relevance:** non-aging performance fault standalone; conditionally plausible aging mechanism only via the Finding B linkage (progressively increasing per-request latency as underlying data grows, not from this code path alone).
- **final severity:** low
- **final confidence:** med

---
## Finding E — Unconfigured HttpServer defaults (standalone: RE-5)

- **static validity:** qualified (mostly an absence-of-evidence observation, not a demonstrated fault)
- **direct code evidence:** HttpServer::new(...) (lines 133–138) .bind("0.0.0.0:3000")? (lin0–141) — confirmed: no .workers(), .client_request_timeout(),.client_disconnect_timeout(), .max_connections(), or .keep_alive() calls anywhere in the file.
- **affected resource:** OS sockets/connection slots managed by actix-web's HttpServer, if d
- **triggering condition:** slow/idle/adversarial client connections or connection bursts — entirely dependent on actual actix-web version defaults, none of which are visible or verifiable from this source file.
- **existing cleanup/bounding:** none explicit; relies entirely on framework defaults, whichtatic code alone.
- **evidence vs. assumption:** the absence of explicit configuration is a direct code fact; any resulting performance consequence is entirely a framework-default and workload assumption, not something this file provides evidence for either way.
- **mechanism class:** speculative finite-resource exhaustion (connection table/FDs) — unsupported by direct evidence in this file.
- **aging relevance:** unsupported / at most conditionally plausible pending confirmation ofues and load-test observation; this finding is the weakest of the set and largelynon-actionable from static review.
- **final severity:** low
- **final confidence:** low (matches RE-5's own self-assessed low confidence)

---
Consolidated Priority Ranking (performance/aging relevance)

1. Finding B (unbounded map/set growth) — strongest aging-mechanism candidate; direct eving criteria as a hypothesis.
2. Finding C and Finding D — real but standalone-transient; become aging-relevant only in combination with Finding B's growth (a compounding relationship both original handoffs correctly flagged).
3. Finding A — real code pattern but does not meet aging-mechanism criteria (binary trigbility unconfirmed.
4. Finding E — weakest; purely absence-of-configuration observation, no demonstrable code-level fault.

---
SELF-SOURCED — UNVALIDATED

1. Read-guard hold duration in retrieve_cards extends beyond the loop. Both CR-3 and RE-0) is held only "across the loop" (lines 94–112). On direct verification, there is noexplicit drop(map) in the source; the RwLockReadGuard bound to map (line 90) remains alive until the enclosing function scope ends (the sort() call at line 116 and the HttpResponse::Ok().json(...) construction at lines 118–120 execute before the guard is dropped on the success path). This slightly extends the actual read-lock exposure window described in Findings C/D beyond what either reviewer stated, meaning the contention window under concurrent write load is marginally longer than reported. This is a refinement of an existing finding rather than a wholly new mechanism, flagged here since it was not stated by either reviewer and was noticed only while verifying their specific line-r

---
UNSAFE BLOCKS — TRIAGE

None found.

---
2. Appendix — Raw Phase 1 Handoffs (unedited)

Handoff 1: code-reviewer (CR-1..CR-4)

### CR-1
- **ID/file/lines:** CR-1, coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs, lines 69 and 90
- **fault and evidence:** data.storage.write().unwrap() (line 69) and data.storage.read().un() directly on the Result<Guard, PoisonError> returned by RwLock::write()/read(), with nopoisoning-recovery logic (no unwrap_or_else, into_inner(), or clear_poison()) anywhere in the file.
- **relevant execution path:** any request to /associate_card or /retrieve_cards that acquir...>>.
- **affected state or resource:** AppState.storage (the single shared RwLock, lines 31-34), and by extension every future request handler for both endpoints.
- **triggering conditions:** a panic occurring while any thread holds the write or read guare inside entry/or_insert_with/insert at lines 72-74, or any future code change introducing a panicking call inside the critical section) poisons the lock for the remainder of the process lifetime.
- **existing cleanup/lifecycle/bounding logic:** none; there is no poison-clearing path, ands app_state.storage once constructed (lines 126-141).
- **plausible runtime consequence:** once poisoned, every subsequent .unwrap() on the lock panics, so both endpoints return 500 (or crash the worker task) for the remainder of the process's life — a permanent full-service outage requiring a process restart, triggered by a single unlucky panic.
- **severity:** med; confidence: med
- **assumptions needing validation:** whether actix-web's per-request panic isolation preveny yes) but does not un-poison the lock; whether allocation failure or other panics are realistically reachable in this environment.

### CR-2
- **ID/file/lines:** CR-2, coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs, line
- **fault and evidence:** storage: RwLock<HashMap<String, HashSet<String>>> (lines 31-34) is populated by map.entry(phone).or_insert_with(HashSet::new).insert(card); (lines 72-74) with no eviction, expiration, maximum-key-count, or maximum-set-size logic anywhere in the codebase.
- **relevant execution path:** every successful call to /associate_card.
- **affected state or resource:** process heap memory backing the global HashMap/HashSet str of the server process.
- **triggering conditions:** sustained or repeated calls to /associate_card with distinct phone numbers and/or card numbers over the server's uptime.
- **existing cleanup/lifecycle/bounding logic:** none present; the map is created once in maed, capped, or pruned.
- **plausible runtime consequence:** monotonic, unbounded growth of resident memory over the process lifetime, eventually leading to memory pressure/OOM under long-running or high-volume usage.
- **severity:** med; confidence: high
- **assumptions needing validation:** actual request volume/uniqueness in production and whether the process is periodically restarted, which would bound real-world impact.

### CR-3
- **ID/file/lines:** CR-3, coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs, line
- **fault and evidence:** a single global RwLock (line 34) guards the entire HashMap for both handlers; associate_card takes an exclusive write() lock (line 69) over the whole map merely to mutate one key's HashSet, and retrieve_cards takes a read() lock (line 90) that is held across the full iines 94-112).
- **relevant execution path:** concurrent requests to /associate_card and /retrieve_cards under load.
- **affected state or resource:** AppState.storage, contended by every request-handling taskads.
- **triggering conditions:** any overlap between an associate_card write and concurrent reads/writes (all readers block during the write; the write blocks until all current readers finish) — more likely as concurrent request rate increases.
- **existing cleanup/lifecycle/bounding logic:** none; there is no sharding, no per-key locking, and no bound on how long the read lock in retrieve_cards is held (it spans the entire clone/retain loop, lines 94-112, before being dropped).
- **plausible runtime consequence:** writer/reader contention serializes otherwise-independent requests, degrading throughput and increasing tail latency as concurrency and map size grow, since even unrelated phone-number keys serialize behind the single lock.
- **severity:** low; confidence: med
- **assumptions needing validation:** actual concurrent request rate and lock hold duration r contention is measurable versus purely theoretical at expected scale.

### CR-4
- **ID/file/lines:** CR-4, coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs, lines 91-116
- **fault and evidence:** retrieve_cards computes the intersection from scratch on every cal; (line 99) fully clones the first phone's card set, then result_set.retain(|card|cards.contains(card)); (line 102) performs an O(current result size) scan per additional phone, with no caching/memoization of repeated queries and no upper bound on req.phone_numbers.len() before the loop begins (only an empty-list check at line 84).
- **relevant execution path:** every call to /retrieve_cards, scaling with phone_numbers.len() and the size of each associated HashSet<String>.
- **affected state or resource:** CPU/heap allocations transiently created per request (clonat line 115).
- **triggering conditions:** requests supplying many phone numbers and/or phone numbers associated with large card sets.
- **existing cleanup/lifecycle/bounding logic:** none beyond the empty-list check (line 84);et sizes is enforced before the clone/retain work is performed.
- **plausible runtime consequence:** CPU and transient-allocation cost grows with input size on every request with no caching, causing degraded latency/throughput for large inputs; combined with CR-2's unbounded set growth, per-request cost can increase over the life of the service.
- **severity:** low; confidence: med
- **assumptions needing validation:** realistic distribution of phone_numbers.len() and per-ction traffic.

UNSAFE BLOCKS — TRIAGE None found.

Handoff 2: rust-engineer (RE-1..RE-5)

### RE-1
- **ID:** RE-1
- **file:** coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs
- **lines:** 69, 90 (also declaration at line 34)
- **fault and direct code evidence:** std::sync::RwLock (line 4, use std::sync::RwLock;; field at line 34 storage: RwLock<HashMap<String, HashSet<String>>>) is locked synchronously inside async fn handlers via data.storage.write().unwrap() (line 69) and data.storage.read().unwrap() (line 90). No .is held, but the acquisition itself is a blocking OS-level primitive.
- **relevant execution path:** any concurrent invocation of associate_card (writer) contending with other associate_card writers or retrieve_cards readers on the same actix worker thread.
- **affected state or resource:** AppState.storage and the actix worker's per-thread task ex
- **triggering conditions:** concurrent requests hitting the same worker thread while a writer holds the lock; actix-web workers by default each run their own single-threaded task executor, so a thread blocked waiting on RwLock::write()/read() cannot progress any other async task scheduled on thats acquired.
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: none — no spawn_blocking, tokio::sync::RwLock, or block_in_place wrapper is used; the lock section itself is short (map mutation only), which reduces but does not eliminate the exposure since acquisition can rite contention.
- **plausible runtime consequence:** worker-thread stalls / latency spikes for unrelated concurrent requests during write contention; degraded throughput under concurrent associate_card load.
- **severity:** med
- **confidence:** med
- **assumptions that would need runtime/profiling validation:** actual actix-web worker threersion (single-threaded-per-worker vs. multi-threaded runtime configuration), measuredlock hold/wait times under load, and worker count relative to CPU cores.

### RE-2
- **ID:** RE-2
- **file:** coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs
- **lines:** 69, 90
- **fault and direct code evidence:** let mut map = data.storage.write().unwrap(); (line 69) and let map = data.storage.read().unwrap(); (line 90) unconditionally .unwrap() the LockResult, with no poison recovery (no unwrap_or_else, no clear_poison).
- **relevant execution path:** any panic occurring while the write guard is held between lines 69–75 (e.g., allocation failure in or_insert_with/insert) poisons the RwLock; every subsequent call to either handler across the process then panics at its own .unwrap().
- **affected state or resource:** the single shared AppState.storage RwLock, wrapped in web::Data (Arc) and shared by every worker/thread via app_data(app_state.clone()) at line 135.
- **triggering conditions:** a single panic anywhere inside the critical sections of either d.
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: none present; because the same Arc<AppState> instance is shared across all workers (line 127/135), poisoning is global and permanent for the life of the process — there is no per-request isolation or recovery pa
- **plausible runtime consequence:** total, permanent loss of service for both endpoints (every future request panics/500s) until process restart, triggered by a single panic anywhere under the lock.
- **severity:** high
- **confidence:** med
- **assumptions that would need runtime/profiling validation:** whether any code path insidetually panic in practice (currently only infallible HashMap/HashSet operations arepresent, so likelihood is low but not proven impossible, e.g. under allocator OOM).

### RE-3
- **ID:** RE-3
- **file:** coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs
- **lines:** 34, 69-74
- **fault and direct code evidence:** storage: RwLock<HashMap<String, HashSet<String>>> (line 34) is only ever inserted into — map.entry(phone).or_insert_with(HashSet::new).insert(card); (lines 72-74) — with no eviction, expiry, or capacity bound anywhere in the file.
- **relevant execution path:** every successful POST /associate_card call.
- **affected state or resource:** process heap memory backing AppState.storage.
- **triggering conditions:** sustained or high-volume traffic to /associate_card with varying phone/card values over the process lifetime.
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: none etonically for the life of the server process.
- **plausible runtime consequence:** unbounded memory growth leading to increased GC/allocator pressure and eventual OOM under long-running, high-throughput deployments.
- **severity:** med
- **confidence:** high
- **assumptions that would need runtime/profiling validation:** actual request volume/uniquen production traffic and observed RSS growth over time.

### RE-4
- **ID:** RE-4
- **file:** coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs
- **lines:** 94-112
- **fault and direct code evidence:** the intersection loop clones the first phone's entire clone();, line 99) and then performs result_set.retain(|card| cards.contains(card));(line 102) for each subsequent phone, with req.phone_numbers (line 16, Vec<String>) unbounded in length and no limit on request payload size enforced in code.
- **relevant execution path:** every POST /retrieve_cards call with phone_numbers containing entries mapping to large card sets.
- **affected state or resource:** CPU time and transient heap allocations per request (result_set clone plus repeated retain scans against data.storage read guard held for the whole loop, line 90).
- **triggering conditions:** large phone_numbers arrays and/or phone numbers associated withd lock (line 90) is held for the entire loop duration (lines 94-112), extending exposuretime under RE-1's contention concern.
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: no expn() or per-phone card-set size in the handler; the only bound is actix-web's default JSONpayload size limit, which is not visible in this file/Cargo.toml (no web::JsonConfig override present).
- **plausible runtime consequence:** O(k·n) CPU/allocation cost per request (k = number of ple holding the shared read lock, degrading throughput and increasing read-lock hold timeunder adversarial or large legitimate inputs.
- **severity:** low
- **confidence:** med
- **assumptions that would need runtime/profiling validation:** default actix-web JSON payloect for this app (no explicit JsonConfig found in main.rs) and real-world distribution ofphone_numbers list sizes / card-set sizes.

### RE-5
- **ID:** RE-5
- **file:** coding-task-shared/rust/Credit_Card/Credit_Card/src/main.rs
- **lines:** 125-142
- **fault and direct code evidence:** HttpServer::new(...) (lines 133-138) .bind("0.0.0.0:3000")? (line 139) .run().await (lines 140-141) is constructed with no calls to .workers(...), .client_request_timeout(...), .client_disconnect_timeout(...), .max_connections(...), orlts are left implicit.
- **relevant execution path:** server startup and the entire connection-accept lifecycle for the process.
- **affected state or resource:** OS sockets/file descriptors and per-connection worker resob HttpServer.
- **triggering conditions:** any client behavior relying on default timeout/connection-limit values (e.g., slow or idle clients, or connection bursts exceeding the implicit default backlog/limits).
- existing cleanup, lifecycle, or bounding logic, and why it is/isn't sufficient: reliest-in defaults; the source shows no explicit bounding/timeout configuration to verify orreason about, so connection-lifecycle behavior under load cannot be confirmed from this code.
- **plausible runtime consequence:** potential accumulation of slow/idle connections consumiources beyond what an explicitly tuned deployment would allow, under sustained oradversarial client load.
- **severity:** low
- **confidence:** low
- **assumptions that would need runtime/profiling validation:** actual actix-web version   default values for timeouts/max connections/workers and observed connection-table/file-descriptor behavior under loadtesting.

UNSAFE BLOCKS — TRIAGE None found.