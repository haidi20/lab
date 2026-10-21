import pymysql

from modules.telegram_group_reader import (
    default_since,
    load_env_file,
    MysqlMessageStore,
    SyncConfig,
    TelethonBackend,
    TelegramGroupReader,
    run_sync,
)


def main() -> None:
    load_env_file()
    config = SyncConfig.from_env()

    db = pymysql.connect(
        host=config.mysql_host,
        port=config.mysql_port,
        user=config.mysql_user,
        password=config.mysql_password,
        database=config.mysql_database,
        charset="utf8mb4",
    )
    store = MysqlMessageStore(db)

    backend = TelethonBackend(
        api_id=config.api_id,
        api_hash=config.api_hash,
        session=config.session,
    )
    reader = TelegramGroupReader(backend=backend, chat_id="")

    since = default_since(days=10)
    result = run_sync(reader, store, since=since)
    print(f"Sync selesai: {result['groups']} group, {result['messages']} pesan tersimpan (upsert).")


if __name__ == "__main__":
    main()
