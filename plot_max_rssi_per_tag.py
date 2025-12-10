import os
import re
import matplotlib.pyplot as plt
import pandas as pd


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


# pandasで全データをまとめて処理
records = []
for csv_path in all_csv_files:
    parts = csv_path.split(os.sep)
    cond_name = parts[-3] if len(parts) >= 4 else ''
    cc = get_cc_from_cond(cond_name)
    if cc is None:
        print(f'  [警告] ccが取得できずスキップ: {csv_path}')
        continue
    csv_name = os.path.basename(csv_path)
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except Exception as e:
        print(f'  [警告] CSV読込失敗: {csv_path}, {e}')
        continue
    for tag in valid_tags:
        tag_df = df[df['tag_alias'].astype(str).str.replace(' ', '').str.replace('　', '') == tag]
        if not tag_df.empty:
            max_rssi = tag_df['rssi'].max()
            records.append({
                'csv': csv_name,
                'cc': cc,
                'tag': tag,
                'label': f'{tag}_{cc}cc',
                'max_rssi': max_rssi
            })

result_df = pd.DataFrame(records)

# x軸ラベルを指定順で並べる
def custom_x_labels():
    labels = []
    for mm in valid_tags:
        for cc in valid_ccs:
            labels.append(f'{mm}_{cc}cc')
    return labels
x_labels = custom_x_labels()
print('x_labels:', x_labels)
print('csvファイル一覧:', result_df["csv"].unique())



# tag_aliasごとに色を固定

color_list = plt.cm.get_cmap('tab10').colors
tag_color_map = {tag: color_list[i%len(color_list)] for i, tag in enumerate(valid_tags)}
marker_list = ['o','s','^','D','v','*','x','+','1','2','3','4','8','p','h']

plt.figure(figsize=(12,10))

# 各csvごとに同じx順で横並びでプロット
csv_names = result_df["csv"].unique()
for i, csv_name in enumerate(csv_names):
    df_csv = result_df[result_df["csv"] == csv_name]
    for j, label in enumerate(x_labels):
        row = df_csv[df_csv["label"] == label]
        tag = label.split('_')[0]  # 例: '40mm_0cc' → '40mm'
        if not row.empty:
            y = row["max_rssi"].values[0]
            plt.scatter(j, y, color=tag_color_map[tag], marker='o')

# 「通信不可」表示
for idx, label in enumerate(x_labels):
    has_data = any((result_df[result_df["label"] == label]["max_rssi"].notnull()))
    if not has_data:
        plt.text(idx, 0, '通信不可', color='red', ha='center', va='bottom', fontsize=10, rotation=90)

plt.xticks(range(len(x_labels)), x_labels, rotation=45)
plt.xlabel('条件_tag_alias')
plt.ylabel('Max RSSI')
plt.title(f'{subject} 各測定ごとの条件・tag_alias別最大RSSI')
 # plt.legend()  # 凡例削除
plt.grid(True)
plt.tight_layout()
output_png = f'max_rssi_plot_{subject}.png'
plt.savefig(output_png)
print(f'グラフを保存しました: {output_png}')
plt.close()
