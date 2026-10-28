from typing import Any


def load_article(connection: Any, url: str | None = None) -> dict[str, Any]:
    query = (
        "SELECT url, title, source, region, summary, published_at "
        "FROM news_articles WHERE region = 'kaltim' "
        "AND published_date = CURDATE()"
    )
    params: tuple[str, ...] = ()
    if url:
        query += " AND url = %s"
        params = (url,)
    query += " ORDER BY published_at DESC LIMIT 1"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()
    if not row:
        raise LookupError("Artikel Kaltim hari ini tidak ditemukan")
    return dict(row)


def load_latest_kaltim_articles(
    connection: Any,
    limit: int = 3,
    today_only: bool = True,
) -> list[dict[str, Any]]:
    query = (
        "SELECT url, title, source, region, summary, published_at "
        "FROM news_articles WHERE region = 'kaltim' "
        + ("AND published_date = CURDATE() " if today_only else "")
        +
        "ORDER BY published_at DESC LIMIT %s"
    )
    with connection.cursor() as cursor:
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
    if len(rows) < limit:
        raise LookupError(f"Artikel Kaltim hari ini kurang dari {limit}")
    return [dict(row) for row in rows]
