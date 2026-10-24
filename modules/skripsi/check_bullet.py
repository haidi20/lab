import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'D:\learns\random\panduan_text.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Search for bullet-related terms
terms = ['bullet', 'bulat', 'simbol', 'symbol', 'daftar berjenjang', 'list', 'penomoran', 'poin']
for term in terms:
    positions = []
    lower = text.lower()
    start = 0
    while True:
        idx = lower.find(term.lower(), start)
        if idx == -1:
            break
        positions.append(idx)
        start = idx + 1
    if positions:
        print(f'=== "{term}" ditemukan di {len(positions)} lokasi ===')
        for pos in positions[:5]:
            ctx = text[max(0,pos-100):pos+150].replace('\n', ' ')
            print(f'  ...{ctx}...')
            print()
