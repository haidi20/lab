import zipfile, re, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

# Find table captions (text starting with "Tabel X.Y") and check their font size
# Search for paragraphs containing "Tabel " followed by number
paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

print('=== JUDUL TABEL (Caption) ===')
for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts)
    if re.match(r'^Tabel\s+\d+\.\d+', full_text.strip()):
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]
        size_counts = Counter(sizes_pt)
        print(f'  "{full_text[:70]}" -> sizes: {dict(size_counts)}')

print()
print('=== JUDUL GAMBAR (Caption) ===')
for p in paragraphs:
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts)
    if re.match(r'^Gambar\s+\d+\.\d+', full_text.strip()):
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]
        size_counts = Counter(sizes_pt)
        print(f'  "{full_text[:70]}" -> sizes: {dict(size_counts)}')
