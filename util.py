import os
import h5py
from streamlit_antd_components import TreeItem


class HDFPath:
    """HDF5のパスと構造を管理するクラス"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.structure = None  # HDF5構造を保存する
        self.path_map = {}  # フルパスのマッピング

    def get_structure(self) -> list[TreeItem]:
        """HDF5ファイルの構造を再帰的に取得する"""
        if self.structure is not None:
            return self.structure  # すでに取得済みなら再利用

        with h5py.File(self.file_path, 'r') as h5obj:
            self.structure = self._traverse_hdf5(h5obj)
        return self.structure

    def _traverse_hdf5(self, h5obj, parent_path="") -> list[TreeItem]:
        """HDF5構造を再帰的に探査する内部メソッド"""
        sub_items = []
        for key, val in h5obj.items():
            full_path = os.path.join(parent_path, key) if parent_path else key
            self.path_map[full_path] = full_path  # フルパスをマッピング

            if isinstance(val, h5py.Group):
                # グループの場合
                sub_items.append(
                    TreeItem(
                        label=full_path,
                        children=self._traverse_hdf5(val, full_path),
                        disabled=False
                    )
                )
            elif isinstance(val, h5py.Dataset):
                # データセットの場合
                sub_items.append(TreeItem(label=full_path, disabled=False))
        return sub_items
