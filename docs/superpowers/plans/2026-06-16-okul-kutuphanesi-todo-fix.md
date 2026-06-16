# Todo Items Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the tasks listed in todo.md: set digital resource title to filename, make importDB and uploadStudents automatic on file selection, and auto-open browser when running app.py.

**Architecture:** Modify existing HTML and JavaScript files to change upload behavior, and modify app.py to auto-open browser. Changes are localized to admin.html and app.py.

**Tech Stack:** HTML, JavaScript, Python (Flask)

---

### Task 1: Digital resource title should be filename

**Files:**
- Modify: `admin.html:793-848` (saveDijital function and showFiles function)

- [ ] **Step 1: Modify showFiles function to set title to filename without extension when file selected**

```javascript
function showFiles(input) {
  const list  = document.getElementById('fileList');
  const names = document.getElementById('uploadedNames');
  list.innerHTML = '';
  let nameList = [];
  for (const f of input.files) {
    const li = document.createElement('li');
    li.innerHTML = '📄 ' + f.name;
    list.appendChild(li);
    nameList.push(f.name);
  }
  names.textContent = input.files.length + ' dosya seçildi: ' + nameList.join(', ');
  
  // Set title to filename without extension if title is empty
  if (input.files.length > 0 && document.getElementById('dTitle').value.trim() === '') {
    const fileName = input.files[0].name;
    const titleWithoutExtension = fileName.replace(/\.[^/.]+$/, "");
    document.getElementById('dTitle').value = titleWithoutExtension;
  }
}
```

- [ ] **Step 2: Verify the change works by selecting a file and checking title field**

Run: Open admin.html in browser, select a file for digital resource, observe title field auto-fills with filename (no extension)

Expected: Title field populated with filename without extension

- [ ] **Step 3: Commit**

```bash
git add admin.html
git commit -m "feat: set digital resource title to filename when file selected"
```

---

### Task 2: Make importDB automatic on file selection

**Files:**
- Modify: `admin.html:362-370` (upload-zone for import)
- Modify: `admin.html:693-718` (importDB function)

- [ ] **Step 1: Remove importDB button and add onchange to file input**

```html
<div class="upload-zone" onclick="document.getElementById('importFile').click()">
  <div class="icon">⬆️</div>
  <p>Dosya seçmek için tıklayın</p>
  <input type="file" id="importFile" style="display:none" accept=".db" onchange="importDB()">
</div>
```

- [ ] **Step 2: Update importDB function to show filename in alerts**

```javascript
function importDB() {
  const f = document.getElementById('importFile').files[0];
  if (!f) { alert('Lütfen bir .db dosyası seçin.'); return; }
  if (!f.name.endsWith('.db')) { alert('Lütfen bir .db dosyası seçin.'); return; }

  const formData = new FormData();
  formData.append('file', f);

  fetch('/api/admin/import', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Veri tabanı başarıyla yüklendi: ' + f.name + '. Lütfen uygulamayı yeniden başlatın.');
      document.getElementById('importFile').value = '';
    } else {
      alert('Yükleme başarısız: ' + data.message + ' (Dosya: ' + f.name + ')');
    }
  })
  .catch(error => {
    alert('Bir hata oluştu: ' + error.message + ' (Dosya: ' + f.name + ')');
    console.error('Error:', error);
  });
}
```

- [ ] **Step 3: Verify the change works by selecting a .db file and observing automatic upload**

Run: Open admin.html, click upload zone for DB import, select a .db file, observe automatic upload attempt

Expected: Upload starts automatically, alert shows filename

- [ ] **Step 4: Commit**

```bash
git add admin.html
git commit -m "feat: make importDB automatic on file selection"
```

---

### Task 3: Make uploadStudents automatic on file selection

**Files:**
- Modify: `admin.html:350-357` (upload-zone for students)
- Modify: `admin.html:641-665` (uploadStudents function)

- [ ] **Step 1: Remove uploadStudents button and add onchange to file input**

```html
<div class="upload-zone" onclick="document.getElementById('studentFile').click()">
  <div class="icon">⬆️</div>
  <p>Dosya seçmek için tıklayın</p>
  <input type="file" id="studentFile" style="display:none" accept=".csv,.xlsx,.xls" onchange="uploadStudents()">
</div>
```

- [ ] **Step 2: Update uploadStudents function to show filename in alerts**

```javascript
function uploadStudents() {
  const f = document.getElementById('studentFile').files[0];
  if (!f) { alert('Lütfen bir dosya seçin.'); return; }

  const fileName = f.name; // Store for use in callbacks

  const formData = new FormData();
  formData.append('file', f);

  fetch('/api/students/upload', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Öğrenci listesi yüklendi: ' + fileName + '. ' + data.added + ' öğrenci eklendi, ' + data.updated + ' öğrenci güncellendi.');
      document.getElementById('studentFile').value = '';
    } else {
      alert('Yükleme başarısız: ' + data.message + ' (Dosya: ' + fileName + ')');
    }
  })
  .catch(error => {
    alert('Bir hata oluştu: ' + error.message + ' (Dosya: ' + fileName + ')');
    console.error('Error:', error);
  });
}
```

- [ ] **Step 3: Verify the change works by selecting a student file and observing automatic upload**

Run: Open admin.html, click upload zone for student list, select a .csv/.xlsx file, observe automatic upload attempt

Expected: Upload starts automatically, alert shows filename

- [ ] **Step 4: Commit**

```bash
git add admin.html
git commit -m "feat: make uploadStudents automatic on file selection"
```

---

### Task 4: Auto-open browser when running app.py

**Files:**
- Modify: `app.py:549-550` (main block)

- [ ] **Step 1: Add webbrowser import and open browser before running app**

```python
import webbrowser

# ... existing imports ...

if __name__ == '__main__':
    webbrowser.open('http://192.168.0.20:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)
```

- [ ] **Step 2: Verify the change works by running app.py and observing browser opens**

Run: `python app.py`

Expected: Browser opens automatically to http://192.168.0.20:5000

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: auto-open browser when running app.py"
```

---