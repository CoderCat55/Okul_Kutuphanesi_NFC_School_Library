**Ollama** — run once in PowerShell:
```powershell
winget install --id Ollama.Ollama --exact
ollama pull qwen2.5:1.5b
```
If Ollama isn’t already running, start it in a separate PowerShell window with `ollama serve`. The app is configured to use that model on `localhost:11434`.

**Set up and run the app** — from its folder in PowerShell:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```
This creates and uses the virtual environment without needing to activate it.

One separate prerequisite: install the **Tesseract OCR program** with its `eng`, `tur`, and `deu` language data. `pytesseract` in the requirements file is only the Python wrapper; the app also expects the Tesseract executable at `C:\Program Files\Tesseract-OCR\tesseract.exe`.

#teserract downloader for windows https://github.com/UB-Mannheim/tesseract/wiki
#https://pypi.org/project/pytesseract/

In PowerShell, check that Tesseract is installed:

```powershell
tesseract --version
```

Then check the OCR languages are available:

```powershell
tesseract --list-langs
```

You should see `eng`, `tur`, and `deu`. If `tesseract` isn’t recognized, try the path your app expects:

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```