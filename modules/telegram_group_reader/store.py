from typing import Any

from modules.telegram_group_reader.reader import (
    TelegramGroupInfo,
    TelegramMessage,
)


class MysqlMessageStore:
    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self._create_schema()

    def _create_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_groups (
                group_id VARCHAR(64) PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                group_type VARCHAR(20) NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_messages (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                group_title VARCHAR(255) NOT NULL,
                message_id BIGINT NOT NULL,
                sender VARCHAR(255) NOT NULL,
                text MEDIUMTEXT,
                INDEX idx_group_title (group_title),
                UNIQUE KEY uq_group_message (group_title, message_id)
            )
            """
        )
        self._connection.commit()

    def save_group(self, group: TelegramGroupInfo) -> None:
        cursor = self._connection.cursor()
        cursor.executemany(
            """
            INSERT INTO telegram_groups (group_id, title, group_type)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE title = VALUES(title), group_type = VALUES(group_type)
            """,
            [(group.group_id, group.title, group.group_type)],
        )
        self._connection.commit()

    def save_groups(self, groups: list[TelegramGroupInfo]) -> None:
        if not groups:
            return
        cursor = self._connection.cursor()
        cursor.executemany(
            """
            INSERT INTO telegram_groups (group_id, title, group_type)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE title = VALUES(title), group_type = VALUES(group_type)
            """,
            [(group.group_id, group.title, group.group_type) for group in groups],
        )
        self._connection.commit()

    def save_messages(self, group_title: str, messages: list[TelegramMessage]) -> None:
        cursor = self._connection.cursor()
        cursor.executemany(
            """
            INSERT INTO telegram_messages (group_title, message_id, sender, text)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE sender = VALUES(sender), text = VALUES(text)
            """,
            [(group_title, m.message_id, m.sender, m.text) for m in messages],
        )
        self._connection.commit()

    def load_messages(self, group_title: str) -> list[TelegramMessage]:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            SELECT message_id, sender, text
            FROM telegram_messages
            WHERE group_title = %s
            ORDER BY message_id
            """,
            (group_title,),
        )
        return [
            TelegramMessage(message_id=row[0], sender=row[1], text=row[2] or "")
            for row in cursor.fetchall()
        ]
