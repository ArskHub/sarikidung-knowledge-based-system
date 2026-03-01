def get_platform(url):
    if not url:
        return None
    if "soundcloud.com" in url:
        return "soundcloud"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return None


def get_soundcloud_embed(url):
    if not url:
        return None
    clean = url.split("?")[0]
    return (
        f"https://w.soundcloud.com/player/?url={clean}"
        f"&color=%23926237&auto_play=false&hide_related=true"
        f"&show_comments=false&show_user=true&show_reposts=false&visual=false"
    )


def get_youtube_embed(url):
    if not url:
        return None
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url:
        video_id = url.split("watch?v=")[1].split("&")[0]
    else:
        return None
    return f"https://www.youtube.com/embed/{video_id}"


def get_kidung_detail(onto, nama_individu):
    try:
        kidung = onto.search_one(iri=f"*{nama_individu}")
        if not kidung:
            return None

        def s(prop_name):
            """Ambil data property string dengan aman — tidak error walau property belum ada di ontologi."""
            try:
                val = getattr(kidung, prop_name, [])
                return str(val[0]).strip() if val else ""
            except:
                return ""

        def o(prop_name):
            """Ambil object property sebagai string bersih."""
            try:
                val = getattr(kidung, prop_name, [])
                return val[0].name.replace("_Ref", "").replace("_", " ").strip() if val else ""
            except:
                return ""

        def i(prop_name):
            """Ambil property integer."""
            try:
                val = getattr(kidung, prop_name, [])
                return int(val[0]) if val else 99
            except:
                return 99

        judul = s("judulKidung") or nama_individu.replace("_", " ")

        # Audio — coba beberapa cara baca karena owlready2 kadang
        # tidak map property dengan underscore lewat getattr biasa
        url_audio = s("url_audio")
        if not url_audio:
            try:
                for prop in kidung.get_properties():
                    if "url_audio" in str(prop.iri):
                        vals = prop[kidung]
                        url_audio = str(vals[0]).strip() if vals else ""
                        break
            except:
                pass

        platform  = get_platform(url_audio) if url_audio else None
        if platform == "soundcloud":
            embed_url = get_soundcloud_embed(url_audio)
        elif platform == "youtube":
            embed_url = get_youtube_embed(url_audio)
        else:
            embed_url = None

        catatan = s("catatan")

        return {
            "judul":                 judul,
            "bahasa":                s("bahasa") or "-",
            "catatan":               catatan or "-",
            "sumber":                s("sumberData") or "-",
            "teks":                  s("teksKidung") or "Teks belum tersedia.",
            "makna_mendalam":        s("maknaMendalam") or catatan or "Makna belum tersedia.",
            "teknik_menyanyi":       s("teknikMenyanyi") or catatan or "Teknik belum tersedia.",
            "pola_melodi":           s("polaMelodi") or "-",
            "tingkat_kesulitan":     s("tingkatKesulitan") or "Sedang",
            "status_validasi":       s("statusValidasi") or "Belum Divalidasi",
            "divalidasi_oleh":       s("divalidasiOleh") or "-",
            "kualifikasi_validator": s("kualifikasiValidator") or "-",
            "jenis_yadnya":          o("memilikiJenisYadnya"),
            "upacara":               o("digunakanPadaUpacara"),
            "tahap":                 o("digunakanPadaTahap"),
            "pura":                  o("digunakanDiPura"),
            "jenis_sekar":           o("memilikiJenisKidung"),
            "makna_kategori":        o("memilikiMakna"),
            "urutan_tahap":          i("urutanTahap"),
            "makna":                 s("maknaMendalam") or o("memilikiMakna") or "-",
            # audio
            "url_audio":             url_audio or None,
            "platform_audio":        platform,
            "embed_url":             embed_url,
            "has_audio":             embed_url is not None,
        }
    except Exception as e:
        print(f"Error get_kidung_detail '{nama_individu}': {e}")
        return None


def get_kidung_by_context(onto, df, yadnya=None, upacara=None, pura=None, tahap_filter=None):
    try:
        tmp = df.copy()

        if yadnya and yadnya != "None":
            tmp = tmp[tmp['yadnya'].str.strip().str.lower() == yadnya.strip().lower()]
        if upacara and upacara != "None":
            tmp = tmp[tmp['upacara'].str.strip().str.lower() == upacara.strip().lower()]

        if tahap_filter and tahap_filter not in ("None", ""):
            tmp_tahap = tmp[tmp['tahap'].str.strip().str.lower() == tahap_filter.strip().lower()]
            if not tmp_tahap.empty:
                tmp = tmp_tahap

        if pura and pura not in ("None", "", None):
            tmp_pura = tmp[tmp['pura'].str.strip().str.lower() == pura.strip().lower()]
            if not tmp_pura.empty:
                tmp = tmp_pura

        if tmp.empty and yadnya:
            tmp = df[df['yadnya'].str.strip().str.lower() == yadnya.strip().lower()]

        results = []
        for _, row in tmp.iterrows():
            detail = get_kidung_detail(onto, row['target'])
            if detail:
                results.append(detail)

        results.sort(key=lambda x: x.get('urutan_tahap', 99))
        return results

    except Exception as e:
        print(f"Error get_kidung_by_context: {e}")
        return []