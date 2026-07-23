import io, sys

p = r"C:\Users\A802\Desktop\anbos-local\ocr_runtime\commission\steps\step2_text_recognition.py"
s = io.open(p, encoding="utf-8").read()

marker = "'device': self.processing_params['device']"
occ = s.count(marker)
print("occurrences of marker:", occ)

if s.count("enable_mkldnn") >= 2:
    print("already patched (enable_mkldnn appears >=2 times)")
    sys.exit(0)

# Only replace the FIRST occurrence (which is inside ocr_params, 3.x path).
idx = s.find(marker)
if idx == -1:
    print("marker not found, abort")
    sys.exit(1)

replacement = marker + ",\n                'enable_mkldnn': False,"
s_new = s[:idx] + s[idx:].replace(marker, replacement, 1)

io.open(p, "w", encoding="utf-8").write(s_new)
print("PATCHED: inserted enable_mkldnn=False into ocr_params (first occurrence only)")
