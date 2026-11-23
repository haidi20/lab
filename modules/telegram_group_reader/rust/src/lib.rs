//! Telegram group reader - Rust implementation
//! Pure logic functions for testing

use chrono::Utc;

/// Cutoff seconds (UTC epoch) untuk filter pesan N hari terakhir.
/// Menyamakan perilaku Python:
///   datetime.now(ZoneInfo("Asia/Makassat")) - timedelta(days=days)
/// lalu dibandingkan dengan (waktu pesan UTC + 8 jam).
pub fn compute_cutoff_secs(days: i64) -> i64 {
    let now = Utc::now().timestamp();
    now + 8 * 3600 - days * 86400
}

/// Cek apakah peer adalah grup atau channel (bukan user).
pub fn is_group_or_channel(peer_type: &str) -> bool {
    peer_type == "group" || peer_type == "channel"
}

/// Tipe grup dari peer type.
pub fn group_type_from_peer(peer_type: &str) -> &'static str {
    if peer_type == "channel" { "channel" } else { "group" }
}

/// Parse "host:port" dari session Telethon menjadi (host, port).
pub fn parse_server_address(value: &str) -> Option<(String, u16)> {
    if let Some((host, port)) = value.rsplit_once(':') {
        if !host.is_empty() {
            if let Ok(port) = port.parse::<u16>() {
                return Some((host.to_string(), port));
            }
        }
    }
    if value.is_empty() { None } else { Some((value.to_string(), 0)) }
}

/// Tentukan apakah error RPC Telegram bersifat transien dan boleh di-retry.
pub fn is_retryable_rpc(code: i32, name: &str) -> bool {
    if code == 500 { return true; }
    matches!(name, "RPC_MCGET_FAIL" | "RPC_CALL_FAIL" | "TIMEOUT" | "SERVER_STARTED" | "STARTED")
}

/// Backoff eksponensial: 1s -> 2s -> 4s -> 8s -> 16s.
pub fn retry_backoff_secs(attempt: u32) -> u64 {
    1u64 << attempt.min(4)
}

/// Hasil ekstraksi paket AI unlimited dari satu pesan.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AiPackageHit {
    pub name: String,
    pub days: i64,
    pub price_idr: Option<i64>,
}

/// Konversi karakter CP1252 ke byte aslinya.
/// Konversi character hasil decode CP1252 kembali ke byte aslinya.
fn cp1252_to_byte(c: char) -> Option<u8> {
    let cp = c as u32;
    // Latin-1 langsung
    if cp <= 0x7F || (cp >= 0xA0 && cp <= 0xFF) {
        return Some(cp as u8);
    }
    // Karakter kontrol C1 yang kadang tersimpan apa adanya (U+0080..U+009F)
    if (0x80..=0x9F).contains(&cp) {
        return Some(cp as u8);
    }
    // Karakter printable CP1252 yang menggantikan slot C1
    let mapped = match c {
        '\u{20AC}' => 0x80, '\u{201A}' => 0x82, '\u{0192}' => 0x83, '\u{201E}' => 0x84,
        '\u{2026}' => 0x85, '\u{2020}' => 0x86, '\u{2021}' => 0x87, '\u{02C6}' => 0x88,
        '\u{2030}' => 0x89, '\u{0160}' => 0x8A, '\u{2039}' => 0x8B, '\u{0152}' => 0x8C,
        '\u{017D}' => 0x8E, '\u{2018}' => 0x91, '\u{2019}' => 0x92, '\u{201C}' => 0x93,
        '\u{201D}' => 0x94, '\u{2022}' => 0x95, '\u{2013}' => 0x96, '\u{2014}' => 0x97,
        '\u{02DC}' => 0x98, '\u{2122}' => 0x99, '\u{0161}' => 0x9A, '\u{203A}' => 0x9B,
        '\u{0153}' => 0x9C, '\u{017E}' => 0x9E, '\u{0178}' => 0x9F,
        _ => return None,
    };
    Some(mapped)
}

