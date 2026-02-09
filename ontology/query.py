def get_kidung_detail(onto, nama_individu):
    """Mengambil detail teks kidung dan catatan dari ontology."""
    try:
        # Mencari individu berdasarkan nama asli (ID) yang dikirim oleh AI
        # Contoh: Kidung_Wargasari_Ref
        kidung = onto.search_one(iri=f"*{nama_individu}")
        
        if kidung:
            # PENTING: Semua harus dibungkus str() atau diambil .name-nya
            # agar bisa dikirim sebagai teks (JSON)
            return {
                "teks": str(kidung.teksKidung[0]) if kidung.teksKidung else "Teks tidak tersedia",
                "catatan": str(kidung.catatan[0]) if kidung.catatan else "-",
                # Jika 'memilikiMakna' adalah Object Property, ambil .name-nya
                "makna": str(kidung.memilikiMakna[0].name.replace("_", " ")) if kidung.memilikiMakna else "-"
            }
        return None
    except Exception as e:
        print(f"Error pada Query Detail: {e}")
        return None