import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

styles_xml = z.read('word/styles.xml').decode('utf-8')

# Get Caption style size
caption_match = re.search(r'<w:style[^>]*w:styleId="Caption"[^>]*>.*?</w:style>', styles_xml, re.DOTALL)
caption_size = 11.0  # confirmed from previous check

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

caption_keywords = ['menunjukkan', 'memperlihatkan', 'menggambarkan', 'terlihat', 'adalah', 'dapat']

sudah_11 = []
belum_11 = []

for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if re.match(r'^Gambar\s+\d+\.\d+', full_text) and not re.search(r'\d{2}$', full_text):
        is_body = len(full_text) > 100 or any(kw in full_text.lower() for kw in caption_keywords)
        if is_body:
            continue

        # Check if uses Caption style
        styles = re.findall(r'<w:pStyle w:val="([^"]+)"/>', p)
        uses_caption_style = 'Caption' in styles

        # Check explicit sz in paragraph
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]

        if uses_caption_style and not sizes_pt:
            sudah_11.append((full_text, 'Caption style (11pt)'))
        elif sizes_pt and all(s == 11.0 for s in sizes_pt):
            sudah_11.append((full_text, '11pt eksplisit'))
        elif sizes_pt:
            belum_11.append((full_text, ', '.join(str(s) for s in sorted(set(sizes_pt)))))
        else:
            belum_11.append((full_text, 'default(12pt)'))

print(f'=== SUDAH 11pt ({len(sudah_11)}) ===')
for text, size in sudah_11:
    print(f'  {text[:75]}')

print()
print(f'=== BELUM 11pt ({len(belum_11)}) ===')
for text, size in belum_11:
    print(f'  [{size}] {text[:75]}')
