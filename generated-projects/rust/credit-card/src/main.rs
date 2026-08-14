use actix_web::{post, web, App, HttpResponse, HttpServer, Responder};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::sync::RwLock;

// --- Estruturas de Dados (Models) ---

#[derive(Deserialize)]
struct AssociateRequest {
    credit_card: String,
    phone: String,
}

#[derive(Deserialize)]
struct RetrieveRequest {
    phone_numbers: Vec<String>,
}

#[derive(Serialize)]
struct CardsResponse {
    card_numbers: Vec<String>,
}

#[derive(Serialize)]
struct ErrorResponse {
    error: String,
}

// --- Estado Global (In-Memory Storage) ---

struct AppState {
    /// Mapeia um número de telefone para um conjunto de números de cartão.
    /// RwLock permite múltiplas leituras simultâneas ou uma escrita exclusiva.
    storage: RwLock<HashMap<String, HashSet<String>>>,
}

// --- Validações ---

fn is_valid_card(card: &str) -> bool {
    let card = card.trim();
    !card.is_empty() && 
    card.len() >= 13 && 
    card.len() <= 19 && 
    card.chars().all(|c| c.is_ascii_digit())
}

// --- Handlers ---

#[post("/associate_card")]
async fn associate_card(
    data: web::Data<AppState>,
    req: web::Json<AssociateRequest>,
) -> impl Responder {
    let card = req.credit_card.trim().to_string();
    let phone = req.phone.trim().to_string();

    if !is_valid_card(&card) {
        return HttpResponse::BadRequest().json(ErrorResponse {
            error: "Formato de cartão de crédito inválido".to_string(),
        });
    }

    if phone.is_empty() {
        return HttpResponse::BadRequest().json(ErrorResponse {
            error: "O número de telefone não pode ser vazio".to_string(),
        });
    }

    let mut map = data.storage.write().unwrap();
    
    // Insere a associação. O HashSet garante que duplicatas não sejam criadas.
    map.entry(phone)
        .or_insert_with(HashSet::new)
        .insert(card);

    HttpResponse::Ok().finish()
}

#[post("/retrieve_cards")]
async fn retrieve_cards(
    data: web::Data<AppState>,
    req: web::Json<RetrieveRequest>,
) -> impl Responder {
    if req.phone_numbers.is_empty() {
        return HttpResponse::BadRequest().json(ErrorResponse {
            error: "A lista de números de telefone não pode estar vazia".to_string(),
        });
    }

    let map = data.storage.read().unwrap();
    let mut result_set: HashSet<String> = HashSet::new();
    
    // Regra: Se QUALQUER número não tiver associação, retornar lista vazia.
    for (i, phone) in req.phone_numbers.iter().enumerate() {
        match map.get(phone) {
            Some(cards) => {
                if i == 0 {
                    // Primeiro telefone define o conjunto inicial
                    result_set = cards.clone();
                } else {
                    // Interseção: O cartão deve estar associado a TODOS os telefones enviados
                    result_set.retain(|card| cards.contains(card));
                }
            }
            None => {
                // Um dos números não possui cartões, logo a condição falha para todos.
                return HttpResponse::Ok().json(CardsResponse {
                    card_numbers: Vec::new(),
                });
            }
        }
    }

    // Converter para vetor e ordenar lexicograficamente
    let mut sorted_cards: Vec<String> = result_set.into_iter().collect();
    sorted_cards.sort();

    HttpResponse::Ok().json(CardsResponse {
        card_numbers: sorted_cards,
    })
}

// --- Inicialização do Servidor ---

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let app_state = web::Data::new(AppState {
        storage: RwLock::new(HashMap::new()),
    });

    println!("Servidor rodando em http://0.0.0.0:3000");

    HttpServer::new(move || {
        App::new()
            .app_data(app_state.clone())
            .service(associate_card)
            .service(retrieve_cards)
    })
    .bind("0.0.0.0:3000")?
    .run()
    .await
}