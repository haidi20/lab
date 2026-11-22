//! Telegram group reader binary (Rust)
//! Fungsi sama dengan Python: fetch semua group/channel + pesan N hari terakhir, upsert ke MySQL.

use anyhow::{anyhow, Result};
use dotenvy::dotenv;
use grammers_client::peer::Peer;
use grammers_client::client::{DialogIter, MessageIter};
use grammers_client::{Client, InvocationError, SignInError};
use grammers_mtsender::SenderPool;
use grammers_session::storages::SqliteSession;
use mysql_async::{Opts, Params, Pool, Value};
use mysql_async::prelude::Queryable;
use std::env;
use std::io::{self, BufRead, Write};
use std::sync::Arc;
use telegram_group_reader_rust::{compute_cutoff_secs, group_type_from_peer, is_group_or_channel, is_retryable_rpc, retry_backoff_secs};

const SYNC_DAYS: i64 = 30;
const SESSION_FILE: &str = "telegram_group_reader.session";

fn get_env(key: &str, default: &str) -> String {
    env::var(key).unwrap_or_else(|_| default.to_string())
}



async fn retryable_dialog_next(
    iter: &mut DialogIter,
) -> std::result::Result<Option<grammers_client::peer::Dialog>, InvocationError> {
    let mut attempt = 0u32;
    loop {
        match iter.next().await {
            Err(InvocationError::Rpc(rpc)) if is_retryable_rpc(rpc.code, &rpc.name) && attempt < 5 => {
                let delay = retry_backoff_secs(attempt);
                tracing::warn!(
                    "RPC retryable {}: {} - retry dialog {} dalam {} dtk",
                    rpc.code, rpc.name, attempt + 1, delay
                );
                tokio::time::sleep(std::time::Duration::from_secs(delay)).await;
                attempt += 1;
            }
            Err(InvocationError::Io(e)) if attempt < 5 => {
                let delay = retry_backoff_secs(attempt);
                tracing::warn!("I/O error {} - retry dialog {} dalam {} dtk", e, attempt + 1, delay);
                tokio::time::sleep(std::time::Duration::from_secs(delay)).await;
                attempt += 1;
            }
            other => return other,
        }
    }
}

async fn retryable_message_next(
    iter: &mut MessageIter,
) -> std::result::Result<Option<grammers_client::message::Message>, InvocationError> {
    let mut attempt = 0u32;
    loop {
        match iter.next().await {
            Err(InvocationError::Rpc(rpc)) if is_retryable_rpc(rpc.code, &rpc.name) && attempt < 5 => {
                let delay = retry_backoff_secs(attempt);
                tracing::warn!(
                    "RPC retryable {}: {} - retry message {} dalam {} dtk",
                    rpc.code, rpc.name, attempt + 1, delay
                );
                tokio::time::sleep(std::time::Duration::from_secs(delay)).await;
                attempt += 1;
            }
            Err(InvocationError::Io(e)) if attempt < 5 => {
                let delay = retry_backoff_secs(attempt);
                tracing::warn!("I/O error {} - retry message {} dalam {} dtk", e, attempt + 1, delay);
                tokio::time::sleep(std::time::Duration::from_secs(delay)).await;
                attempt += 1;
            }
            other => return other,
        }
    }
}

fn normalize_session_name(value: &str) -> String {
    if value.ends_with(".session") {
        value.to_string()
    } else {
        format!("{}.session", value)
    }
}

fn prompt(message: &str) -> Result<String> {
    let stdout = io::stdout();
    let mut stdout = stdout.lock();
    stdout.write_all(message.as_bytes())?;
    stdout.flush()?;

    let stdin = io::stdin();
    let mut line = String::new();
    stdin.lock().read_line(&mut line)?;
    Ok(line.trim().to_string())
}

struct Config {
    api_id: i64,
    api_hash: String,
    session: String,
    mysql_host: String,
    mysql_port: u16,
    mysql_user: String,
    mysql_password: String,
    mysql_db: String,
}

