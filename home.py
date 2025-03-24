import streamlit as st
from streamlit_antd_components import tree
import h5py
import numpy as np
import matplotlib.pyplot as plt
import io
import os
import json

# 同じディレクトリにある HDFTreeHandler.py をインポート
from HDFTreeHandler import HDFTreeHandler

TEMPLATE_FILE = "template_paths.json"

def set_streamlit_config():
    """
    Streamlit 全体のレイアウトとタイトルを設定。
    """
    st.set_page_config(page_title="HDF Viewer", layout="wide")
    st.title("HDF Viewer")


def get_template_paths():
    """
    テンプレートファイル (template_paths.json) から登録済みのパス一覧を取得。
    存在しない・エラー時には空リストを返す。
    """
    if not os.path.exists(TEMPLATE_FILE):
        return []
    try:
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("paths", [])
    except Exception as e:
        st.error(f"テンプレートファイル読み込みエラー: {e}")
        return []


def save_template_path(new_path):
    """
    ユーザーが追加したパスをテンプレートに保存する。
    """
    paths = get_template_paths()
    if new_path not in paths:
        paths.append(new_path)
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"paths": paths}, f, ensure_ascii=False, indent=4)


def delete_template_path(target):
    """
    テンプレートに登録されているパスを削除する。
    """
    paths = get_template_paths()
    if target in paths:
        paths.remove(target)
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"paths": paths}, f, ensure_ascii=False, indent=4)


def display_template_path_manager():
    """
    登録済みテンプレートパスの一覧表示と、削除ボタンを設置。
    """
    st.markdown("##### 📌 登録済みテンプレートパス")
    stored_paths = get_template_paths()
    if not stored_paths:
        st.info("現在、テンプレートに登録されたパスはありません。")
        return

    for i, path in enumerate(stored_paths, 1):
        cols = st.columns([0.9, 0.1])
        with cols[0]:
            st.code(path, language="bash")
        with cols[1]:
            if st.button("🗑️", key=f"del_{i}"):
                delete_template_path(path)
                st.rerun()


def display_template_save_input():
    """
    新たにテンプレートに登録するパスの入力欄と登録ボタン。
    """
    st.markdown("##### ➕ テンプレートへのパス登録")
    new_path = st.text_input("テンプレートに追加するパスを入力", key="template_input")
    if new_path and st.button("💾 登録"):
        save_template_path(new_path)
        st.rerun()


def get_file_path():
    """
    ユーザーに HDF5 ファイルのパスを入力してもらい、妥当性をチェック。
    """
    file_path = st.text_input("📂 HDF5 ファイルパスを入力")
    if not file_path:
        st.stop()
    if not h5py.is_hdf5(file_path):
        st.warning("指定されたファイルは HDF5 形式ではありません。")
        st.stop()

    filename = os.path.basename(file_path)
    st.markdown(f"##### 選択されたファイル: `{filename}`")
    return file_path


def display_hdf5_tree(handler: HDFTreeHandler):
    """
    HDFTreeHandler から取得した TreeItem のリストを基に、ツリー構造を表示。
    label はフルパス、description は末端名。
    """
    st.markdown("### HDF5 ファイル構造")
    selected_label = tree(
        items=handler.get_treeitems(),  # label=フルパス, description=末端名
        open_all=True,
        checkbox=False,
        show_line=True,
        key="hdf5_tree"
    )

    if selected_label:
        # antd_components.tree は選択したノードの label (ここではフルパス) を返す
        return selected_label
    return None


def display_dataset(file_path, dataset_path):
    """
    ユーザーが選択したフルパス dataset_path に対して、
    HDF5 内のデータセットを読み取り、メタ情報や可視化を行う。
    """
    with h5py.File(file_path, "r") as f:
        if dataset_path not in f:
            st.error(f"パス '{dataset_path}' は HDF5 内に存在しません。")
            return
        dataset = f[dataset_path]

        st.success(f"選択されたノードのフルパス: {selected_label}")

        # Groupの場合はデータが無いので止まる
        if isinstance(dataset, h5py.Group):
            st.warning(dataset.name + ' はグループです。')
            st.stop()

        # データのメタ情報を表示
        st.write(f"データ型 (dtype): `{dataset.dtype}`")
        st.write(f"データの形状 (shape): `{dataset.shape}`")
        st.divider()

        if 1 <= dataset.ndim <= 2:
            display_csv_download(dataset)
            st.divider()

        visualize_dataset(dataset)


def display_csv_download(dataset):
    """
    1次元 or 2次元のデータを CSV ダウンロード可能にする。
    """
    data = dataset[()]
    buf = io.StringIO()
    np.savetxt(buf, data, delimiter=",")
    st.download_button(
        label="📥 CSVダウンロード",
        data=buf.getvalue(),
        file_name="dataset.csv",
        mime="text/csv"
    )


def visualize_dataset(dataset):
    """
    HDF5 の Dataset を簡易的に可視化する。
    次元数 (ndim) ごとに処理を切り替え。
    """
    try:
        ndim = dataset.ndim

        if ndim == 0:
            # スカラー値
            scalar = dataset[()]
            st.write(f"### スカラー値: {scalar}")
            return

        elif ndim == 1:
            # 1次元 → プロット
            data = dataset[()]
            st.write("### 1次元データ")
            fig, ax = plt.subplots()
            ax.plot(data)
            ax.set_title(dataset.name)
            st.pyplot(fig)
            st.write(data)

        elif ndim == 2:
            # 2次元 → heatmap 的に imshow
            data = dataset[()]
            st.write("### 2次元データ")
            fig, ax = plt.subplots()
            im = ax.imshow(data, aspect="auto")
            fig.colorbar(im, ax=ax)
            ax.set_title(dataset.name)
            st.pyplot(fig)
            st.write(data)

        elif ndim == 3:
            # 3次元 → 0次元目をスライダーで選択
            st.write("### 3次元データ（スライス表示）")
            max_idx = dataset.shape[0]
            slice_idx = st.slider("スライス選択 (次元0)", 0, max_idx - 1, 0)
            slice_data = dataset[slice_idx]
            fig, ax = plt.subplots()
            im = ax.imshow(slice_data, aspect="auto")
            fig.colorbar(im, ax=ax)
            ax.set_title(f"{dataset.name} - Slice {slice_idx} / {max_idx}")
            st.pyplot(fig)

        else:
            # 4次元以上は簡易対応
            st.warning(f"{ndim}次元データには現在対応していません。shape: {dataset.shape}")

    except Exception as e:
        st.error(f"可視化中にエラーが発生しました: {e}")


# """
# Streamlit アプリのエントリーポイント。
# テンプレートパス管理と、HDF5 表示機能をまとめて提供する。
# """

set_streamlit_config()

st.divider()
st.header("テンプレートの設定")
display_template_path_manager()
display_template_save_input()

st.divider()
st.header("HDF5 の表示")

# ファイルパスを取得し、HDFTreeHandler を使ってツリー構造を描画
file_path = get_file_path()
handler = HDFTreeHandler(file_path)
st.divider()

tree_col, view_col = st.columns(2)

with tree_col:
    selected_label = display_hdf5_tree(handler)

# 選択されたラベル(=フルパス)を用いて、データセット可視化
with view_col:
    if selected_label:
        display_dataset(file_path, selected_label)
