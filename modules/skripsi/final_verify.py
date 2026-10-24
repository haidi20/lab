import zipfile, re, sys, io, os, datetime
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
print('File modified:', datetime.datetime.fromtimestamp(os.path.getmtime(path)).isoformat())
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')
styles_xml = z.read('word/styles.xml').decode('utf-8')

caption_match = re.search(r'<w:style[^>]*w:styleId="Caption"[^>]*>.*?</w:style>', styles_xml, re.DOTALL)
caption_size = int(re.findall(r'<w:sz w:val="(\d+)"/>', caption_match.group())[0])/2 if caption_match else None

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)
caption_keywords = ['menunjukkan', 'memperlihatkan', 'menggambarkan', 'terlihat', 'adalah', 'dapat']

def effective_font(p):
    styles = re.findall(r'<w:pPr>.*?<w:pStyle w:val="([^"]+)"/>', p, re.DOTALL)
    base_style = styles[0] if styles else 'Normal'
    base_size = caption_size if base_style == 'Caption' else 12
    run_sizes = []
    for rm in re.finditer(r'<w:r(?:\s[^>]*)?>(.*?)</w:r>', p, re.DOTALL):
        run = rm.group(1)
        if '<w:t' not in run:
            continue
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', run)
        if sizes:
            run_sizes.append(int(sizes[-1])/2)
        else:
            run_sizes.append(base_size)
    if not run_sizes:
        return base_size, base_style
    return Counter(run_sizes).most_common(1)[0][0], base_style

print()
print('=== JUDUL TABEL ===')
t_belum = []
t_sudah = 0
for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if re.match(r'^Tabel\s+\d+\.\d+', full_text) and not re.search(r'\d{2}$', full_text) and len(full_text) <= 100 and not any(kw in full_text.lower() for kw in caption_keywords):
        eff, style = effective_font(p)
        if eff == 11.0:
            t_sudah += 1
        else:
            t_belum.append((full_text, eff, style))
print(f'Sudah 11pt: {t_sudah}')
for t, eff, style in t_belum:
    print(f'  ❌ [{eff:g}pt | {style}] {t[:75]}')
if not t_belum:
    print('✅ SEMUA sudah 11pt')

print()
print('=== JUDUL GAMBAR ===')
g_belum = []
g_sudah = 0
for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if re.match(r'^Gambar\s+\d+\.\d+', full_text) and not re.search(r'\d{2}$', full_text) and len(full_text) <= 100 and not any(kw in full_text.lower() for kw in caption_keywords):
        eff, style = effective_font(p)
        if eff == 11.0:
            g_sudah += 1
        else:
            g_belum.append((full_text, eff, style))
print(f'Sudah 11pt: {g_sudah}')
for t, eff, style in g_belum:
    print(f'  ❌ [{eff:g}pt | {style}] {t[:75]}')
if not g_belum:
    print('✅ SEMUA sudah 11pt')

print()
print('=== URL & TYPO ===')
texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml)
full = ''.join(texts)
url_match = re.search(r'Sumber:\s*(https?://[^\n]{0,120})', full)
if url_match and 'gambar 2.1' in full[max(0,url_match.start()-200):url_match.start()].lower():
    print(f'URL Gambar 2.1: {url_match.group(1)[:80]}')
print('URL ganda:', '❌ MASIH ADA' if 'https://www. https' in full else '✅ diperbaiki')
print('"Tenik":', '❌' if 'Tenik' in full else '✅')
print('"Celcius":', '❌' if 'Celcius' in full else '✅')
