import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder

class KidungDecisionTree:
    def __init__(self):
        # Menggunakan entropy untuk Information Gain yang tajam
        self.model = DecisionTreeClassifier(criterion='entropy', random_state=42)
        self.encoders = {}
        self.features = ['yadnya', 'upacara', 'tahap', 'makna', 'pura']

    def train(self, df):
        """Melatih model AI berdasarkan data dari DataFrame Ontologi."""
        if df.empty:
            print("Peringatan: DataFrame kosong, tidak bisa melatih AI.")
            return

        df_encoded = df.copy()
        
        # 1. Encoding Fitur (X) dan Target (y)
        all_cols = self.features + ['target']
        
        for col in all_cols:
            le = LabelEncoder()
            # Ambil semua nilai unik dan pastikan 'None' selalu ada sebagai pengaman
            unique_values = df_encoded[col].astype(str).unique().tolist()
            if 'None' not in unique_values:
                unique_values.append('None')
            if 'unknown' not in unique_values: # Tambahkan unknown untuk data baru
                unique_values.append('unknown')
            
            le.fit(unique_values)
            self.encoders[col] = le
            df_encoded[col] = le.transform(df_encoded[col].astype(str))

        # 2. Pemisahan Data
        X = df_encoded[self.features]
        y = df_encoded['target']

        # 3. Training Model
        self.model.fit(X, y)
        print(f"AI Engine: Berhasil melatih model dengan {len(df)} baris data.")

    def predict(self, input_dict):
        try:
            if not self.encoders:
                return None

            encoded_input = []
            for feat in self.features:
                val = str(input_dict.get(feat, 'None'))
                
                if val in self.encoders[feat].classes_:
                    encoded_val = self.encoders[feat].transform([val])[0]
                else:
                    encoded_val = self.encoders[feat].transform(['None'])[0]
                
                encoded_input.append(encoded_val)

            # --- PERBAIKAN DI SINI ---
            # Ubah list menjadi DataFrame agar memiliki nama fitur yang valid
            input_df = pd.DataFrame([encoded_input], columns=self.features)

            # Gunakan input_df untuk prediksi
            prediction_proba = self.model.predict_proba(input_df)
            max_proba = np.max(prediction_proba)

            if max_proba < 0.05: 
                return None

            pred_idx = self.model.predict(input_df)[0]
            # -------------------------
            
            return self.encoders['target'].inverse_transform([pred_idx])[0]

        except Exception as e:
            print(f"AI Prediction Error: {e}")
            return None