impl Config {
    fn from_env() -> Self {
        Self {
            api_id: get_env("TELEGRAM_API_ID", "0").parse().unwrap_or(0),
            api_hash: get_env("TELEGRAM_API_HASH", ""),
            session: normalize_session_name(&get_env("TELEGRAM_SESSION", SESSION_FILE)),
            mysql_host: get_env("MYSQL_HOST", "127.0.0.1"),
            mysql_port: get_env("MYSQL_PORT", "3306").parse().unwrap_or(3306),
            mysql_user: get_env("MYSQL_USER", "root"),
            mysql_password: get_env("MYSQL_PASSWORD", ""),
            mysql_db: get_env("MYSQL_DATABASE", "telegram_data"),
        }
    }
}

async fn ensure_schema(pool: &Pool) -> Result<()> {
    let mut conn = pool.get_conn().await?;

    conn.query_drop(
        "CREATE TABLE IF NOT EXISTS telegram_groups (
            group_id VARCHAR(64) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            group_type VARCHAR(20) NOT NULL
        )",
    )
    .await?;

    conn.query_drop(
        "CREATE TABLE IF NOT EXISTS telegram_messages (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            group_title VARCHAR(255) NOT NULL,
            message_id BIGINT NOT NULL,
            sender VARCHAR(255) NOT NULL,
            text MEDIUMTEXT,
            created DATETIME NULL,
            INDEX idx_group_title (group_title),
            UNIQUE KEY uq_group_message (group_title, message_id)
        )",
    )
    .await?;

    Ok(())
}

struct GroupInfo {
    group_id: String,
    title: String,
    group_type: String,
}

struct MessageInfo {
    message_id: i64,
    sender: String,
    text: String,
    created: String,
}

async fn save_groups(pool: &Pool, groups: &[GroupInfo]) -> Result<()> {
    if groups.is_empty() {
        return Ok(());
    }
    let mut conn = pool.get_conn().await?;
    let mut values: Vec<mysql_async::Value> = Vec::with_capacity(groups.len() * 3);
    for group in groups {
        values.push(Value::from(group.group_id.clone()));
        values.push(Value::from(group.title.clone()));
        values.push(Value::from(group.group_type.clone()));
    }
    let placeholders = vec!["(?, ?, ?)"; groups.len()].join(", ");
    let sql = format!(
        "INSERT INTO telegram_groups (group_id, title, group_type) VALUES {}
         ON DUPLICATE KEY UPDATE title = VALUES(title), group_type = VALUES(group_type)",
        placeholders
    );
    conn.exec_drop(&sql, Params::Positional(values)).await?;
    Ok(())
}

async fn save_messages(pool: &Pool, group_title: &str, messages: &[MessageInfo]) -> Result<()> {
    if messages.is_empty() {
        return Ok(());
    }
    let mut conn = pool.get_conn().await?;
    let chunk_size = 500;
    for chunk in messages.chunks(chunk_size) {
        let mut values: Vec<mysql_async::Value> = Vec::with_capacity(chunk.len() * 5);
        for msg in chunk {
            values.push(Value::from(group_title.to_string()));
            values.push(Value::from(msg.message_id));
            values.push(Value::from(msg.sender.clone()));
            values.push(Value::from(msg.text.clone()));
            values.push(Value::from(msg.created.clone()));
        }
        let placeholders = vec!["(?, ?, ?, ?, ?)"; chunk.len()].join(", ");
        let sql = format!(
            "INSERT INTO telegram_messages (group_title, message_id, sender, text, created) VALUES {}
             ON DUPLICATE KEY UPDATE sender = VALUES(sender), text = VALUES(text)",
            placeholders
        );
        conn.exec_drop(&sql, Params::Positional(values)).await?;
    }
    Ok(())
}

fn sender_name(sender: &Peer) -> String {
    match sender {
        Peer::User(u) => u.full_name(),
        Peer::Group(g) => g.title().unwrap_or("").to_string(),
        Peer::Channel(c) => c.title().to_string(),
        Peer::Community(c) => c.title().to_string(),
    }
}