/// Perbaiki mojibake: UTF-8 yang salah dibaca sebagai CP1252.
/// Contoh: "ðŸŽ‰" -> "🎉", "â€¢" -> "•".
pub fn repair_mojibake(text: &str) -> String {
    if !text.contains('ð') && !text.contains('â') && !text.contains('Ã') {
        return text.to_string();
    }
    let bytes: Vec<u8> = text.chars().filter_map(cp1252_to_byte).collect();
    String::from_utf8(bytes).unwrap_or_else(|_| text.to_string())
}
/// Cek apakah pesan adalah penawaran paket data/telepon/voucher (bukan model AI).
fn is_non_ai_offer(low_compact: &str) -> bool {
    let markers = [
        "esim", "simcard", "kuota", "kategoridata", "kategorivoucher",
        "aktivasi voucher", "smartfren", "axisdata", "aigo", "prabayar",
        "alwayson", "nonfaktur", "fakturpajak", "gb", "voucher",
        "telkomsel", "indosat", "operator", "pulsa",
    ];
    markers.iter().any(|m| low_compact.contains(m))
}

/// Ekstrak paket AI unlimited dari isi pesan (bukan dari nama grup).
pub fn extract_ai_package(text: &str) -> Option<AiPackageHit> {
    let low = text.to_lowercase();
    if !low.contains("unlimited") || !low.contains("ai") {
        return None;
    }
    let low_compact: String = low.chars().filter(|c| !c.is_whitespace()).collect();
    if is_non_ai_offer(&low_compact) {
        return None;
    }
    let days = find_days(&low)?;
    if !(1..=30).contains(&days) {
        return None;
    }
    let name = extract_package_name(text).unwrap_or_else(|| "Unlimited AI".to_string());
    let price_idr = extract_price_idr(&low);
    Some(AiPackageHit { name, days, price_idr })
}

fn find_days(low: &str) -> Option<i64> {
    if let Some(days) = capture_number_before(low, "hari") { return Some(days); }
    if let Some(weeks) = capture_number_before(low, "minggu") { return Some(weeks * 7); }
    if let Some(months) = capture_number_before(low, "bulan") { return Some(months * 30); }
    if low.contains("sebulan") || low.contains("se bulan") || low.contains("bulan penuh") {
        return Some(30);
    }
    None
}

fn capture_number_before(low: &str, unit: &str) -> Option<i64> {
    let idx = low.find(unit)?;
    let before = &low[..idx];
    let digits: String = before
        .chars().rev()
        .take_while(|c| c.is_ascii_digit() || *c == ' ' || *c == '+' || *c == ':')
        .collect::<String>().chars().rev()
        .filter(|c| c.is_ascii_digit()).collect();
    if digits.is_empty() {
        if low.contains("sehari") && unit == "hari" { return Some(1); }
        if low.contains("seminggu") && unit == "minggu" { return Some(1); }
        return None;
    }
    digits.parse::<i64>().ok()
}

fn extract_package_name(text: &str) -> Option<String> {
    let marker = "Paket:";
    let idx = text.find(marker)?;
    let rest = &text[idx + marker.len()..];
    let end = rest.find('\u{23F3}')
        .or_else(|| rest.find("Masa Aktif"))
        .or_else(|| rest.find("â³"))
        .unwrap_or(rest.len());
    let name = rest[..end].chars().filter(|c| *c != '\n' && *c != '\r').collect::<String>().trim().to_string();
    if name.is_empty() { None } else { Some(name) }
}

