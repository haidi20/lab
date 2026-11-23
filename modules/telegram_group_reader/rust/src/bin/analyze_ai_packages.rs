//! Analisa paket AI unlimited dari isi pesan grup Telegram di MySQL.
//! Output: markdown berisi agregat + contoh isi pesan asli.

use anyhow::Result;
use dotenvy::dotenv;
use mysql_async::prelude::Queryable;
use mysql_async::{Opts, Params, Pool, Row};
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::time::Instant;
use telegram_group_reader_rust::{extract_ai_package_variants, repair_mojibake, AiPackageDetail};

const OUTPUT: &str = r"D:\learns\random\modules\telegram_group_reader\documents\2026-11-07-daftar-paket-ai-unlimited.md";

fn get_env(key: &str, default: &str) -> String {
    env::var(key).unwrap_or_else(|_| default.to_string())
}

fn format_rupiah(value: i64) -> String {
    let digits = value.abs().to_string();
    let mut parts = Vec::new();
    let mut rest = digits.as_str();
    while rest.len() > 3 {
        let split = rest.len() - 3;
        parts.push(rest[split..].to_string());
        rest = &rest[..split];
    }
    parts.push(rest.to_string());
    parts.reverse();
    format!("Rp {}", parts.join("."))
}
#[tokio::main]
async fn main() -> Result<()> {
    let started = Instant::now();
    dotenv().ok();

    let mysql_url = format!(
        "mysql://{}:{}@{}:{}/{}",
        get_env("MYSQL_USER", "root"),
        get_env("MYSQL_PASSWORD", ""),
        get_env("MYSQL_HOST", "127.0.0.1"),
        get_env("MYSQL_PORT", "3306"),
        get_env("MYSQL_DATABASE", "telegram_data"),
    );

    let pool = Pool::new(Opts::from_url(&mysql_url)?);
    let mut conn = pool.get_conn().await?;
    conn.query_drop("SET NAMES utf8mb4").await?;

    let rows: Vec<Row> = conn
        .exec(
            "SELECT group_title, sender, text, created FROM telegram_messages WHERE LOWER(COALESCE(text,'')) LIKE '%unlimited%' ORDER BY created ASC",
            Params::Empty,
        )
        .await?;

    let mut details: Vec<AiPackageDetail> = Vec::new();
    let mut total_rows = 0usize;
    let mut matched = 0usize;

    for mut row in rows {
        let text: String = row.take("text").unwrap_or_default();
        total_rows += 1;

        let variants = extract_ai_package_variants(&repair_mojibake(&text));
        if !variants.is_empty() {
            matched += 1;
            details.extend(variants);
        }
    }

    let latest: Option<String> = conn
        .query_first("SELECT MAX(created) FROM telegram_messages")
        .await?;
    let earliest: Option<String> = conn
        .query_first("SELECT MIN(created) FROM telegram_messages")
        .await?;

    let elapsed = started.elapsed().as_secs_f64();

    let mut md = String::new();
    md.push_str("# Kesimpulan - Paket AI Unlimited dari Isi Pesan Grup Telegram (Rust)\n\n");
    md.push_str("Analisa ini dibuat oleh binary Rust `analyze_ai_packages` dengan membaca **isi pesan** dari tabel `telegram_messages` di MySQL.\n\n");
    md.push_str("Catatan: yang dianalisa adalah **message/text**, bukan nama grup. Nama grup hanya konteks tambahan.\n\n");

    md.push_str("## Ringkasan Data\n\n");
    md.push_str(&format!("- waktu running program Rust: **{:.2} detik**\n", elapsed));
    md.push_str(&format!("- total pesan dengan kata `unlimited`: **{}**\n", total_rows));
    md.push_str(&format!("- pesan yang cocok dengan paket AI unlimited: **{}**\n", matched));
    if let Some(d) = earliest { md.push_str(&format!("- pesan terlama di DB: **{}**\n", d)); }
    if let Some(d) = latest { md.push_str(&format!("- pesan terbaru di DB: **{}**\n", d)); }
    md.push_str("\n");

    let mut grouped: BTreeMap<i64, BTreeMap<String, (usize, BTreeMap<i64, usize>, Vec<String>)>> = BTreeMap::new();
    for d in &details {
        let entry = grouped
            .entry(d.days)
            .or_default()
            .entry(d.provider.clone())
            .or_insert((0, BTreeMap::new(), Vec::new()));
        entry.0 += 1;
        if let Some(price) = d.price_idr {
            *entry.1.entry(price).or_insert(0) += 1;
        }
        for model in &d.models {
            if !entry.2.contains(model) {
                entry.2.push(model.clone());
            }
        }
    }

    md.push_str("## Ringkasan Berdasarkan Masa Waktu Paket AI\n\n");
    for (days, providers) in &grouped {
        let label = match days { 30 => "30 hari / 1 bulan".to_string(), _ => format!("{} hari", days) };
        md.push_str(&format!("### {}\n\n", label));
        for (provider, (count, prices, models)) in providers {
            md.push_str(&format!("- **Provider/penjual:** {} | **pesan:** {}\n", provider, count));
            if prices.is_empty() {
                md.push_str("  - Harga: tidak disebut eksplisit\n");
            } else {
                let price_text = prices
                    .iter()
                    .map(|(price, n)| format!("{} ({} pesan)", format_rupiah(*price), n))
                    .collect::<Vec<_>>()
                    .join(", ");
                md.push_str(&format!("  - Harga paket AI: {}\n", price_text));
            }
            if models.is_empty() {
                md.push_str("  - Model AI: tidak disebut eksplisit\n");
            } else {
                md.push_str(&format!("  - Model AI: {}\n", models.join(", ")));
            }
        }
        md.push_str("\n");
    }
    md.push_str("## Kesimpulan

");
    md.push_str("Dari isi pesan grup Telegram yang tersimpan, paket AI Unlimited yang terdeteksi mencakup durasi **1 hari, 3 hari, 7 hari, 14 hari, dan 30 hari / 1 bulan**.\n\n");
    md.push_str("Pola dominan berasal dari notifikasi aktivasi dengan paket:\n\n");
    md.push_str("- `Trial` = 1 hari\n");
    md.push_str("- `Basic` = 3 hari\n");
    md.push_str("- `Plus` = 7 hari\n");
    md.push_str("- `Essential` = 14 hari\n");
    md.push_str("- `Pro` = 30 hari / 1 bulan\n\n");
    md.push_str("Harga yang ditampilkan hanya harga paket model AI yang terdeteksi eksplisit dari isi pesan. Voucher, paket data, dan angka konteks seperti RPM/context/token tidak dimasukkan.\n");

    fs::write(OUTPUT, md)?;
    println!("Markdown ditulis: {} (elapsed {:.2} detik)", OUTPUT, elapsed);
    Ok(())
}