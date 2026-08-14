use actix_web::{error, post, web, App, HttpResponse, HttpServer, Responder};
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::process::Command;

// Estrutura de entrada (Request Body)
#[derive(Deserialize)]
struct CommandRequest {
    filter_flags: Option<String>,
    command_regex: String,
}

// Estrutura do item de processo na resposta
#[derive(Serialize)]
struct ProcessItem {
    processId: i32,
    processString: String,
}

// Estrutura de erro padrão
#[derive(Serialize)]
struct ErrorResponse {
    code: u16,
    message: String,
}

#[post("/monitor/commands")]
async fn execute_command(
    req: web::Json<CommandRequest>,
) -> actix_web::Result<impl Responder> {
    // Validação: Regex não pode ser vazio
    if req.command_regex.is_empty() {
        return Ok(HttpResponse::BadRequest().json(ErrorResponse {
            code: 400,
            message: "Invalid request".to_string(),
        }));
    }

    // Compilar a Regex
    let re = match Regex::new(&req.command_regex) {
        Ok(r) => r,
        Err(_) => {
            return Ok(HttpResponse::BadRequest().json(ErrorResponse {
                code: 400,
                message: "Invalid request".to_string(),
            }));
        }
    };

    // Construção segura do comando "ps"
    let mut cmd = Command::new("ps");

    // Adicionar flags se existirem (split_whitespace previne injeção simples de argumentos)
    if let Some(flags) = &req.filter_flags {
        cmd.args(flags.split_whitespace());
    }

    // Executar o comando
    let output = match cmd.output() {
        Ok(o) => o,
        Err(_) => {
            // Se o ps falhar na execução, retorna lista vazia (segurança/determinismo)
            return Ok(HttpResponse::Ok().json(Vec::<ProcessItem>::new()));
        }
    };

    let stdout = String::from_utf8_lossy(&output.stdout);
    let mut processes = Vec::new();
    let mut seen_pids = HashSet::new();

    // Processar saída linha por linha
    for line in stdout.lines() {
        if re.is_match(line) {
            // Tenta extrair o PID. O PID geralmente é o 1º ou 2º token dependendo das flags do ps.
            let tokens: Vec<&str> = line.split_whitespace().collect();
            let mut pid: Option<i32> = None;

            // Checa o primeiro token
            if let Some(first) = tokens.get(0) {
                if let Ok(p) = first.parse::<i32>() {
                    pid = Some(p);
                }
            }

            // Se não achou, checa o segundo (caso comum com USER PID ...)
            if pid.is_none() {
                if let Some(second) = tokens.get(1) {
                    if let Ok(p) = second.parse::<i32>() {
                        pid = Some(p);
                    }
                }
            }

            // Se encontrou um PID válido e não é duplicado, adiciona à lista
            if let Some(p) = pid {
                if !seen_pids.contains(&p) {
                    seen_pids.insert(p);
                    processes.push(ProcessItem {
                        processId: p,
                        processString: line.to_string(),
                    });
                }
            }
        }
    }

    Ok(HttpResponse::Ok().json(processes))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        // Configuração para rejeitar JSON malformado com a mensagem de erro específica exigida
        let json_config = web::JsonConfig::default()
            .limit(4096)
            .error_handler(|err, _req| {
                let response = ErrorResponse {
                    code: 400,
                    message: "Invalid request".to_string(),
                };
                error::InternalError::from_response(
                    err,
                    HttpResponse::BadRequest().json(response),
                )
                .into()
            });

        App::new()
            .app_data(json_config)
            .service(execute_command)
    })
    .bind(("0.0.0.0", 3000))?
    .run()
    .await
}