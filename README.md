# twspeech - 智慧語音服務 API

本專案為系統提供語音轉文字 (Speech-to-Text) 功能。透過 Azure Functions 接收前端傳來的語音音訊 (WAV)，並串接 Azure Microsoft Foundry (Speech Service) 進行辨識，最後回傳文字結果。

## ✨ 核心功能
* **音訊接收**：接收前端傳來的 HTTP POST 語音資料。
* **語音辨識**：支援繁體中文 (zh-TW) 與英文 (en-US) 的自動偵測與語音轉文字。

## 📁 檔案結構
* `function_app.py`：核心程式邏輯，定義 API 路由。
* `host.json`：Azure Functions 全域設定檔。
* `local.settings.json`：本地開發環境設定檔，需設定 Azure 語音服務的金鑰 (KEY) 與區域 (REGION)。
* `requirements.txt`：Python 依賴套件清單，包含 `azure-cognitiveservices-speech`。

## 🚀 安裝與執行流程
1. **取得 Azure 金鑰**：至 Azure Portal 建立「語音服務」，取得 `KEY` 與 `REGION`。
2. **本地環境設定**：將取得的金鑰與區域填入 `local.settings.json` 中的 `SPEECH_SUBSCRIPTION_KEY` 與 `SPEECH_SERVICE_REGION`。
3. **本地測試**：按下 `F5` 啟動，可進入 `http://localhost:7072/api/index` 使用內建的簡易網頁測試麥克風錄音與辨識。
4. **部署至 Azure**：
   * 部署程式碼至 Azure Function App。
   * **重要**：至 Azure Portal 的「環境變數」設定中，手動新增 `SPEECH_SUBSCRIPTION_KEY` 與 `SPEECH_SERVICE_REGION`。
   * 紀錄部署後的函式 URL。
