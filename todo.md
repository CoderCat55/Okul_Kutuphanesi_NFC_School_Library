2) for div autobook 
div has width of student activities div. height of the "panel basili". horizantally left half of autobook div is reserved for livestreaming starting when admin page is opened.
right side of the div is seperated into 2 columns. 

left column includes:
<div class="form-row">
      <label>NFC Kart No</label>
      <input type="text" placeholder="Kart okuyucu (R20C-USB) ile okutun" id="bNfcTag" autocomplete="off" />
      <div class="tag-hint">İmleci bu alana getirip kitabın NFC etiketini okuyucuya okutun. Boş bırakılırsa bu kaynak NFC ile ödünç alınamaz.</div>
    </div>

<button class="save frame and send it to gemini">


<div class="form-row">
      <label>Raf Yeri</label>
      <input type="text" placeholder="A-12" id="bRaf" />
    </div>
    
<div class="form-row">
      <label>Etiketler (Tag)</label>
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

the functionality of this part would be to livestream camera also capture a photo when button is pressed. then returned answer will be filled to right column (right column should still allow for edits)
another explanation I would capture a frame when user pressed the button send t to gemini to fill up the right column. 

do not overcomplicate things but just fix the code. After reviewing code and undertanding how to solve this problem. ell me where to change and what to change specifically 
how this would be implemented to current system , which parts should be changed which parts should be added and where.
You may only write which parts of the code I should change and where changes should be made to save time instead of writing the whole script again.