import streamlit as st
from streamlit_antd_components import tree, TreeItem

import numpy as np
import matplotlib.pyplot as plt
import io
import os
import json
import h5py

from HDFPath import HDFPath

TEMPLATE_FILE = "template_paths.json"

# ==============================
# Streamlit 設定
# ==============================
def set_streamlit_config():
    st.set_page_config(
        page_title="HDF Viewer",
        layout="wide",
    )
    st.title("HDF Viewer")

# ==============================
# ファイル 関連
# ==============================
def get_template_paths():
    if not os.path.exists(TEMPLATE_FILE):
        return []
    try:
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("paths", [])
    except Exception as e:
        st.error(f"テンプレートファイルの読み込み中にエラーが発生しました: {e}")
        return []

def save_template_path(new_path):
    paths = get_template_paths()
    if new_path not in paths:
        paths.append(new_path)
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"paths": paths}, f, ensure_ascii=False, indent=4)

def delete_template_path(path_to_delete):
    paths = get_template_paths()
    if path_to_delete in paths:
        paths.remove(path_to_delete)
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"paths": paths}, f, ensure_ascii=False, indent=4)

def get_file_path():
    """使用するHDF5ファイルのパスを入力"""
    file_path = st.text_input(
        label="🔍 使用する .hdf5 ファイルのフルパスを貼り付け",
        value=""
    )

    if not file_path:
        st.stop()

    if not is_hdf5_file(file_path):
        st.warning("⚠️ 指定されたファイルはHDF5形式ではありません。対応しているファイルを選択してください。")
        st.stop()

    st.session_state.file_path = file_path
    filename = os.path.basename(file_path)
    st.markdown(f"##### 選択されたファイル : `{filename}`")
    return file_path

def display_template_path_manager():
    """登録済みテンプレートパスの表示・削除機能付き"""
    st.markdown("##### 📌 登録済みのテンプレートパス一覧")

    template_paths = get_template_paths()

    if not template_paths:
        st.info("テンプレートパスはまだ登録されていません。")
        return

    for i, p in enumerate(template_paths, 1):
        cols = st.columns([0.9, 0.1])
        with cols[0]:
            st.code(p, language="bash")
        with cols[1]:
            if st.button("🗑️", key=f"delete_{i}"):
                delete_template_path(p)
                st.rerun()

def display_template_save_input():
    """ユーザーが手動でテンプレートにパスを保存するUI"""
    st.markdown("##### ➕ パスをテンプレートへ登録")
    new_path = st.text_input("保存して使い回すPathを入力", key="new_template_input")

    if new_path:
        if st.button("💾 登録"):
            save_template_path(new_path)
            st.rerun()

def is_hdf5_file(file_path):
    """ファイルがHDF5フォーマットかどうかをチェック"""
    try:
        return h5py.is_hdf5(file_path)
    except Exception:
        return False

# ==============================
# HDF5 関連の処理
# ==============================
def display_hdf5_tree(path_obj):
    """HDF5ファイルのツリー構造を表示し、選択されたデータパスを返す"""
    st.markdown("### 【HDF5ファイル構造】")

    tree_items = path_obj.get_structure()

    selected_item = tree(
        items=tree_items,
        open_all=True,
        checkbox=False,
        show_line=True,
        key="hdf5_tree"
    )

    if selected_item and selected_item in path_obj.path_map:
        st.session_state.selected_dataset = path_obj.path_map[selected_item]
        return st.session_state.selected_dataset
    else:
        return None


def display_dataset(file_path, dataset_path):
    """選択されたHDF5データセットを表示"""
    with h5py.File(file_path, "r") as f:
        dataset = f[dataset_path]
        st.markdown(f"**選択したデータパス:** `{dataset_path}`")

        # データのメタ情報を表示
        st.write(f"データの形状 (shape): `{dataset.shape}`")
        st.write(f"データ型 (dtype): `{dataset.dtype}`")

        st.divider()

        # CSVダウンロードボタンの追加 (1D, 2Dデータのみ対応)
        if dataset.ndim <= 2:
            display_csv_download_button(dataset)

        st.divider()

        # データの可視化
        visualize_data(dataset)



def display_csv_download_button(dataset):
    """CSVダウンロードボタンを表示 (1Dまたは2Dデータ)"""
    data = dataset[()]  # データを取得

    if data.ndim > 2:
        st.warning("CSVダウンロードは1次元または2次元のデータにのみ対応しています。")
        return

    # CSVデータをメモリ上のバッファに保存
    buffer = io.StringIO()
    np.savetxt(buffer, data, delimiter=",")
    buffer.seek(0)

    # ダウンロードボタンを表示
    st.download_button(
        label="📁 Download CSV",
        data=buffer.getvalue(),
        type="primary",
        file_name="dataset.csv",
        mime="text/csv"
    )


def visualize_data(dataset):
    """HDF5データを可視化"""
    data = dataset[()] if dataset.ndim < 3 else np.array([[[1]]])  # 3次元以上の場合の仮データ

    fig, ax = plt.subplots()

    if dataset.ndim == 0:
        st.write(f"### スカラー値: {data}")
    elif dataset.ndim == 1:
        st.write("### 1次元データ")
        ax.plot(data)
        ax.set_title(dataset.name)
        st.pyplot(fig)
        st.write(data)
    elif dataset.ndim == 2:
        st.write("### 2次元データ")
        im = ax.imshow(data, cmap="jet", aspect='auto')
        fig.colorbar(im, ax=ax)
        ax.set_title(dataset.name)
        st.pyplot(fig)
        st.write(data)
    elif dataset.ndim == 3:
        st.write("### 3次元データのスライス")
        slice_index = st.slider("Frame数", min_value=1, max_value=dataset.shape[0], step=1) - 1
        data = dataset[slice_index]
        im = ax.imshow(data, cmap="jet")
        fig.colorbar(im, ax=ax)
        ax.set_title(f"{slice_index + 1} frame")
        st.pyplot(fig)
    else:
        st.warning(f"未対応データ形式です (shape: {dataset.shape})")


# ==============================
# メイン処理
# ==============================

# 設定とタイトル表示
set_streamlit_config()
st.divider()

# テンプレートPathの表示
st.header('テンプレートの設定')
display_template_path_manager()
display_template_save_input()
st.divider()

# HDF5を調べる
st.header('HDF表示')
file_path = get_file_path()

tree_col, display_col = st.columns(2)
if file_path:
    path_obj = HDFPath(file_path)
    with tree_col:
        selected_path = display_hdf5_tree(path_obj)

    if selected_path:
        with display_col:
            display_dataset(file_path, selected_path)
