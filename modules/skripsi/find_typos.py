import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

# Find all occurrences of ESP32 followed by anything
# Show the raw XML around ESP32 mentions
for m in re.finditer(r'ESP32', xml):
    idx = m.start()
    # Get surrounding 200 chars of raw XML
    start = max(0, idx-100)
    end = min(len(xml), idx+200)
    snippet = xml[start:end]
    # Check if followed by 68 or 66
    after = xml[idx+5:idx+10]
    if '68' in after or '66' in after:
        print(f'=== Found ESP32 followed by 68/66 at XML pos {idx} ===')
        print(f'Raw XML: {snippet}')
        print()

# Also search for "ESP32" in the flattened text (without page breaks)
texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml)
full = ''.join(texts)
for m in re.finditer(r'ESP32\d*', full):
    print(f'Text: "{m.group()}" at pos {m.start()}')
    ctx_start = max(0, m.start()-50)
    ctx_end = min(len(full), m.end()+50)
    print(f'  Context: ...{full[ctx_start:ctx_end]}...')
    print()
