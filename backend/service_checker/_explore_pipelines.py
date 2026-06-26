import os

path = r'H:\Projects\PKB_neuroassistant_develop\backend\service_checker\pipelines'
for f in sorted(os.listdir(path)):
    fpath = os.path.join(path, f)
    size = os.path.getsize(fpath)
    print(f"{f} ({size} bytes)")
