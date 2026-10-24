//! Spintax expansion matching the Python `SpintaxProcessor` semantics
//! (`{a|b|c}` patterns, pipe-split with nested-brace awareness, leftmost
//! non-nested `{...}` discovery). Designed for bulk parallel expansion.

use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use rayon::prelude::*;

/// Expand a single spintax template once.
pub fn process(text: &str, seed: Option<u64>) -> (String, usize) {
    if text.is_empty() {
        return (String::new(), 0);
    }

    let patterns = find_spintax_patterns(text);
    if patterns.is_empty() {
        return (text.to_string(), 1);
    }

    let mut rng = match seed {
        Some(s) => StdRng::seed_from_u64(s),
        None => StdRng::from_entropy(),
    };

    let mut result = text.to_string();
    let mut total_variants: usize = 1;

    for pattern in &patterns {
        let variants = extract_variants(pattern);
        if variants.is_empty() {
            continue;
        }
        let idx = rng.gen_range(0..variants.len());
        let selected = variants[idx];
        if let Some(pos) = result.find(pattern) {
            result.replace_range(pos..pos + pattern.len(), selected);
        }
        total_variants = total_variants.saturating_mul(variants.len());
    }

    (result, total_variants)
}

/// Expand the same template `count` times in parallel.
/// When `seed` is set, expansion `i` uses `seed.wrapping_add(i as u64)` so
/// results are reproducible and independent across threads.
pub fn expand_batch(text: &str, count: usize, seed: Option<u64>) -> Vec<String> {
    if count == 0 {
        return Vec::new();
    }
    (0..count)
        .into_par_iter()
        .map(|i| {
            let item_seed = seed.map(|s| s.wrapping_add(i as u64));
            process(text, item_seed).0
        })
        .collect()
}

fn find_spintax_patterns(text: &str) -> Vec<String> {
    // Match Python: r"\{[^{}]*\}" — non-nested braces only.
    let bytes = text.as_bytes();
    let mut out = Vec::new();
    let mut i = 0usize;
    while i < bytes.len() {
        if bytes[i] == b'{' {
            let start = i;
            i += 1;
            while i < bytes.len() {
                match bytes[i] {
                    b'{' => break, // nested — skip (matches Python non-nested regex)
                    b'}' => {
                        out.push(text[start..=i].to_string());
                        i += 1;
                        break;
                    }
                    _ => i += 1,
                }
            }
        } else {
            i += 1;
        }
    }
    out
}

fn extract_variants(pattern: &str) -> Vec<&str> {
    if pattern.len() < 2 {
        return Vec::new();
    }
    let content = &pattern[1..pattern.len() - 1];
    split_by_pipe(content)
        .into_iter()
        .map(str::trim)
        .collect()
}

fn split_by_pipe(text: &str) -> Vec<&str> {
    let mut variants = Vec::new();
    let mut start = 0usize;
    let mut brace_count = 0i32;
    let chars: Vec<(usize, char)> = text.char_indices().collect();

    for &(idx, ch) in &chars {
        match ch {
            '{' => brace_count += 1,
            '}' => brace_count -= 1,
            '|' if brace_count == 0 => {
                variants.push(&text[start..idx]);
                start = idx + ch.len_utf8();
            }
            _ => {}
        }
    }
    variants.push(&text[start..]);
    variants
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn simple_expand() {
        let (out, variants) = process("Hello {John|Jane|User}", Some(42));
        assert!(out.starts_with("Hello "));
        assert_eq!(variants, 3);
        assert!(["Hello John", "Hello Jane", "Hello User"].contains(&out.as_str()));
    }

    #[test]
    fn batch_seeded_deterministic() {
        let a = expand_batch("Hi {a|b}", 5, Some(7));
        let b = expand_batch("Hi {a|b}", 5, Some(7));
        assert_eq!(a, b);
        assert_eq!(a.len(), 5);
    }
}