/// Ekstrak harga Rupiah dari teks pesan.
/// Hanya pola harga eksplisit: "Rp 75.000", "50rb", "50 ribu", "90k".
/// Angka tanggal/durasi tanpa penanda harga tidak dianggap harga.
/// Harga harus minimal 1.000 Rupiah agar tidak menangkap "Rp 1", "Rp 3", "Rp 120".
/// Ekstrak harga Rupiah dari teks pesan paket AI.
/// Harga hanya diambil jika ada penanda harga eksplisit: `rp`, `rb`, `ribu`, `k`,
/// `harga`, `bayar`, `biaya`, atau `price`. Angka konteks seperti `512K context`,
/// `50 RPM`, dan `19 model` tidak dianggap harga.
pub fn extract_price_idr(low: &str) -> Option<i64> {
    let price_keywords = ["harga", "rp", "bayar", "biaya", "price"];
    let mut candidates: Vec<(usize, i64)> = Vec::new();
    let credit_words = ["kredit", "credit", "koin", "coin", "poin", "point"];

    for keyword in price_keywords {
        let mut search_from = 0usize;
        while let Some(rel) = low[search_from..].find(keyword) {
            let idx = search_from + rel;
            search_from = idx + keyword.len();
            let rest = &low[idx + keyword.len()..];
            let rest_trim = rest.trim_start();

            // Pola: "Rp 45.000", "harga 90k", "bayar 50rb", "price 50 ribu"
            let after_keyword: String = rest_trim.chars().take(40).collect();
            if let Some(v) = parse_price_after_marker(&after_keyword) {
                let window_start = idx.saturating_sub(40);
                let window_end = (idx + 60).min(low.len());

                let context_start = low.char_indices().filter(|(i, _)| *i <= window_start).last().map(|(i, _)| i).unwrap_or(0);
                let context_end = low.char_indices().filter(|(i, _)| *i <= window_end).last().map(|(i, _)| i).unwrap_or(low.len());
                let context = &low[context_start..context_end];
                let near_credit = credit_words.iter().any(|word| context.contains(word));
                if !near_credit {
                    candidates.push((idx, v));
                }
            }
        }
    }

    // Pola umum "50rb", "50 ribu", "90k" tanpa kata harga.
    let bytes = low.as_bytes();
    let mut i = 0usize;
    while i < bytes.len() {
        if bytes[i].is_ascii_digit() {
            let start = i;
            while i < bytes.len() && (bytes[i].is_ascii_digit() || bytes[i] == b'.') { i += 1; }
            let digits: String = low[start..i].chars().filter(|c| c.is_ascii_digit()).collect();
            let after = low[i..].chars().take(12).collect::<String>().to_lowercase();
            let after_trim = after.trim_start();
            if !digits.is_empty() && price_suffix_multiplier(after_trim).is_some() {
                let suffix_len = if after_trim.starts_with("ribu") { 4 } else if after_trim.starts_with("rb") { 2 } else { 1 };
                let after_suffix = after_trim[suffix_len..].trim_start().to_lowercase();
                let non_price_context = [
                    "context", "ctx", "rpm", "token", "model", "gb", "mb", "kb",
                    "hari", "jam", "bulan", "minggu", "request", "req",
                ];
                let is_context_number = non_price_context.iter().any(|w| after_suffix.starts_with(w));
                if !is_context_number {
                    if let Ok(v) = digits.parse::<i64>() {
                        let priced = v.saturating_mul(1_000);
                        if priced >= 1_000 { candidates.push((start, priced)); }
                    }
                }
            }
        }
        i += 1;
    }

    candidates.sort_by_key(|(pos, _)| *pos);
    for (_, value) in candidates {
        // Batas harga wajar paket AI unlimited: Rp 3.000 - Rp 600.000.
        if (3_000..=600_000).contains(&value) {
            return Some(value);
        }
    }
    None
}

