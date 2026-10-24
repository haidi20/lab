import zipfile, re, sys, io, os, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
print('Modified:', datetime.datetime.fromtimestamp(os.path.getmtime(path)).isoformat())
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')
styles_xml = z.read('word/styles.xml').decode('utf-8')
caption = re.search(r'<w:style[^>]*w:styleId="Caption"[^>]*>.*?</w:style>', styles_xml, re.DOTALL)
print('Caption style sz:', re.findall(r'<w:sz w:val="(\d+)"/>', caption.group()) if caption else None)
paragraphs = re.findall(r'<w:p\b[^>]*>.*?</w:p>', xml, re.DOTALL)
for i,p in enumerate(paragraphs):
    text = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)).strip()
    if text in ('Tabel 2.1 Kajian Pustaka','Tabel 2.1 Kajian Pustaka (Lanjutan)'):
        print('\nTEXT:', text)
        print('STYLE:', re.findall(r'<w:pStyle w:val="([^"]+)"/>', p))
        print('RUN SIZES:', [int(v)/2 for v in re.findall(r'<w:sz w:val="(\d+)"/>', p)])
        print('XML:', p[:1200])
