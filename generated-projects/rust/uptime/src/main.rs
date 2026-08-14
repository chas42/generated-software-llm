use actix_web::{error, web, App, HttpResponse, HttpServer, Responder};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

// -----------------------------------------------------------------------------
// Domain Models & State
// -----------------------------------------------------------------------------

// In-memory store: Token -> ServiceID -> LastNotification(ISO8601 String)
type Db = Mutex<HashMap<String, HashMap<String, String>>>;

struct AppState {
    db: Db,
}

#[derive(Deserialize)]
struct HeartbeatRequest {
    serviceId: String,
    token: String,
}

#[derive(Deserialize)]
struct ServicesRequest {
    token: String,
}

#[derive(Serialize)]
struct ServiceResponse {
    serviceId: String,
    lastNotification: String,
}

// -----------------------------------------------------------------------------
// Helper Functions
// -----------------------------------------------------------------------------

/// Generates an ISO 8601 UTC timestamp string (e.g., "2023-10-05T14:30:00Z")
/// Uses pure std::time calculation to avoid external `chrono` dependency.
fn get_iso_time() -> String {
    let now = SystemTime::now();
    let duration = now.duration_since(UNIX_EPOCH).unwrap_or_default();
    let total_seconds = duration.as_secs();

    let seconds_per_day = 86400;
    let z = (total_seconds / seconds_per_day) + 719468;
    let era = (if z >= 0 { z } else { z - 146096 }) / 146097;
    let doe = (z - era * 146097) as u64;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe as i32 + era as i32 * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u8;
    let m = (if mp < 10 { mp + 3 } else { mp - 9 }) as u8;
    let year = y + if m <= 2 { 1 } else { 0 };

    let rem_seconds = total_seconds % seconds_per_day;
    let hour = rem_seconds / 3600;
    let minute = (rem_seconds % 3600) / 60;
    let second = rem_seconds % 60;

    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        year, m, d, hour, minute, second
    )
}

// -----------------------------------------------------------------------------
// Handlers
// -----------------------------------------------------------------------------

async fn heartbeat(
    data: web::Data<AppState>,
    req: web::Json<HeartbeatRequest>,
) -> impl Responder {
    // Validate Input
    if req.serviceId.trim().is_empty() || req.token.trim().is_empty() {
        return HttpResponse::BadRequest().json(json!({
            "description": "Invalid request payload"
        }));
    }

    let timestamp = get_iso_time();
    
    let mut db = match data.db.lock() {
        Ok(guard) => guard,
        Err(_) => {
            return HttpResponse::InternalServerError().json(json!({
                "description": "Internal server error"
            }));
        }
    };

    // Update state safely
    let service_map = db.entry(req.token.clone()).or_insert_with(HashMap::new);
    service_map.insert(req.serviceId.clone(), timestamp);

    HttpResponse::Ok().json(json!({
        "description": "Heartbeat registered successfully."
    }))
}

async fn get_services(
    data: web::Data<AppState>,
    req: web::Json<ServicesRequest>,
) -> impl Responder {
    // Validate Input
    if req.token.trim().is_empty() {
        return HttpResponse::BadRequest().json(json!({
            "description": "Invalid request payload"
        }));
    }

    let db = match data.db.lock() {
        Ok(guard) => guard,
        Err(_) => {
            return HttpResponse::InternalServerError().json(json!({
                "description": "Internal server error"
            }));
        }
    };

    // Retrieve and transform services for the token
    let mut response_list: Vec<ServiceResponse> = Vec::new();
    
    if let Some(service_map) = db.get(&req.token) {
        for (sid, time) in service_map.iter() {
            response_list.push(ServiceResponse {
                serviceId: sid.clone(),
                lastNotification: time.clone(),
            });
        }
    }

    // Sort lexicographically by serviceId
    response_list.sort_by(|a, b| a.serviceId.cmp(&b.serviceId));

    HttpResponse::Ok().json(response_list)
}

// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize thread-safe state
    let state = web::Data::new(AppState {
        db: Mutex::new(HashMap::new()),
    });

    HttpServer::new(move || {
        // Configure JSON error handler to return strictly JSON on malformed requests
        let json_config = web::JsonConfig::default().error_handler(|err, _req| {
            error::InternalError::from_response(
                err,
                HttpResponse::BadRequest().json(json!({
                    "description": "Invalid request payload"
                })),
            )
            .into()
        });

        App::new()
            .app_data(state.clone())
            .app_data(json_config)
            .route("/heartbeat", web::post().to(heartbeat))
            .route("/services", web::post().to(get_services))
    })
    .bind(("0.0.0.0", 3000))?
    .run()
    .await
}