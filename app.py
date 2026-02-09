from flask import Flask, render_template, request, jsonify
from ontology.loader import load_ontology, get_kidung_dataframe
from ontology.rules import KidungDecisionTree
from ontology.query import get_kidung_detail
import os
import pandas as pd

app = Flask(__name__)

# ==========================================
# BOOTING SYSTEM & KNOWLEDGE BASE
# ==========================================
# Inisialisasi variabel global agar TIDAK NameError jika booting gagal
onto = None
ai_engine = None
# Membuat DataFrame kosong dengan kolom yang sesuai sebagai cadangan
df = pd.DataFrame(columns=['target', 'yadnya', 'upacara', 'tahap', 'makna', 'pura'])

try:
    onto = load_ontology()
    df = get_kidung_dataframe(onto)
    ai_engine = KidungDecisionTree()
    ai_engine.train(df)
    print("✅ Sistem Berhasil Booting: Ontology & AI Ready.")
except Exception as e:
    print(f"❌ Gagal Memuat Sistem: {e}")

# Urutan kriteria pertanyaan untuk Expert System
FEATURES = ['yadnya', 'upacara', 'tahap', 'makna', 'pura']

# ==========================================
# ROUTES - NAVIGATION
# ==========================================

@app.route('/')
def landing():
    """Halaman Landing Page (Halaman Transparan dengan tombol ENTER ARCHIVE)"""
    return render_template('pages/index.html')

@app.route('/home')
def home():
    """Halaman Utama (Halaman dengan tulisan Rahajeng Rauh)"""
    return render_template('pages/home.html')

@app.route('/browsing')
def browsing():
    # Menggunakan df yang sudah diinisialisasi (kosong atau isi)
    yadnyas = sorted([y for y in df['yadnya'].unique() if y != "None"]) if not df.empty else []
    return render_template('pages/browsing.html', yadnyas=yadnyas)

@app.route('/library')
def library():
    # Menggunakan df yang sudah diinisialisasi
    kidung_list = df.to_dict(orient='records') if not df.empty else []
    return render_template('pages/library.html', kidungs=kidung_list)

@app.route('/about')
def about():
    return render_template('pages/about.html')

@app.route('/questionnaire')
def questionnaire():
    return render_template('pages/questionnaire.html')

# ==========================================
# API ENDPOINTS (Logic Processor)
# ==========================================

@app.route('/get_filtered_options', methods=['POST'])
def get_options():
    selections = request.json
    if df.empty:
        return jsonify({"status": "error", "message": "Data tidak tersedia"})
        
    temp_df = df.copy()

    # 1. Filter data dengan toleransi spasi (strip)
    for key, val in selections.items():
        if val and val != "None":
            # Pastikan perbandingan dilakukan dengan string yang bersih dari spasi di ujung
            temp_df = temp_df[temp_df[key].astype(str).str.strip() == str(val).strip()]

    current_step_count = len(selections)
    if current_step_count < len(FEATURES):
        next_feature = FEATURES[current_step_count]
        # 2. Ambil opsi unik dan bersihkan hasilnya
        options = sorted([str(opt).strip() for opt in temp_df[next_feature].unique() if str(opt) != "None"])
        
        return jsonify({
            "status": "next",
            "next_feature": next_feature,
            "options": options
        })
    
    return jsonify({"status": "complete"})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if ai_engine is None:
            return jsonify({"status": "error", "message": "AI Engine tidak siap"})
            
        data = request.json
        # 1. Bersihkan input dari spasi gaib
        cleaned_data = {k: str(v).strip() for k, v in data.items()}
        
        # AI memprediksi nama individu asli (misal: Kidung_Wargasari_Ref)
        nama_individu = ai_engine.predict(cleaned_data)
        
        if nama_individu:
            # PENTING: Gunakan nama asli hasil prediksi AI untuk ambil detail
            detail = get_kidung_detail(onto, nama_individu)
            
            if detail:
                # Judul untuk tampilan di web baru boleh kita bersihkan
                judul_tampilan = str(nama_individu).replace("_Ref", "").replace("_", " ")
                
                return jsonify({
                    "status": "success", 
                    "judul": judul_tampilan,
                    **detail
                })
        
        return jsonify({
            "status": "error", 
            "message": "Maaf, sistem tidak menemukan Kidung yang sesuai."
        })
    except Exception as e:
        print(f"Error pada /predict: {e}")
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)