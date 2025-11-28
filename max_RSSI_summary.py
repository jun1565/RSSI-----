import os
import csv
from collections import defaultdict


# data直下の各被験者フォルダごとに最大RSSIデータを抽出し、被験者ごとに個別CSVファイルを出力
data_dir = 'data'




for subject in os.listdir(data_dir):
    subject_path = os.path.join(data_dir, subject)
    if not os.path.isdir(subject_path):
        continue
    print(f"被験者: {subject}")
    # 測定条件フォルダ（例: 300cc_supine_120mm）を探索
    for cond_folder in os.listdir(subject_path):
        cond_path = os.path.join(subject_path, cond_folder)
        if not os.path.isdir(cond_path):
            continue
        print(f"  測定条件: {cond_folder}")
        # 測定日時フォルダ（例: 20251128-154231）を取得
        measure_dirs = [os.path.join(cond_path, d) for d in os.listdir(cond_path) if os.path.isdir(os.path.join(cond_path, d))]
        measure_dirs = sorted(measure_dirs)
        print(f"    測定日時フォルダ数: {len(measure_dirs)}")

        # tag_aliasごと・測定ごとに最大RSSIデータを格納（測定回数分動的にリスト生成）
        tag_measure_data = defaultdict(list)

        for idx, measure_dir in enumerate(measure_dirs):
            print(f"      測定日時: {os.path.basename(measure_dir)}")
            tag_max = dict()
            # 測定日時フォルダ内の全CSVファイルを探索
            csv_found = False
            for file in os.listdir(measure_dir):
                if file.endswith('.csv'):
                    csv_found = True
                    filepath = os.path.join(measure_dir, file)
                    print(f"        CSVファイル: {file}")
                    try:
                        with open(filepath, encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                tag_alias = row.get('tag_alias')
                                rssi = float(row.get('rssi', '-9999'))
                                current = tag_max.get(tag_alias)
                                if current is None or rssi > current['rssi']:
                                    tag_max[tag_alias] = {
                                        'rssi': rssi,
                                        'arm_x': row.get('arm_x'),
                                        'arm_y': row.get('arm_y'),
                                        'arm_z': row.get('arm_z'),
                                        'elapsed_time': row.get('elapsed_time')
                                    }
                    except Exception as e:
                        print(f"        Error reading {filepath}: {e}")
            if not csv_found:
                print(f"        CSVファイルが見つかりません")
            # 各tag_aliasごとに最大値をリストに追加
            for tag_alias, d in tag_max.items():
                while len(tag_measure_data[tag_alias]) < idx:
                    tag_measure_data[tag_alias].append(None)
                tag_measure_data[tag_alias].append(d)
            # 測定回にデータがないtag_aliasにもNoneを追加
            for tag_alias in tag_measure_data:
                if len(tag_measure_data[tag_alias]) < idx+1:
                    tag_measure_data[tag_alias].append(None)

        # CSV出力（tag_alias, number, max_rssi, arm_x, arm_y, arm_z, elapsed_time）
        output_csv = os.path.abspath(f'max_rssi_{subject}_{cond_folder}.csv')
        print(f"  出力: {output_csv}")
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            header = ['tag_alias', 'number', 'max_rssi', 'arm_x', 'arm_y', 'arm_z', 'elapsed_time']
            writer.writerow(header)
            max_len = max(len(data_list) for data_list in tag_measure_data.values()) if tag_measure_data else 0
            for tag_alias, data_list in tag_measure_data.items():
                for idx in range(max_len):
                    d = data_list[idx] if idx < len(data_list) else None
                    writer.writerow([
                        tag_alias,
                        idx+1,
                        d['rssi'] if d else '',
                        d['arm_x'] if d else '',
                        d['arm_y'] if d else '',
                        d['arm_z'] if d else '',
                        d['elapsed_time'] if d else ''
                    ])

    # CSV出力（tag_alias, number, max_rssi, arm_x, arm_y, arm_z, elapsed_time）
    output_csv = f'max_rssi_{subject}.csv'
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['tag_alias', 'number', 'max_rssi', 'arm_x', 'arm_y', 'arm_z', 'elapsed_time']
        writer.writerow(header)
        # 測定回数の最大値を取得
        max_len = max(len(data_list) for data_list in tag_measure_data.values()) if tag_measure_data else 0
        for tag_alias, data_list in tag_measure_data.items():
            # 測定回数分ループ（必ず1からmax_lenまで）
            for idx in range(max_len):
                d = data_list[idx] if idx < len(data_list) else None
                writer.writerow([
                    tag_alias,
                    idx+1,
                    d['rssi'] if d else '',
                    d['arm_x'] if d else '',
                    d['arm_y'] if d else '',
                    d['arm_z'] if d else '',
                    d['elapsed_time'] if d else ''
                ])