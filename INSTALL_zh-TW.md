# 安裝指南 / Installation Guide (繁體中文)

## 快速安裝步驟

### 方法一：使用自動安裝腳本（推薦）

1. 開啟命令提示字元（cmd）或 PowerShell
2. 切換到專案目錄：
   ```bash
   cd D:\PycharmProjects\One_Sentence_OCR
   ```

3. 執行安裝腳本：
   ```bash
   install.bat
   ```

### 方法二：手動安裝

1. **檢查 Python 版本**（需要 Python 3.7 或更高版本）
   ```bash
   python --version
   ```

2. **啟動虛擬環境**（如果有使用 .venv）
   ```bash
   .venv\Scripts\activate
   ```

3. **升級 pip**
   ```bash
   python -m pip install --upgrade pip
   ```

4. **安裝 Python 套件**
   ```bash
   pip install -r requirements.txt
   ```

   這會安裝以下套件：
   - PyQt5 (圖形介面)
   - pytesseract (OCR 文字辨識)
   - Pillow (圖片處理)
   - pyperclip (剪貼簿功能)

5. **安裝 Tesseract OCR**（系統必要套件）
   
   下載並安裝 Tesseract OCR：
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - 建議安裝位置：`C:\Program Files\Tesseract-OCR`
   
   安裝後，確認 tesseract.exe 在系統 PATH 中，或在程式碼中設定路徑。

6. **測試安裝**
   ```bash
   python test_setup.py
   ```

7. **執行程式**
   ```bash
   python one_sentence_ocr.py
   ```

## 常見問題

### 問題：找不到 PyQt5 模組
```
Error: Failed to import PyQt5: No module named 'PyQt5'
```

**解決方法：**
```bash
pip install PyQt5
```

### 問題：找不到 Tesseract
```
TesseractNotFoundError: tesseract is not installed
```

**解決方法：**
1. 從 https://github.com/UB-Mannheim/tesseract/wiki 下載安裝
2. 將 Tesseract 路徑加入系統 PATH
3. 或在 `one_sentence_ocr.py` 中設定路徑：
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### 問題：虛擬環境無法啟動

**PowerShell 執行政策錯誤：**
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然後再次執行：
```bash
.venv\Scripts\activate
```

## 確認安裝成功

執行測試腳本應該會看到：
```
✓ PyQt5 imported successfully
✓ pytesseract imported successfully
✓ PIL (Pillow) imported successfully
✓ pyperclip imported successfully
✓ one_sentence_ocr.py module structure is valid

Total: 4/4 tests passed
```

## 執行應用程式

```bash
python one_sentence_ocr.py
```

程式會最小化到系統托盤。右鍵點擊托盤圖示可以：
- 顯示視窗
- 開始新的擷取
- 結束程式

## 需要協助？

如果遇到其他問題，請在 GitHub Issues 中回報，並附上完整的錯誤訊息。
