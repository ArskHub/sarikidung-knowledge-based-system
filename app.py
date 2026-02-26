from flask import Flask, render_template, request, jsonify
from ontology.loader import load_ontology, get_kidung_dataframe
from ontology.rules import KidungDecisionTree
from ontology.query import get_kidung_detail, get_kidung_by_context
import os, pandas as pd, requests, time
from dotenv import load_dotenv

load_dotenv()

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
    print("SariKidung siap.")
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

SEMUA_TAHAP = "── Semua Tahap (Panduan Lengkap) ──"

# ─── KONFIGURASI GROQ ───────────────────────────────────────────
# Daftar gratis di console.groq.com → API Keys → Create API Key
# Ganti GROQ_API_KEY di file .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"  # gratis, cepat, pintar

SYSTEM_PROMPT = """Kamu adalah asisten ahli bernama "SariBot" yang khusus membahas:
- Kidung Panca Yadnya Bali (lirik, makna, fungsi, teknik menyanyi)
- Upacara adat Hindu Bali (Dewa Yadnya, Pitra Yadnya, Manusa Yadnya, Bhuta Yadnya, Rsi Yadnya)
- Dharma Gita, Sekar Alit, Sekar Madya, Sekar Agung, Wargasari
- Filosofi dan sastra Hindu Bali

ATURAN PENTING:
1. Jawab HANYA pertanyaan seputar Kidung dan upacara Bali.
2. Jika ditanya di luar topik, tolak dengan sopan dan arahkan kembali ke topik Kidung/upacara Bali.
3. Gunakan bahasa Indonesia yang ramah dan mudah dipahami.
4. Boleh sesekali menyisipkan kata Bali yang relevan (contoh: "ring", "pinaka", "mangda").
5. Jawaban singkat dan padat — maksimal 3-4 paragraf.
6. Jangan pernah mengarang informasi yang tidak kamu yakini kebenarannya."""


# ═══════════════════════════════════════════════════════════════
# ROUTES — HALAMAN
# ═══════════════════════════════════════════════════════════════

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


@app.route('/chat')
def chat_page():
    return render_template('pages/chat.html')


# ═══════════════════════════════════════════════════════════════
# API — EXPERT SYSTEM: GET OPTIONS
# ═══════════════════════════════════════════════════════════════

@app.route('/get_filtered_options', methods=['POST'])
def get_options():
    if df.empty:
        return jsonify({"status": "error", "message": "Data tidak tersedia."})

    selections = request.json or {}
    tmp = df.copy()

    for key, val in selections.items():
        if not val or val in ('None', SEMUA_TAHAP):
            continue
        if key in tmp.columns:
            tmp = tmp[tmp[key].astype(str).str.strip().str.lower()
                      == str(val).strip().lower()]

    answered   = [k for k in FEATURES if k in selections and selections[k]]
    step_index = len(answered)

    if step_index < len(FEATURES):
        next_feat = FEATURES[step_index]

        if next_feat == 'tahap':
            tahap_options = sorted([
                str(o).strip() for o in tmp['tahap'].unique()
                if str(o).strip() not in ('None', '', 'nan')
            ])
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

        if next_feat == 'pura':
            pura_options = sorted([
                str(o).strip() for o in tmp['pura'].unique()
                if str(o).strip() not in ('None', '', 'nan')
            ])
            if len(pura_options) <= 1:
                return jsonify({"status": "complete"})
            options = pura_options
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


# ═══════════════════════════════════════════════════════════════
# API — EXPERT SYSTEM: PREDICT
# ═══════════════════════════════════════════════════════════════

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if ai_engine is None or onto is None:
            return jsonify({"status": "error", "message": "Sistem belum siap."})

        data = request.json or {}

        if 'target' in data and len(data) == 1:
            detail = get_kidung_detail(onto, data['target'])
            if detail:
                return jsonify({"status": "success", **detail})
            return jsonify({"status": "error", "message": "Kidung tidak ditemukan."})

        cleaned     = {k: str(v).strip() for k, v in data.items()}
        tahap_pilih = cleaned.get('tahap', '')
        mode_semua  = (not tahap_pilih or tahap_pilih in ('None', SEMUA_TAHAP))

        nama = ai_engine.predict({
            k: v for k, v in cleaned.items()
            if k != 'tahap' or not mode_semua
        })

        per_tahap = get_kidung_by_context(
            onto, df,
            yadnya       = cleaned.get('yadnya'),
            upacara      = cleaned.get('upacara'),
            pura         = cleaned.get('pura'),
            tahap_filter = None if mode_semua else tahap_pilih,
        )

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
            {k: v for k, v in cleaned.items() if k in ['yadnya', 'upacara', 'pura']},
            n=3
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


# ═══════════════════════════════════════════════════════════════
# API — CHAT AI (Groq - LLaMA 3.1)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
            return jsonify({
                "status": "error",
                "reply":  "API key Groq belum dikonfigurasi. Silakan isi GROQ_API_KEY di file .env"
            })

        data    = request.json or {}
        pesan   = data.get('message', '').strip()
        riwayat = data.get('history', [])

        if not pesan:
            return jsonify({"status": "error", "reply": "Pesan kosong."})

        # Bangun messages untuk Groq (format OpenAI-compatible)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Tambah riwayat percakapan sebelumnya (max 10 pesan terakhir)
        for item in riwayat[-10:]:
            role = "user" if item.get('role') == 'user' else "assistant"
            messages.append({
                "role":    role,
                "content": item.get('text', '')
            })

        # Tambah pesan user saat ini
        messages.append({"role": "user", "content": pesan})

        # Kirim ke Groq API
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type":  "application/json"
            },
            json={
                "model":       GROQ_MODEL,
                "messages":    messages,
                "max_tokens":  1024,
                "temperature": 0.7
            },
            timeout=30
        )

        print(f"🔍 Groq Status: {resp.status_code}")

        if resp.status_code == 429:
            return jsonify({
                "status": "error",
                "reply":  "Server AI sedang sibuk. Tunggu beberapa detik lalu coba lagi. 🙏"
            })

        if resp.status_code != 200:
            print(f"🔍 Groq Error: {resp.text[:300]}")
            return jsonify({
                "status": "error",
                "reply":  f"Chat AI error: {resp.status_code}. Periksa API key Groq kamu."
            })

        reply = resp.json()['choices'][0]['message']['content']
        return jsonify({"status": "success", "reply": reply})

    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "reply": "Timeout — server AI tidak merespons. Coba lagi."})
    except Exception as e:
        print(f"❌ /api/chat error: {e}")
        return jsonify({"status": "error", "reply": "Terjadi kesalahan pada sistem chat."})


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, port=5000)