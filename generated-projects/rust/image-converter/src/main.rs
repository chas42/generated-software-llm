use actix_multipart::Multipart;
use actix_web::{middleware, post, web, App, HttpResponse, HttpServer, Result};
use futures_util::TryStreamExt;
use serde::Serialize;
use std::env;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use uuid::Uuid;

#[derive(Serialize)]
struct ErrorResponse {
    error: String,
}

fn create_error(status: actix_web::http::StatusCode, message: &str) -> HttpResponse {
    HttpResponse::build(status).json(ErrorResponse {
        error: message.to_string(),
    })
}

#[post("/create-gif")]
async fn create_gif(mut payload: Multipart) -> Result<HttpResponse> {
    let request_id = Uuid::new_v4();
    let temp_dir = env::temp_dir().join(format!("gif-api-{}", request_id));

    if let Err(e) = fs::create_dir(&temp_dir) {
        return Ok(create_error(
            actix_web::http::StatusCode::INTERNAL_SERVER_ERROR,
            &format!("Failed to create temp directory: {}", e),
        ));
    }

    let mut image_paths: Vec<PathBuf> = Vec::new();
    let mut target_size: Option<String> = None;
    let mut delay_val: u64 = 10; // Renomeado de delay_ms para delay_val para clareza
    let mut append_reverted: bool = false;

    while let Ok(Some(mut field)) = payload.try_next().await {
        let content_disposition = field.content_disposition();
        
        let field_name = content_disposition.get_name().unwrap_or("").to_string();
        let filename = content_disposition.get_filename().unwrap_or("unknown").to_string();

        if field_name == "images" {
            let ext = Path::new(&filename)
                .extension()
                .and_then(|s| s.to_str())
                .unwrap_or("bin");
            
            let save_filename = format!("{}.{}", Uuid::new_v4(), ext);
            let file_path = temp_dir.join(&save_filename);
            
            let f = std::fs::File::create(&file_path);
            match f {
                Ok(mut file) => {
                    while let Ok(Some(chunk)) = field.try_next().await {
                        if let Err(_) = file.write_all(&chunk) {
                            let _ = fs::remove_dir_all(&temp_dir);
                            return Ok(create_error(
                                actix_web::http::StatusCode::INTERNAL_SERVER_ERROR,
                                "Failed to write image data",
                            ));
                        }
                    }
                    image_paths.push(file_path);
                }
                Err(_) => {
                    let _ = fs::remove_dir_all(&temp_dir);
                    return Ok(create_error(
                        actix_web::http::StatusCode::INTERNAL_SERVER_ERROR,
                        "Failed to create temp file",
                    ));
                }
            }
        } else {
            let mut value_bytes = Vec::new();
            while let Ok(Some(chunk)) = field.try_next().await {
                value_bytes.extend_from_slice(&chunk);
            }
            let value_str = String::from_utf8(value_bytes).unwrap_or_default();

            match field_name.as_str() {
                "targetSize" => target_size = Some(value_str),
                "delay" => {
                    if let Ok(d) = value_str.parse::<u64>() {
                        delay_val = d;
                    }
                }
                "appendReverted" => {
                    if let Ok(b) = value_str.parse::<bool>() {
                        append_reverted = b;
                    }
                }
                _ => {}
            }
        }
    }

    if image_paths.is_empty() {
        let _ = fs::remove_dir_all(&temp_dir);
        return Ok(create_error(
            actix_web::http::StatusCode::BAD_REQUEST,
            "No images provided",
        ));
    }

    let size_str = match target_size {
        Some(s) => s,
        None => {
            let _ = fs::remove_dir_all(&temp_dir);
            return Ok(create_error(
                actix_web::http::StatusCode::BAD_REQUEST,
                "Missing required field: targetSize",
            ));
        }
    };


    let delay_ticks = delay_val; 

    let output_gif_path = temp_dir.join("output.gif");

    let mut args: Vec<String> = Vec::new();
    args.push("-delay".to_string());
    args.push(delay_ticks.to_string());
    args.push("-loop".to_string());
    args.push("0".to_string());

    for path in &image_paths {
        args.push(path.to_string_lossy().to_string());
    }

    if append_reverted {
        for path in image_paths.iter().rev() {
            args.push(path.to_string_lossy().to_string());
        }
    }

    args.push("-resize".to_string());
    args.push(size_str);
    args.push(output_gif_path.to_string_lossy().to_string());

    let command_result = web::block(move || {
        Command::new("convert")
            .args(&args)
            .output()
    }).await;

    match command_result {
        Ok(Ok(output)) => {
            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr);
                let _ = fs::remove_dir_all(&temp_dir);
                return Ok(create_error(
                    actix_web::http::StatusCode::BAD_REQUEST,
                    &format!("Image processing failed: {}", stderr),
                ));
            }
        }
        _ => {
            let _ = fs::remove_dir_all(&temp_dir);
            return Ok(create_error(
                actix_web::http::StatusCode::INTERNAL_SERVER_ERROR,
                "Failed to execute image processor",
            ));
        }
    }

    let gif_content = match fs::read(&output_gif_path) {
        Ok(data) => data,
        Err(_) => {
            let _ = fs::remove_dir_all(&temp_dir);
            return Ok(create_error(
                actix_web::http::StatusCode::INTERNAL_SERVER_ERROR,
                "Failed to read generated GIF",
            ));
        }
    };

    let _ = fs::remove_dir_all(&temp_dir);

    Ok(HttpResponse::Ok()
        .content_type("image/gif")
        .body(gif_content))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenvy::dotenv().ok();
    println!("Starting server at http://localhost:3000");

    HttpServer::new(|| {
        App::new()
            .wrap(middleware::Logger::default())
            .service(create_gif)
    })
    .bind(("0.0.0.0", 3000))?
    .run()
    .await
}