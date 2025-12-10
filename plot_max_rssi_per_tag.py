import os
import csv
import re
import matplotlib.pyplot as plt
from collections import defaultdict

# dataディレクトリから被験者名一覧を取得
data_dir = 'data'
subjects = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]

# 被験者選択
print('被験者を選択してください:')
for i, s in enumerate(subjects):
    print(f'{i+1}: {s}')
idx = int(input('番号を入力: ')) - 1
subject = subjects[idx]
print(f'選択: {subject}')

# 試験条件・日付・csv探索
target_dir = os.path.join(data_dir, subject)
all_csv_files = []
for cond in os.listdir(target_dir):
    cond_path = os.path.join(target_dir, cond)
    if not os.path.isdir(cond_path):
        continue
    for date in os.listdir(cond_path):
        date_path = os.path.join(cond_path, date)
        if not os.path.isdir(date_path):
            continue
        for file in os.listdir(date_path):
            if file.endswith('.csv'):
                all_csv_files.append(os.path.join(date_path, file))



valid_tags = ['0mm', '40mm', '80mm', '120mm', '160mm', '200mm']
valid_ccs = ['0', '600']
def is_mm_tag(tag):
    tag = str(tag).replace(' ', '').replace('　', '')
    return tag in valid_tags


# 試験条件ccを取得する関数

# 試験条件ccを取得する関数（先頭に0ccや600ccがある場合に対応）
def get_cc_from_cond(cond_name):
    m = re.match(r'^(\d+)cc', cond_name)
    if m:
        return m.group(1)
    # 先頭以外にもccが含まれる場合
    m2 = re.search(r'(\d+)cc', cond_name)
    if m2:
        return m2.group(1)
    print(f'  [警告] 試験条件ccが取得できません: {cond_name}')
    return None

# x軸ラベル生成とデータ格納
x_labels = []
tag_cc_label_list = [] # [(cc, tag_alias, label)]
cc_tag_set = set()
csv_data = defaultdict(dict) # {csv名: {label: rssi}}


for csv_path in all_csv_files:
    # パス分割内容をデバッグ表示
    parts = csv_path.split(os.sep)
    print(f'csv_path: {csv_path}')
    print(f'parts: {parts}')
    # 試験条件cc取得（data/被験者名/試験条件/日付/ファイル名）
    # 例: parts[-5]=data, parts[-4]=被験者名, parts[-3]=試験条件, parts[-2]=日付, parts[-1]=ファイル名
    cond_name = parts[-3] if len(parts) >= 4 else ''
    cc = get_cc_from_cond(cond_name)
    if cc is None:
        print(f'  [警告] ccが取得できずスキップ: {csv_path}')
        continue
    date_name = parts[-2] if len(parts) >= 3 else ''
    csv_name = os.path.basename(csv_path)
    tag_max = {}
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tag = row.get('tag_alias')
            tag = str(tag).replace(' ', '').replace('　', '')
            if not is_mm_tag(tag):
                continue
            try:
                rssi = float(row.get('rssi', '-9999'))
            except:
                continue
            if tag not in tag_max or rssi > tag_max[tag]:
                tag_max[tag] = rssi
    # x軸ラベル生成
    for tag in valid_tags:
        label = f'{tag}_{cc}cc'
        cc_tag_set.add(label)
        if tag in tag_max:
            csv_data[csv_name][label] = tag_max[tag]

# x軸ラベルを指定順で並べる
def label_sort_key(label):
    m = re.match(r'(\d+)cc_(\d+)mm', label)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return (float('inf'), float('inf'))

def custom_x_labels():
    labels = []
    for mm in valid_tags:
        for cc in valid_ccs:
            labels.append(f'{mm}_{cc}cc')
    return labels
x_labels = custom_x_labels()
print('x_labels:', x_labels)
print('csv_data keys:', list(csv_data.keys()))
for k, v in csv_data.items():
    print(f'csv: {k}, data: {v}')



# tag_aliasごとに色を固定
import itertools
color_list = plt.cm.get_cmap('tab10').colors
tag_color_map = {tag: color_list[i%len(color_list)] for i, tag in enumerate(valid_tags)}
marker_list = ['o','s','^','D','v','*','x','+','1','2','3','4','8','p','h']

plt.figure(figsize=(12,10))



# プロットが重ならないようにオフセットを与えて横に並べる
num_csv = len(csv_data)
offsets = []
if num_csv > 1:
    step = 0.6 / (num_csv-1) if num_csv > 1 else 0
    offsets = [(-0.3 + i*step) for i in range(num_csv)]
else:
    offsets = [0]

csv_names = list(csv_data.keys())
for tag in valid_tags:
    for cc in valid_ccs:
        label = f'{tag}_{cc}cc'
        for i, csv_name in enumerate(csv_names):
            y = csv_data[csv_name].get(label, None)
            if y is not None:
                x_pos = x_labels.index(label) + offsets[i]
                plt.scatter(x_pos, y, color=tag_color_map[tag], marker='o', s=100, label=f'{csv_name}' if tag==valid_tags[0] else None)

# 「通信不可」表示
for idx, label in enumerate(x_labels):
    has_data = any(csv_data[csv_name].get(label, None) is not None for csv_name in csv_data.keys())
    if not has_data:
        plt.text(idx, 0, '通信不可', color='red', ha='center', va='bottom', fontsize=10, rotation=90)

plt.xticks(range(len(x_labels)), x_labels, rotation=45)
plt.xlabel('条件_tag_alias')
plt.ylabel('Max RSSI')
plt.title(f'{subject} 各測定ごとの条件・tag_alias別最大RSSI')
plt.legend()
plt.grid(True)
plt.tight_layout()
output_png = f'max_rssi_plot_{subject}.png'
plt.savefig(output_png)
print(f'グラフを保存しました: {output_png}')
plt.close()
