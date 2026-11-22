//! Telegram group reader - Rust implementation
//! Pure logic functions for testing

use chrono::Utc;

/// Cutoff seconds (UTC epoch) untuk filter pesan N hari terakhir.
/// Menyamakan perilaku Python:
///   datetime.now(ZoneInfo("Asia/Makassar")) - timedelta(days=days)
/// lalu dibandingkan dengan (waktu pesan UTC + 8 jam).
pub fn compute_cutoff_secs(days: i64) -> i64 {
    let now = Utc::now().timestamp();
    now + 8 * 3600 - days * 86400
}

/// Check if a peer is a group or channel (not a user)
pub fn is_group_or_channel(peer_type: &str) -> bool {
    peer_type == "group" || peer_type == "channel"
}

/// Get group type string from peer type
pub fn group_type_from_peer(peer_type: &str) -> &'static str {
    if peer_type == "channel" {
        "channel"
    } else {
        "group"
    }
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
    // Telethon menyimpan host saja; port diambil dari kolom lain (0 = pakai port DB).
    if value.is_empty() {
        None
    } else {
        Some((value.to_string(), 0))
    }
}


/// Tentukan apakah error RPC Telegram bersifat transien dan boleh di-retry.
/// Mengikuti Telethon: 500 (RPC_MCGET_FAIL, RPC_CALL_FAIL, TIMEOUT, dll)
/// dan error I/O dikategorikan retryable.
pub fn is_retryable_rpc(code: i32, name: &str) -> bool {
    if code == 500 {
        return true;
    }
    matches!(
        name,
        "RPC_MCGET_FAIL"
            | "RPC_CALL_FAIL"
            | "TIMEOUT"
            | "SERVER_STARTED"
            | "STARTED"
    )
}

/// Backoff eksponensial: 1s -> 2s -> 4s -> 8s -> 16s.
pub fn retry_backoff_secs(attempt: u32) -> u64 {
    1u64 << attempt.min(4)
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    #[test]
    fn test_compute_cutoff_30_days() {
        let cutoff = compute_cutoff_secs(30);
        let now = Utc::now().timestamp();
        let expected = now + 8 * 3600 - 30 * 86400;
        assert!((cutoff - expected).abs() < 2, "Cutoff should be within 2 seconds of expected");
    }

    #[test]
    fn test_is_group_or_channel() {
        assert!(is_group_or_channel("group"));
        assert!(is_group_or_channel("channel"));
        assert!(!is_group_or_channel("user"));
    }


    #[test]
    fn test_parse_server_address() {
        assert_eq!(
            parse_server_address("91.108.56.120:443"),
            Some(("91.108.56.120".to_string(), 443))
        );
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
        assert!(is_retryable_rpc(500, "RPC_CALL_FAIL"));
    }

    #[test]
    fn test_group_type_from_peer() {
        assert_eq!(group_type_from_peer("channel"), "channel");
        assert_eq!(group_type_from_peer("group"), "group");
    }
}