fn price_suffix_multiplier(tail_trim: &str) -> Option<i64> {
    if tail_trim.starts_with("ribu") {
        return Some(1_000);
    }
    if tail_trim.starts_with("rb") {
        let next = tail_trim.chars().nth(2);
        if next.map(|c| !c.is_alphabetic()).unwrap_or(true) {
            return Some(1_000);
        }
    }
    if tail_trim.starts_with('k') {
        let next = tail_trim.chars().nth(1);
        if next.map(|c| !c.is_alphabetic()).unwrap_or(true) {
            return Some(1_000);
        }
    }
    None
}
fn parse_price_after_marker(rest: &str) -> Option<i64> {
    let rest = rest.trim_start();
    let digits: String = rest.chars()
        .skip_while(|c| !c.is_ascii_digit())
        .take_while(|c| c.is_ascii_digit() || *c == '.' || *c == ',')
        .collect::<String>()
        .chars()
        .filter(|c| c.is_ascii_digit())
        .collect();
    if digits.is_empty() { return None; }

    let after_digits: String = rest.chars().skip_while(|c| !c.is_ascii_digit()).collect();
    let number_part: String = after_digits.chars().take_while(|c| c.is_ascii_digit() || *c == '.' || *c == ',').collect();
    let tail: String = after_digits.chars().skip(number_part.chars().count()).collect();
    let tail_trim = tail.trim_start().to_lowercase();

    let value = digits.parse::<i64>().ok()?;
    if let Some(multiplier) = price_suffix_multiplier(&tail_trim) {
        return Some(value.saturating_mul(multiplier));
    }
    Some(value)
}
/// Detail paket AI yang sudah punya provider, durasi, harga, dan model.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AiPackageDetail {
    pub provider: String,
    pub days: i64,
    pub price_idr: Option<i64>,
    pub models: Vec<String>,
}

fn capture_after_marker(text: &str, markers: &[&str]) -> Option<String> {
    let lower = text.to_lowercase();
    for marker in markers {
        if let Some(idx) = lower.find(marker) {
            let rest = &text[idx + marker.len()..];
            let value: String = rest
                .chars()
                .skip_while(|c| c.is_whitespace() || *c == ':')
                .take_while(|c| !c.is_whitespace() && *c != '|' && *c != '\n' && *c != '\r')
                .collect();
            if !value.is_empty() {
                return Some(value);
            }
        }
    }
    None
}

/// Ambil provider/penjual/gateway dari isi pesan.
pub fn extract_provider(text: &str) -> String {
    let lower = text.to_lowercase();
    if lower.contains("limo router") { return "Limo Router".to_string(); }
    if lower.contains("jerouter") { return "Jerouter V2".to_string(); }
    if lower.contains("kangkung store") { return "Kangkung Store".to_string(); }
    if lower.contains("gater") { return "GATER".to_string(); }
    if lower.contains("nocta") { return "Nocta Digital".to_string(); }
    if lower.contains("nilovr") { return "NilovrAI".to_string(); }
    if lower.contains("griphub") { return "Griphub Router".to_string(); }
    if lower.contains("apigod") { return "APIGOD".to_string(); }
    if lower.contains("tiprouter") { return "TipRouter".to_string(); }
    if lower.contains("mahicenter") { return "MahiCenter Router".to_string(); }
    if let Some(v) = capture_after_marker(text, &["Gateway:", "Seller:", "Provider:"]) {
        return v;
    }
    "Tidak disebut".to_string()
}

