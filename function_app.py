import azure.functions as func
import azure.cognitiveservices.speech as speechsdk
import logging
import os

app = func.FunctionApp()

# --- 1. 使用說明與前端介面路由 ---
@app.route(route="index", methods=["GET"])
def index(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Serving the instruction and UI page.')
    
    # 這裡放我們之前寫好的 HTML + RecordRTC 程式碼
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>Azure Speech 語音辨識系統</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/RecordRTC/5.6.2/RecordRTC.min.js"></script>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; line-height: 1.6; max-width: 800px; margin: auto; background-color: #f4f7f9; }
            .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #0078d4; }
            .instructions { background: #e7f3ff; padding: 15px; border-left: 5px solid #0078d4; margin-bottom: 20px; }
            button { padding: 12px 24px; font-size: 16px; cursor: pointer; border: none; border-radius: 4px; transition: 0.3s; }
            #startBtn { background-color: #28a745; color: white; }
            #startBtn:hover { background-color: #218838; }
            #stopBtn { background-color: #dc3545; color: white; }
            #stopBtn:hover { background-color: #c82333; }
            button:disabled { background-color: #ccc; cursor: not-allowed; }
            #status { margin-top: 20px; padding: 15px; border-radius: 4px; background: #eee; min-height: 50px; white-space: pre-wrap; }
            code { background: #333; color: #fff; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Azure Speech 語音辨識系統</h1>
            
            <div class="instructions">
                <h3>使用說明：</h3>
                <ul>
                    <li>點擊 <strong>「開始錄音」</strong> 並允許瀏覽器存取麥克風。</li>
                    <li>說完話後點擊 <strong>「停止錄音並送出」</strong>。</li>
                    <li>系統會將音訊傳送到 <code>/api/speech_to_text</code> 進行辨識。</li>
                    <li>本系統支援 <strong>繁體中文 (zh-TW)</strong> 與 <strong>英文 (en-US)</strong> 自動偵測。</li>
                </ul>
            </div>

            <button id="startBtn">開始錄音</button>
            <button id="stopBtn" disabled>停止錄音並送出</button>
            
            <div id="status">準備就緒...</div>
        </div>

        <script>
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const statusText = document.getElementById('status');
            let recorder, microphone;

            startBtn.onclick = async () => {
                try {
                    microphone = await navigator.mediaDevices.getUserMedia({ audio: true });
                    recorder = RecordRTC(microphone, {
                        type: 'audio', mimeType: 'audio/wav',
                        recorderType: RecordRTC.StereoAudioRecorder,
                        desiredSampRate: 16000, numberOfAudioChannels: 1
                    });
                    recorder.startRecording();
                    statusText.innerText = "🔴 錄音中... 請說話";
                    startBtn.disabled = true; stopBtn.disabled = false;
                } catch (err) {
                    statusText.innerText = "錯誤：無法取得麥克風權限。";
                }
            };

            stopBtn.onclick = () => {
                startBtn.disabled = false; stopBtn.disabled = true;
                statusText.innerText = "⏳ 辨識中，請稍候...";
                recorder.stopRecording(async function() {
                    const audioBlob = recorder.getBlob();
                    microphone.getTracks().forEach(track => track.stop());
                    
                    try {
                        const response = await fetch('/api/speech_to_text', {
                            method: 'POST',
                            body: audioBlob,
                            headers: { 'Content-Type': 'application/octet-stream' }
                        });
                        const result = await response.text();
                        statusText.innerText = response.ok ? "✅ 辨識結果：\\n" + result : "❌ 錯誤：\\n" + result;
                    } catch (error) {
                        statusText.innerText = "❌ 無法連線至 API。";
                    }
                    recorder.destroy(); recorder = null;
                });
            };
        </script>
    </body>
    </html>
    """
    return func.HttpResponse(html_content, mimetype="text/html")


# --- 2. 原有的語音辨識 API ---
@app.route(route="speech_to_text", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def speech_to_text(req: func.HttpRequest) -> func.HttpResponse:
    # (此處維持您之前的辨識邏輯)
    speech_key = os.environ.get("SPEECH_SUBSCRIPTION_KEY", "").strip()
    service_region = os.environ.get("SPEECH_SERVICE_REGION", "").strip()

    audio_data = req.get_body()
    if not audio_data or len(audio_data) < 44:
        return func.HttpResponse("音訊資料無效。", status_code=400)

    try:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_recognition_language = "zh-TW"
        
        auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["en-US", "zh-TW"])
        
        push_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
        push_stream.write(audio_data)
        push_stream.close()

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, 
            auto_detect_source_language_config=auto_detect_config,
            audio_config=audio_config
        )

        result = recognizer.recognize_once()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info(f"👉 語音辨識結果: {result.text}")
            return func.HttpResponse(result.text)
        return func.HttpResponse(f"辨識失敗: {result.reason}", status_code=400)

    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)