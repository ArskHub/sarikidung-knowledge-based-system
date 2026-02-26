from flask import Flask, render_template, request, jsonify
from ontology.loader import load_ontology, get_kidung_dataframe
from ontology.rules import KidungDecisionTree
from ontology.query import get_kidung_detail, get_kidung_by_context
import os, pandas as pd

app = Flask(__name__)

# ─── BOOTING ────────────────────────────────────────────────────
onto      = None
ai_engine = None
df = pd.DataFrame(columns=['target','judul','yadnya','upacara','pura','tahap','makna','jenis_sekar'])

try:
    onto      = load_ontology()
    df        = get_kidung_dataframe(onto)
    ai_engine = KidungDecisionTree()
    ai_engine.train(df)
    print("✅ SariKidung siap.")
except Exception as e:
    print(f"❌ Gagal booting: {e}")

# ──────────────────────────────────────────────────────────────────
# ALUR PERTANYAAN:
#   Q1: Yadnya   → selalu tampil
#   Q2: Upacara  → selalu tampil, pilihan dinamis dari Q1
#   Q3: Tahap    → selalu tampil, dengan pilihan "Semua Tahap (Panduan Lengkap)"
#   Q4: Pura     → hanya muncul jika ada >1 pilihan pura yang relevan
# ──────────────────────────────────────────────────────────────────
FEATURES = ['yadnya', 'upacara', 'tahap', 'pura']

QUESTION_LABELS = {
    'yadnya':  'Apa Jenis Yadnya yang akan dilaksanakan?',
    'upacara': 'Pilih Upacara yang sesuai:',
    'tahap':   'Dalam tahapan apa Kidung akan dinyanyikan?',
    'pura':    'Di Pura atau Tempat mana upacara dilaksanakan?',
}

# Opsi khusus "semua tahap" — ditampilkan selalu di posisi pertama Q3
SEMUA_TAHAP = "── Semua Tahap (Panduan Lengkap) ──"

# ─── ROUTES ─────────────────────────────────────────────────────
@app.route('/')
def landing():
    return render_template('pages/index.html')

@app.route('/home')
def home():
    total = len(df) if not df.empty else 0
    return render_template('pages/home.html', total_kidung=total)

@app.route('/browsing')
def browsing():
    return render_template('pages/browsing.html')

@app.route('/library')
def library():
    kidung_list = df.to_dict(orient='records') if not df.empty else []
    return render_template('pages/library.html', kidungs=kidung_list)

@app.route('/about')
def about():
    return render_template('pages/about.html')

@app.route('/questionnaire')
def questionnaire():
    return render_template('pages/questionnaire.html')

# ─── API: GET OPTIONS ────────────────────────────────────────────
@app.route('/get_filtered_options', methods=['POST'])
def get_options():
    if df.empty:
        return jsonify({"status": "error", "message": "Data tidak tersedia."})

    selections = request.json or {}
    tmp = df.copy()

    # Filter berdasarkan jawaban yang sudah ada
    # (kecuali tahap = SEMUA_TAHAP, itu tidak difilter)
    for key, val in selections.items():
        if not val or val in ('None', SEMUA_TAHAP):
            continue
        if key in tmp.columns:
            tmp = tmp[tmp[key].astype(str).str.strip().str.lower()
                      == str(val).strip().lower()]

    # Tentukan pertanyaan berikutnya
    answered = [k for k in FEATURES if k in selections and selections[k]]
    step_index = len(answered)

    if step_index < len(FEATURES):
        next_feat = FEATURES[step_index]

        # ── Q3: Tahap ─────────────────────────────────────────────
        if next_feat == 'tahap':
            tahap_options = sorted([
                str(o).strip() for o in tmp['tahap'].unique()
                if str(o).strip() not in ('None', '', 'nan')
            ])
            # Selalu tambahkan opsi "Semua Tahap" di posisi pertama
            options = [SEMUA_TAHAP] + tahap_options
            return jsonify({
                "status":       "next",
                "next_feature": "tahap",
                "label":        QUESTION_LABELS['tahap'],
                "options":      options,
                "step":         step_index + 1,
                "total_steps":  len(FEATURES),
                "hint":         "Pilih tahap tertentu atau 'Semua Tahap' untuk panduan lengkap upacara.",
            })

        # ── Q4: Pura — lewati jika hanya ≤1 pilihan ──────────────
        if next_feat == 'pura':
            pura_options = sorted([
                str(o).strip() for o in tmp['pura'].unique()
                if str(o).strip() not in ('None', '', 'nan')
            ])
            if len(pura_options) <= 1:
                return jsonify({"status": "complete"})
            options = pura_options

        # ── Q1 & Q2 ───────────────────────────────────────────────
        else:
            options = sorted([
                str(o).strip() for o in tmp[next_feat].unique()
                if str(o).strip() not in ('None', '', 'nan')
            ])

        if not options:
            return jsonify({"status": "complete"})

        return jsonify({
            "status":       "next",
            "next_feature": next_feat,
            "label":        QUESTION_LABELS.get(next_feat, f"Pilih {next_feat}:"),
            "options":      options,
            "step":         step_index + 1,
            "total_steps":  len(FEATURES),
        })

    return jsonify({"status": "complete"})


