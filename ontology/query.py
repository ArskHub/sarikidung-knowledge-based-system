def get_kidung_detail(onto, nama_individu):
    try:
        kidung = onto.search_one(iri=f"*{nama_individu}")
        if not kidung:
            return None

        def s(p):
            try: return str(p[0]).strip() if p else ""
            except: return ""
        def o(p):
            try: return p[0].name.replace("_Ref","").replace("_"," ").strip() if p else ""
            except: return ""
        def i(p):
            try: return int(p[0]) if p else 99
            except: return 99

        judul = s(kidung.judulKidung) or nama_individu.replace("_"," ")

        return {
            "judul":                 judul,
            "bahasa":                s(kidung.bahasa) or "-",
            "catatan":               s(kidung.catatan) or "-",
            "sumber":                s(kidung.sumberData) or "-",
            "teks":                  s(kidung.teksKidung) or "Teks belum tersedia.",
            "makna_mendalam":        s(kidung.maknaMendalam) or "Makna belum tersedia.",
            "teknik_menyanyi":       s(kidung.teknikMenyanyi) or "Teknik belum tersedia.",
            "pola_melodi":           s(kidung.polaMelodi) or "-",
            "tingkat_kesulitan":     s(kidung.tingkatKesulitan) or "Sedang",
            "status_validasi":       s(kidung.statusValidasi) or "Belum Divalidasi",
            "divalidasi_oleh":       s(kidung.divalidasiOleh) or "-",
            "kualifikasi_validator": s(kidung.kualifikasiValidator) or "-",
            "jenis_yadnya":          o(kidung.memilikiJenisYadnya),
            "upacara":               o(kidung.digunakanPadaUpacara),
            "tahap":                 o(kidung.digunakanPadaTahap),
            "pura":                  o(kidung.digunakanDiPura),
            "jenis_sekar":           o(kidung.memilikiJenisKidung),
            "makna_kategori":        o(kidung.memilikiMakna),
            "urutan_tahap":          i(kidung.urutanTahap),
            # backward compat
            "makna": s(kidung.maknaMendalam) or o(kidung.memilikiMakna) or "-",
        }
    except Exception as e:
        print(f"Error get_kidung_detail '{nama_individu}': {e}")
        return None


def get_kidung_by_context(onto, df, yadnya=None, upacara=None, pura=None, tahap_filter=None):
    """
    Ambil kidung sesuai konteks, diurutkan berdasarkan urutan_tahap.
    - tahap_filter=None  → ambil semua tahap (mode panduan lengkap)
    - tahap_filter='...' → hanya ambil kidung untuk tahap tertentu
    """
    try:
        tmp = df.copy()

        if yadnya and yadnya != "None":
            tmp = tmp[tmp['yadnya'].str.strip().str.lower() == yadnya.strip().lower()]
        if upacara and upacara != "None":
            tmp = tmp[tmp['upacara'].str.strip().str.lower() == upacara.strip().lower()]

        # Filter tahap hanya jika user memilih tahap tertentu
        if tahap_filter and tahap_filter not in ("None", ""):
            tmp_tahap = tmp[tmp['tahap'].str.strip().str.lower() == tahap_filter.strip().lower()]
            if not tmp_tahap.empty:
                tmp = tmp_tahap

        # Filter pura (opsional, tidak wajib cocok sempurna)
        if pura and pura not in ("None", "", None):
            tmp_pura = tmp[tmp['pura'].str.strip().str.lower() == pura.strip().lower()]
            if not tmp_pura.empty:
                tmp = tmp_pura

        # Fallback jika kosong: longgarkan filter, hanya pakai yadnya
        if tmp.empty and yadnya:
            tmp = df[df['yadnya'].str.strip().str.lower() == yadnya.strip().lower()]

        results = []
        for _, row in tmp.iterrows():
            detail = get_kidung_detail(onto, row['target'])
            if detail:
                results.append(detail)

        # Urutkan berdasarkan urutan_tahap
        results.sort(key=lambda x: x.get('urutan_tahap', 99))
        return results

    except Exception as e:
        print(f"Error get_kidung_by_context: {e}")
        return []
