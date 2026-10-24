import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

# Find paragraphs containing "Tabel 2.1" (not TOC)
for i, p in enumerate(paragraphs):
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if 'Tabel 2.1' in full_text and not re.search(r'\d{2}$', full_text):
        print(f'--- Paragraf {i+1} ---')
        print(f'Text: "{full_text[:100]}"')
        styles = re.findall(r'<w:pStyle w:val="([^"]+)"/>', p)
        print(f'pStyle: {styles}')
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]
        print(f'sz: {sizes_pt}')
        print(f'Raw XML: {p[:800]}')
        print()
