# Project Setup / プロジェクトセットアップ / 项目环境配置

---

## 🧩 Installation Guide / インストール手順 / 安装指南

### 1. System Dependencies / システム依存関係 / 系统依赖安装

Please run the following commands before installation:  
インストール前に次のコマンドを実行してください：  
安装前请先执行以下命令：

```bash
sudo apt update
sudo apt install python3-dev libpq-dev gcc
````

This is required to fix the following error:
次のエラーを修正するために必要です：
这是为了解决以下错误：

```
× Failed to build psycopg2==2.9.10
```

---


### 2. Package Installation / パッケージのインストール / 安装依赖包

Use the following command to install all dependencies:
すべての依存関係をインストールするには次のコマンドを使用してください：
使用以下命令安装所有依赖：

```bash
uv sync
```

---

## ⚙️ Environment Variables / 環境変数 / 环境变量设置

Please set the following environment variables before running the application:
アプリケーションを実行する前に、次の環境変数を設定してください：
运行程序前请设置以下环境变量：

| Variable Name / 変数名 / 变量名            | Description / 説明 / 说明                                      |
| ------------------------------------ | ---------------------------------------------------------- |
| `AZURE_DEPLOYMENT_CHAT_MODEL`        | Chat model deployment name / チャットモデルのデプロイ名 / 聊天模型部署名称      |
| `AZURE_DEPLOYMENT_EMBEDDING_MODEL`   | Embedding model deployment name / 埋め込みモデルのデプロイ名 / 向量模型部署名称 |
| `AZURE_BASE`                         | Azure base URL / Azure ベースURL / Azure 基础 URL               |
| `AZURE_KEY`                          | Azure API key / Azure APIキー / Azure API 密钥                 |
| `AZURE_API_VERSION`                  | Azure API version / Azure APIバージョン / Azure API 版本号         |
| `AZURE_DEPLOYMENT_CHAT_ANSWER_MODEL` | Chat answer model name / チャット応答モデル名 / 聊天回答模型名称             |
| `AZURE_ANSWER_BASE`                  | Answer API base URL / 応答APIのベースURL / 回答 API 基础 URL         |
| `AZURE_KEY_ANSWER`                   | Answer API key / 応答APIキー / 回答 API 密钥                       |

---

## ✅ Summary / まとめ / 总结

* Update system packages first
  まずシステムパッケージを更新します
  请先更新系统软件包
* Install Python build dependencies
  Pythonビルド依存関係をインストールします
  安装 Python 构建依赖
* Use `uv sync` to set up your environment
  `uv sync`で環境を構築します
  使用 `uv sync` 初始化环境
* Configure environment variables before running
  実行前に環境変数を設定します
  运行前请配置环境变量

---