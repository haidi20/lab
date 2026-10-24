import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

# Actual captions are short (title only), body text is long sentences
# Filter: caption if text is short (< 100 chars) and doesn't contain common sentence starters
caption_keywords = ['menunjukkan', 'memperlihatkan', 'menggambarkan', 'terlihat', 'adalah', 'dapat']

print('=== JUDUL GAMBAR ASLI YANG BELUM 11pt ===')
print()
count = 0
for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if re.match(r'^Gambar\s+\d+\.\d+', full_text) and not re.search(r'\d{2}$', full_text):
        # Skip body paragraphs (long sentences)
        is_body = len(full_text) > 100 or any(kw in full_text.lower() for kw in caption_keywords)
        if is_body:
            continue
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]
        size_str = ', '.join(str(s) for s in sorted(set(sizes_pt))) if sizes_pt else 'default(12)'
        count += 1
        print(f'  {count}. [{size_str}pt] {full_text}')
