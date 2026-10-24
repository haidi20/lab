import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')
numbering_xml = z.read('word/numbering.xml').decode('utf-8')

num_map = {}
for m in re.finditer(r'<w:num w:numId="(\d+)"[^>]*>\s*<w:abstractNumId w:val="(\d+)"/>', numbering_xml):
    num_map[m.group(1)] = m.group(2)
num_formats = {}
for m in re.finditer(r'<w:abstractNum w:abstractNumId="(\d+)"[^>]*>(.*?)</w:abstractNum>', numbering_xml, re.DOTALL):
    aid, body = m.groups()
    lvl0 = re.search(r'<w:lvl w:ilvl="0"[^>]*>(.*?)</w:lvl>', body, re.DOTALL)
    if lvl0:
        fmt = re.search(r'<w:numFmt w:val="([^"]+)"/>', lvl0.group(1))
        if fmt:
            num_formats[aid] = fmt.group(1)

paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)

in_section = False
for i, p in enumerate(paragraphs):
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    full_text = ''.join(texts).strip()
    if '4.3.3' in full_text and 'Rancangan Pengujian' in full_text:
        in_section = True
    elif '4.3.4' in full_text:
        break
    if in_section and full_text:
        numm = re.search(r'<w:numPr>.*?<w:numId w:val="(\d+)"/>.*?</w:numPr>', p, re.DOTALL)
        ilvl = re.search(r'<w:ilvl w:val="(\d+)"/>', p)
        marker = '  '
        if numm:
            numid = numm.group(1)
            aid = num_map.get(numid)
            fmt = num_formats.get(aid, '?')
            level = ilvl.group(1) if ilvl else '0'
            marker = f'[{fmt}|L{level}]'
        print(f'{marker} {full_text[:100]}')
