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


# --- グラフ描画: 各条件ごとに最大5測定分を横並びで表示 ---
csv_names = result_df["csv"].unique()
plt.figure(figsize=(max(12, len(x_labels)*0.8), 6))

# x軸の間隔とオフセット幅を明示的に分ける
x_gap = 3  # x軸の条件間隔
offset_width = 0.3  # 横並びの最大幅（±0.09）
x_pos_list = [j * x_gap for j in range(len(x_labels))]

csv_names = result_df["csv"].unique()
for j, label in enumerate(x_labels):
    # このx軸ラベルに該当する全csvの値を取得
    y_list = []
    for i, csv_name in enumerate(csv_names):
        row = result_df[(result_df["csv"] == csv_name) & (result_df["label"] == label)]
        if not row.empty:
            y_list.append(row["max_rssi"].values[0])
        else:
            y_list.append(None)
    # 横並びオフセット: 5測定なら[-0.24, -0.12, 0, 0.12, 0.24]
    n = len(y_list)
    # Noneでない値だけを抽出
    y_valid = [y for y in y_list if y is not None]
    n_valid = len(y_valid)
    # 実際に値がある測定の中央がx軸の中心に来るようにオフセット計算
    if n_valid > 1:
        offsets_valid = [offset_width * (i - (n_valid-1)/2) for i in range(n_valid)]
    else:
        offsets_valid = [0]
    tag = label.split('_')[0]
    idx_valid = 0
    for i, y in enumerate(y_list):
        if y is not None:
            plt.scatter(x_pos_list[j] + offsets_valid[idx_valid], y, color=tag_color_map[tag], marker='o', s=80, edgecolors='black', linewidth=1.2, alpha=0.8, zorder=3)
            idx_valid += 1
    # 通信不可表示
    if all(v is None for v in y_list):
        plt.text(j, 0, '通信不可', color='red', ha='center', va='bottom', fontsize=10, rotation=90)

offset_width = 0.09  # 横並びの最大幅（±0.09）
x_pos_list = [j * x_gap for j in range(len(x_labels))]
plt.xticks(x_pos_list, x_labels, rotation=45, ha='right', fontsize=12)
plt.xlabel('条件_tag_alias')
plt.ylabel('Max RSSI')
plt.title(f'{subject} 各測定ごとの条件・tag_alias別最大RSSI')
plt.grid(axis='y', alpha=0.3, linestyle='--')
plt.xlim(-x_gap, x_pos_list[-1] + x_gap)
plt.subplots_adjust(left=0.12, right=0.98, bottom=0.22)
plt.tight_layout()
output_png = f'max_rssi_plot_{subject}.png'
plt.savefig(output_png)
print(f'グラフを保存しました: {output_png}')
plt.close()