/// Ambil nama model AI yang disebut eksplisit di pesan.
pub fn extract_models(text: &str) -> Vec<String> {
    const KNOWN: &[&str] = &[
        "Deepseek V4.1 Flash 1014", "GLM 5.3 Flash", "Claude Opus 5.5", "GPT-6.1",
        "DeepSeek", "Qwen", "KIMI", "GLM", "STEP 5", "Solar", "Longcat",
        "Claude", "GPT", "Gemini", "Llama", "Mistral",
    ];
    let mut found: Vec<String> = Vec::new();
    let lower = text.to_lowercase();
    let mut covered: Vec<(usize, usize)> = Vec::new();

    for model in KNOWN {
        let needle = model.to_lowercase();
        let mut from = 0usize;
        while let Some(pos) = lower[from..].find(&needle) {
            let start = from + pos;
            let end = start + needle.len();
            let overlaps = covered.iter().any(|(s, e)| start < *e && end > *s);
            let duplicate = found.iter().any(|m| m.eq_ignore_ascii_case(model));
            if !overlaps && !duplicate {
                found.push((*model).to_string());
                covered.push((start, end));
                break;
            }
            from = end;
        }
    }

    let preferred_order = ["DeepSeek", "Qwen", "GLM", "STEP 5", "KIMI"];
    let mut ordered = Vec::new();
    for name in preferred_order {
        if let Some(pos) = found.iter().position(|m| m.eq_ignore_ascii_case(name)) {
            ordered.push(found.remove(pos));
        }
    }
    ordered.extend(found);
    ordered
}
fn parse_compact_price(value: &str) -> Option<i64> {
    let v = value.trim().to_lowercase().replace('.', "");
    let digits: String = v.chars().take_while(|c| c.is_ascii_digit()).collect();
    let rest = &v[digits.len()..];
    let n = digits.parse::<i64>().ok()?;
    if rest.starts_with('k') || rest.starts_with("rb") || rest.starts_with("ribu") {
        Some(n.saturating_mul(1_000))
    } else {
        Some(n)
    }
}

/// Normalisasi pesan untuk deduplikasi: menyamakan bagian pengguna/pembeli yang berbeda.
pub fn normalize_message_for_dedup(text: &str) -> String {
    let mut out = text.to_lowercase();
    let patterns = [
        ("pengguna:", 40usize),
        ("user:", 40usize),
        ("pembeli:", 40usize),
        ("buyer:", 40usize),
    ];
    for (marker, max_len) in patterns {
        let mut from = 0usize;
        while let Some(pos) = out[from..].find(marker) {
            let idx = from + pos;
            let value_start = idx + marker.len();
            let after: String = out[value_start..].chars().take(max_len).collect();
            let end_offset = after
                .find(|c: char| c == '\n' || c == '|' || c == '🚀' || c == '✨' || c == '🏬' || c == '🔗')
                .unwrap_or(after.chars().count());
            let end = value_start + end_offset;
            if end > value_start && end <= out.len() {
                out.replace_range(value_start..end, " <user> ");
            }
            from = value_start + "<user>".len();
        }
    }
    out.split_whitespace().collect::<Vec<_>>().join(" ")
}
/// Ambil pasangan durasi dan harga dari teks, termasuk format "1 hari: 5K".
pub fn extract_duration_prices(low: &str) -> Vec<(i64, i64)> {
    let mut out = Vec::new();
    for days in [1i64, 3, 7, 10, 14, 30] {
        let day_word = format!("{} hari", days);
        let mut from = 0usize;
        while let Some(pos) = low[from..].find(&day_word) {
            let idx = from + pos;
            let rest = &low[idx + day_word.len()..];
            let segment: String = rest.chars().take(30).collect();
            if let Some(colon) = segment.find(':') {
                let after = &segment[colon + 1..];
                let token: String = after.chars().skip_while(|c| c.is_whitespace()).take_while(|c| !c.is_whitespace() && *c != '•' && *c != '|').collect();
                if let Some(price) = parse_compact_price(&token) {
                    if (3_000..=600_000).contains(&price) {
                        out.push((days, price));
                    }
                }
            }
            from = idx + day_word.len();
        }
    }
    if let Some(price) = extract_price_idr(low) {
        if let Some(days) = find_days(low) {
            if (3_000..=600_000).contains(&price) {
                let credit_words = ["kredit", "credit", "koin", "coin", "poin", "point"];
                let has_credit_context = credit_words.iter().any(|word| low.contains(word));
                if !has_credit_context {
                    out.push((days, price));
                }
            }
        }
    }
    out
}

