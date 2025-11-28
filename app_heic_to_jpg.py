import io
import zipfile
import os
from flask import Flask, render_template, request, send_file
from PIL import Image
from pillow_heif import register_heif_opener

# Ενεργοποίηση υποστήριξης HEIC
register_heif_opener()

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_images():
    uploaded_files = request.files.getlist('heic_files')
    
    if not uploaded_files or uploaded_files[0].filename == '':
        return "Δεν επιλέχθηκαν αρχεία", 400

    # Δημιουργία buffer στη μνήμη για το ZIP
    zip_buffer = io.BytesIO()

    # Μετρητής για να δούμε αν μετατράπηκε έστω και ένα αρχείο
    files_converted = 0

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in uploaded_files:
            filename = file.filename.lower()
            
            # Έλεγχος αν είναι HEIC
            if filename.endswith('.heic'):
                try:
                    # Άνοιγμα και μετατροπή
                    image = Image.open(file)
                    image = image.convert("RGB")
                    
                    # Αλλαγή κατάληξης
                    new_filename = filename.rsplit('.', 1)[0] + ".jpg"
                    
                    # Αποθήκευση στο ZIP (μέσω μνήμης)
                    img_io = io.BytesIO()
                    image.save(img_io, 'JPEG', quality=90)
                    zip_file.writestr(new_filename, img_io.getvalue())
                    files_converted += 1
                except Exception as e:
                    print(f"Σφάλμα στο αρχείο {filename}: {e}")

    if files_converted == 0:
        return "Δεν βρέθηκαν έγκυρα αρχεία .HEIC ή υπήρξε σφάλμα.", 400

    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='converted_images.zip'
    )

if __name__ == '__main__':
    # Το port=5000 είναι η πόρτα που θα ακούει η εφαρμογή
    app.run(debug=True, port=5000)