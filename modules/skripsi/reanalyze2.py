import zipfile, re, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'G:\My Drive\tugas kuliah\STMIK\skripsi\share\17. LAPORAN FULL V2.6.docx'
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8')

all_sizes = re.findall(r'<w:sz w:val="(\d+)"/>', xml)
all_sizes_pt = [int(s)/2 for s in all_sizes]
print('=== SEMUA UKURAN FONT DI DOKUMEN ===')
print(Counter(all_sizes_pt))
print()

tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.DOTALL)
print('=== TABEL 17-20 (Detail) ===')
for t_idx in [16, 17, 18, 19]:
    tbl = tables[t_idx]
    rfonts = re.findall(r'<w:rFonts[^/]*/>', tbl)
    sz = re.findall(r'<w:sz[^/]*/>', tbl)
    szcs = re.findall(r'<w:szCs[^/]*/>', tbl)
    styles = re.findall(r'<w:pStyle w:val="([^"]+)"/>', tbl)
    print(f'Tabel {t_idx+1}:')
    print(f'  rFonts: {rfonts[:3]}')
    print(f'  sz: {sz[:5]}')
    print(f'  szCs: {szcs[:5]}')
    print(f'  pStyle: {styles[:3]}')
    print()

texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml)
full = ''.join(texts)
print('=== CEK TYPO ===')
print(f'"Tenik" ditemukan: {"Tenik" in full}')
print(f'"Teknik" ditemukan: {"Teknik" in full}')
print(f'"Celcius" ditemukan: {"Celcius" in full}')
print(f'"Celsius" ditemukan: {"Celsius" in full}')
ph_pattern = re.compile(r"PH\s")
ph_match = ph_pattern.search(full)
print(f'"PH " (kapital): ditemukan = {bool(ph_match)}')
if ph_match:
    idx = ph_match.start()
    print(f'  Context: ...{full[max(0,idx-30):idx+50]}...')
print(f'"pH" ditemukan: {"pH" in full}')
print()

print(f'URL ganda ditemukan: {"https://www. https" in full}')
