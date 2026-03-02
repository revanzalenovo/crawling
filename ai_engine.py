import google.generativeai as genai
import pandas as pd
import json

# Masukkan API Key Gemini Anda di sini
# Dapatkan gratis di: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = "AIzaSyCSV8Ly8wzQ-bgkp-NloHCQSuRuv9Q8cSI"

genai.configure(api_key=GEMINI_API_KEY)

# Gunakan model Gemini terbaru
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_threat(domain, evidence, source_engine):
    """
    Mengirim data temuan ke AI untuk dianalisis tingkat risikonya.
    """
    if pd.isna(evidence) or evidence == "" or evidence == "N/A":
        evidence = "Tidak ada snippet teks tambahan."

    prompt = f"""
    Anda adalah seorang Analis Security Operations Center (SOC) tingkat Senior.
    Tugas Anda adalah mengevaluasi temuan OSINT berikut dan menentukan tingkat risikonya.
    
    Detail Temuan:
    - Sumber Intelijen: {source_engine}
    - Target Domain/URL: {domain}
    - Potongan Bukti (Snippet/Konteks): {evidence}
    
    Berdasarkan data di atas, tolong berikan analisis singkat dengan format persis seperti ini:
    [RISK LEVEL]: (Pilih salah satu: CRITICAL / HIGH / MEDIUM / LOW / FALSE POSITIVE)
    [ANALYSIS]: (Jelaskan dalam 1-2 kalimat mengapa temuan ini berbahaya atau tidak)
    [ACTION]: (Satu tindakan teknis yang harus dilakukan tim IT)
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[RISK LEVEL]: ERROR\n[ANALYSIS]: Gagal menghubungi AI ({str(e)})\n[ACTION]: Cek koneksi API."

def run_ai_analysis_on_dorks(dorks_file_path="threat_data_dorks.json"):
    """
    Fungsi ini akan membaca file JSON Dorks, mengirimnya ke AI satu per satu,
    lalu mengembalikan DataFrame yang sudah diperkaya dengan Analisis AI.
    """
    try:
        df = pd.read_json(dorks_file_path)
    except:
        return pd.DataFrame() # File tidak ada atau kosong

    if df.empty:
        return df

    # Kita hanya menganalisis 5 temuan terbaru agar tidak kena rate-limit API
    df_to_analyze = df.tail(5).copy()
    
    ai_results = []
    for index, row in df_to_analyze.iterrows():
        # Kirim ke Gemini
        analysis = analyze_threat(row['Domain Terdeteksi'], row['Evidence'], "Google Dork")
        ai_results.append(analysis)
        
    df_to_analyze['AI Threat Analysis'] = ai_results
    return df_to_analyze