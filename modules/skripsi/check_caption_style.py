import zipfile, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
styles_xml = z.read('word/styles.xml').decode('utf-8')

# Find the Caption style definition
caption_match = re.search(r'<w:style[^>]*w:styleId="Caption"[^>]*>.*?</w:style>', styles_xml, re.DOTALL)
if caption_match:
    style_def = caption_match.group()
    print('=== STYLE "Caption" ===')
    print(style_def)
    sizes = re.findall(r'<w:sz w:val="(\d+)"/>', style_def)
    if sizes:
        print()
        print(f'Font size: {int(sizes[0])/2} pt')
    else:
        print()
        print('No explicit size in Caption style')