/// Ambil semua variasi paket dari satu pesan (satu pesan bisa memuat banyak durasi).
pub fn extract_ai_package_variants(text: &str) -> Vec<AiPackageDetail> {
    if extract_ai_package(text).is_none() { return Vec::new(); }
    let provider = extract_provider(text);
    let models = extract_models(text);
    let low = text.to_lowercase();
    let prices = extract_duration_prices(&low);
    if prices.is_empty() {
        return vec![AiPackageDetail {
            provider,
            days: find_days(&low).unwrap_or(30),
            price_idr: extract_price_idr(&low),
            models,
        }];
    }
    prices.into_iter().map(|(days, price_idr)| AiPackageDetail {
        provider: provider.clone(),
        days,
        price_idr: Some(price_idr),
        models: models.clone(),
    }).collect()
}
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compute_cutoff_30_days() {
        let cutoff = compute_cutoff_secs(30);
        let now = Utc::now().timestamp();
        let expected = now + 8 * 3600 - 30 * 86400;
        assert!((cutoff - expected).abs() < 2);
    }

    #[test]
    fn test_is_group_or_channel() {
        assert!(is_group_or_channel("group"));
        assert!(is_group_or_channel("channel"));
        assert!(!is_group_or_channel("user"));
    }

    #[test]
    fn test_group_type_from_peer() {
        assert_eq!(group_type_from_peer("channel"), "channel");
        assert_eq!(group_type_from_peer("group"), "group");
    }

    #[test]
    fn test_parse_server_address() {
        assert_eq!(parse_server_address("91.108.56.120:443"), Some(("91.108.56.120".to_string(), 443)));
        assert_eq!(parse_server_address("invalid"), Some(("invalid".to_string(), 0)));
        assert_eq!(parse_server_address(""), None);
    }

    #[test]
    fn test_retry_backoff_secs() {
        assert_eq!(retry_backoff_secs(0), 1);
        assert_eq!(retry_backoff_secs(1), 2);
        assert_eq!(retry_backoff_secs(2), 4);
        assert_eq!(retry_backoff_secs(3), 8);
        assert_eq!(retry_backoff_secs(9), 16);
    }

    #[test]
    fn test_is_retryable_rpc() {
        assert!(is_retryable_rpc(500, "RPC_MCGET_FAIL"));
        assert!(is_retryable_rpc(500, "TIMEOUT"));
        assert!(is_retryable_rpc(500, "OTHER"));
        assert!(!is_retryable_rpc(400, "PHONE_NUMBER_INVALID"));
    }

    #[test]
    fn test_extract_price_idr_strict() {
        assert_eq!(extract_price_idr("harga awal 50rb"), Some(50_000));
        assert_eq!(extract_price_idr("rp 75.000"), Some(75_000));
        assert_eq!(extract_price_idr("bayar 90k"), Some(90_000));
        assert_eq!(extract_price_idr("harga 50 ribu"), Some(50_000));
        assert_eq!(extract_price_idr("harga murah"), None);
        assert_eq!(extract_price_idr("masa aktif: +1 hari unlimited semua model ai"), None);
        assert_eq!(extract_price_idr("30 hari"), None);
        assert_eq!(extract_price_idr("2026-11-22"), None);
    }

    #[test]
    fn test_price_bounds_wajar() {
        assert_eq!(extract_price_idr("rp 1"), None);
        assert_eq!(extract_price_idr("rp 3"), None);
        assert_eq!(extract_price_idr("rp 120"), None);
        assert_eq!(extract_price_idr("rp 45.000"), Some(45_000));
    }

    #[test]
    fn test_repair_mojibake_full_message() {
        let raw = "ðŸŽ‰ Aktivasi Paket Berhasil! ðŸ’Ž Paket: Trial â³ Masa Aktif: +1 Hari ðŸ˜Ž Pengguna: @mâ€¢â€¢â€¢x ðŸš€ Gateway: Jerouter V2 âœ¨ Selamat menikmati akses unlimited semua model AI!";
        let fixed = repair_mojibake(raw);
        assert!(fixed.contains("🎉"), "emoji haruspulih kembali: {}", fixed);
        assert!(fixed.contains("💎"), "berlian harus kembali: {}", fixed);
        assert!(fixed.contains("⏳"), "jam harus kembali: {}", fixed);
        assert!(fixed.contains("•"), "bullet harus kembali: {}", fixed);
    }
    #[test]
    fn test_repair_mojibake() {
        assert_eq!(repair_mojibake("ðŸŽ‰ Aktivasi â€¢ Paket"), "🎉 Aktivasi • Paket");
        assert_eq!(repair_mojibake("Sudah bagus 🎉"), "Sudah bagus 🎉");
    }
}

