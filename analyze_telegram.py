import pymysql
import re
from collections import defaultdict


AI_KEYWORDS = [
    "ai", "artificial intelligence", "gpt", "chatgpt", "openai", "claude",
    "gemini", "llm", "llama", "mistral", "deepseek", "copilot", "midjourney",
    "stable diffusion", "prompt", "agent", "rag", "fine-tune", "fine tune",
    "embedding", "vector", "transformer", "neural", "machine learning",
    "deep learning", "model", "training", "inference", "gpu", "cuda",
    "ollama", "hugging face", "huggingface", "langchain", "cursor",
    "windsurf", "codex", "copilot", "vibe coding", "mcp", "api",
]

TECH_KEYWORDS = [
    "server", "vps", "cloud", "docker", "kubernetes", "linux", "windows",
    "ubuntu", "debian", "nginx", "apache", "mysql", "postgresql", "mongodb",
    "redis", "database", "sql", "nosql", "python", "javascript", "typescript",
    "golang", "go", "rust", "php", "java", "kotlin", "swift", "flutter",
    "react", "vue", "angular", "next", "nuxt", "node", "express", "laravel",
    "django", "flask", "fastapi", "spring", "git", "github", "gitlab",
    "ci/cd", "devops", "deploy", "hosting", "domain", "dns", "ssl", "https",
    "vpn", "proxy", "firewall", "router", "mikrotik", "network", "bandwidth",
    "latency", "uptime", "backup", "storage", "ssd", "nvme", "ram", "cpu",
    "encryption", "security", "auth", "jwt", "oauth", "token", "blockchain",
    "crypto", "bitcoin", "ethereum", "web3", "nft", "smart contract",
    "iot", "raspberry", "arduino", "sensor", "api", "rest", "graphql",
    "websocket", "grpc", "microservice", "monolith", "queue", "kafka",
    "rabbitmq", "elasticsearch", "kibana", "prometheus", "grafana",
]


def fetch_messages():
    conn = pymysql.connect(
        host="127.0.0.1", user="root", password="",
        database="telegram_data", charset="utf8mb4",
    )
    cursor = conn.cursor()
    cursor.execute(
        "SELECT group_title, sender, text FROM telegram_messages "
        "WHERE text IS NOT NULL AND text != ''"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def classify(text):
    lower = text.lower()
    ai_hits = [kw for kw in AI_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", lower)]
    tech_hits = [kw for kw in TECH_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", lower)]

    if len(ai_hits) >= 2 or (len(ai_hits) >= 1 and len(tech_hits) >= 2):
        return "ai_tech", ai_hits, tech_hits
    if len(tech_hits) >= 3:
        return "tech", [], tech_hits
    return None, [], []


def main():
    rows = fetch_messages()
    print(f"Total messages with text: {len(rows)}")

    ai_messages = []
    tech_messages = []
    term_freq = defaultdict(int)
    group_stats = defaultdict(lambda: {"ai": 0, "tech": 0, "total": 0})

    for group_title, sender, text in rows:
        group_stats[group_title]["total"] += 1
        category, ai_hits, tech_hits = classify(text)
        if category is None:
            continue

        entry = {"group": group_title, "sender": sender, "text": text[:500]}
        if category == "ai_tech":
            ai_messages.append(entry)
            group_stats[group_title]["ai"] += 1
            for kw in ai_hits + tech_hits:
                term_freq[kw] += 1
        elif category == "tech":
            tech_messages.append(entry)
            group_stats[group_title]["tech"] += 1
            for kw in tech_hits:
                term_freq[kw] += 1

    lines = []
    lines.append("# Analisa Diskusi AI & Teknologi dari Grup Telegram")
    lines.append("")
    lines.append(f"> Sumber: {len(rows)} pesan teks dari {len(group_stats)} group")
    lines.append(f"> Teridentifikasi: {len(ai_messages)} pesan AI/tech, {len(tech_messages)} pesan tech")
    lines.append("")

    lines.append("## Topik yang Sering Dibahas")
    lines.append("")
    top_terms = sorted(term_freq.items(), key=lambda x: -x[1])[:30]
    for term, count in top_terms:
        lines.append(f"- **{term}** — disebut {count}x")
    lines.append("")

    lines.append("## Statistik per Group")
    lines.append("")
    lines.append("| Group | Total Pesan | AI/Tech | Tech |")
    lines.append("|---|---|---|---|")
    for group, stats in sorted(group_stats.items(), key=lambda x: -(x[1]["ai"] + x[1]["tech"])):
        if stats["ai"] + stats["tech"] > 0:
            lines.append(f"| {group} | {stats['total']} | {stats['ai']} | {stats['tech']} |")
    lines.append("")

    lines.append("## Pesan AI/Tech Relevan (bukan obrolan biasa)")
    lines.append("")
    seen_groups = set()
    for msg in ai_messages:
        if msg["group"] not in seen_groups:
            seen_groups.add(msg["group"])
            lines.append(f"### {msg['group']}")
            lines.append("")
        clean_text = msg["text"].replace("\n", " ").strip()
        if len(clean_text) < 20:
            continue
        lines.append(f"- **{msg['sender']}**: {clean_text[:300]}")
    lines.append("")

    lines.append("## Pesan Tech Saja (tanpa AI)")
    lines.append("")
    for msg in tech_messages[:50]:
        clean_text = msg["text"].replace("\n", " ").strip()
        if len(clean_text) < 30:
            continue
        lines.append(f"- **[{msg['group']}]** {msg['sender']}: {clean_text[:250]}")
    lines.append("")

    output = "\n".join(lines)
    with open("telegram_ai_analysis.md", "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Written to telegram_ai_analysis.md ({len(output)} chars)")


if __name__ == "__main__":
    main()
