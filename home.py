import streamlit as st
from streamlit_antd_components import tree, TreeItem

import numpy as np
import matplotlib.pyplot as plt
import io
import os
import h5py

import util

# ==============================
# Streamlit 設定
# ==============================
def set_streamlit_config():
    st.set_page_config(
        page_title="HDF Viewer",
        layout="wide",
    )
    st.title("HDF Viewer")

def is_hdf5_file(file_path):
    """ファイルがHDF5フォーマットかどうかをチェック"""
    try:
        return h5py.is_hdf5(file_path)
    except Exception:
        return False

def get_file_path():
    """ユーザーからのHDF5ファイルのパス入力を処理する"""
    file_path = st.text_input(".hdf5ファイルのフルパスを貼り付け", "/Users/ishizawaosamu/work/MasterThesis/save/processed_hdf/OIbDia06_2nd_down_processed.hdf")

    # validation
    if not is_hdf5_file(file_path):
        st.error("⚠️ 指定されたファイルはHDF5形式ではありません。対応しているファイルを選択してください。")
        st.stop()
    st.session_state.file_path = file_path
    filename = os.path.basename(file_path)
    st.markdown(f"##### Selected file : `{filename}`")
    return file_path

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
set_streamlit_config()
file_path = get_file_path()

tree_col, display_col = st.columns(2)
if file_path:
    path_obj = util.HDFPath(file_path)
    with tree_col:
        selected_path = display_hdf5_tree(path_obj)

    if selected_path:
        with display_col:
            display_dataset(file_path, selected_path)
