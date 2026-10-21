import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TelegramMessage:
    message_id: int
    sender: str
    text: str
    date: datetime | None = None


@dataclass(frozen=True)
class TelegramGroupInfo:
    group_id: str
    title: str
    group_type: str


class InMemoryTelegramBackend:
    def __init__(
        self,
        messages: list[TelegramMessage],
        groups: list[TelegramGroupInfo] | None = None,
        messages_by_group: dict[str, list[TelegramMessage]] | None = None,
    ) -> None:
        self._messages = messages
        self._groups = groups or []
        self._messages_by_group = messages_by_group or {}

    def fetch_messages(self, chat_id: str, since: datetime | None = None) -> list[TelegramMessage]:
        if self._messages_by_group:
            messages = list(self._messages_by_group.get(chat_id, []))
        else:
            messages = list(self._messages)
        if since is not None:
            messages = [m for m in messages if m.date is not None and m.date >= since]
        return messages

    def fetch_groups(self) -> list[TelegramGroupInfo]:
        return list(self._groups)


class TelethonBackend:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session: str = "telegram_group_reader",
        client: Any = None,
    ) -> None:
        self._api_id = api_id
        self._api_hash = api_hash
        self._session = session
        self._client = client

    def _ensure_client(self) -> Any:
        if self._client is None:
            from telethon import TelegramClient

            self._client = TelegramClient(self._session, self._api_id, self._api_hash)
        return self._client

    def fetch_messages(self, chat_id: str, since: datetime | None = None) -> list[TelegramMessage]:
        client = self._ensure_client()
        if not client.is_connected():
            client.start()
        return client.loop.run_until_complete(self._collect_messages(client, chat_id, since))

    async def _collect_messages(self, client: Any, chat_id: str, since: datetime | None = None) -> list[TelegramMessage]:
        messages: list[TelegramMessage] = []
        target: Any = chat_id
        if isinstance(chat_id, str) and chat_id.lstrip("-").isdigit():
            target = int(chat_id)
        async for message in client.iter_messages(target):
            if since is not None and message.date is not None and message.date < since:
                break
            sender_name = await self._resolve_sender_name(message)
            messages.append(
                TelegramMessage(
                    message_id=message.id,
                    sender=sender_name,
                    text=message.text or "",
                    date=message.date,
                )
            )
        return messages

    async def _resolve_sender_name(self, message: Any) -> str:
        sender = await message.get_sender()
        if sender is None:
            return ""
        title = getattr(sender, "title", None)
        if title:
            return title
        first_name = getattr(sender, "first_name", "") or ""
        last_name = getattr(sender, "last_name", "") or ""
        return f"{first_name} {last_name}".strip()

    def fetch_groups(self) -> list[TelegramGroupInfo]:
        client = self._ensure_client()
        if not client.is_connected():
            client.start()
        return client.loop.run_until_complete(self._collect_groups(client))

    async def _collect_groups(self, client: Any) -> list[TelegramGroupInfo]:
        groups: list[TelegramGroupInfo] = []
        async for dialog in client.iter_dialogs():
            if not dialog.is_group and not dialog.is_channel:
                continue
            entity = dialog.entity
            group_type = "channel" if getattr(entity, "broadcast", False) else "group"
            groups.append(
                TelegramGroupInfo(
                    group_id=str(dialog.id),
                    title=dialog.name or "",
                    group_type=group_type,
                )
            )
        return groups


class TelegramGroupReader:
    def __init__(self, backend: InMemoryTelegramBackend, chat_id: str) -> None:
        self._backend = backend
        self._chat_id = chat_id

    def get_all_groups(self) -> list[TelegramGroupInfo]:
        return self._backend.fetch_groups()

    def get_all_messages_from_all_groups(self, since: datetime | None = None) -> dict[str, list[TelegramMessage]]:
        result: dict[str, list[TelegramMessage]] = {}
        for group in self.get_all_groups():
            reader = TelegramGroupReader(self._backend, chat_id=group.group_id)
            result[group.title] = reader.get_all_messages(since=since)
        return result

    def count_messages_all_groups(self) -> int:
        return sum(
            len(messages) for messages in self.get_all_messages_from_all_groups().values()
        )

    def get_all_messages(self, since: datetime | None = None) -> list[TelegramMessage]:
        return self._backend.fetch_messages(self._chat_id, since=since)

    def get_messages_by_sender(self, sender: str) -> list[TelegramMessage]:
        return [m for m in self.get_all_messages() if m.sender == sender]

    def get_messages_by_keyword(self, keyword: str) -> list[TelegramMessage]:
        return [m for m in self.get_all_messages() if keyword.lower() in m.text.lower()]

    def count_messages(self) -> int:
        return len(self.get_all_messages())
