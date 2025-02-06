import streamlit as st
from streamlit_antd_components import tree, TreeItem

import numpy as np
import matplotlib.pyplot as plt

import os
import h5py

import util

st.set_page_config(
    page_title="HDF Viewer",
    layout="wide",
)

st.title("HDF Viewer")

up_col1, up_col2 = st.columns(2)
with up_col1:
    st.markdown(
        """
        ### 【概要】
        - `.hdf5`などのHDFファイルの中身を表示します。`.nxs`もHDF5の一種なので見れます。
        - ファイルパス(絶対パス)を貼り付けてください。
            - Macでは `option` を押しながら`command + c` (コピー)
            - Windowsでは...
        """
    )
with up_col2:
    # セッション情報を表示
    st.markdown("### 【セッション情報】")
    st.write("ブラウザに一時的に記憶されている情報。表示がおかしいときに参照したりクリアしてください。")
    st.write(st.session_state)
    # クリアボタンの作成
    if st.button("セッション情報をクリア"):
        st.session_state.clear()

file_path = st.text_input(".hdf5ファイルのフルパスを貼り付け", "")

# ファイルパスが入力されたらsession_stateに保存
if file_path and os.path.isfile(file_path):
    st.session_state.file_path = file_path
    filename = file_path.split("/")[-1]
    location = file_path.replace(filename, "")
    st.markdown(
        f"##### File set : `{filename}`"
    )
else:
    if file_path:
        st.error("The file path is invalid or the file does not exist.")
        st.stop()

st.divider()

# フルパスを取得・保持するためのオブジェクトを作成
if 'file_path' in st.session_state:
    path_obj = util.HDFPath(st.session_state.file_path)
else:
    st.stop()  # ファイルが指定されていない場合処理を中断

# HDF5ファイルのツリー構造を表示
if os.path.isfile(st.session_state.file_path):
    with h5py.File(st.session_state.file_path, 'r') as f:
        # 左右のカラムを作成
        view_col1, view_col2 = st.columns(2)

        with view_col1:
            st.markdown("### 【HDF5ファイル構造】")
            tree_items = [TreeItem(label="Root", children=path_obj.get_structure(), disabled=False)]

            selected_item = tree(
                items=tree_items,
                width=500,
                height=500,
                open_all=True,
                checkbox=False,
                show_line=True,
                key="hdf5_tree"
            )

            # ユーザーが選択したアイテムを処理
            if selected_item:
                # `path_map` から対応するフルパスを取得
                if selected_item in path_obj.path_map:
                    selected_path = path_obj.path_map[selected_item]
                    st.session_state.selected_dataset = selected_path
                else:
                    st.error(f"Path '{selected_item}' に対応するフルパスが見つかりません。")

                if False:  # デバッグにするときにTrue
                    # デバッグ用にアプリ上に表示して確認
                    st.divider()
                    st.markdown("#### デバッグ用情報")
                    st.markdown(f"**選択されたパス:** `{selected_item}`")
                    # path_map の全てのキーを表示
                    st.markdown("**path_map のキー一覧:**")
                    st.write(list(path_obj.path_map.keys()))

        with view_col2:
            st.markdown("### 【データ表示】")
            if 'selected_dataset' in st.session_state:
                dataset_path = st.session_state.selected_dataset
                if dataset_path in f:
                    st.markdown(f"**選択したデータパス:** `{dataset_path}`")

                    # shape と type を表示
                    dataset = f[dataset_path]
                    st.write(f"**データの形状 (shape):** {dataset.shape}")
                    st.write(f"**データ型 (dtype):** {dataset.dtype}")
                    st.divider()
                    # 2次元データ以下ならデータを読み込む。3次元では分岐先で1frame分のデータのみを読み込む
                    if len(dataset.shape) < 3:
                        data = dataset[...]
                    else:
                        data = np.array([[[1]]]) # HACK: 3次元のndarrayを仮に作って↓の分岐に正しく入るようにした

                    # データの型や次元に応じた可視化
                    if isinstance(data, np.ndarray):
                        if data.ndim == 0:  # スカラー値の場合
                            st.write(f"### スカラー値: {data}")
                        elif data.ndim == 1:  # 1次元配列の場合
                            st.write("### 1次元データ")
                            fig, ax = plt.subplots()
                            ax.plot(data)
                            ax.set_title(dataset_path)
                            st.pyplot(fig)
                            st.write(data)
                        elif data.ndim == 2:  # 2次元配列の場合
                            st.write("### 2次元データ")
                            fig, ax = plt.subplots()
                            im = ax.imshow(data, cmap="jet", aspect='auto') # aspectをautoにしている
                            fig.colorbar(im, ax=ax)
                            ax.set_title(dataset_path)
                            st.pyplot(fig)
                            st.write(data)
                        elif data.ndim == 3:  # 3次元配列の場合
                            st.write("### 3次元データのスライス")
                            # 0次元方向のスライスを表示
                            slice_index = st.slider("Frame数", min_value=1, max_value=dataset.shape[0], step=1) - 1 # 表示では1始まりにする
                            fig, ax = plt.subplots()
                            data = dataset[slice_index]
                            im = ax.imshow(data, cmap="jet")
                            fig.colorbar(im, ax=ax)
                            ax.set_title(f"{slice_index+1} frame")
                            st.pyplot(fig)
                        else:  # 高次元データの場合
                            st.warning(f"高次元データの視覚化は未対応です (shape: {data.shape})")
                    elif isinstance(data, (str, bytes)):  # 文字列データの場合
                        st.write("### 文字列データ")
                        st.text(data.decode() if isinstance(data, bytes) else data)
                    elif isinstance(data, (bool, np.bool_)):  # ブール型データの場合
                        st.write(f"### ブール値: {data}")
                    else:  # その他のデータ型
                        st.write("### 未対応のデータ型")
                        st.write(data)
                else:
                    st.error(f"The selected dataset '{dataset_path}' does not exist in the file.")
            else:
                st.markdown("### データセットが選択されていません。")
