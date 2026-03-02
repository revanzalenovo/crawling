import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import os
import urllib.parse
import json
import urllib3

# Disable insecure request warnings untuk fuzzing target HTTPS yang sertifikatnya invalid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="BTN Threat Intel & Recon",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (ULTRA-PREMIUM SOC THEME) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #09090b; color: #f8fafc; } 
    
    .title-glow {
        font-size: 2.2rem; font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #3b82f6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 5px; padding-bottom: 0px; text-transform: uppercase;
        letter-spacing: 1px;
    }
    .subtitle { color: #94a3b8; font-size: 1rem; margin-bottom: 2rem; font-weight: 400; letter-spacing: 0.5px;}
    
    .metric-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 2.5rem; }
    .metric-card {
        background: rgba(30, 41, 59, 0.5); backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05); padding: 24px; border-radius: 16px; flex: 1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); 
        border-top: 4px solid #3b82f6; transition: all 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2); }
    
    @keyframes subtle-pulse {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .metric-card.alert { 
        border-top: 4px solid #ef4444; 
        background: linear-gradient(180deg, rgba(239, 68, 68, 0.05) 0%, rgba(30, 41, 59, 0.5) 100%);
        animation: subtle-pulse 2s infinite;
    }
    .metric-card.safe { border-top: 4px solid #10b981; }
    
    .m-title { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; }
    .m-value { font-size: 2.5rem; font-weight: 800; color: #ffffff; margin: 10px 0; font-family: 'JetBrains Mono', monospace; line-height: 1;}
    .m-sub { font-size: 0.8rem; color: #64748b; font-weight: 500;}
    
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; border-bottom: 1px solid #334155; gap: 10px;}
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 600; padding: 12px 20px; font-size: 0.95rem; border-radius: 6px 6px 0 0;}
    .stTabs [aria-selected="true"] { color: #38bdf8 !important; border-bottom-color: #38bdf8 !important; background: rgba(56, 189, 248, 0.1); }
    
    [data-testid="stDataFrame"] { font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem; }
    .query-box { background: #1e293b; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px; border-left: 4px solid #3b82f6; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: #e2e8f0; display: flex; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    
    div.stButton > button[kind="primary"] { background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%); color: white; border: none; font-weight: 600; border-radius: 8px; padding: 10px; transition: all 0.2s ease;}
    div.stButton > button[kind="primary"]:hover { background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 100%); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA MANAGEMENT (CT LOGS) ---
DATA_FILE = "threat_data.json"
QUERIES_FILE = "queries_data.json"

DEFAULT_TARGETS = {
    "KORPORA": ["korpora.btn.co.id", "%korpora%btn%"],
    "CASHMANAGEMENT": ["cashmanagement.btn.co.id", "%cashmanagement%btn%"],
    "IBBISNIS": ["ibbisnis.btn.co.id", "%ibbisnis%btn%"],
    "BALEBISNIS": ["balebisnis.btn.co.id", "%balebisnis%btn%"]
}

def load_json(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except: return default_val
    return default_val

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f)

if 'user_queries' not in st.session_state:
    st.session_state.user_queries = load_json(QUERIES_FILE, DEFAULT_TARGETS)

def load_data():
    expected_columns = ["Waktu", "Kategori", "Query", "Domain Terdeteksi", "Issuer CA", "Not Before", "Not After", "Status", "Evidence"]
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_json(DATA_FILE)
            if "Not Before" in df.columns: return df.reset_index(drop=True)
        except: pass
    return pd.DataFrame(columns=expected_columns)

def save_data(df):
    df.to_json(DATA_FILE, orient="records")

if 'crawled_data' not in st.session_state:
    st.session_state.crawled_data = load_data()

if 'fuzz_results' not in st.session_state:
    st.session_state.fuzz_results = pd.DataFrame(columns=["Target URL", "Path", "Status Code", "Length", "Result"])

if 'auto_crawl_enabled' not in st.session_state:
    st.session_state.auto_crawl_enabled = False
if 'last_crawl_time' not in st.session_state:
    st.session_state.last_crawl_time = time.time()

# --- 4. ENGINE: CT LOGS PENGINTAIAN ---
def check_domain_alive(domain):
    try:
        url_https = f"https://{domain}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
        
        session = requests.Session()
        response = session.get(url_https, timeout=8, headers=headers, verify=False, allow_redirects=True)
        
        if response.status_code in [403, 401, 406]:
            return "🔴 Alive", f"HTTP {response.status_code} (Protected by WAF)"
        elif response.status_code >= 500:
            return "🔴 Alive", f"HTTP {response.status_code} (Server Error)"
        else:
            return "🔴 Alive", f"HTTP {response.status_code}"
            
    except requests.exceptions.ReadTimeout:
        try:
            res_head = requests.head(url_https, timeout=5, headers=headers, verify=False, allow_redirects=True)
            return "🔴 Alive", f"HTTP {res_head.status_code} (via HEAD)"
        except:
            return "⚪ Dead", "Timeout (WAF Drop/Lambat)"
            
    except requests.exceptions.ConnectionError:
        try:
            url_http = f"http://{domain}"
            res_http = requests.get(url_http, timeout=5, headers=headers, verify=False, allow_redirects=True)
            return "🔴 Alive", f"HTTP {res_http.status_code} (Non-SSL)"
        except:
            return "⚪ Dead", "Connection Refused"
            
    except Exception as e:
        return "⚪ Dead", "Unreachable / DNS Error"

def fetch_crtsh_data(query):
    url = f"https://crt.sh/?q={urllib.parse.quote(query)}&output=json"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError: return [], 0
            unique_certs = {}
            for cert in data:
                domain_names = cert.get('name_value', '').lower()
                for d in domain_names.split('\n'):
                    d = d.strip().replace('*.', '')
                    if d not in unique_certs: unique_certs[d] = cert 
            return list(unique_certs.values()), len(data)
        else: return [], 0
    except Exception: return [], 0

def execute_ct_logs_crawl():
    total_queries = sum(len(q) for q in st.session_state.user_queries.values())
    if total_queries == 0: 
        st.error("Tidak ada query aktif. Silakan tambahkan query di menu Settings.")
        return
    
    current_progress = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []

    with st.spinner("🔄 Menarik data CT Logs..."):
        for cat, queries in st.session_state.user_queries.items():
            for q in queries:
                status_text.text(f"Mencari data untuk '{q}'...")
                certs_found, total_raw = fetch_crtsh_data(q)
                if certs_found:
                    st.toast(f"✅ '{q}': Ditemukan {len(certs_found)} domain unik.", icon='ℹ️')
                    for cert_obj in certs_found[:30]: 
                        domain_name = cert_obj.get('name_value', '').split('\n')[0].strip().replace('*.', '')
                        issuer = cert_obj.get('issuer_name', 'Unknown').split(',')[0].replace('C=', '') 
                        not_before = cert_obj.get('not_before', 'N/A')
                        not_after = cert_obj.get('not_after', 'N/A')
                        status, evidence = check_domain_alive(domain_name)
                        results.append({
                            "Waktu": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "Kategori": cat, "Query": q, "Domain Terdeteksi": domain_name,
                            "Issuer CA": issuer, "Not Before": not_before[:10] if not_before != 'N/A' else 'N/A', 
                            "Not After": not_after[:10] if not_after != 'N/A' else 'N/A',
                            "Status": status, "Evidence": evidence
                        })
                else:
                    st.toast(f"⚠️ '{q}': Tidak ada data.", icon='ℹ️')
                
                current_progress += 1
                progress_bar.progress(current_progress / total_queries)
                time.sleep(1.5) 
            
        status_text.empty()
        progress_bar.empty()

        if results:
            df_new = pd.DataFrame(results)
            df_combined = pd.concat([st.session_state.crawled_data, df_new])
            df_combined = df_combined.drop_duplicates(subset=['Domain Terdeteksi'], keep='last').reset_index(drop=True)
            st.session_state.crawled_data = df_combined
            save_data(df_combined)
            st.success(f'✅ Selesai! Berhasil menarik {len(df_new)} sertifikat baru.')
        else:
            st.info('✅ Selesai. Kondisi Aman (Tidak ada data baru).')


# --- 5. ENGINE: DIRECTORY FUZZER (GOBUSTER STYLE) ---
def execute_fuzzer(target_url, wordlist_text):
    if not target_url.startswith("http"): target_url = "https://" + target_url
    if not target_url.endswith("/"): target_url += "/"
    words = [w.strip() for w in wordlist_text.split('\n') if w.strip()]
    if not words: return
    st.session_state.fuzz_results = pd.DataFrame(columns=["Target URL", "Path", "Status Code", "Length", "Result"])
    
    current_progress = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    fuzz_data = []

    with st.spinner("🚀 Fuzzing in progress..."):
        for word in words:
            test_url = target_url + word
            status_text.text(f"Testing: {test_url}")
            try:
                res = requests.get(test_url, timeout=3, verify=False, allow_redirects=False, headers={'User-Agent': 'Mozilla/5.0 Fuzz/1.0'})
                if res.status_code in [200, 204, 301, 302, 307, 401, 403, 500]:
                    icon = "🟢 Found" if res.status_code == 200 else ("🟡 Redirect" if res.status_code in [301,302,307] else "🔴 Restricted")
                    fuzz_data.append({"Target URL": target_url, "Path": f"/{word}", "Status Code": res.status_code, "Length": len(res.content), "Result": icon})
            except requests.exceptions.RequestException: pass 
            current_progress += 1
            progress_bar.progress(current_progress / len(words))
            time.sleep(0.05) 
            
    status_text.empty()
    progress_bar.empty()
    if fuzz_data:
        st.session_state.fuzz_results = pd.DataFrame(fuzz_data)
        st.success(f"🎉 Fuzzing selesai! Ditemukan {len(fuzz_data)} direktori.")

# --- 6. TAMPILAN SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <img src="https://logowik.com/content/uploads/images/osint4157.logowik.com.webp" width="160" style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🧭 Main Menu")
    menu_selection = st.radio("Navigasi:", ["📡 Threat Intelligence", "🔎 Directory Fuzzer", "⚙️ Settings & Queries"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### ⚙️ Automation Engine")
    
    auto_refresh_toggle = st.toggle("⏱️ Enable 1-Hour Auto Crawl", value=st.session_state.auto_crawl_enabled)
    
    if auto_refresh_toggle != st.session_state.auto_crawl_enabled:
        st.session_state.auto_crawl_enabled = auto_refresh_toggle
        if auto_refresh_toggle:
             st.session_state.last_crawl_time = time.time()
             st.rerun()

    if st.session_state.auto_crawl_enabled:
        elapsed_time = time.time() - st.session_state.last_crawl_time
        remaining_time = 3600 - elapsed_time
        
        if remaining_time <= 0:
            execute_ct_logs_crawl()
            st.session_state.last_crawl_time = time.time()
            st.rerun()
        else:
            mins, secs = divmod(int(remaining_time), 60)
            st.markdown(f"""
                <div style="background-color: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; padding: 10px; border-radius: 4px; margin-top: 10px;">
                    <span style="font-size: 0.8rem; color: #94a3b8;">STATUS SIAGA (CT LOGS)</span><br>
                    <span style="font-weight: 600; color: #60a5fa;">Next Auto-Crawl: {mins:02d}m {secs:02d}s</span>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗑️ Data Management")
    if menu_selection == "📡 Threat Intelligence":
        if st.button("Clear CT Logs Data", use_container_width=True):
            st.session_state.crawled_data = pd.DataFrame(columns=[
                "Waktu", "Kategori", "Query", "Domain Terdeteksi", 
                "Issuer CA", "Not Before", "Not After", "Status", "Evidence"
            ])
            save_data(st.session_state.crawled_data)
            st.toast("Database CT Logs berhasil dibersihkan!", icon="🧹")
            time.sleep(0.5)
            st.rerun()
            
    elif menu_selection == "🔎 Directory Fuzzer":
        if st.button("Clear Fuzzer Results", use_container_width=True):
            st.session_state.fuzz_results = pd.DataFrame(columns=["Target URL", "Path", "Status Code", "Length", "Result"])
            st.toast("Hasil Fuzzer dibersihkan!", icon="🧹")
            time.sleep(0.5)
            st.rerun()

# --- 7. MAIN AREA (ROUTING) ---

if menu_selection == "📡 Threat Intelligence":
    st.markdown('<p class="title-glow">CT LOGS THREAT INTELLIGENCE</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Continuous monitoring of SSL Certificates & Typosquatting Reconnaissance</p>', unsafe_allow_html=True)
    
    colA, colB = st.columns([8, 2])
    with colB:
        if st.button("🚀 FORCE CRAWL NOW", use_container_width=True, type="primary"):
            execute_ct_logs_crawl()
            st.rerun()

    df = st.session_state.crawled_data.reset_index(drop=True)
    total_domains = len(df)
    alive_domains = len(df[df["Status"] == "🔴 Alive"]) if not df.empty else 0
    dead_domains = len(df[df["Status"] == "⚪ Dead"]) if not df.empty else 0

    tab_dashboard, tab_logs, tab_analytics = st.tabs(["📡 Command Center", "📋 Comprehensive Logs", "📊 Threat Analytics"])

    with tab_dashboard:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card">
                    <div class="m-title">Active Queries</div>
                    <div class="m-value">{sum(len(q) for q in st.session_state.user_queries.values())}</div>
                    <div class="m-sub">Monitored in CT Logs</div>
                </div>
                <div class="metric-card">
                    <div class="m-title">Total Certificates</div>
                    <div class="m-value">{total_domains}</div>
                    <div class="m-sub">Records in DB</div>
                </div>
                <div class="metric-card {'alert' if alive_domains > 0 else 'safe'}">
                    <div class="m-title">Active Domains (Alive)</div>
                    <div class="m-value">{alive_domains}</div>
                    <div class="m-sub" style="color: {'#ef4444' if alive_domains > 0 else '#10b981'};">Servers currently responding</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("### ⚡ Latest Discovered Certificates")
        if not df.empty: 
            st.dataframe(df.tail(8).iloc[::-1].reset_index(drop=True), use_container_width=True, hide_index=True)
        else:
            st.info("Awaiting execution. Click 'FORCE CRAWL NOW' to start reconnaissance.")

    with tab_logs:
        if not df.empty:
            def highlight_alive(val):
                return 'background-color: rgba(239, 68, 68, 0.2); color: #fca5a5; font-weight: bold;' if val == '🔴 Alive' else ''
            
            try:
                styled_df = df.style.map(highlight_alive, subset=['Status'])
            except AttributeError:
                styled_df = df.style.applymap(highlight_alive, subset=['Status'])
                
            st.dataframe(styled_df, use_container_width=True, height=500, hide_index=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export DB", data=csv, file_name=f"CTLogs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")
        else:
            st.info("Database is currently empty.")

    # --- DASHBOARD VISUALIZATION PRO ---
    with tab_analytics:
        if not df.empty:
            st.markdown("### 📈 Visual Intelligence Report")
            col1, col2 = st.columns(2)
            
            # CHART 1: Donut Chart - Distribusi Kategori (Modern Look)
            with col1:
                cat_counts = df['Kategori'].value_counts().reset_index()
                cat_counts.columns = ['Kategori', 'Jumlah']
                fig1 = px.pie(cat_counts, values='Jumlah', names='Kategori', hole=0.55, 
                              color_discrete_sequence=px.colors.qualitative.Pastel)
                fig1.update_layout(
                    title_text="Asset Distribution by Category", title_x=0.5,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='#e2e8f0'), margin=dict(t=50, b=20, l=20, r=20),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                # Tambah angka total di tengah donut
                fig1.add_annotation(text=f"Total<br><b>{total_domains}</b>", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="#e2e8f0")
                st.plotly_chart(fig1, use_container_width=True)
            
            # CHART 2: Horizontal Bar - Server Status
            with col2:
                status_counts = df['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                # Custom color mapping
                color_map = {'🔴 Alive': 'rgba(239, 68, 68, 0.8)', '⚪ Dead': 'rgba(71, 85, 105, 0.8)'}
                
                fig2 = px.bar(status_counts, x='Count', y='Status', orientation='h', text='Count',
                              color='Status', color_discrete_map=color_map)
                fig2.update_layout(
                    title_text="Target Availability (Alive vs Dead)", title_x=0.5,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='#e2e8f0'), showlegend=False, xaxis_title="", yaxis_title="",
                    margin=dict(t=50, b=20, l=20, r=20)
                )
                fig2.update_traces(textposition='inside', textfont_size=14, textfont_color="white")
                st.plotly_chart(fig2, use_container_width=True)

            # CHART 3: Area Chart - Tren Penerbitan Sertifikat (Timeline)
            st.markdown("---")
            df['Year Issued'] = df['Not Before'].astype(str).str[:4]
            year_counts = df[df['Year Issued'] != 'N/A']['Year Issued'].value_counts().reset_index().sort_values(by='Year Issued')
            
            if not year_counts.empty:
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(
                    x=year_counts['Year Issued'], y=year_counts['count'], 
                    fill='tozeroy', mode='lines+markers',
                    line=dict(color='#3b82f6', width=3),
                    marker=dict(size=8, color='#60a5fa', line=dict(width=2, color='white'))
                ))
                fig3.update_layout(
                    title_text="SSL Certificate Issuance Timeline", title_x=0.5,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='#e2e8f0'), xaxis_title="Year", yaxis_title="Certificates Found",
                    margin=dict(t=50, b=40, l=20, r=20),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Insufficient data for generating analytics. Run a crawl first.")

elif menu_selection == "🔎 Directory Fuzzer":
    st.markdown('<p class="title-glow">WEB DIRECTORY FUZZER</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Brute-force hidden directories and sensitive files (Gobuster-style Engine)</p>', unsafe_allow_html=True)
    
    with st.form("fuzzer_form"):
        target_url = st.text_input("Target URL", placeholder="https://example.com")
        default_wordlist = "admin\nlogin\napi\nbackup\n.git\nconfig\n.env\ndashboard\ntest"
        wordlist_input = st.text_area("Wordlist (One path per line)", value=default_wordlist, height=150)
        btn_fuzz = st.form_submit_button("🔥 INITIATE FUZZING SEQUENCE", type="primary")
        if btn_fuzz and target_url: execute_fuzzer(target_url, wordlist_input)
            
    if not st.session_state.fuzz_results.empty:
        st.markdown("### 📑 Discovered Paths")
        def highlight_fuzz(val):
            if val == '🟢 Found': return 'color: #10b981; font-weight: bold;'
            if val == '🟡 Redirect': return 'color: #fbbf24;'
            if val == '🔴 Restricted': return 'color: #ef4444;'
            return ''
        try:
            fuzz_df = st.session_state.fuzz_results.style.map(highlight_fuzz, subset=['Result'])
        except AttributeError:
            fuzz_df = st.session_state.fuzz_results.style.applymap(highlight_fuzz, subset=['Result'])
        st.dataframe(fuzz_df, use_container_width=True, hide_index=True)


elif menu_selection == "⚙️ Settings & Queries":
    st.markdown('<p class="title-glow">ENGINE SETTINGS</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Manage Target Categories and Automation Queries</p>', unsafe_allow_html=True)
    
    st.markdown("### ➕ Tambah Target CT Logs")
    with st.form("form_ct_logs"):
        c1, c2, c3 = st.columns([3, 5, 2])
        new_cat_ct = c1.text_input("Kategori Target", placeholder="ex: CORPORATE")
        new_query_ct = c2.text_input("Sintaks CT Logs", placeholder="ex: %btn%")
        submit_ct = c3.form_submit_button("Simpan Target")
        
        if submit_ct and new_cat_ct and new_query_ct:
            c = new_cat_ct.upper()
            if c not in st.session_state.user_queries: st.session_state.user_queries[c] = []
            if new_query_ct not in st.session_state.user_queries[c]:
                st.session_state.user_queries[c].append(new_query_ct)
                save_json(st.session_state.user_queries, QUERIES_FILE)
                st.success("Target CT Logs disimpan!"); time.sleep(1); st.rerun()

    st.markdown("### 📋 Database Target CT Logs")
    for cat, qs in st.session_state.user_queries.items():
        st.markdown(f"**📂 {cat}**")
        for idx, q in enumerate(qs):
            c_q, c_b = st.columns([10, 1])
            c_q.markdown(f"<div class='query-box'>🔍 {q}</div>", unsafe_allow_html=True)
            if c_b.button("🗑️", key=f"del_ct_{cat}_{idx}"):
                st.session_state.user_queries[cat].remove(q)
                if not st.session_state.user_queries[cat]: del st.session_state.user_queries[cat]
                save_json(st.session_state.user_queries, QUERIES_FILE); st.rerun()

    st.markdown("---")
    st.markdown("#### ⚠️ Master Factory Reset")
    if st.button("Hapus SEMUA Pengaturan & Log (Hard Reset)", type="primary"):
        st.session_state.crawled_data = pd.DataFrame()
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        if os.path.exists(QUERIES_FILE): os.remove(QUERIES_FILE)
        # Hapus file dorks lama jika masih ada
        if os.path.exists("dorks_results.json"): os.remove("dorks_results.json")
        if os.path.exists("dorks_queries.json"): os.remove("dorks_queries.json")
        st.success("Sistem dikembalikan ke pengaturan pabrik."); time.sleep(1); st.rerun()

# --- REFRESH LOGIC UNTUK TIMER ---
if st.session_state.auto_crawl_enabled:
    time.sleep(2)
    st.rerun()