# daily_login_bot

「キラメキのトリ」アプリの一日一回スクラッチを自動実行するためのツールです。

**必ず自分が所有する端末・自分のアカウントに対してのみ使用してください。**
アプリの利用規約で自動操作(BOT)が禁止されている場合は使用しないでください。

## 仕組み

Android端末をUSB(または同一Wi-Fi経由のADB)でPCに接続し、
[uiautomator2](https://github.com/openatx/uiautomator2) でアプリを起動 →
画面上のボタンをタップ → 結果をスクリーンショットで記録、という流れを
Pythonスクリプトで自動化し、cron等で毎日決まった時刻に実行します。

PC側でスクリプトを動かし続ける必要があるため、常時電源が入っているPCや
Raspberry Piなどでの運用を想定しています(スマホ単体では完結しません)。

## セットアップ

### 1. 必要なものをインストール

```bash
cd daily_login_bot
pip install -r requirements.txt

# ADB (Android Debug Bridge) をインストール
# Mac: brew install android-platform-tools
# Ubuntu: sudo apt install android-tools-adb
```

### 2. 端末側の設定

1. スマホの「設定 > 端末情報」で「ビルド番号」を7回タップし開発者向けオプションを有効化
2. 「設定 > 開発者向けオプション」で「USBデバッグ」をON
3. PCとUSB接続し、`adb devices` で端末が表示されることを確認
4. 画面ロックはできれば解除しておく(PIN/パターンがあると `d.unlock()` だけでは開かない場合があります)

### 3. uiautomator2の初期化

```bash
python -m uiautomator2 init
```

これで端末側にuiautomator2のエージェントアプリがインストールされます。

### 4. 対象アプリの情報を調べる

```bash
# パッケージ名を調べる(アプリ名の一部で絞り込み)
adb shell pm list packages | grep -i kirameki

# UIの階層をダンプして、ボタンのtext/resource-idを確認する
python -m uiautomator2 dump  # または weditor (pip install weditor) でGUI確認
```

`config.yaml` の `app.package_name` と `app.steps` を、実際にアプリを操作した
時の画面遷移(例: トップ画面 → スクラッチ画面 → 「けずる」ボタン → 結果ダイアログを閉じる)
に合わせて書き換えてください。

### 5. 動作確認

```bash
# まずはスクリーンショットだけ撮って接続確認
python bot.py --dry-run

# 手順どおりに実行
python bot.py
```

`logs/` ディレクトリに実行結果のスクリーンショットが保存されるので、
意図通りスクラッチが引けているか確認してください。

### 6. 毎日自動実行する(cron)

```bash
crontab -e
```

以下を追記(毎朝9時に実行する例。config.yamlのschedule値と合わせてください):

```
0 9 * * * cd /path/to/daily_login_bot && /usr/bin/python3 bot.py >> logs/cron.log 2>&1
```

Windowsの場合はタスクスケジューラで同様のコマンドを毎日実行するように登録してください。

## 注意事項

- アプリのアップデートでUIが変わると `steps` のtext/resource-idがずれて失敗します。
  失敗時は `logs/*_error.png` を確認し、`config.yaml` を調整してください。
- 実行時は画面をタップするため、他の操作と同時に走らせるとボタンを誤タップする
  可能性があります。実行中は端末を触らないようにしてください。
- 本ツールは特定アプリの内部UIには依存しない汎用フレームワークです。
  実際のボタン名・画面遷移はご自身の端末で確認の上、`config.yaml` に反映してください。
