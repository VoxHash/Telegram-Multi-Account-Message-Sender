//! Multi-account send-slot scheduler.
//!
//! Builds a compact wait schedule so the Python campaign loop can sleep exact
//! delays instead of holding large intermediate Python objects or computing
//! jitter/token windows on the GUI-adjacent thread for every recipient.

use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct PaceSlot {
    pub recipient_index: usize,
    pub account_id: i64,
    /// Milliseconds to wait *before* sending this message (0 for the first).
    pub wait_before_ms: u64,
}

#[derive(Debug, Clone)]
pub struct PaceRequest {
    pub recipient_count: usize,
    pub account_ids: Vec<i64>,
    pub messages_per_minute: u32,
    pub messages_per_hour: u32,
    pub jitter_seconds: f64,
    pub max_concurrent_accounts: u32,
    pub seed: Option<u64>,
}

/// Build a round-robin + rate-limited schedule.
///
/// Per-account minimum interval is derived from `messages_per_minute`.
/// Global spacing also respects that rate so the desktop process does not
/// burst when many accounts share one campaign. Optional jitter is applied
/// on top of the base wait (never negative).
pub fn build_schedule(req: &PaceRequest) -> Vec<PaceSlot> {
    if req.recipient_count == 0 {
        return Vec::new();
    }

    let accounts = if req.account_ids.is_empty() {
        vec![0]
    } else {
        req.account_ids.clone()
    };

    let mpm = req.messages_per_minute.max(1) as f64;
    let mph = req.messages_per_hour.max(1) as f64;
    // Most restrictive of per-minute vs per-hour spacing (seconds between global sends).
    let min_global_interval = (60.0 / mpm).max(3600.0 / mph);
    // Cap concurrency by limiting how "tight" account reuse can be.
    let concurrent = req.max_concurrent_accounts.max(1) as f64;
    let per_account_interval = min_global_interval * (accounts.len() as f64).min(concurrent)
        / concurrent.max(1.0);

    let mut rng = match req.seed {
        Some(s) => StdRng::seed_from_u64(s),
        None => StdRng::from_entropy(),
    };

    // Next eligible time (seconds from schedule start) per account and globally.
    let mut next_account: Vec<f64> = vec![0.0; accounts.len()];
    let mut next_global: f64 = 0.0;
    let mut slots = Vec::with_capacity(req.recipient_count);
    let mut prev_send_at: f64 = 0.0;

    for i in 0..req.recipient_count {
        let acct_idx = i % accounts.len();
        let mut send_at = next_global.max(next_account[acct_idx]);

        if req.jitter_seconds > 0.0 {
            let jitter: f64 = rng.gen_range(0.0..=req.jitter_seconds);
            send_at += jitter;
        }

        let wait_before = if i == 0 {
            0.0
        } else {
            (send_at - prev_send_at).max(0.0)
        };

        slots.push(PaceSlot {
            recipient_index: i,
            account_id: accounts[acct_idx],
            wait_before_ms: (wait_before * 1000.0).round() as u64,
        });

        prev_send_at = send_at;
        next_global = send_at + min_global_interval;
        next_account[acct_idx] = send_at + per_account_interval;
    }

    slots
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn first_slot_no_wait() {
        let slots = build_schedule(&PaceRequest {
            recipient_count: 3,
            account_ids: vec![1, 2],
            messages_per_minute: 60,
            messages_per_hour: 1000,
            jitter_seconds: 0.0,
            max_concurrent_accounts: 2,
            seed: Some(1),
        });
        assert_eq!(slots[0].wait_before_ms, 0);
        assert_eq!(slots.len(), 3);
        assert_eq!(slots[0].account_id, 1);
        assert_eq!(slots[1].account_id, 2);
    }
}