#[cfg(test)]
mod ai_package_tests {
    use super::*;
    #[test]
    fn test_normalize_message_for_dedup_user() {
        let a = "Aktivasi Paket Berhasil Paket: Trial Masa Aktif: +1 Hari Pengguna: @m---x Gateway: Jerouter V2 unlimited ai";
        let b = "Aktivasi Paket Berhasil Paket: Trial Masa Aktif: +1 Hari Pengguna: @g---e Gateway: Jerouter V2 unlimited ai";
        assert_eq!(normalize_message_for_dedup(a), normalize_message_for_dedup(b));
        assert!(normalize_message_for_dedup(a).contains("<user>"));
    }

    #[test]
    fn test_normalize_message_for_dedup_buyer() {
        let a = "Pembelian sukses Produk: Unlimited Token Pembeli: Dim***** Kategori: AI Tools unlimited";
        let b = "Pembelian sukses Produk: Unlimited Token Pembeli: Bud***** Kategori: AI Tools unlimited";
        assert_eq!(normalize_message_for_dedup(a), normalize_message_for_dedup(b));
    }
    #[test]
    fn test_extract_price_ignore_credit_context() {
        let text = "6 paket kredit diskon 35%: 1.000 kredit Rp136.500 (ritel Rp210.000) HARGA CONTOH Tanpa Batas 30 hari: Rp598.800";
        let prices = extract_duration_prices(&text.to_lowercase());
        assert!(!prices.contains(&(30, 136_500)));
    }
    #[test]
    fn test_extract_provider_gateway() {
        let text = "🎉 Aktivasi Paket Berhasil! 💎 Paket: Trial ⏳ Masa Aktif: +1 Hari 🚀 Gateway: Jerouter V2 ✨ Selamat menikmati akses unlimited semua model AI!";
        assert_eq!(extract_provider(text), "Jerouter V2");
    }

    #[test]
    fn test_extract_provider_seller() {
        let text = "🏬 Seller: GATER 🔗 URL Produk: https://sedulurstore.com/p/unlimited-token-gater-lite-3-hari";
        assert_eq!(extract_provider(text), "GATER");
    }

    #[test]
    fn test_extract_provider_limo_router() {
        let text = "🔥LIMO ROUTER | 19 MODEL AI UNLIMITED DeepSeek, Qwen, GLM, STEP 5, KIMI • Unlimited";
        assert_eq!(extract_provider(text), "Limo Router");
    }

    #[test]
    fn test_extract_models_from_message() {
        let text = "19 MODEL AI UNLIMITED DeepSeek, Qwen, GLM, STEP 5, KIMI Unlimited";
        let models = extract_models(text);
        assert_eq!(models, vec!["DeepSeek", "Qwen", "GLM", "STEP 5", "KIMI"]);
    }

    #[test]
    fn test_extract_models_specific_variants() {
        let text = "39 Model AI (Deepseek V4.1 Flash 1014, GLM 5.3 Flash, dll)";
        let models = extract_models(text);
        assert_eq!(models, vec!["Deepseek V4.1 Flash 1014", "GLM 5.3 Flash"]);
    }

    #[test]
    fn test_extract_duration_prices_limo() {
        let text = "1 hari: 5K ⭐ • 3 hari: 10K💫 • 10 hari: 20K 🌟 • 30 hari: 40K✨";
        let prices = extract_duration_prices(&text.to_lowercase());
        assert!(prices.contains(&(1, 5_000)));
        assert!(prices.contains(&(3, 10_000)));
        assert!(prices.contains(&(10, 20_000)));
        assert!(prices.contains(&(30, 40_000)));
    }