async fn ensure_authorized(client: &Client, api_hash: &str) -> Result<()> {
    if client.is_authorized().await? {
        return Ok(());
    }

    let phone = prompt("Enter your phone number (international format): ")?;
    let token = client.request_login_code(&phone, api_hash).await?;
    let code = prompt("Enter the code you received: ")?;

    match client.sign_in(&token, &code).await {
        Ok(_) => (),
        Err(SignInError::PasswordRequired(password_token)) => {
            let hint = password_token.hint().unwrap_or("None");
            let password = prompt(&format!("Enter 2FA password (hint {}): ", hint))?;
            client.check_password(password_token, password.as_bytes()).await?;
        }
        Err(e) => return Err(anyhow!("Login gagal: {}", e)),
    }

    Ok(())
}


fn jiff_ts_to_epoch_secs(ts: jiff::Timestamp) -> i64 {
    // jiff Timestamp -> string ISO8601 -> chrono parse -> unix timestamp
    let s = ts.to_string();
    chrono::DateTime::parse_from_rfc3339(&s)
        .map(|dt| dt.timestamp())
        .unwrap_or(0)
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .without_time()
        .init();

    dotenv().ok();
    let config = Config::from_env();

    if config.api_id == 0 || config.api_hash.is_empty() {
        return Err(anyhow!("TELEGRAM_API_ID / TELEGRAM_API_HASH belum diisi di .env"));
    }

    tracing::info!("Starting Telegram group reader (Rust)...");

    let session = Arc::new(SqliteSession::open(&config.session).await?);
    let SenderPool { runner, handle, .. } = SenderPool::new(Arc::clone(&session), config.api_id as i32);
    let client = Client::new(handle);
    let _ = tokio::spawn(runner.run());

    ensure_authorized(&client, &config.api_hash).await?;
    tracing::info!("Telegram client authorized");

    let mysql_url = format!(
        "mysql://{}:{}@{}:{}/{}",
        config.mysql_user, config.mysql_password,
        config.mysql_host, config.mysql_port, config.mysql_db
    );
    let pool = Pool::new(Opts::from_url(&mysql_url)?);
    ensure_schema(&pool).await?;
    tracing::info!("MySQL schema ready");

    let cutoff_secs = compute_cutoff_secs(SYNC_DAYS);
    let mut dialogs = client.iter_dialogs();
    let mut all_groups: Vec<GroupInfo> = Vec::new();
    let mut total_messages: u64 = 0;

    while let Some(dialog) = retryable_dialog_next(&mut dialogs).await? {
        let peer = dialog.peer();
        let peer_type = match peer {
            Peer::User(_) => continue,
            Peer::Group(_) => "group",
            Peer::Channel(_) => "channel",
            Peer::Community(_) => "group",
        };

        if !is_group_or_channel(peer_type) {
            continue;
        }

        let title = peer.name().unwrap_or("").to_string();
        all_groups.push(GroupInfo {
            group_id: peer.id().to_string(),
            title: title.clone(),
            group_type: group_type_from_peer(peer_type).to_string(),
        });

        tracing::info!("Processing: {} ({})", title, peer_type);

        let mut iter = client.iter_messages(dialog.peer_ref());
        let mut messages: Vec<MessageInfo> = Vec::new();

        while let Some(msg) = retryable_message_next(&mut iter).await? {
            let msg_secs = jiff_ts_to_epoch_secs(msg.date()) + 8 * 3600;
            if msg_secs < cutoff_secs {
                break;
            }

            let sender = msg.sender().map(sender_name).unwrap_or_default();
            let created = chrono::DateTime::from_timestamp(jiff_ts_to_epoch_secs(msg.date()), 0)
                .unwrap_or_default()
                .format("%Y-%m-%d %H:%M:%S")
                .to_string();

            messages.push(MessageInfo {
                message_id: msg.id() as i64,
                sender,
                text: msg.text().to_string(),
                created,
            });
        }

        total_messages += messages.len() as u64;
        tracing::info!("  {} pesan", messages.len());

        if !messages.is_empty() {
            save_messages(&pool, &title, &messages).await?;
        }
    }

    if !all_groups.is_empty() {
        save_groups(&pool, &all_groups).await?;
    }

    tracing::info!(
        "Sync selesai: {} group, {} pesan tersimpan (upsert).",
        all_groups.len(),
        total_messages
    );

    Ok(())
}