# ─── API: PREDICT ────────────────────────────────────────────────
@app.route('/predict', methods=['POST'])
def predict():
    try:
        if ai_engine is None or onto is None:
            return jsonify({"status": "error", "message": "Sistem belum siap."})

        data = request.json or {}

        # ── Mode library: lookup langsung ──
        if 'target' in data and len(data) == 1:
            detail = get_kidung_detail(onto, data['target'])
            if detail:
                return jsonify({"status": "success", **detail})
            return jsonify({"status": "error", "message": "Kidung tidak ditemukan."})

        # ── Mode expert system ──
        cleaned    = {k: str(v).strip() for k, v in data.items()}
        print(f"🔍 /predict dipanggil dengan: {cleaned}")

        tahap_pilih = cleaned.get('tahap', '')
        mode_semua  = (not tahap_pilih or tahap_pilih in ('None', SEMUA_TAHAP))

        # Prediksi kidung utama via decision tree
        nama = ai_engine.predict({k: v for k, v in cleaned.items() if k != 'tahap' or not mode_semua})

        # Ambil kidung sesuai konteks
        per_tahap = get_kidung_by_context(
            onto, df,
            yadnya       = cleaned.get('yadnya'),
            upacara      = cleaned.get('upacara'),
            pura         = cleaned.get('pura'),
            tahap_filter = None if mode_semua else tahap_pilih,
        )

        # Fallback
        if not per_tahap:
            return jsonify({
                "status":  "fallback",
                "message": (
                    "Kidung untuk konteks ini belum tersedia dalam basis pengetahuan. "
                    "Coba pilih konteks yang lebih umum atau konsultasikan dengan pemangku setempat."
                ),
                "konteks": cleaned,
            })

        detail_utama = get_kidung_detail(onto, nama) if nama else None
        if not detail_utama:
            detail_utama = per_tahap[0]

        explanation    = ai_engine.build_explanation(cleaned, detail_utama.get('judul', ''))
        top_candidates = ai_engine.get_top_candidates(
            {k: v for k, v in cleaned.items() if k in ['yadnya','upacara','pura']}, n=3
        )

        return jsonify({
            "status":           "success",
            "judul":            detail_utama.get('judul', ''),
            "teks":             detail_utama.get('teks', '-'),
            "makna":            detail_utama.get('makna_mendalam', '-'),
            "bahasa":           detail_utama.get('bahasa', '-'),
            **detail_utama,
            "kidung_per_tahap": per_tahap,
            "explanation":      explanation,
            "top_candidates":   top_candidates,
            "total_ditemukan":  len(per_tahap),
            "mode_semua_tahap": mode_semua,
            "konteks":          cleaned,
        })

    except Exception as e:
        import traceback
        print(f"❌ /predict error: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Error sistem: {str(e)}"}), 500


@app.route('/api/kidung/<nama>', methods=['GET'])
def detail_kidung(nama):
    if onto is None:
        return jsonify({"status": "error", "message": "Sistem belum siap."})
    detail = get_kidung_detail(onto, nama)
    if detail:
        return jsonify({"status": "success", **detail})
    return jsonify({"status": "error", "message": "Kidung tidak ditemukan."})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