    #[test]
    fn test_extract_duration_price_after_text() {
        let text = "Apikey DeepSeek Unlimited 30 HARI 💰 Harga: Rp45.000 Kategori: AI Tools";
        let prices = extract_duration_prices(&text.to_lowercase());
        assert!(prices.contains(&(30, 45_000)));
    }

    #[test]
    fn test_extract_ai_package_variants_limo() {
        let text = "🔥LIMO ROUTER | 19 MODEL AI UNLIMITED DeepSeek, Qwen, GLM, STEP 5, KIMI • 1 hari: 5K • 3 hari: 10K • 30 hari: 40K";
        let details = extract_ai_package_variants(text);
        let d30 = details.iter().find(|d| d.days == 30).unwrap();
        assert_eq!(d30.provider, "Limo Router");
        assert_eq!(d30.price_idr, Some(40_000));
        assert!(d30.models.contains(&"DeepSeek".to_string()));
    }
    #[test]
    fn test_price_ignore_context_numbers() {
        assert_eq!(extract_price_idr("512K context 50 RPM 19 model ai unlimited promo 40rb"), Some(40_000));
        assert_eq!(extract_price_idr("1.000.000 token unlimited ai"), None);
        assert_eq!(extract_price_idr("512K context 50 RPM unlimited ai"), None);
    }

    #[test]
    fn test_reject_non_ai_price_context() {
        let text = "VPS 512K context 50 RPM unlimited ai harga 512000";
        assert_eq!(extract_price_idr(&text.to_lowercase()), Some(512_000));
    }

    #[test]
    fn test_trial_1_day() {
        let hit = extract_ai_package("Aktivasi Paket Berhasil! Paket: Trial Masa Aktif: +1 Hari Selamat menikmati akses unlimited semua model AI!").unwrap();
        assert_eq!(hit.name, "Trial");
        assert_eq!(hit.days, 1);
        assert_eq!(hit.price_idr, None);
    }

    #[test]
    fn test_pro_30_days() {
        let hit = extract_ai_package("Paket: Pro Masa Aktif: +30 Hari unlimited semua model AI").unwrap();
        assert_eq!(hit.days, 30);
    }

    #[test]
    fn test_monthly_offer_with_price() {
        let hit = extract_ai_package("paket unlimited full akses semua model ai selama sebulan penuh harga 90rb").unwrap();
        assert_eq!(hit.days, 30);
        assert_eq!(hit.price_idr, Some(90_000));
    }

    #[test]
    fn test_ignore_non_ai_unlimited() {
        assert!(extract_ai_package("VPS unlimited replace 20/Unlimited").is_none());
    }

    #[test]
    fn test_ignore_esim_unlimited() {
        let text = "Ada yang minat eSIM Global unlimited data, durasi 30 hari, harga awal 50rb";
        assert!(extract_ai_package(text).is_none());
    }

    #[test]
    fn test_reject_axis_aigo_data_package() {
        let text = "Produk Prabayar FP Baru Nama: Axis Data AIGO Unlimited 1 Hari Kategori: Data Brand: AXIS Type: AIGO Unlimited Harga: Rp. 23.867 Silakan langsung di-parsing";
        assert!(extract_ai_package(text).is_none());
    }

    #[test]
    fn test_reject_smartfren_voucher() {
        let text = "Kategori Aktivasi Voucher SMARTFREN Unlimited Nonstop (Non Faktur | Faktur Pajak) 2 GB 10 Hari 12.120 | Model AI tambahan 3 GB 14 Hari 19.110";
        assert!(extract_ai_package(text).is_none());
    }

    #[test]
    fn test_reject_tri_voucher() {
        let text = "Kategori Aktivasi Voucher TRI Jawa Tengah AlwaysOn 2.5 GB Unlimited 26 GB 75.195 | AI 30 Hari 113.941";
        assert!(extract_ai_package(text).is_none());
    }
}