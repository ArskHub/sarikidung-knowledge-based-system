from owlready2 import *
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ONTO_PATH = os.path.join(BASE_DIR, "kidung.owx")

def load_ontology():
    if not os.path.exists(ONTO_PATH):
        raise FileNotFoundError(f"File {ONTO_PATH} tidak ditemukan!")
    try:
        onto = get_ontology(f"file://{ONTO_PATH}").load()
        return onto
    except Exception as e:
        raise Exception(f"Gagal memuat ontology: {str(e)}")

def get_v(prop):
    """Ambil nilai object property sebagai string bersih."""
    try:
        if prop:
            return prop[0].name.replace("_Ref", "").replace("_", " ").strip()
        return "None"
    except:
        return "None"

def get_s(prop):
    """Ambil nilai data property string."""
    try:
        if prop:
            return str(prop[0]).strip()
        return ""
    except:
        return ""

def get_kidung_dataframe(onto):
    """
    Mengekstrak data dari ontology ke DataFrame.
    Fitur decision tree : yadnya, upacara, pura  (3 fitur)
    Kolom tambahan      : tahap, makna, jenis_sekar (untuk tampilan)
    """
    data = []
    try:
        instances = list(onto.KidungPancaYadnya.instances())
        print(f"🔍 Berhasil menarik {len(instances)} data dari Ontology.")
    except AttributeError:
        print("⚠️ Class 'KidungPancaYadnya' tidak ditemukan!")
        return pd.DataFrame(columns=['target','judul','yadnya','upacara','pura','tahap','makna','jenis_sekar'])

    for k in instances:
        judul = get_s(k.judulKidung) or k.name.replace("_", " ")
        data.append({
            "target":      k.name,
            "judul":       judul,
            # === 3 FITUR DECISION TREE ===
            "yadnya":      get_v(k.memilikiJenisYadnya),
            "upacara":     get_v(k.digunakanPadaUpacara),
            "pura":        get_v(k.digunakanDiPura),
            # === KOLOM TAMBAHAN (tampilan, bukan pertanyaan) ===
            "tahap":       get_v(k.digunakanPadaTahap),
            "makna":       get_v(k.memilikiMakna),
            "jenis_sekar": get_v(k.memilikiJenisKidung),
        })

    df = pd.DataFrame(data)
    print(f"✅ DataFrame siap: {len(df)} baris | kolom: {list(df.columns)}")
    return df
