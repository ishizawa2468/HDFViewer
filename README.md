# 概要

HDFファイルの内容を表示、図示、ダウンロードするアプリです。

# 起動方法

- AppManagerから起動する
    - AppManagerと同じ階層にcloneしてください
    - 起動方法は〜で確認してください
- ターミナルから起動する場合
    - どちらかのコマンドを実行してください
    - `python main.py`
    - `streamlit run home.py`

# デモ

一時停止などしたい場合はdocsにあるdemo.mp4をダウンロードしてください。


# HDF Viewer – コード構成と解説  (by ChatGPT)

本ドキュメントでは、StreamlitベースのHDF5可視化アプリケーションの構造とその機能について、各関数・構成要素を詳細に解説します。

---

## ✅ アプリ全体の目的と構成

このアプリは、ローカルの `.hdf5` ファイルを読み込み、ツリー構造およびデータセットの内容を視覚的かつインタラクティブに操作・確認できるウェブインターフェースを提供します。

### 主な機能

| カテゴリ | 概要 |
|----------|------|
| **ファイル管理** | HDF5ファイルのパス入力・検証・テンプレート登録・削除 |
| **構造表示** | HDFPathクラスによるHDF5階層構造のツリー表示 |
| **データ表示** | 選択されたデータセットの情報と内容の可視化 |
| **エクスポート** | 1D/2DデータをCSV形式でダウンロード可能 |

---

## 📁 主要セクション別解説

### 1. Streamlitの初期設定

```python
def set_streamlit_config():
```

- ページ設定（タイトル・レイアウト）
- アプリタイトル表示（"HDF Viewer"）

---

### 2. テンプレートパス管理

HDF5ファイルのパスをテンプレートとしてJSONファイルに保存・再利用可能にします。

#### 関連ファイル

- `template_paths.json` (自動で生成されます)

#### 主な関数

| 関数名 | 説明 |
|--------|------|
| `get_template_paths()` | 登録済みパスを読み込み |
| `save_template_path(new_path)` | 新しいパスを保存 |
| `delete_template_path(path_to_delete)` | パスを削除 |
| `display_template_path_manager()` | Streamlitでパス一覧と削除ボタンを表示 |
| `display_template_save_input()` | 新規パスの登録UIを表示 |

---

### 3. HDF5ファイルパスの取得と検証

```python
def get_file_path():
```

- ユーザーからファイルパスを入力
- `h5py.is_hdf5()` による形式検証
- セッションステートへ保存

---

### 4. HDF5構造のツリー表示

```python
def display_hdf5_tree(path_obj):
```

- `HDFPath` クラスの `get_structure()` により `TreeItem` リストを取得
- Streamlitの `tree()` コンポーネントで可視化
- 選択結果を `session_state.selected_dataset` に保存

---

### 5. データセットの表示と操作

```python
def display_dataset(file_path, dataset_path)
```

- HDF5データセットを開き以下を表示：
  - データの形状 (`shape`)
  - データ型 (`dtype`)
  - データの可視化
  - CSVダウンロード（1D/2D限定）

#### 補助関数

| 関数 | 内容 |
|------|------|
| `display_csv_download_button(dataset)` | データをCSV形式でダウンロード可能に |
| `visualize_data(dataset)` | 次元に応じたMatplotlib可視化（0D〜3D） |

---

## ▶️ メイン処理のフロー

```python
set_streamlit_config()
display_template_path_manager()
display_template_save_input()

file_path = get_file_path()

path_obj = HDFPath(file_path)
selected_path = display_hdf5_tree(path_obj)

if selected_path:
    display_dataset(file_path, selected_path)
```

- タイトル・テンプレートパス表示
- HDF5ファイル選択・ツリー構造表示
- 選択したデータセットの詳細表示と操作

---

## 🧩 技術的工夫と利点

- **セッションステートの活用**：UI選択情報を維持し、連携を容易に
- **Streamlit + Antd**：ツリー構造を視覚的に表示
- **可視化の柔軟性**：スカラーから3Dデータまでを一貫して処理
- **即時CSV出力**：`io.StringIO` による軽量なダウンロード対応

---

## 関連クラス：HDFPath

このアプリでは、`HDFPath` クラスが中心的役割を果たします。HDF5ファイルの内部構造を辞書およびツリー構造として抽象化し、ユーザーインターフェースとの橋渡しを行います。

---

ご不明点・改善提案等がございましたら、お気軽にご連絡ください。
