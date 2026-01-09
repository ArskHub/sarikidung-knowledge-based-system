from owlready2 import *
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ONTO_PATH = os.path.join(BASE_DIR, "kidung.owx")

def load_ontology():
    """Memuat file ontology dengan error handling."""
    if not os.path.exists(ONTO_PATH):
        print(f"Error: File {ONTO_PATH} tidak ditemukan!")
        return None
    return get_ontology(ONTO_PATH).load()

def get_kidung_dataframe(onto):
    """Mengekstrak data individu ke dalam DataFrame untuk AI."""
    data = []
    for k in onto.KidungPancaYadnya.instances():
        data.append({
            "yadnya": k.memilikiJenisYadnya[0].name if k.memilikiJenisYadnya else "None",
            "upacara": k.digunakanPadaUpacara[0].name if k.digunakanPadaUpacara else "None",
            "tahap": k.digunakanPadaTahap[0].name if k.digunakanPadaTahap else "None",
            "makna": k.memilikiMakna[0].name if k.memilikiMakna else "None",
            "pura": k.digunakanDiPura[0].name if k.digunakanDiPura else "None",
            "target": k.name
        })
    return pd.DataFrame(data)

def get_dropdown_options(onto):
    """Menyediakan daftar pilihan untuk form di website."""
    return {
        "yadnyas": sorted([i.name for i in onto.JenisYadnya.instances()]),
        "upacaras": sorted([i.name for i in onto.UpacaraPancaYadnya.instances()]),
        "tahaps": sorted([i.name for i in onto.TahapPelaksanaanUpacara.instances()]),
        "maknas": sorted([i.name for i in onto.MaknaKidung.instances()]),
        "puras": sorted([i.name for i in onto.PuraTempatPelaksanaan.instances()])
    }