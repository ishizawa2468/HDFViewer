import os
import h5py
from streamlit_antd_components import TreeItem

class HDFPath:
    """HDF5のパスと構造を管理するクラス"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.structure = None  # HDF5ツリー構造を保存
        self.path_map = {}  # フルパスのマッピング

    def get_structure(self) -> list[TreeItem]:
        """HDF5ファイルのツリー構造を取得"""
        if self.structure is not None:
            return self.structure

        with h5py.File(self.file_path, 'r') as h5obj:
            hdf_tree = self._build_tree(h5obj)
            self.structure = self._convert_to_treeitems(hdf_tree)

        return self.structure

    def _build_tree(self, h5obj) -> dict:
        """HDF5のネストされた辞書構造を作成"""
        tree = {}

        def visitor_func(name, obj):
            parts = name.strip("/").split("/")
            node = tree
            for part in parts[:-1]:  # 最後の要素を除く（グループ名）
                node = node.setdefault(part, {})

            if isinstance(obj, h5py.Group):
                node[parts[-1]] = {}  # グループのための辞書
            else:
                full_path = "/" + name  # HDF5の絶対パス
                node[parts[-1]] = full_path  # データセットのフルパスを保存
                self.path_map[parts[-1]] = full_path  # パスをマッピング

        h5obj.visititems(visitor_func)
        return tree

    def _convert_to_treeitems(self, tree: dict) -> list[TreeItem]:
        """辞書からTreeItemのリストに変換"""
        def build_treeitems(node_dict):
            items = []
            for key, val in node_dict.items():
                if isinstance(val, dict):
                    items.append(TreeItem(label=key, children=build_treeitems(val), disabled=False))
                else:
                    items.append(TreeItem(label=key, disabled=False))  # データセット
            return items

        return build_treeitems(tree)
