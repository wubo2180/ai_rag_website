import io, sys

p = r"C:\Users\A802\Desktop\anbos-local\ocr_runtime\commission\steps\step2_text_recognition.py"
s = io.open(p, encoding="utf-8").read()

target = "                'enable_mkldnn': True,"
replacement = "                'enable_mkldnn': False,"

count = s.count(target)
print("found enable_mkldnn=True:", count)

if count > 0:
    s_new = s.replace(target, replacement)
    io.open(p, "w", encoding="utf-8").write(s_new)
    print("PATCHED: enable_mkldnn back to False (crash-free mode)")
else:
    print("not found, checking current state...")
    idx = s.find("enable_mkldnn")
    if idx >= 0:
        print(s[idx-20:idx+40])
