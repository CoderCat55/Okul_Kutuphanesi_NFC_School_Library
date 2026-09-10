
2) for div autobook 
div has width of student activities div. height of the "panel basili". horizantally left half of autobook div is reserved for livestreaming starting when admin page is opened.

right side of the div is seperated into 2 columns. 

left column includes:
<div class="form-row">
      <label>NFC Kart No</label>
      <input type="text" placeholder="Kart okuyucu (R20C-USB) ile okutun" id="bNfcTag" autocomplete="off" />
      <div class="tag-hint">İmleci bu alana getirip kitabın NFC etiketini okuyucuya okutun. Boş bırakılırsa bu kaynak NFC ile ödünç alınamaz.</div>
    </div>

<button>

<div class="form-row">
      <label>Raf Yeri</label>
      <input type="text" placeholder="A-12" id="bRaf" />
    </div>
    
<div class="form-row">
      <label>Etiketler (Tag)</label>
      <div class="tag-grid" id="bTagGrid">
        <label class="tag-check"><input type="checkbox"> 📖 Okuma Kitabı</label>
        <label class="tag-check"><input type="checkbox"> 🎓 Akademik</label>
        <label class="tag-check"><input type="checkbox" checked> ⚗️ Fizik</label>
        <label class="tag-check"><input type="checkbox"> 📐 Matematik</label>
        <label class="tag-check"><input type="checkbox"> 🔤 Kince</label>
        <label class="tag-check"><input type="checkbox"> 📅 Edebiyat Tarihi</label>
      </div>
      <!-- Serbest tag girişi: virgülle ayırarak birden fazla tag eklenebilir -->
      <div class="tag-add-row">
        <input type="text" id="bCustomTag" placeholder="Yeni tag... (virgülle ayır: Kimya, 9. Sınıf)" />
        <button onclick="addCustomTags('bTagGrid', 'bCustomTag')">+ Ekle</button>
      </div>
      <div class="tag-hint">Birden fazla tag için virgülle ayırın: "Kimya, 9. Sınıf, Olimpiyat"</div>
    </div>

<div class="sep"></div>
<button class="btn btn-primary" onclick="saveBasili()">💾 Kaydet</button>
 


right column includes: 
    <div class="form-row">
      <label>Ad</label>
      <input type="text" placeholder="Kaynak adı" id="bAd" />
    </div>
    <div class="form-row">
      <label>Yazar</label>
      <input type="text" placeholder="Yazar adı" id="bYazar" />
    </div>
    <div class="form-row">
      <label>Dil</label>
      <div class="lang-row">
        <label><input type="radio" name="bDil" value="TR" checked> TR</label>
        <label><input type="radio" name="bDil" value="EN"> EN</label>
        <label><input type="radio" name="bDil" value="DE"> DE</label>
      </div>
    </div>
    