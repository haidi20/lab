import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

# Show full XML for paragraphs containing "Arduino Development Environment"
for i, p in enumerate(paragraphs):
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if 'Arduino Development Environment' in full_text:
        print(f'--- Paragraf {i+1} ---')
        print(f'Text: "{full_text[:100]}"')
        # Show all sz values
        sizes = re.findall(r'<w:sz w:val="(\d+)"/>', p)
        sizes_pt = [int(s)/2 for s in sizes]
        print(f'Sizes found: {sizes_pt}')
        # Show szCs too
        szcs = re.findall(r'<w:szCs w:val="(\d+)"/>', p)
        szcs_pt = [int(s)/2 for s in szcs]
        print(f'szCs found: {szcs_pt}')
        # Show if there is a pStyle
        styles = re.findall(r'<w:pStyle w:val="([^"]+)"/>', p)
        print(f'pStyle: {styles}')
        # Show raw XML (first 2000 chars)
        print(f'Raw XML (first 2000):')
        print(p[:2000])
        print()
