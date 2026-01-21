from flask import Flask, render_template, request, jsonify
from ontology.loader import load_ontology, get_kidung_dataframe, get_dropdown_options
from ontology.rules import KidungDecisionTree
from ontology.query import get_kidung_detail

app = Flask(__name__)

# ==========================================
# BOOTING SYSTEM & KNOWLEDGE BASE
# ==========================================
onto = load_ontology()
df = get_kidung_dataframe(onto)
ai_engine = KidungDecisionTree()
ai_engine.train(df)

# ==========================================
# ROUTES - NAVIGATION
# ==========================================

@app.route('/')
def index():
    """Halaman Splash/Landing awal"""
    return render_template('pages/index.html')

@app.route('/home')
def home():
    """Halaman Dashboard Utama"""
    return render_template('pages/home.html')

@app.route('/browsing')
def browsing():
    """Halaman Expert System (AI)"""
    options = get_dropdown_options(onto)
    return render_template('pages/browsing.html', **options)

@app.route('/library')
def library():
    """Halaman Pustaka Kidung (Daftar Manual)"""
    # Mengubah dataframe menjadi list of dictionary agar mudah dibaca oleh Jinja2
    kidung_list = df.to_dict(orient='records')
    return render_template('pages/library.html', kidungs=kidung_list)

@app.route('/questionnaire')
def questionnaire():
    """Halaman Evaluasi Sistem"""
    return render_template('pages/questionnaire.html')

@app.route('/about')
def about():
    """Halaman Metodologi & Profil"""
    return render_template('pages/about.html')

# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint untuk memproses logika Decision Tree"""
    data = request.json
    nama_individu = ai_engine.predict(data)
    
    if nama_individu:
        detail = get_kidung_detail(onto, nama_individu)
        if detail:
            return jsonify({"status": "success", **detail})
            
    return jsonify({"status": "error", "message": "Kidung tidak ditemukan untuk kombinasi ini."})

# ==========================================
# RUN APP
# ==========================================
if __name__ == '__main__':
    app.run(debug=True)