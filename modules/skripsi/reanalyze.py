import zipfile, re, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

# Parse all tables
tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.DOTALL)
print(f'Total tables found: {len(tables)}')
print()

for t_idx, tbl in enumerate(tables):
    sizes = re.findall(r'<w:sz w:val="(\d+)"/>', tbl)
    sizes_pt = [int(s)/2 for s in sizes]
    size_counts = Counter(sizes_pt)

    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', tbl)
    sample_text = ''.join(texts)[:70]

    print(f'--- Tabel {t_idx+1} ---')
    print(f'  Sample: "{sample_text}"')
    print(f'  Font sizes (pt): {dict(size_counts)}')
    print()

# Check default
styles_xml = z.read('word/styles.xml').decode('utf-8')
default_sizes = re.findall(r'<w:docDefaults>.*?</w:docDefaults>', styles_xml, re.DOTALL)
if default_sizes:
    sz_matches = re.findall(r'<w:sz w:val="(\d+)"/>', default_sizes[0])
    if sz_matches:
        print(f'Default font size (docDefaults): {int(sz_matches[0])/2} pt')

# Check table captions
paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)
print()
print('=== JUDUL TABEL (Caption) ===')
for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts)
    if re.match(r'^Tabel\s+\d+\.\d+', full_text.strip()):
        # Skip TOC entries (those have page numbers appended)
        if re.search(r'\d+$', full_text.strip()) and re.search(r'\d{2}$', full_text.strip()):
            continue
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]
        size_counts = Counter(sizes_pt)
        print(f'  "{full_text.strip()[:70]}" -> {dict(size_counts)}')
