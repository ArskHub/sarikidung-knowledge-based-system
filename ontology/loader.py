from owlready2 import *
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ONTO_PATH = os.path.join(BASE_DIR, "kidung.owx")

def load_ontology():
    if not os.path.exists(ONTO_PATH):
        raise FileNotFoundError(f"File {ONTO_PATH} tidak ditemukan!")
    try:
        onto = get_ontology(ONTO_PATH).load()
        return onto
    except Exception as e:
        raise Exception(f"Gagal memuat ontology: {str(e)}")

def get_v(prop):
    try:
        if prop:
            # Gunakan .strip() dan .title() agar seragam
            return prop[0].name.replace("_Ref", "").replace("_", " ").strip()
        return "None"
    except:
        return "None"

def get_kidung_dataframe(onto):
    """Mengekstrak data dari ontology ke DataFrame."""
    data = []
    try:
        # Mengambil instance dari class KidungPancaYadnya
        instances = onto.KidungPancaYadnya.instances()
        print(f"🔍 Berhasil menarik {len(instances)} data dari Ontology.")
    except AttributeError:
        print("⚠️ Class 'KidungPancaYadnya' tidak ditemukan!")
        return pd.DataFrame(columns=['target', 'yadnya', 'upacara', 'tahap', 'makna', 'pura'])

    for k in instances:
        # PENTING: 'target' harus k.name ASLI agar get_kidung_detail bisa bekerja
        data.append({
            "target": k.name, 
            "yadnya": get_v(k.memilikiJenisYadnya),
            "upacara": get_v(k.digunakanPadaUpacara),
            "tahap": get_v(k.digunakanPadaTahap),
            "makna": get_v(k.memilikiMakna),
            "pura": get_v(k.digunakanDiPura)
        })
    return pd.DataFrame(data)

def get_filtered_options(df, current_selections):
    """Melakukan filter data dengan toleransi spasi dan huruf besar/kecil."""
    temp_df = df.copy()
    for key, value in current_selections.items():
        if value and value != "None":
            # Bandingkan dengan menghapus spasi dan mengubah ke huruf kecil agar sinkron
            temp_df = temp_df[temp_df[key].astype(str).str.strip().str.lower() == str(value).strip().lower()]
    return temp_df
