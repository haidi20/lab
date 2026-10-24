import zipfile, re, sys, io, os
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
print('File modified:', os.path.getmtime(path))
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')
styles_xml = z.read('word/styles.xml').decode('utf-8')

# Resolve style sizes
style_sizes = {}
for match in re.finditer(r'<w:style[^>]*w:styleId="([^"]+)"[^>]*>(.*?)</w:style>', styles_xml, re.DOTALL):
    sid, body = match.groups()
    sizes = re.findall(r'<w:sz w:val="(\d+)"/>', body)
    style_sizes[sid] = int(sizes[-1])/2 if sizes else None
print('Caption style size:', style_sizes.get('Caption'))
print('Default style size:', style_sizes.get('Normal'))
print()

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)
caption_keywords = ['menunjukkan', 'memperlihatkan', 'menggambarkan', 'terlihat', 'adalah', 'dapat']

def effective_font_for_paragraph(p):
    styles = re.findall(r'<w:pPr>.*?<w:pStyle w:val="([^"]+)"/>', p, re.DOTALL)
    base_style = styles[0] if styles else 'Normal'
    base_size = style_sizes.get(base_style, style_sizes.get('Normal', 12))
    # Get direct sizes only from actual text runs
    run_sizes = []
    for rm in re.finditer(r'<w:r(?:\s[^>]*)?>(.*?)</w:r>', p, re.DOTALL):
        run = rm.group(1)
        if '<w:t' not in run:
            continue
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', run)
        if sizes:
            run_sizes.append(int(sizes[-1])/2)
        else:
            run_sizes.append(base_size if base_size else 12)
    if not run_sizes:
        return base_size if base_size else 12, base_style, []
    return Counter(run_sizes).most_common(1)[0][0], base_style, run_sizes

def is_caption_like(text, prefix):
    return bool(re.match(rf'^{prefix}\s+\d+\.\d+', text)) and not re.search(r'\d{2}$', text) and len(text) <= 100 and not any(kw in text.lower() for kw in caption_keywords)

tables = []
images = []
for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if is_caption_like(full_text, 'Tabel'):
        eff, style, runs = effective_font_for_paragraph(p)
        tables.append((full_text, eff, style, runs))
    elif is_caption_like(full_text, 'Gambar'):
        eff, style, runs = effective_font_for_paragraph(p)
        images.append((full_text, eff, style, runs))

print('=== JUDUL TABEL (EFektif) ===')
for text, eff, style, runs in tables:
    print(f'[{eff:g}pt | style={style} | run_sizes={sorted(set(runs))}] {text}')
print(f'Total: {len(tables)}; belum 11pt: {sum(1 for x in tables if x[1] != 11.0)}')
print()

print('=== JUDUL GAMBAR (EFektif) ===')
for text, eff, style, runs in images:
    print(f'[{eff:g}pt | style={style} | run_sizes={sorted(set(runs))}] {text}')
print(f'Total: {len(images)}; belum 11pt: {sum(1 for x in images if x[1] != 11.0)}')
print()

# Typo checks
texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml)
full = ''.join(texts)
print('=== TYPO ===')
print('"Tenik":', 'MASIH ADA' if 'Tenik' in full else 'sudah diperbaiki')
print('"Celcius":', 'MASIH ADA' if 'Celcius' in full else 'sudah diperbaiki')
ph_match = re.search(r'PH\s', full)
print('"PH" kapital:', 'MASIH ADA: ' + full[max(0,ph_match.start()-30):ph_match.end()+40] if ph_match else 'sudah diperbaiki')
print('URL ganda:', 'MASIH ADA' if 'https://www. https' in full else 'sudah diperbaiki')
