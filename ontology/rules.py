from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder

class KidungDecisionTree:
    def __init__(self):
        self.model = DecisionTreeClassifier(criterion='entropy', random_state=42)
        self.encoders = {}
        self.features = ['yadnya', 'upacara', 'tahap', 'makna', 'pura']

    def train(self, df):
        if df.empty: return
        df_encoded = df.copy()
        # Encoding data kategori menjadi angka
        for col in df_encoded.columns:
            le = LabelEncoder()
            # Tambahkan 'Unknown' agar sistem tidak crash jika ada input baru
            le.fit(list(df_encoded[col].unique()) + ['Unknown'])
            df_encoded[col] = le.transform(df_encoded[col])
            self.encoders[col] = le
        
        X = df_encoded[self.features]
        y = df_encoded['target']
        self.model.fit(X, y)

    def predict(self, input_dict):
        try:
            # Mengonversi input user menjadi angka yang dipahami AI
            encoded_input = []
            for feat in self.features:
                val = input_dict.get(feat, 'Unknown')
                if val not in self.encoders[feat].classes_: val = 'Unknown'
                encoded_input.append(self.encoders[feat].transform([val])[0])
            
            pred_idx = self.model.predict([encoded_input])[0]
            return self.encoders['target'].inverse_transform([pred_idx])[0]
        except Exception as e:
            print(f"Prediction Error: {e}")
            return None