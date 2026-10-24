//! TMMS native accelerator sidecar.
//!
//! Protocol: one JSON object on stdin → one JSON object on stdout.
//!
//! Ops:
//! - `spintax_process`  — single expansion
//! - `spintax_expand`   — parallel batch expansion (rayon)
//! - `pace_schedule`    — multi-account send-slot schedule
//! - `ping`             — health / version check

mod pacing;
mod spintax;

use pacing::{build_schedule, PaceRequest};
use serde::{Deserialize, Serialize};
use std::io::{self, Read};

const VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Debug, Deserialize)]
struct Request {
    op: String,
    #[serde(default)]
    text: Option<String>,
    #[serde(default)]
    count: Option<usize>,
    #[serde(default)]
    seed: Option<u64>,
    #[serde(default)]
    recipient_count: Option<usize>,
    #[serde(default)]
    account_ids: Option<Vec<i64>>,
    #[serde(default)]
    messages_per_minute: Option<u32>,
    #[serde(default)]
    messages_per_hour: Option<u32>,
    #[serde(default)]
    jitter_seconds: Option<f64>,
    #[serde(default)]
    max_concurrent_accounts: Option<u32>,
}

#[derive(Debug, Serialize)]
struct Response {
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    backend: Option<&'static str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    version: Option<&'static str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    text: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    variants_count: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    texts: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    slots: Option<Vec<pacing::PaceSlot>>,
}

fn main() {
    let mut input = String::new();
    if let Err(e) = io::stdin().read_to_string(&mut input) {
        emit_err(&format!("failed to read stdin: {e}"));
        std::process::exit(1);
    }

    let trimmed = input.trim();
    if trimmed.is_empty() {
        emit_err("empty request");
        std::process::exit(1);
    }

    let req: Request = match serde_json::from_str(trimmed) {
        Ok(r) => r,
        Err(e) => {
            emit_err(&format!("invalid JSON: {e}"));
            std::process::exit(1);
        }
    };

    let resp = match req.op.as_str() {
        "ping" => Response {
            ok: true,
            error: None,
            backend: Some("rust"),
            version: Some(VERSION),
            text: None,
            variants_count: None,
            texts: None,
            slots: None,
        },
        "spintax_process" => {
            let text = req.text.unwrap_or_default();
            let (out, variants) = spintax::process(&text, req.seed);
            Response {
                ok: true,
                error: None,
                backend: Some("rust"),
                version: Some(VERSION),
                text: Some(out),
                variants_count: Some(variants),
                texts: None,
                slots: None,
            }
        }
        "spintax_expand" => {
            let text = req.text.unwrap_or_default();
            let count = req.count.unwrap_or(1).min(500_000);
            let texts = spintax::expand_batch(&text, count, req.seed);
            Response {
                ok: true,
                error: None,
                backend: Some("rust"),
                version: Some(VERSION),
                text: None,
                variants_count: None,
                texts: Some(texts),
                slots: None,
            }
        }
        "pace_schedule" => {
            let pace = PaceRequest {
                recipient_count: req.recipient_count.unwrap_or(0).min(2_000_000),
                account_ids: req.account_ids.unwrap_or_default(),
                messages_per_minute: req.messages_per_minute.unwrap_or(1),
                messages_per_hour: req.messages_per_hour.unwrap_or(60),
                jitter_seconds: req.jitter_seconds.unwrap_or(0.0).max(0.0),
                max_concurrent_accounts: req.max_concurrent_accounts.unwrap_or(1),
                seed: req.seed,
            };
            let slots = build_schedule(&pace);
            Response {
                ok: true,
                error: None,
                backend: Some("rust"),
                version: Some(VERSION),
                text: None,
                variants_count: None,
                texts: None,
                slots: Some(slots),
            }
        }
        other => Response {
            ok: false,
            error: Some(format!("unknown op: {other}")),
            backend: Some("rust"),
            version: Some(VERSION),
            text: None,
            variants_count: None,
            texts: None,
            slots: None,
        },
    };

    match serde_json::to_string(&resp) {
        Ok(s) => {
            println!("{s}");
            if !resp.ok {
                std::process::exit(1);
            }
        }
        Err(e) => {
            emit_err(&format!("serialize failed: {e}"));
            std::process::exit(1);
        }
    }
}

fn emit_err(msg: &str) {
    let resp = Response {
        ok: false,
        error: Some(msg.to_string()),
        backend: Some("rust"),
        version: Some(VERSION),
        text: None,
        variants_count: None,
        texts: None,
        slots: None,
    };
    if let Ok(s) = serde_json::to_string(&resp) {
        eprintln!("{s}");
        println!("{s}");
    }
}
