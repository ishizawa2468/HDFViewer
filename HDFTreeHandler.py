# HDFTreeHandler.py
"""
HDFTreeHandler クラスは、HDF5ファイルの構造を解析し、
Streamlit の Tree UI 表示用データ (TreeItem) を生成します。

本サンプルでは、
  - TreeItem.label に「HDF5 ファイル内の絶対パス (例: /entry/data)」
  - TreeItem.description に「末端（短い名前）」
を設定し、重名があってもフルパスで区別できるようにしています。
"""

import h5py
from streamlit_antd_components import TreeItem
import os

class HDFTreeHandler:
    def __init__(self, file_path: str):
        """
        :param file_path: HDF5 ファイルのパス
        """
        self.file_path = file_path
        # 階層的にグループやデータセットを格納する辞書
        self.tree_dict = {}
        # ツリー構造を構築
        self._build_tree_dict()

    def _build_tree_dict(self):
        """
        HDF5ファイルを再帰的に走査し、self.tree_dict に階層構造を格納する。
        具体的には以下のような構造:
            {
              'entry': [
                {
                  'name': 'entry',
                  'type': 'group',
                  'children': {
                    'data': [
                      {
                        'name': 'data',
                        'type': 'dataset',
                        'path': '/entry/data'
                      },
                      ...
                    ]
                  }
                }
              ]
            }

        のように、グループ/データセットをまとめる。
        """
        with h5py.File(self.file_path, "r") as h5obj:
            def visitor(name, obj):
                """
                name: "/entry/frame/T" のような絶対パス
                obj: h5py.Group もしくは h5py.Dataset
                """
                parts = name.strip("/").split("/")
                node = self.tree_dict

                # 中間のグループ階層を潜っていく
                for part in parts[:-1]:
                    if part not in node:
                        node[part] = []
                    found_group = None
                    for item in node[part]:
                        if item["name"] == part and item["type"] == "group":
                            found_group = item
                            break
                    if found_group is None:
                        found_group = {
                            "name": part,
                            "type": "group",
                            "children": {}
                        }
                        node[part].append(found_group)
                    node = found_group["children"]

                # 最下層 (leaf) の処理
                leaf_name = parts[-1]
                if not leaf_name:
                    # ルート "/" だけならスキップ
                    return

                if leaf_name not in node:
                    node[leaf_name] = []

                if isinstance(obj, h5py.Group):
                    node[leaf_name].append({
                        "name": leaf_name,
                        "type": "group",
                        "children": {}
                    })
                else:
                    # Dataset
                    node[leaf_name].append({
                        "name": leaf_name,
                        "type": "dataset",
                        "path": "/" + name  # フルパス
                    })

            # visititems を使って全 Group/Dataset を探索
            h5obj.visititems(visitor)

    def get_treeitems(self):
        """
        self.tree_dict から再帰的に TreeItem のリストを生成して返す。
        ここでは「label=フルパス」「description=末端の短い名前」という形にする。
        """
        return self._to_treeitems(self.tree_dict, parent_path="")

    def _to_treeitems(self, current_dict: dict, parent_path: str):
        """
        再帰的に current_dict をたどり、TreeItem を生成する。
        :param current_dict: グループ階層を表す辞書
        :param parent_path: 親のパス ("/entry" など)
        """
        items = []
        for key, node_list in current_dict.items():
            for node in node_list:
                node_name = node["name"]
                if node["type"] == "group":
                    # グループの場合
                    new_path = f"{parent_path}/{node_name}".replace("//", "/")

                    # 子要素を再帰取得
                    children = self._to_treeitems(node["children"], new_path)

                    # グループ用 TreeItem
                    tree_item = TreeItem(
                        label=new_path,         # フルパスをlabelに
                        description=node_name,  # 短い名前をdescriptionに
                        children=children
                    )
                    items.append(tree_item)

                else:
                    # Dataset の場合
                    dataset_path = node["path"]  # 例: "/entry/data"
                    tree_item = TreeItem(
                        label=dataset_path,      # フルパス
                        description=node_name    # 末端名
                    )
                    items.append(tree_item)

        return items
