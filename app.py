from flask import Flask, render_template, request, jsonify
from ontology.loader import load_ontology, get_kidung_dataframe, get_dropdown_options
from ontology.rules import KidungDecisionTree
from ontology.query import get_kidung_detail
import os

app = Flask(__name__)

# ==========================================
# BOOTING SYSTEM & KNOWLEDGE BASE
# ==========================================
try:
    # Memuat file OWL dari folder ontology
    onto = load_ontology()
    # Mengambil data awal untuk Library
    df = get_kidung_dataframe(onto)
    # Inisialisasi AI (Decision Tree)
    ai_engine = KidungDecisionTree()
    ai_engine.train(df)
    print("✅ Sistem Berhasil Booting: Ontology & AI Ready.")
except Exception as e:
    print(f"❌ Gagal Memuat Sistem: {e}")

# ==========================================
# ROUTES - NAVIGATION (Folder: templates/pages/)
# ==========================================

@app.route('/')
def index():
    # Mengarah ke templates/pages/index.html
    return render_template('pages/index.html')

@app.route('/home')
def home():
    # Mengarah ke templates/pages/home.html
    return render_template('pages/home.html')

@app.route('/browsing')
def browsing():
    # Mengambil data dropdown (Yadnya, Upacara, dll) langsung dari Ontology
    options = get_dropdown_options(onto)
    return render_template('pages/browsing.html', **options)

@app.route('/library')
def library():
    # Mengonversi dataframe ke list dictionary agar bisa dibaca looping Jinja2
    kidung_list = df.to_dict(orient='records')
    return render_template('pages/library.html', kidungs=kidung_list)

@app.route('/questionnaire')
def questionnaire():
    return render_template('pages/questionnaire.html')

@app.route('/about')
def about():
    return render_template('pages/about.html')

# ==========================================
# API ENDPOINTS (Logic Processor)
# ==========================================

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        # 1. AI memprediksi ID Individu Kidung
        nama_individu = ai_engine.predict(data)
        
        if nama_individu:
            # 2. Query ke Ontology untuk mengambil Teks, Bahasa, dan Makna
            detail = get_kidung_detail(onto, nama_individu)
            if detail:
                return jsonify({
                    "status": "success", 
                    "judul": nama_individu,
                    **detail
                })
        
        return jsonify({
            "status": "error", 
            "message": "Kombinasi kriteria tidak ditemukan dalam database pakar."
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ==========================================
# RUN APP
# ==========================================
if __name__ == '__main__':
    # debug=True sangat membantu untuk melihat error detail di browser
    app.run(debug=True, port=5000)