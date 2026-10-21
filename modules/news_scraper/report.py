from datetime import date

from modules.news_scraper.scraper import NewsArticle


def render_markdown(
    articles: list[NewsArticle],
    scrape_date: date,
    errors: list[tuple[str, str]] | None = None,
) -> str:
    lines: list[str] = []
    lines.append("# Berita Hari Ini")
    lines.append("")
    lines.append(f"> Tanggal: {scrape_date.isoformat()} (Asia/Makassar)")
    lines.append(f"> Total artikel: {len(articles)}")
    lines.append("")

    by_source: dict[str, list[NewsArticle]] = {}
    for article in articles:
        by_source.setdefault(article.source, []).append(article)

    for source, items in by_source.items():
        lines.append(f"## {source}")
        lines.append("")
        for article in items:
            time_part = article.published_at.strftime("%H:%M") if article.published_at else "--:--"
            lines.append(f"- [{article.title}]({article.url}) — {time_part}")
        lines.append("")

    if errors:
        lines.append("## Gagal Diambil")
        lines.append("")
        for name, message in errors:
            lines.append(f"- {name}: {message}")
        lines.append("")

    return "\n".join(lines)
