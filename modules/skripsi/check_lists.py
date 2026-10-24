import zipfile, re, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')
numbering_xml = z.read('word/numbering.xml').decode('utf-8') if 'word/numbering.xml' in z.namelist() else ''

# Map numId to format (bullet vs decimal)
num_formats = {}
if numbering_xml:
    # abstractNumId mapping
    num_map = {}
    for m in re.finditer(r'<w:num w:numId="(\d+)"[^>]*>\s*<w:abstractNumId w:val="(\d+)"/>', numbering_xml):
        num_map[m.group(1)] = m.group(2)
    for m in re.finditer(r'<w:abstractNum w:abstractNumId="(\d+)"[^>]*>(.*?)</w:abstractNum>', numbering_xml, re.DOTALL):
        aid, body = m.groups()
        lvl0 = re.search(r'<w:lvl w:ilvl="0"[^>]*>(.*?)</w:lvl>', body, re.DOTALL)
        if lvl0:
            fmt = re.search(r'<w:numFmt w:val="([^"]+)"/>', lvl0.group(1))
            if fmt:
                num_formats[aid] = fmt.group(1)

print('=== FORMAT NUMBERING YANG TERSEDIA ===')
for aid, fmt in sorted(num_formats.items(), key=lambda x: int(x[0])):
    print(f'  abstractNum {aid}: {fmt}')
print()

# Find paragraphs with numbering
paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)
bullet_paras = []
number_paras = []

for p in paragraphs:
    numm = re.search(r'<w:numPr>.*?<w:numId w:val="(\d+)"/>.*?</w:numPr>', p, re.DOTALL)
    if numm:
        numid = numm.group(1)
        aid = num_map.get(numid)
        fmt = num_formats.get(aid, 'unknown')
        texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
        full_text = ''.join(texts).strip()
        if fmt == 'bullet':
            bullet_paras.append((full_text, numid))
        else:
            number_paras.append((full_text, numid, fmt))

print(f'=== PARAGRAF DENGAN BULLET (bulat): {len(bullet_paras)} ===')
for text, numid in bullet_paras:
    print(f'  [{numid}] {text[:90]}')
print()
print(f'=== PARAGRAF DENGAN NUMBERING (angka/huruf): {len(number_paras)} ===')
for text, numid, fmt in number_paras[:30]:
    print(f'  [{numid}|{fmt}] {text[:90]}')
if len(number_paras) > 30:
    print(f'  ... dan {len(number_paras)-30} lagi')
