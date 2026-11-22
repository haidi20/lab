//! Integration test for cutoff logic (no network/DB).

use telegram_group_reader_rust::compute_cutoff_secs;

#[test]
fn test_cutoff_for_15_days() {
    use chrono::Utc;
    let cutoff = compute_cutoff_secs(15);
    let now = Utc::now().timestamp();
    let expected = now + 8 * 3600 - 15 * 86400;
    assert!((cutoff - expected).abs() < 5);
}
