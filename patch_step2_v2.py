import io, sys

p = r"C:\Users\A802\Desktop\anbos-local\ocr_runtime\commission\steps\step2_text_recognition.py"
s = io.open(p, encoding="utf-8").read()

target = "                'enable_mkldnn': False,"
replacement = "                'enable_mkldnn': True,"

count = s.count(target)
print("found enable_mkldnn=False occurrences:", count)

if count == 0:
    print("already patched to True or not found")
    sys.exit(0)

s_new = s.replace(target, replacement, 1)
io.open(p, "w", encoding="utf-8").write(s_new)
print("PATCHED: changed enable_mkldnn back to True (will use FLAGS_enable_pir_in_executor=0 instead)")
