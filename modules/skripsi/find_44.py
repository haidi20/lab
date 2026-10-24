import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

# Find ALL paragraphs containing "Tabel 4.4" and show context
for i, p in enumerate(paragraphs):
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if 'Tabel 4.4' in full_text:
        styles = re.findall(r'<w:pStyle w:val="([^"]+)"/>', p)
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]
        print(f'--- Paragraf {i+1} ---')
        print(f'Text: "{full_text[:90]}"')
        print(f'Style: {styles} | Sizes: {sorted(set(sizes_pt))}')
        # Check if inside a table by looking at surrounding XML
        pos = xml.find(p[:100])
        # Count table opens before this position
        before = xml[:pos]
        opens = before.count('<w:tbl>')
        closes = before.count('</w:tbl>')
        inside_table = opens > closes
        print(f'Inside table: {inside_table}')
        print()
