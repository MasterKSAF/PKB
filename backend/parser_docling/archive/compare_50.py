import json

with open('output_50.json', encoding='utf-8') as f:
    doc = json.load(f)
with open('odo_50.json', encoding='utf-8') as f:
    odo = json.load(f)

d_doc = doc['document']
d_odo = odo['document']

print(f"{'Метрика':30s} {'Docling':>10s} {'ODO':>10s}")
print('-' * 52)
print(f"{'Всего блоков':30s} {len(d_doc['block']):>10d} {len(d_odo['block']):>10d}")
print(f"{'Заголовки (heading)':30s} {sum(1 for b in d_doc['block'] if b['type']=='heading'):>10d} {sum(1 for b in d_odo['block'] if b['type']=='heading'):>10d}")
print(f"{'Параграфы':30s} {sum(1 for b in d_doc['block'] if b['type']=='paragraph'):>10d} {sum(1 for b in d_odo['block'] if b['type']=='paragraph'):>10d}")
print(f"{'Таблицы':30s} {sum(1 for b in d_doc['block'] if b['type']=='table'):>10d} {sum(1 for b in d_odo['block'] if b['type']=='table'):>10d}")
print(f"{'Изображения':30s} {sum(1 for b in d_doc['block'] if b['type']=='image'):>10d} {sum(1 for b in d_odo['block'] if b['type']=='image'):>10d}")
print(f"{'Списки':30s} {sum(1 for b in d_doc['block'] if b['type']=='list'):>10d} {sum(1 for b in d_odo['block'] if b['type']=='list'):>10d}")
print(f"{'Quality confidence':30s} {doc['quality']['confidence']:>10.3f} {odo['quality']['confidence']:>10.3f}")
