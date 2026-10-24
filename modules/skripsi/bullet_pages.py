import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')
numbering_xml = z.read('word/numbering.xml').decode('utf-8') if 'word/numbering.xml' in z.namelist() else ''

# Map numId to format
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

# Track pages with lastRenderedPageBreak
pattern = r'(<w:lastRenderedPageBreak\s*/?>)|(<w:br w:type="page"[^>]*/>)|(<w:t[^>]*>([^<]*)</w:t>)|(<w:numPr>.*?<w:numId w:val="(\d+)"/>.*?</w:numPr>)'
tokens = re.findall(pattern, xml, re.DOTALL)

page = 1
results = []
current_numid = None
current_text = ''

for token in tokens:
    if token[0] or token[1]:
        page += 1
panic = False
# Simpler approach: iterate over paragraph blocks with page tracking
paragraphs_with_pos = []
for m in re.finditer(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL):
    paragraphs_with_pos.append((m.start(), m.group()))

# Page breaks positions
page_breaks = [m.start() for m in re.finditer(r'<w:lastRenderedPageBreak\s*/?>|<w:br w:type="page"[^>]*/>', xml)]

def get_page(pos):
    page = 1
    for bp in page_breaks:
        if bp < pos:
            page += 1
        else:
            break
    return page

bullet_pages = {}
for pos, p in paragraphs_with_pos:
    numm = re.search(r'<w:numPr>.*?<w:numId w:val="(\d+)"/>.*?</w:numPr>', p, re.DOTALL)
    if numm:
        numid = numm.group(1)
        aid = num_map.get(numid)
        fmt = num_formats.get(aid, 'unknown')
        if fmt == 'bullet':
            texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
            full_text = ''.join(texts).strip()
            pg = get_page(pos)
            if pg not in bullet_pages:
                bullet_pages[pg] = []
            bullet_pages[pg].append(full_text[:80])

print('=== LOKASI LIST BULLET PER HALAMAN ===')
for pg in sorted(bullet_pages):
    print(f'Halaman {pg}:')
    for t in bullet_pages[pg]:
        print(f'  • {t}')
