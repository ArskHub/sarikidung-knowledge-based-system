def get_kidung_detail(onto, nama_individu):
    """
    Fungsi Data Access Object (DAO) untuk mengambil detail individu.
    """
    # Cari objek di ontology berdasarkan namanya
    res_obj = onto.search_one(iri=f"*{nama_individu}")
    
    if res_obj:
        return {
            "judul": res_obj.judulKidung[0] if res_obj.judulKidung else nama_individu,
            "teks": res_obj.teksKidung[0] if res_obj.teksKidung else "Lirik tidak ditemukan.",
            "bahasa": res_obj.bahasa[0] if res_obj.bahasa else "Bali",
            "keterangan": res_obj.keterangan[0] if hasattr(res_obj, 'keterangan') and res_obj.keterangan else "-"
        }
    return None