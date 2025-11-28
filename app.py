# ... (Ο υπάρχων κώδικας εισαγωγής βιβλιοθηκών) ...

from flask import Flask, request, send_file, render_template, abort
from PIL import Image
from pillow_heif import register_heif_opener
import io
import zipfile
import os
import shutil

register_heif_opener()

app = Flask(__name__)

# ... (Ο υπάρχων κώδικας για την αρχική σελίδα) ...

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    files = request.files.getlist('heic_files')
    
    # -----------------------------------------------------------
    # ΝΕΟΣ ΕΛΕΓΧΟΣ: Περιορισμός 10 αρχείων
    # -----------------------------------------------------------
    if not files:
        return "Δεν βρέθηκαν αρχεία.", 400
    
    if len(files) > 10:
        return f"Υπέρβαση ορίου. Επιτρέπονται μόνο 10 αρχεία, αλλά λάβαμε {len(files)}.", 413 # 413 Request Entity Too Large
    # -----------------------------------------------------------

    # Δημιουργία προσωρινού χώρου
    temp_dir = 'temp_converted'
    os.makedirs(temp_dir, exist_ok=True)
    
    # Δημιουργία προσωρινού buffer για το ZIP
    zip_buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, file_storage in enumerate(files):
                if file_storage.filename.lower().endswith('.heic'):
                    try:
                        # Ανάγνωση αρχείου σε bytes
                        heic_bytes = file_storage.read()
                        heif_image = Image.open(io.BytesIO(heic_bytes))
                        
                        # Μετατροπή σε RGB αν είναι απαραίτητο (για JPG)
                        if heif_image.mode not in ('RGB', 'RGBA'):
                            heif_image = heif_image.convert('RGB')
                        
                        # Δημιουργία buffer για το JPG
                        jpg_buffer = io.BytesIO()
                        # Αφαίρεση της επέκτασης HEIC και προσθήκη JPG
                        jpg_filename = os.path.splitext(file_storage.filename)[0] + '.jpg'
                        
                        # Αποθήκευση ως JPG (ποιότητα 90)
                        heif_image.save(jpg_buffer, format='JPEG', quality=90)
                        jpg_buffer.seek(0)
                        
                        # Προσθήκη του JPG στο ZIP
                        zf.writestr(jpg_filename, jpg_buffer.getvalue())

                    except Exception as e:
                        # Εδώ μπορούμε να αγνοήσουμε τα σφάλματα μετατροπής
                        print(f"Σφάλμα μετατροπής για το αρχείο {file_storage.filename}: {e}")
                        continue
        
        # Επιστροφή του ZIP αρχείου
        zip_buffer.seek(0)
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='converted_images.zip')

    finally:
        # Καθαρισμός του προσωρινού φακέλου (αν και δεν χρησιμοποιείται στο Render)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    # Χρησιμοποιούμε θύρα 5000 για τοπική ανάπτυξη
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))