import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder

SEMUA_TAHAP = "── Semua Tahap (Panduan Lengkap) ──"

class KidungDecisionTree:
    def __init__(self):
        self.model = DecisionTreeClassifier(criterion='entropy', random_state=42, min_samples_leaf=1)
        self.encoders = {}
        # Fitur utama untuk decision tree (tanpa tahap karena tahap = filter tampilan)
        self.features = ['yadnya', 'upacara', 'pura']
        self.is_trained = False

    def train(self, df):
        if df.empty:
            print("⚠️ DataFrame kosong.")
            return
        df_enc = df.copy()
        all_cols = self.features + ['target']
        for col in all_cols:
            le = LabelEncoder()
            vals = df_enc[col].astype(str).unique().tolist()
            for x in ['None','unknown']:
                if x not in vals: vals.append(x)
            le.fit(vals)
            self.encoders[col] = le
            df_enc[col] = le.transform(df_enc[col].astype(str))
        self.model.fit(df_enc[self.features], df_enc['target'])
        self.is_trained = True
        print(f"✅ Decision Tree trained: {len(df)} data")

    def predict(self, input_dict):
        try:
            if not self.is_trained: return None
            enc = []
            for feat in self.features:
                val = str(input_dict.get(feat, 'None')).strip()
                e   = self.encoders[feat]
                enc.append(e.transform([val])[0] if val in e.classes_ else e.transform(['None'])[0])
            idf   = pd.DataFrame([enc], columns=self.features)
            proba = self.model.predict_proba(idf)
            if np.max(proba) < 0.01: return None
            idx = self.model.predict(idf)[0]
            return self.encoders['target'].inverse_transform([idx])[0]
        except Exception as e:
            print(f"❌ Predict error: {e}")
            return None

    def get_top_candidates(self, input_dict, n=3):
        try:
            if not self.is_trained: return []
            enc = []
            for feat in self.features:
                val = str(input_dict.get(feat, 'None')).strip()
                e   = self.encoders[feat]
                enc.append(e.transform([val])[0] if val in e.classes_ else e.transform(['None'])[0])
            idf    = pd.DataFrame([enc], columns=self.features)
            probas = self.model.predict_proba(idf)[0]
            top    = np.argsort(probas)[::-1][:n]
            return [
                {'nama': self.encoders['target'].inverse_transform([self.model.classes_[i]])[0],
                 'probabilitas': round(float(probas[i])*100, 1)}
                for i in top if probas[i] > 0
            ]
        except: return []

    def build_explanation(self, input_dict, nama_kidung):
        yadnya  = str(input_dict.get('yadnya', '')).replace('_',' ')
        upacara = str(input_dict.get('upacara', '')).replace('_',' ')
        pura    = str(input_dict.get('pura', '')).replace('_',' ')
        tahap   = str(input_dict.get('tahap', '')).replace('_',' ')

        alasan = []
        if yadnya  and yadnya  != 'None': alasan.append(f"merupakan bagian dari <strong>{yadnya}</strong>")
        if upacara and upacara != 'None': alasan.append(f"digunakan pada upacara <strong>{upacara}</strong>")
        if tahap   and tahap not in ('None', '', SEMUA_TAHAP):
            alasan.append(f"dinyanyikan pada tahap <strong>{tahap}</strong>")
        if pura    and pura not in ('None', ''):
            alasan.append(f"dilaksanakan di <strong>{pura}</strong>")

        if alasan:
            return (f"Kidung ini direkomendasikan karena {', '.join(alasan)}, "
                    f"sesuai dengan relasi yang tersimpan dalam basis pengetahuan ontologi Kidung Panca Yadnya.")
        return "Kidung ini direkomendasikan berdasarkan kesesuaian konteks upacara yang dipilih."
