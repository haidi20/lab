import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'D:\learns\random\panduan_text.txt', 'r', encoding='utf-8') as f:
    text = f.read()
# Find the table caption rule
idx = text.find('Judul tabel yang ditulis setelah nomor tabel')
if idx == -1:
    idx = text.find('Judul tabel')
print(text[idx:idx+700])
