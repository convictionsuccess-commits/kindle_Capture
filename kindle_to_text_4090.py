import os, time, pyautogui, requests, base64, shutil, re
import tkinter.simpledialog as sd
import tkinter as tk
from PIL import Image

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
BASE_DIR = r"E:\アプリ\Kindle_Capture"

def qwen_ocr(image_path, history):
    for i in range(3):  # リトライ3回
        try:
            with Image.open(image_path) as img:
                img = img.resize((1920, int(img.size[1] * 1920 / img.size[0])), Image.LANCZOS)
                img.save(image_path, "JPEG", quality=85)

            with open(image_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "model": "qwen2.5-vl",
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": "画像内の日本語を正確に書き写してください。本文のみ。重複厳禁。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}],
                "temperature": 0.1
            }
            response = requests.post("http://localhost:1234/v1/chat/completions", json=payload, timeout=30)
            raw_text = response.json()['choices'][0]['message']['content'].strip()

            lines = raw_text.split('\n')
            unique_lines = []
            seen_chunks = set()

            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                chunk = line[:15]
                if chunk in seen_chunks:
                    break
                if any(line[:15] == h[:15] for h in history[-150:]):
                    continue
                unique_lines.append(line)
                seen_chunks.add(chunk)
                history.append(line)

            if len(history) > 300:
                history = history[-300:]

            return "\n".join(unique_lines)
        except:
            time.sleep(1)
    return "ERROR"

def main():
    pyautogui.FAILSAFE = True
    root = tk.Tk(); root.withdraw()
    input_name = sd.askstring("入力", "本の名前:")
    root.destroy()
    if not input_name:
        return

    input_name = re.sub(r'[\\/:*?"<>|]', '', input_name).strip()
    output_file = os.path.join(BASE_DIR, f"{input_name}.txt")

    img_temp = os.path.join(BASE_DIR, "temp_capture")
    if os.path.exists(img_temp):
        shutil.rmtree(img_temp, ignore_errors=True)
    os.makedirs(img_temp, exist_ok=True)

    NEXT_PAGE_X, CENTER_Y = 200, 720
    INTERVAL = 1.0
    history = []
    last_text = ""
    same_count = 0

    print(f"🚀 開始: {input_name}")
    for i in range(5, 0, -1):
        print(f"{i}...", end=" ", flush=True); time.sleep(1)
    print("\n🔥 実行中...")

    try:
        for p in range(1, 4000):
            img_path = os.path.join(img_temp, f"p{p}.jpg")
            pyautogui.screenshot(region=(650, 150, 3820, 1150)).convert('RGB').save(img_path, 'JPEG')

            text = qwen_ocr(img_path, history)
            print(f"P{p} 完了 ({len(text)}文字)", flush=True)

            # 文字数ベースの終端検知
            if len(text) < 20:
                same_count += 1
                if same_count >= 5:
                    print("\n🏁 終端検知。終了。")
                    break
            else:
                same_count = 0

            if text != "ERROR" and len(text) >= 20:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\n--- P{p} ---\n{text}")
                last_text = text

            # ページ送り後に待機追加
            pyautogui.click(x=NEXT_PAGE_X, y=CENTER_Y)
            time.sleep(0.3)
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 中断。")
    finally:
        if os.path.exists(img_temp):
            shutil.rmtree(img_temp, ignore_errors=True)
        print(f"✅ 完了: {output_file}")

if __name__ == "__main__":
    # プログラムのエントリーポイントとしてmain()を呼び出します
    main()
