import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

# Find all 11pt and 14pt font usages with context
paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

print('=== LOKASI FONT 11pt ===')
for p in paragraphs:
    if '<w:sz w:val="22"/>' in p:
        texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
        full_text = ''.join(texts).strip()
        print(f'  "{full_text[:80]}"')

print()
print('=== LOKASI FONT 14pt ===')
for p in paragraphs:
    if '<w:sz w:val="28"/>' in p:
        texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
        full_text = ''.join(texts).strip()
        print(f'  "{full_text[:80]}"')

print()
print('=== LOKASI FONT 12pt (eksplisit) ===')
for p in paragraphs:
    if '<w:sz w:val="24"/>' in p:
        texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
        full_text = ''.join(texts).strip()
        if full_text:
            print(f'  "{full_text[:80]}"')
