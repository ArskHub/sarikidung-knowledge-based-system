from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ontology.loader import load_ontology, get_kidung_dataframe
from owlready2 import destroy_entity as destroy
from ontology.rules import KidungDecisionTree
from ontology.query import get_kidung_detail, get_kidung_by_context
import os, pandas as pd, requests, time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ─── CONFIG ─────────────────────────────────────────────────────
app.config['SECRET_KEY']         = os.getenv('SECRET_KEY', 'sarikidung-secret-2026')
app.config['SQLALCHEMY_DATABASE_URI']         = 'sqlite:///admin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']  = False

# ─── EXTENSIONS ─────────────────────────────────────────────────
db           = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view        = 'admin_login'
login_manager.login_message     = 'Silakan login terlebih dahulu.'
login_manager.login_message_category = 'warning'

# ─── MODEL USER ─────────────────────────────────────────────────
class AdminUser(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

# ─── INIT DB & SEED ADMIN ───────────────────────────────────────
def init_db():
    with app.app_context():
        db.create_all()
        # Buat akun admin default jika belum ada
        if not AdminUser.query.filter_by(username='admin').first():
            admin = AdminUser(
                username = 'admin',
                password = generate_password_hash('sarikidung2026')
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Akun admin dibuat: admin / sarikidung2026")

# ─── BOOTING ONTOLOGI ───────────────────────────────────────────
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
FEATURES = ['yadnya', 'upacara', 'tahap', 'pura']

QUESTION_LABELS = {
    'yadnya':  'Apa Jenis Yadnya yang akan dilaksanakan?',
    'upacara': 'Pilih Upacara yang sesuai:',
    'tahap':   'Dalam tahapan apa Kidung akan dinyanyikan?',
    'pura':    'Di Pura atau Tempat mana upacara dilaksanakan?',
}

SEMUA_TAHAP = "── Semua Tahap (Panduan Lengkap) ──"

# ─── GROQ CONFIG ────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"

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
# ROUTES — HALAMAN PUBLIK
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
# ROUTES — ADMIN
# ═══════════════════════════════════════════════════════════════

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Kalau sudah login, langsung ke panel
    if current_user.is_authenticated:
        return redirect(url_for('admin_panel'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user     = AdminUser.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login berhasil. Rahajeng! 🙏', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Username atau password salah.', 'danger')

    return render_template('admin/login.html')


@app.route('/admin/panel')
@login_required
def admin_panel():
    total_kidung = len(df) if not df.empty else 0
    stats_yadnya = {}
    if not df.empty and 'yadnya' in df.columns:
        stats_yadnya = df['yadnya'].value_counts().to_dict()
    # Kirim semua kidung untuk tabel CRUD
    all_kidungs = []
    if not df.empty:
        for _, row in df.iterrows():
            detail = get_kidung_detail(onto, row['target']) or {}
            all_kidungs.append({
                'target':     row['target'],
                'judul':      detail.get('judul', row['target'].replace('_',' ')),
                'yadnya':     row.get('yadnya',''),
                'upacara':    row.get('upacara',''),
                'jenis_sekar':row.get('jenis_sekar',''),
                'has_audio':  detail.get('has_audio', False),
            })
    return render_template('admin/panel.html',
                           total_kidung=total_kidung,
                           stats_yadnya=stats_yadnya,
                           all_kidungs=all_kidungs)


@app.route('/admin/tambah', methods=['GET', 'POST'])
@login_required
def admin_tambah():
    if request.method == 'POST':
        # Ambil data dari form
        data = {
            'judul':         request.form.get('judul', '').strip(),
            'yadnya':        request.form.get('yadnya', '').strip(),
            'upacara':       request.form.get('upacara', '').strip(),
            'tahap':         request.form.get('tahap', '').strip(),
            'pura':          request.form.get('pura', '').strip(),
            'jenis_sekar':   request.form.get('jenis_sekar', '').strip(),
            'bahasa':        request.form.get('bahasa', '').strip(),
            'teks':          request.form.get('teks', '').strip(),
            'makna':         request.form.get('makna', '').strip(),
            'teknik':        request.form.get('teknik', '').strip(),
            'sumber':        request.form.get('sumber', '').strip(),
        }
        # Validasi minimal
        if not data['judul'] or not data['yadnya']:
            flash('Judul dan Jenis Yadnya wajib diisi.', 'danger')
            return render_template('admin/tambah.html', data=data)

        # TODO: Simpan ke ontologi OWL
        # Saat ini flash sukses dulu — integrasi ontologi menyusul
        flash(f'Kidung "{data["judul"]}" berhasil ditambahkan! (pending sync ke ontologi)', 'success')
        return redirect(url_for('admin_panel'))

    return render_template('admin/tambah.html', data={})


@app.route('/admin/ganti-password', methods=['GET', 'POST'])
@login_required
def admin_ganti_password():
    if request.method == 'POST':
        lama  = request.form.get('password_lama', '')
        baru  = request.form.get('password_baru', '')
        ulang = request.form.get('password_ulang', '')

        if not check_password_hash(current_user.password, lama):
            flash('Password lama salah.', 'danger')
        elif len(baru) < 8:
            flash('Password baru minimal 8 karakter.', 'danger')
        elif baru != ulang:
            flash('Konfirmasi password tidak cocok.', 'danger')
        else:
            current_user.password = generate_password_hash(baru)
            db.session.commit()
            flash('Password berhasil diubah!', 'success')
            return redirect(url_for('admin_panel'))

    return render_template('admin/ganti_password.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Logout berhasil.', 'info')
    return redirect(url_for('admin_login'))


# ═══════════════════════════════════════════════════════════════
# API — EXPERT SYSTEM
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








@app.route('/admin/kidung')
@login_required
def admin_kidung():
    all_kidungs = []
    if not df.empty:
        for _, row in df.iterrows():
            detail = get_kidung_detail(onto, row['target']) or {}
            all_kidungs.append({
                'target':      row['target'],
                'judul':       detail.get('judul', row['target'].replace('_',' ')),
                'yadnya':      row.get('yadnya',''),
                'upacara':     row.get('upacara',''),
                'jenis_sekar': row.get('jenis_sekar',''),
                'has_audio':   detail.get('has_audio', False),
            })
    return render_template('admin/kidung.html', all_kidungs=all_kidungs)

@app.route('/admin/edit/<target>', methods=['GET', 'POST'])
@login_required
def admin_edit(target):
    if request.method == 'POST':
        data = {
            'target':    request.form.get('target', target).strip(),
            'judul':     request.form.get('judul', '').strip(),
            'yadnya':    request.form.get('yadnya', '').strip(),
            'upacara':   request.form.get('upacara', '').strip(),
            'tahap':     request.form.get('tahap', '').strip(),
            'pura':      request.form.get('pura', '').strip(),
            'jenis_sekar':request.form.get('jenis_sekar', '').strip(),
            'bahasa':    request.form.get('bahasa', '').strip(),
            'teks':      request.form.get('teks', '').strip(),
            'makna':     request.form.get('makna', '').strip(),
            'teknik':    request.form.get('teknik', '').strip(),
            'sumber':    request.form.get('sumber', '').strip(),
            'url_audio': request.form.get('url_audio', '').strip(),
        }
        try:
            import re as _re
            from ontology.query import get_platform
            from ontology.loader import ONTO_PATH
            onto_admin = load_ontology()
            kidung = onto_admin.search_one(iri=f"*{target}")
            if not kidung:
                flash('Kidung tidak ditemukan.', 'danger')
                return redirect(url_for('admin_panel'))

            # Update data properties
            if data['judul']:     kidung.judulKidung    = [data['judul']]
            if data['bahasa']:    kidung.bahasa          = [data['bahasa']]
            if data['teks']:      kidung.teksKidung      = [data['teks']]
            if data['sumber']:    kidung.sumberData      = [data['sumber']]
            if data['makna']:     kidung.maknaMendalam   = [data['makna']]
            if data['teknik']:    kidung.teknikMenyanyi  = [data['teknik']]
            if data['url_audio']:
                kidung.url_audio = [data['url_audio']]
                plat = get_platform(data['url_audio'])
                if plat: kidung.platform_audio = [plat]
            else:
                kidung.url_audio     = []
                kidung.platform_audio = []

            yadnya_map = {
                'Dewa Yadnya': 'DewaYadnya', 'Pitra Yadnya': 'PitraYadnya',
                'Manusa Yadnya': 'ManusaYadnya', 'Bhuta Yadnya': 'BhutaYadnya',
                'Rsi Yadnya': 'RsiYadnya'
            }
            sekar_map = {
                'Sekar Alit': 'KidungSekarAlit', 'Sekar Madya': 'KidungSekarMadya',
                'Sekar Agung': 'KidungWargasari'
            }
            if data['yadnya'] in yadnya_map:
                ref = onto_admin.search_one(iri=f"*{yadnya_map[data['yadnya']]}")
                if ref: kidung.memilikiJenisYadnya = [ref]
            if data['jenis_sekar'] in sekar_map:
                ref = onto_admin.search_one(iri=f"*{sekar_map[data['jenis_sekar']]}")
                if ref: kidung.memilikiJenisKidung = [ref]
            for field, prop in [('upacara','digunakanPadaUpacara'),('tahap','digunakanPadaTahap'),('pura','digunakanDiPura')]:
                if data[field]:
                    clean = data[field].replace(' ', '_')
                    ref = onto_admin.search_one(iri=f"*{clean}_Ref") or onto_admin.search_one(iri=f"*{clean}")
                    if ref: setattr(kidung, prop, [ref])

            onto_admin.save(file=ONTO_PATH, format="rdfxml")
            global df_kidung, tree
            onto_new = load_ontology()
            df_kidung = get_kidung_dataframe(onto_new)
            tree = KidungDecisionTree()
            tree.train(df_kidung)

            flash(f'Kidung "{data["judul"]}" berhasil diperbarui!', 'success')
            return redirect(url_for('admin_panel'))
        except Exception as e:
            flash(f'Gagal update: {str(e)}', 'danger')
            return render_template('admin/edit.html', data=data)

    # GET — load data kidung untuk form
    detail = get_kidung_detail(onto, target)
    if not detail:
        flash('Kidung tidak ditemukan.', 'danger')
        return redirect(url_for('admin_panel'))
    detail['target'] = target
    return render_template('admin/edit.html', data=detail)


@app.route('/admin/hapus/<target>', methods=['POST'])
@login_required
def admin_hapus(target):
    try:
        from ontology.loader import ONTO_PATH
        onto_admin = load_ontology()
        kidung = onto_admin.search_one(iri=f"*{target}")
        if not kidung:
            flash('Kidung tidak ditemukan.', 'danger')
            return redirect(url_for('admin_panel'))

        judul = (kidung.judulKidung[0] if kidung.judulKidung else target.replace('_',' '))
        destroy(kidung)
        onto_admin.save(file=ONTO_PATH, format="rdfxml")

        global df_kidung, tree
        onto_new = load_ontology()
        df_kidung = get_kidung_dataframe(onto_new)
        tree = KidungDecisionTree()
        tree.train(df_kidung)

        flash(f'Kidung "{judul}" berhasil dihapus.', 'success')
    except Exception as e:
        flash(f'Gagal hapus: {str(e)}', 'danger')
    return redirect(url_for('admin_panel'))

@app.route('/api/options', methods=['GET'])
def api_options():
    """Return semua pilihan dropdown dari ontologi untuk form admin."""
    if onto is None:
        return jsonify({"status": "error"})
    try:
        def get_individuals(class_name):
            cls = onto.search_one(iri=f"*{class_name}")
            if not cls:
                return []
            return sorted([
                ind.name.replace("_Ref", "").replace("_", " ").strip()
                for ind in cls.instances()
                if ind.name.endswith("_Ref")
            ])

        return jsonify({
            "status":   "success",
            "upacara":  get_individuals("UpacaraPancaYadnya"),
            "tahap":    get_individuals("TahapPelaksanaanUpacara"),
            "pura":     get_individuals("PuraTempatPelaksanaan"),
            "makna":    get_individuals("MaknaKidung"),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/kidung/<nama>', methods=['GET'])
def detail_kidung(nama):
    if onto is None:
        return jsonify({"status": "error", "message": "Sistem belum siap."})
    detail = get_kidung_detail(onto, nama)
    if detail:
        return jsonify({"status": "success", **detail})
    return jsonify({"status": "error", "message": "Kidung tidak ditemukan."})


# ═══════════════════════════════════════════════════════════════
# API — CHAT AI (Groq)
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

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for item in riwayat[-10:]:
            role = "user" if item.get('role') == 'user' else "assistant"
            messages.append({"role": role, "content": item.get('text', '')})
        messages.append({"role": "user", "content": pesan})

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

        if resp.status_code == 429:
            return jsonify({"status": "error", "reply": "Server AI sedang sibuk. Tunggu beberapa detik lalu coba lagi. 🙏"})
        if resp.status_code != 200:
            return jsonify({"status": "error", "reply": f"Chat AI error: {resp.status_code}."})

        reply = resp.json()['choices'][0]['message']['content']
        return jsonify({"status": "success", "reply": reply})

    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "reply": "Timeout — server AI tidak merespons. Coba lagi."})
    except Exception as e:
        print(f"❌ /api/chat error: {e}")
        return jsonify({"status": "error", "reply": "Terjadi kesalahan pada sistem chat."})


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)