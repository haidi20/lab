import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

print('=== SEMUA JUDUL GAMBAR (Caption) ===')
print()
belum_11 = []
sudah_11 = []

for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    # Match image captions (skip TOC entries with page numbers)
    if re.match(r'^Gambar\s+\d+\.\d+', full_text) and not re.search(r'\d{2}$', full_text):
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]
        if sizes_pt:
            size_str = ', '.join(str(s) for s in sorted(set(sizes_pt)))
            if all(s == 11.0 for s in sizes_pt):
                sudah_11.append((full_text, size_str))
            else:
                belum_11.append((full_text, size_str))
        else:
            belum_11.append((full_text, 'default(12)'))

print(f'--- SUDAH 11pt ({len(sudah_11)}) ---')
for text, size in sudah_11:
    print(f'  [{size}pt] {text[:75]}')

print()
print(f'--- BELUM 11pt ({len(belum_11)}) ---')
for text, size in belum_11:
    print(f'  [{size}pt] {text[:75]}')
