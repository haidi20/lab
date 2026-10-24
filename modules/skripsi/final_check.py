import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')
styles_xml = z.read('word/styles.xml').decode('utf-8')

# Get Caption style size
caption_match = re.search(r'<w:style[^>]*w:styleId="Caption"[^>]*>.*?</w:style>', styles_xml, re.DOTALL)
caption_size = int(re.findall(r'<w:sz w:val="(\d+)"/>', caption_match.group())[0])/2 if caption_match else None
print(f'Caption style size: {caption_size}pt')

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

caption_keywords = ['menunjukkan', 'memperlihatkan', 'menggambarkan', 'terlihat', 'adalah', 'dapat']

print()
print('=== VERIFIKASI JUDUL GAMBAR ===')
print()
all_ok = True
belum = []
for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if re.match(r'^Gambar\s+\d+\.\d+', full_text) and not re.search(r'\d{2}$', full_text):
        is_body = len(full_text) > 100 or any(kw in full_text.lower() for kw in caption_keywords)
        if is_body:
            continue
        styles = re.findall(r'<w:pStyle w:val="([^"]+)"/>', p)
        uses_caption_style = 'Caption' in styles
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]

        if uses_caption_style and not sizes_pt:
            status = 'OK (Caption 11pt)'
        elif sizes_pt and all(s == 11.0 for s in sizes_pt):
            status = 'OK (11pt eksplisit)'
        else:
            status = 'BELUM ('
            status += ', '.join(str(s) for s in sorted(set(sizes_pt))) if sizes_pt else 'default 12pt'
            status += 'pt)'
            belum.append(full_text)
            all_ok = False
        print(f'  {status}: {full_text[:70]}')

print()
if all_ok:
    print('✅ SEMUA judul gambar sudah 11pt')
else:
    print(f'❌ {len(belum)} judul gambar belum 11pt:')
    for t in belum:
        print(f'   - {t[:70]}')

# Also verify table captions
print()
print('=== VERIFIKASI JUDUL TABEL ===')
print()
t_all_ok = True
t_belum = []
for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if re.match(r'^Tabel\s+\d+\.\d+', full_text) and not re.search(r'\d{2}$', full_text):
        is_body = len(full_text) > 100 or any(kw in full_text.lower() for kw in caption_keywords)
        if is_body:
            continue
        styles = re.findall(r'<w:pStyle w:val="([^"]+)"/>', p)
        uses_caption_style = 'Caption' in styles
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]

        if uses_caption_style and not sizes_pt:
            status = 'OK (Caption 11pt)'
        elif sizes_pt and all(s == 11.0 for s in sizes_pt):
            status = 'OK (11pt eksplisit)'
        else:
            status = 'BELUM ('
            status += ', '.join(str(s) for s in sorted(set(sizes_pt))) if sizes_pt else 'default 12pt'
            status += 'pt)'
            t_belum.append(full_text)
            t_all_ok = False
        print(f'  {status}: {full_text[:70]}')

print()
if t_all_ok:
    print('✅ SEMUA judul tabel sudah 11pt')
else:
    print(f'❌ {len(t_belum)} judul tabel belum 11pt:')
    for t in t_belum:
        print(f'   - {t[:70]}')

# Final typo check
print()
print('=== CEK TYPO FINAL ===')
texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml)
full = ''.join(texts)
print(f'"Tenik": {"❌ MASIH ADA" if "Tenik" in full else "✅ Sudah diperbaiki"}')
print(f'"Celcius": {"❌ MASIH ADA" if "Celcius" in full else "✅ Sudah diperbaiki"}')
ph_pattern = re.compile(r"PH\s")
ph_match = ph_pattern.search(full)
print(f'"PH" kapital: {"❌ MASIH ADA di: " + full[max(0,ph_match.start()-20):ph_match.end()+30] if ph_match else "✅ Sudah diperbaiki"}')
print(f'URL ganda: {"❌ MASIH ADA" if "https://www. https" in full else "✅ Sudah diperbaiki"}')
