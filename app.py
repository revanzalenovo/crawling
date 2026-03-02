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

# --- IMPORT FILE AI ENGINE BUATAN KITA ---
try:
    import ai_engine
    AI_MODULE_AVAILABLE = True
except ImportError:
    AI_MODULE_AVAILABLE = False

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="BTN Unified Threat Intel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- API KEYS ---
ST_API_KEYS = [
    "PUHUV9Ezz8VR6ZQBLyVdhXrqv5OELC5v", 
    "DjcPz8qmbKFYGu8LWEfz4Nz1BNtu34kk"  
]
WHOISXML_API_KEY = "at_yGLOnhPSTqS3113fo7GSCwXcRTaTv"
GOOGLE_API_KEY = "AIzaSyAaIosP3zWXqS1Urir-kWN_A4atKuCZ8Cg"
GOOGLE_CX = "c797ddd00903b49b7"

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #050505; color: #f8fafc; } 
    
    .title-glow {
        font-size: 2.4rem; font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #2563eb 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0px; padding-bottom: 0px; text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    .subtitle { color: #64748b; font-size: 1.05rem; margin-bottom: 2.5rem; font-weight: 400; letter-spacing: 0.5px;}
    
    .metric-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-bottom: 3rem; }
    .metric-card {
        background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.05); padding: 24px 28px; border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15); 
        border-top: 4px solid #3b82f6; transition: all 0.3s ease; position: relative; overflow: hidden;
    }
    .metric-card::before {
        content: ''; position: absolute; top: 0; right: 0; width: 100px; height: 100px;
        background: radial-gradient(circle, rgba(59,130,246,0.1) 0%, transparent 70%); border-radius: 50%;
    }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4); border-color: rgba(255,255,255,0.1); }
    
    @keyframes subtle-pulse {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.3); }
        70% { box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .metric-card.alert { 
        border-top: 4px solid #ef4444; 
        background: linear-gradient(180deg, rgba(239, 68, 68, 0.08) 0%, rgba(15, 23, 42, 0.6) 100%);
        animation: subtle-pulse 2s infinite;
    }
    .metric-card.safe { border-top: 4px solid #10b981; }
    .metric-card.purple { border-top: 4px solid #8b5cf6; }
    
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;}
    .m-title { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 1.2px; }
    .m-icon { font-size: 1.5rem; opacity: 0.8; }
    .m-value { font-size: 3rem; font-weight: 800; color: #ffffff; margin: 0; font-family: 'JetBrains Mono', monospace; line-height: 1; text-shadow: 0 2px 10px rgba(0,0,0,0.5);}
    .m-sub { font-size: 0.85rem; color: #64748b; font-weight: 500; margin-top: 8px;}
    
    [data-testid="stSidebar"] { background-color: #09090b !important; border-right: 1px solid #1e293b; }
    
    .stRadio div[role="radiogroup"] > label {
        background: transparent; padding: 12px 16px; border-radius: 8px; margin-bottom: 4px;
        transition: all 0.2s ease; cursor: pointer; border: 1px solid transparent;
    }
    .stRadio div[role="radiogroup"] > label:hover { background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.15) 0%, transparent 100%);
        border-left: 4px solid #38bdf8; border-radius: 4px 8px 8px 4px;
    }
    .stRadio div[role="radiogroup"] > label > div:first-child { display: none; } 
    .stRadio div[role="radiogroup"] > label p { font-size: 1rem; font-weight: 500; color: #e2e8f0; margin:0;}
    
    .status-dot { height: 8px; width: 8px; background-color: #10b981; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #10b981; animation: blinker 1.5s linear infinite; margin-right: 8px; }
    @keyframes blinker { 50% { opacity: 0.3; } }
    
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; border-bottom: 2px solid #1e293b; gap: 20px;}
    .stTabs [data-baseweb="tab"] { color: #64748b; font-weight: 600; padding: 15px 5px; font-size: 0.95rem; }
    .stTabs [aria-selected="true"] { color: #f8fafc !important; border-bottom-color: #38bdf8 !important; }
    
    [data-testid="stDataFrame"] { font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem; border: 1px solid #1e293b; border-radius: 8px; overflow: hidden;}
    .query-box { background: #0f172a; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px; border-left: 4px solid #3b82f6; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: #e2e8f0; display: flex; align-items: center; justify-content: space-between; border: 1px solid #1e293b;}
    
    div.stButton > button[kind="primary"] { background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%); color: white; border: none; font-weight: 600; border-radius: 8px; padding: 12px; transition: all 0.3s ease; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);}
    div.stButton > button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 8px 15px rgba(37, 99, 235, 0.4); background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA MANAGEMENT ---
CT_DATA_FILE = "threat_data_ct.json"
ST_DATA_FILE = "threat_data_st.json"
WHOIS_DATA_FILE = "threat_data_whois.json"
DORKS_DATA_FILE = "threat_data_dorks.json"

CT_QUERIES_FILE = "queries_ct.json"
ST_QUERIES_FILE = "queries_st.json"
WHOIS_QUERIES_FILE = "queries_whois.json"
DORKS_QUERIES_FILE = "queries_dorks.json"

def load_json(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f: return json.load(f)
        except: return default_val
    return default_val

def save_json(data, filepath):
    with open(filepath, 'w') as f: json.dump(data, f)

if 'user_queries_ct' not in st.session_state: st.session_state.user_queries_ct = load_json(CT_QUERIES_FILE, {"KORPORA": ["%korpora%btn%"]})
if 'user_queries_st' not in st.session_state: st.session_state.user_queries_st = load_json(ST_QUERIES_FILE, {"BTN_MAIN": ["btn.co.id"]})
if 'user_queries_whois' not in st.session_state: st.session_state.user_queries_whois = load_json(WHOIS_QUERIES_FILE, {"BRAND_PROTECT": ["btn.co.id", "korporabybtn.com"]})
if 'user_queries_dorks' not in st.session_state: st.session_state.user_queries_dorks = load_json(DORKS_QUERIES_FILE, {"CONFIDENTIAL_DOCS": ["site:btn.co.id ext:pdf \"rahasia\""], "EXPOSED_DIR": ["site:btn.co.id intitle:\"index of\""]})

def load_data(filepath):
    expected_columns = ["Waktu", "Kategori", "Query", "Domain Terdeteksi", "Issuer CA", "Not Before", "Not After", "Status", "Evidence"]
    if os.path.exists(filepath):
        try:
            df = pd.read_json(filepath)
            if "Domain Terdeteksi" in df.columns: return df.reset_index(drop=True)
        except: pass
    return pd.DataFrame(columns=expected_columns)

def save_data(df, filepath):
    df.to_json(filepath, orient="records")

if 'crawled_data_ct' not in st.session_state: st.session_state.crawled_data_ct = load_data(CT_DATA_FILE)
if 'crawled_data_st' not in st.session_state: st.session_state.crawled_data_st = load_data(ST_DATA_FILE)
if 'crawled_data_whois' not in st.session_state: st.session_state.crawled_data_whois = load_data(WHOIS_DATA_FILE)
if 'crawled_data_dorks' not in st.session_state: st.session_state.crawled_data_dorks = load_data(DORKS_DATA_FILE)

if 'fuzz_results' not in st.session_state: st.session_state.fuzz_results = pd.DataFrame(columns=["Target URL", "Path", "Status Code", "Length", "Result"])
if 'fuzz_target_url' not in st.session_state: st.session_state.fuzz_target_url = ""
if 'auto_crawl_enabled' not in st.session_state: st.session_state.auto_crawl_enabled = False
if 'last_crawl_time' not in st.session_state: st.session_state.last_crawl_time = time.time()

# --- 4. ENGINES ---
def check_domain_alive(domain):
    try:
        url_https = f"https://{domain}" if not domain.startswith("http") else domain
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url_https, timeout=5, headers=headers, verify=False, allow_redirects=True)
        if response.status_code in [403, 401, 406]: return "🔴 Alive", f"HTTP {response.status_code} (WAF)"
        elif response.status_code >= 500: return "🔴 Alive", f"HTTP {response.status_code} (Error)"
        else: return "🔴 Alive", f"HTTP {response.status_code}"
    except requests.exceptions.ReadTimeout: return "⚪ Dead", "Timeout"
    except requests.exceptions.ConnectionError: return "⚪ Dead", "Conn Refused"
    except Exception: return "⚪ Dead", "Error"

# 4A. CT LOGS CRAWLER
def execute_ct_crawl():
    if not st.session_state.user_queries_ct: return
    progress_bar = st.progress(0); status_text = st.empty(); results = []; current = 0
    total = sum(len(q) for q in st.session_state.user_queries_ct.values())
    with st.spinner("🔄 Menarik data CT Logs..."):
        for cat, queries in st.session_state.user_queries_ct.items():
            for q in queries:
                status_text.text(f"Mengaudit CT Logs: {q}...")
                try:
                    res = requests.get(f"https://crt.sh/?q={urllib.parse.quote(q)}&output=json", headers={'User-Agent': 'Mozilla/5.0'}, timeout=25)
                    if res.status_code == 200:
                        unique_certs = {d.strip().replace('*.', ''): c for c in res.json() for d in c.get('name_value', '').lower().split('\n')}
                        for domain, c in list(unique_certs.items())[:50]: 
                            status, evidence = check_domain_alive(domain)
                            issuer = c.get('issuer_name', 'Unknown').split(',')[0].replace('C=', '') if 'C=' in c.get('issuer_name', '') else 'Unknown'
                            results.append({"Waktu": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Kategori": cat, "Query": q, "Domain Terdeteksi": domain, "Issuer CA": issuer, "Not Before": c.get('not_before', 'N/A')[:10], "Not After": c.get('not_after', 'N/A')[:10], "Status": status, "Evidence": evidence})
                except: pass
                current += 1; progress_bar.progress(current / total); time.sleep(1)
        status_text.empty(); progress_bar.empty()
        if results:
            df_combined = pd.concat([st.session_state.crawled_data_ct, pd.DataFrame(results)]).drop_duplicates(subset=['Domain Terdeteksi'], keep='last').reset_index(drop=True)
            st.session_state.crawled_data_ct = df_combined
            save_data(df_combined, CT_DATA_FILE)
            st.success(f"✅ CT Logs Selesai! {len(results)} aset diproses.")

# 4B. SECURITYTRAILS CRAWLER
def execute_st_crawl():
    if not st.session_state.user_queries_st: return
    progress_bar = st.progress(0); status_text = st.empty(); results = []; current = 0
    total = sum(len(q) for q in st.session_state.user_queries_st.values())
    with st.spinner("🔄 Menarik data SecurityTrails..."):
        for cat, queries in st.session_state.user_queries_st.items():
            for q in queries:
                status_text.text(f"Mengaudit SecurityTrails: {q}...")
                root_domain = q.replace('%', '').replace('*.', '').strip()
                if '.' in root_domain:
                    for i, api_key in enumerate(ST_API_KEYS):
                        try:
                            res = requests.get(f"https://api.securitytrails.com/v1/domain/{root_domain}/subdomains", headers={"accept": "application/json", "apikey": api_key}, timeout=15)
                            if res.status_code == 200:
                                if i > 0: st.toast(f"✅ Beralih ke API Key Backup ke-{i+1}", icon='🔑')
                                subdomains = [f"{s}.{root_domain}" for s in res.json().get('subdomains', [])]
                                for sub in subdomains[:100]:
                                    status, evidence = check_domain_alive(sub)
                                    results.append({"Waktu": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Kategori": cat, "Query": q, "Domain Terdeteksi": sub, "Issuer CA": "SecurityTrails", "Not Before": datetime.now().strftime('%Y-%m-%d'), "Not After": "N/A", "Status": status, "Evidence": evidence})
                                break
                            elif res.status_code in [429, 403]: continue
                            else: break
                        except: continue
                current += 1; progress_bar.progress(current / total); time.sleep(1.5)
        status_text.empty(); progress_bar.empty()
        if results:
            df_combined = pd.concat([st.session_state.crawled_data_st, pd.DataFrame(results)]).drop_duplicates(subset=['Domain Terdeteksi'], keep='last').reset_index(drop=True)
            st.session_state.crawled_data_st = df_combined
            save_data(df_combined, ST_DATA_FILE)
            st.success(f"✅ SecurityTrails Selesai! {len(results)} aset diproses.")

# 4C. WHOISXML TYPOSQUATTING CRAWLER
def execute_whois_crawl():
    if not st.session_state.user_queries_whois: return
    progress_bar = st.progress(0); status_text = st.empty(); results = []; current = 0
    total = sum(len(q) for q in st.session_state.user_queries_whois.values())
    with st.spinner("🔄 Mencari Phishing via WhoisXML..."):
        for cat, queries in st.session_state.user_queries_whois.items():
            for q in queries:
                root_domain = q.replace('%', '').replace('*.', '').strip()
                keyword = root_domain.split('.')[0] if '.' in root_domain else root_domain
                status_text.text(f"Scanning: {root_domain} & lookalikes '{keyword}'...")
                try:
                    url = "https://domains-subdomains-discovery.whoisxmlapi.com/api/v1"
                    payload = {"apiKey": WHOISXML_API_KEY, "domains": {"include": [root_domain, keyword]}}
                    res = requests.post(url, json=payload, timeout=20)
                    if res.status_code == 200:
                        domains_list = res.json().get('domainsList', [])
                        for domain_name in domains_list[:50]:
                            if domain_name.lower() != root_domain.lower():
                                status, evidence = check_domain_alive(domain_name)
                                results.append({"Waktu": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Kategori": cat, "Query": q, "Domain Terdeteksi": domain_name, "Issuer CA": "WhoisXML (Brand Protect)", "Not Before": datetime.now().strftime('%Y-%m-%d'), "Not After": "N/A", "Status": status, "Evidence": evidence})
                except: pass
                current += 1; progress_bar.progress(current / total); time.sleep(1.5)
        status_text.empty(); progress_bar.empty()
        if results:
            df_combined = pd.concat([st.session_state.crawled_data_whois, pd.DataFrame(results)]).drop_duplicates(subset=['Domain Terdeteksi'], keep='last').reset_index(drop=True)
            st.session_state.crawled_data_whois = df_combined
            save_data(df_combined, WHOIS_DATA_FILE)
            st.success(f"✅ WhoisXML Selesai! Ditemukan {len(results)} aset mencurigakan.")

# 4D. GOOGLE DORK ENGINE
def execute_dork_crawl():
    if not st.session_state.user_queries_dorks: return
    progress_bar = st.progress(0); status_text = st.empty(); results = []; current = 0
    total = sum(len(q) for q in st.session_state.user_queries_dorks.values())
    
    with st.spinner("🕵️ Mengeksekusi Google Dorking Engine..."):
        for cat, queries in st.session_state.user_queries_dorks.items():
            for q in queries:
                status_text.text(f"Dorking: {q}...")
                url = "https://www.googleapis.com/customsearch/v1"
                params = {'q': q, 'key': GOOGLE_API_KEY, 'cx': GOOGLE_CX, 'num': 10}
                
                try:
                    res = requests.get(url, params=params, timeout=15)
                    if res.status_code == 200:
                        items = res.json().get('items', [])
                        for item in items:
                            link = item.get('link', '')
                            snippet = item.get('snippet', '')[:100] + "..."
                            results.append({
                                "Waktu": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "Kategori": cat, "Query": q, "Domain Terdeteksi": link, 
                                "Issuer CA": "Google Dork", "Not Before": datetime.now().strftime('%Y-%m-%d'), 
                                "Not After": "N/A", "Status": "🔴 Exposed", "Evidence": snippet
                            })
                    elif res.status_code == 429:
                        st.error("🛑 Limit API Google habis!")
                except Exception as e: 
                    st.error(f"Error: {e}")
                current += 1; progress_bar.progress(current / total); time.sleep(1.5) 
                
        status_text.empty(); progress_bar.empty()
        if results:
            df_combined = pd.concat([st.session_state.crawled_data_dorks, pd.DataFrame(results)]).drop_duplicates(subset=['Domain Terdeteksi'], keep='last').reset_index(drop=True)
            st.session_state.crawled_data_dorks = df_combined
            save_data(df_combined, DORKS_DATA_FILE)
            st.success(f"✅ Dorking Selesai! Ditemukan {len(results)} temuan terekspos.")

# --- MASTER AUTO CRAWL ---
def execute_master_auto_crawl():
    execute_ct_crawl()
    execute_st_crawl()
    execute_whois_crawl()
    execute_dork_crawl() 

# --- 5. FUZZER ENGINE ---
def execute_fuzzer(target_url, wordlist_text):
    if not target_url.startswith("http"): target_url = "https://" + target_url
    if not target_url.endswith("/"): target_url += "/"
    words = [w.strip() for w in wordlist_text.split('\n') if w.strip()]
    if not words: return
    st.session_state.fuzz_results = pd.DataFrame(columns=["Target URL", "Path", "Status Code", "Length", "Result"])
    current = 0; pb = st.progress(0); st_text = st.empty(); fuzz_data = []

    with st.spinner("🚀 Fuzzing in progress..."):
        for w in words:
            test_url = target_url + w
            st_text.text(f"Testing: {test_url}")
            try:
                res = requests.get(test_url, timeout=3, verify=False, allow_redirects=False, headers={'User-Agent': 'Mozilla/5.0 Fuzz/1.0'})
                if res.status_code in [200, 204, 301, 302, 307, 401, 403, 500]:
                    icon = "🟢 Found" if res.status_code == 200 else ("🟡 Redirect" if res.status_code in [301,302,307] else "🔴 Restricted")
                    fuzz_data.append({"Target URL": target_url, "Path": f"/{w}", "Status Code": res.status_code, "Length": len(res.content), "Result": icon})
            except: pass 
            current += 1; pb.progress(current / len(words)); time.sleep(0.05)
            
    st_text.empty(); pb.empty()
    if fuzz_data:
        st.session_state.fuzz_results = pd.DataFrame(fuzz_data)
        st.success(f"🎉 Fuzzing selesai! Ditemukan {len(fuzz_data)} direktori.")

# --- 6. TAMPILAN SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px; padding: 10px; background: rgba(15, 23, 42, 0.5); border-radius: 12px; border: 1px solid #1e293b;">
            <h2 style="margin:0; font-weight:800; color:#f8fafc; letter-spacing: 1px;">OSINT <span style="color:#38bdf8;">PRO</span></h2>
            <p style="margin:0; font-size:0.8rem; color:#64748b;">Attack Surface Management</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='font-size:0.8rem; color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom: 5px;'>Navigation</p>", unsafe_allow_html=True)
    menu_selection = st.radio("Navigasi:", ["🌍 Global Dashboard", "📡 Threat Intel (CT Logs)", "🌐 SecurityTrails Recon", "🕸️ Typosquatting Recon", "🕵️ Google Dork Engine", "🔎 Directory Fuzzer", "⚙️ Target Settings"], label_visibility="collapsed")
    
    st.markdown("<hr style='border-color: #1e293b; margin: 25px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-size:0.8rem; color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom: 10px;'>Engine Control</p>", unsafe_allow_html=True)
    auto_refresh_toggle = st.toggle("⏱️ Enable 3-Hour Engine", value=st.session_state.auto_crawl_enabled)
    
    if auto_refresh_toggle != st.session_state.auto_crawl_enabled:
        st.session_state.auto_crawl_enabled = auto_refresh_toggle
        if auto_refresh_toggle:
             st.session_state.last_crawl_time = time.time()
             st.rerun()

    if st.session_state.auto_crawl_enabled:
        elapsed_time = time.time() - st.session_state.last_crawl_time
        remaining_time = 10800 - elapsed_time 
        
        if remaining_time <= 0:
            execute_master_auto_crawl()
            st.session_state.last_crawl_time = time.time()
            st.rerun()
        else:
            hours, rem = divmod(int(remaining_time), 3600)
            mins, secs = divmod(rem, 60)
            st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 12px; border-radius: 8px; margin-top: 10px;">
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span class="status-dot"></span>
                        <span style="font-size: 0.8rem; font-weight: 700; color: #10b981; text-transform: uppercase;">Quad-Engine Active</span>
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 600; color: #f8fafc; padding-left: 16px;">
                        {hours:02d}:{mins:02d}:{secs:02d} <span style="font-size:0.7rem; color:#64748b;">to next scan</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #1e293b; margin: 25px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.8rem; color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom: 10px;'>Data Management</p>", unsafe_allow_html=True)
    
    if menu_selection == "📡 Threat Intel (CT Logs)":
        if st.button("🗑️ Clear CT Logs Data", use_container_width=True):
            st.session_state.crawled_data_ct = pd.DataFrame(); save_data(pd.DataFrame(), CT_DATA_FILE); st.rerun()
    elif menu_selection == "🌐 SecurityTrails Recon":
        if st.button("🗑️ Clear ST Logs Data", use_container_width=True):
            st.session_state.crawled_data_st = pd.DataFrame(); save_data(pd.DataFrame(), ST_DATA_FILE); st.rerun()
    elif menu_selection == "🕸️ Typosquatting Recon":
        if st.button("🗑️ Clear Whois Data", use_container_width=True):
            st.session_state.crawled_data_whois = pd.DataFrame(); save_data(pd.DataFrame(), WHOIS_DATA_FILE); st.rerun()
    elif menu_selection == "🕵️ Google Dork Engine":
        if st.button("🗑️ Clear Dork Data", use_container_width=True):
            st.session_state.crawled_data_dorks = pd.DataFrame(); save_data(pd.DataFrame(), DORKS_DATA_FILE); st.rerun()
    elif menu_selection == "🔎 Directory Fuzzer":
        if st.button("🗑️ Clear Fuzzer Results", use_container_width=True):
            st.session_state.fuzz_results = pd.DataFrame(columns=["Target URL", "Path", "Status Code", "Length", "Result"]); st.rerun()

# --- 7. MAIN AREA (ROUTING) ---

def build_dashboard(df, queries_dict, title, subtitle, crawl_func):
    st.markdown(f'<p class="title-glow">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">{subtitle}</p>', unsafe_allow_html=True)
    
    colA, colB = st.columns([8, 2])
    with colB:
        if st.button("⚡ FORCE CRAWL", use_container_width=True, type="primary"):
            crawl_func(); st.rerun()

    total_dom = len(df)
    alive_dom = len(df[df["Status"].isin(['🔴 Alive', '🔴 Exposed'])]) if not df.empty else 0
    active_q = sum(len(q) for q in queries_dict.values())

    tab_dash, tab_logs, tab_analytics = st.tabs(["🚀 Command Center", "📋 Asset Database", "📊 Analytics"])

    with tab_dash:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card">
                    <div class="card-header"><span class="m-title">Monitored Targets</span><span class="m-icon">🎯</span></div>
                    <p class="m-value">{active_q}</p><p class="m-sub">Active queries in database</p>
                </div>
                <div class="metric-card">
                    <div class="card-header"><span class="m-title">Assets Discovered</span><span class="m-icon">🔍</span></div>
                    <p class="m-value">{total_dom}</p><p class="m-sub">Total unique records found</p>
                </div>
                <div class="metric-card {'alert' if alive_dom > 0 else 'safe'}">
                    <div class="card-header"><span class="m-title" style="color: {'#fca5a5' if alive_dom > 0 else '#6ee7b7'};">Live Targets / Exposed</span><span class="m-icon">🔴</span></div>
                    <p class="m-value">{alive_dom}</p><p class="m-sub" style="color: {'#ef4444' if alive_dom > 0 else '#10b981'};">Requires attention</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h3 style='font-size: 1.2rem; font-weight: 700; color: #e2e8f0; margin-bottom: 15px;'>⚡ Recent Discoveries</h3>", unsafe_allow_html=True)
        if not df.empty: st.dataframe(df.tail(8).iloc[::-1].reset_index(drop=True), use_container_width=True, hide_index=True)

    with tab_logs:
        if not df.empty:
            def highlight_alive(val): return 'background-color: rgba(239, 68, 68, 0.2); color: #fca5a5; font-weight: bold;' if val in ['🔴 Alive', '🔴 Exposed'] else ''
            try: styled_df = df.style.map(highlight_alive, subset=['Status'])
            except: styled_df = df.style.applymap(highlight_alive, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True, height=500, hide_index=True)
        else: st.info("Database empty.")

    with tab_analytics:
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig1 = px.pie(df['Kategori'].value_counts().reset_index(), values='count', names='Kategori', hole=0.55, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig1.update_layout(title_text="Asset Distribution", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'))
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                fig2 = px.bar(df['Status'].value_counts().reset_index(), x='count', y='Status', orientation='h', color='Status', color_discrete_map={'🔴 Alive': 'rgba(239, 68, 68, 0.8)', '🔴 Exposed': 'rgba(239, 68, 68, 0.8)', '⚪ Dead': 'rgba(71, 85, 105, 0.8)'})
                fig2.update_layout(title_text="Target Availability", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        else: st.info("Run crawl to generate analytics.")

# --- ROUTING LOGIC ---

if menu_selection == "🌍 Global Dashboard":
    st.markdown('<p class="title-glow">GLOBAL COMMAND CENTER</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Unified Threat Intelligence & Attack Surface Overview</p>', unsafe_allow_html=True)
    
    df_ct = st.session_state.crawled_data_ct.copy()
    df_st = st.session_state.crawled_data_st.copy()
    df_whois = st.session_state.crawled_data_whois.copy()
    df_dorks = st.session_state.crawled_data_dorks.copy()
    
    if not df_ct.empty: df_ct['Engine Source'] = 'CT Logs (crt.sh)'
    if not df_st.empty: df_st['Engine Source'] = 'SecurityTrails'
    if not df_whois.empty: df_whois['Engine Source'] = 'WhoisXML (Brand Protect)'
    if not df_dorks.empty: df_dorks['Engine Source'] = 'Google Dorks'
    
    df_all = pd.concat([df_ct, df_st, df_whois, df_dorks])
    if not df_all.empty:
        df_all = df_all.drop_duplicates(subset=['Domain Terdeteksi'], keep='last').reset_index(drop=True)
        
    total_gabungan = len(df_all)
    alive_gabungan = len(df_all[df_all['Status'].isin(['🔴 Alive', '🔴 Exposed'])]) if not df_all.empty else 0
    total_queries_gabungan = sum(len(q) for q in st.session_state.user_queries_ct.values()) + sum(len(q) for q in st.session_state.user_queries_st.values()) + sum(len(q) for q in st.session_state.user_queries_whois.values()) + sum(len(q) for q in st.session_state.user_queries_dorks.values())

    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card purple">
                <div class="card-header"><span class="m-title" style="color: #c4b5fd;">Unified Assets</span><span class="m-icon">🌐</span></div>
                <p class="m-value">{total_gabungan}</p><p class="m-sub">Unique cross-engine domains/URLs</p>
            </div>
            <div class="metric-card">
                <div class="card-header"><span class="m-title">All Queries</span><span class="m-icon">📡</span></div>
                <p class="m-value">{total_queries_gabungan}</p><p class="m-sub">Monitored across 4 engines</p>
            </div>
            <div class="metric-card {'alert' if alive_gabungan > 0 else 'safe'}">
                <div class="card-header"><span class="m-title" style="color: {'#fca5a5' if alive_gabungan > 0 else '#6ee7b7'};">Global Live Attack Surface</span><span class="m-icon">🔥</span></div>
                <p class="m-value">{alive_gabungan}</p><p class="m-sub" style="color: {'#ef4444' if alive_gabungan > 0 else '#10b981'};">Combined responding servers & leaks</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not df_all.empty:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            source_counts = df_all['Engine Source'].value_counts().reset_index()
            fig_g1 = px.pie(source_counts, values='count', names='Engine Source', hole=0.55, color_discrete_sequence=['#3b82f6', '#10b981', '#f97316', '#eab308'])
            fig_g1.update_layout(title_text="Discovery by Engine", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'))
            st.plotly_chart(fig_g1, use_container_width=True)
        with col_c2:
            stat_counts = df_all['Status'].value_counts().reset_index()
            fig_g2 = px.bar(stat_counts, x='count', y='Status', orientation='h', color='Status', color_discrete_map={'🔴 Alive': 'rgba(239, 68, 68, 0.8)', '🔴 Exposed': 'rgba(239, 68, 68, 0.8)', '⚪ Dead': 'rgba(71, 85, 105, 0.8)'})
            fig_g2.update_layout(title_text="Global Target Availability", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), showlegend=False)
            st.plotly_chart(fig_g2, use_container_width=True)

        st.markdown("<h3 style='font-size: 1.2rem; font-weight: 700; color: #e2e8f0; margin-bottom: 15px;'>🗃️ Unified Asset Database</h3>", unsafe_allow_html=True)
        cols = ['Engine Source', 'Waktu', 'Kategori', 'Domain Terdeteksi', 'Status', 'Evidence', 'Issuer CA']
        df_display = df_all[cols]
        
        def highlight_alive(val): return 'background-color: rgba(239, 68, 68, 0.2); color: #fca5a5; font-weight: bold;' if val in ['🔴 Alive', '🔴 Exposed'] else ''
        try: styled_df = df_display.style.map(highlight_alive, subset=['Status'])
        except: styled_df = df_display.style.applymap(highlight_alive, subset=['Status'])
        
        st.dataframe(styled_df, use_container_width=True, height=400, hide_index=True)
        
        csv_global = df_all.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Unified Database", data=csv_global, file_name=f"Global_Recon_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", type="primary")
    else:
        st.info("Global Database is empty. Configure targets in Settings to begin data collection.")

elif menu_selection == "📡 Threat Intel (CT Logs)":
    build_dashboard(st.session_state.crawled_data_ct, st.session_state.user_queries_ct, "CT LOGS ENGINE", "Certificate Transparency Reconnaissance", execute_ct_crawl)

elif menu_selection == "🌐 SecurityTrails Recon":
    build_dashboard(st.session_state.crawled_data_st, st.session_state.user_queries_st, "SECURITYTRAILS ENGINE", "Passive DNS Subdomain Enumeration", execute_st_crawl)

elif menu_selection == "🕸️ Typosquatting Recon":
    build_dashboard(st.session_state.crawled_data_whois, st.session_state.user_queries_whois, "TYPOSQUATTING ENGINE", "Phishing & Brand Impersonation Detection (WhoisXML)", execute_whois_crawl)

elif menu_selection == "🕵️ Google Dork Engine":
    build_dashboard(st.session_state.crawled_data_dorks, st.session_state.user_queries_dorks, "GOOGLE DORK ENGINE", "Automated Sensitive File & Directory Leak Detection", execute_dork_crawl)
    st.info("💡 **Catatan Limit:** API Google Custom Search versi gratis dibatasi maksimal **100 Request / Hari**. Gunakan secara bijak.")
    
    # --- BAGIAN AI THREAT ANALYST ---
    st.markdown("---")
    st.markdown("<h3 style='font-size: 1.2rem; font-weight: 700; color: #a855f7; margin-bottom: 15px;'>🤖 AI Threat Analyst (Powered by Gemini)</h3>", unsafe_allow_html=True)
    
    if AI_MODULE_AVAILABLE:
        st.write("Klik tombol di bawah untuk membiarkan AI menganalisis apakah dokumen/file yang bocor ini adalah ancaman nyata atau False Positive.")
        if st.button("🧠 Analyze Top 5 Leaks with AI", type="primary"):
            with st.spinner("AI sedang membaca dan menganalisis kebocoran data..."):
                df_ai = ai_engine.run_ai_analysis_on_dorks(DORKS_DATA_FILE)
                
                if not df_ai.empty:
                    st.success("Analisis AI Selesai!")
                    for index, row in df_ai.iterrows():
                        st.markdown(f"""
                        <div style="background: rgba(15, 23, 42, 0.8); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #a855f7; border-top: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                            <div style="margin-bottom: 10px;">
                                <span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-right: 10px;">URL BocoR</span>
                                <a href="{row['Domain Terdeteksi']}" target="_blank" style="color: #e2e8f0; text-decoration: none; word-break: break-all;">{row['Domain Terdeteksi']}</a>
                            </div>
                            <div style="margin-bottom: 15px;">
                                <span style="background: rgba(148, 163, 184, 0.2); color: #94a3b8; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-right: 10px;">Snippet Data</span>
                                <span style="color: #94a3b8; font-style: italic;">"{row['Evidence']}"</span>
                            </div>
                            <div style="background: #050505; padding: 15px; border-radius: 8px; border: 1px solid #334155;">
                                <div style="font-family: 'JetBrains Mono', monospace; color: #c4b5fd; white-space: pre-wrap; font-size: 0.9rem; line-height: 1.5;">{row['AI Threat Analysis']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("Belum ada data Dork (file bocor) yang bisa dianalisis.")
    else:
        st.error("Modul AI (`ai_engine.py`) tidak ditemukan atau ada error saat mengimpornya. Pastikan file tersebut ada di folder yang sama dan library `google-generativeai` sudah di-install.")

elif menu_selection == "🔎 Directory Fuzzer":
    st.markdown('<p class="title-glow">DIRECTORY FUZZER</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Brute-force hidden paths & sensitive files (Gobuster Engine Concept)</p>', unsafe_allow_html=True)
    
    with st.form("fuzzer_form"):
        target_url = st.text_input("Target URL", value=st.session_state.fuzz_target_url, placeholder="https://example.com")
        default_wordlist = "admin\nlogin\napi\nbackup\n.git\nconfig\n.env\ndashboard\ntest"
        wordlist_input = st.text_area("Wordlist Payload (One per line)", value=default_wordlist, height=150)
        btn_fuzz = st.form_submit_button("🔥 INITIATE FUZZING SEQUENCE", type="primary")
        
        if btn_fuzz and target_url: execute_fuzzer(target_url, wordlist_input)
            
    if not st.session_state.fuzz_results.empty:
        st.markdown("<h3 style='font-size: 1.2rem; font-weight: 700; color: #e2e8f0; margin-bottom: 15px;'>📑 Discovered Paths</h3>", unsafe_allow_html=True)
        def highlight_fuzz(val):
            if val == '🟢 Found': return 'color: #10b981; font-weight: bold;'
            if val == '🟡 Redirect': return 'color: #fbbf24;'
            if val == '🔴 Restricted': return 'color: #ef4444;'
            return ''
        try: fuzz_df = st.session_state.fuzz_results.style.map(highlight_fuzz, subset=['Result'])
        except: fuzz_df = st.session_state.fuzz_results.style.applymap(highlight_fuzz, subset=['Result'])
        st.dataframe(fuzz_df, use_container_width=True, hide_index=True)

elif menu_selection == "⚙️ Target Settings":
    st.markdown('<p class="title-glow">ENGINE SETTINGS</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Manage target queries for all 4 Intelligence Engines</p>', unsafe_allow_html=True)
    
    tab_ct, tab_st, tab_whois, tab_dorks = st.tabs(["🎯 CT Logs", "🌐 SecurityTrails", "🕸️ Typosquatting", "🕵️ Google Dorks"])
    
    with tab_ct:
        st.markdown("<h3 style='font-size: 1.1rem; font-weight: 600; color: #e2e8f0;'>➕ Tambah Target CT Logs (Dukung Wildcard %)</h3>", unsafe_allow_html=True)
        with st.form("form_ct_logs"):
            c1, c2, c3 = st.columns([3, 5, 2])
            new_cat_ct = c1.text_input("Kategori Target", placeholder="ex: CORPORATE")
            new_query_ct = c2.text_input("Sintaks CT Logs", placeholder="ex: %btn%")
            if c3.form_submit_button("Simpan Target") and new_cat_ct and new_query_ct:
                c = new_cat_ct.upper()
                if c not in st.session_state.user_queries_ct: st.session_state.user_queries_ct[c] = []
                if new_query_ct not in st.session_state.user_queries_ct[c]:
                    st.session_state.user_queries_ct[c].append(new_query_ct)
                    save_json(st.session_state.user_queries_ct, CT_QUERIES_FILE); st.rerun()

        st.markdown("<br><h3 style='font-size: 1.1rem; font-weight: 600; color: #e2e8f0;'>📋 Database CT Logs Queries</h3>", unsafe_allow_html=True)
        for cat, qs in st.session_state.user_queries_ct.items():
            st.markdown(f"**📁 {cat}**")
            for idx, q in enumerate(qs):
                c_q, c_b = st.columns([10, 1])
                c_q.markdown(f"<div class='query-box'><span>🔍 {q}</span></div>", unsafe_allow_html=True)
                if c_b.button("🗑️", key=f"del_ct_{cat}_{idx}"):
                    st.session_state.user_queries_ct[cat].remove(q)
                    if not st.session_state.user_queries_ct[cat]: del st.session_state.user_queries_ct[cat]
                    save_json(st.session_state.user_queries_ct, CT_QUERIES_FILE); st.rerun()

    with tab_st:
        st.markdown("<h3 style='font-size: 1.1rem; font-weight: 600; color: #e2e8f0;'>➕ Tambah Target SecurityTrails (Hanya Root Domain)</h3>", unsafe_allow_html=True)
        with st.form("form_st_logs"):
            c1, c2, c3 = st.columns([3, 5, 2])
            new_cat_st = c1.text_input("Kategori Target", placeholder="ex: CORPORATE MAIN")
            new_query_st = c2.text_input("Root Domain", placeholder="ex: btn.co.id")
            if c3.form_submit_button("Simpan Target") and new_cat_st and new_query_st:
                c = new_cat_st.upper()
                if c not in st.session_state.user_queries_st: st.session_state.user_queries_st[c] = []
                if new_query_st not in st.session_state.user_queries_st[c]:
                    st.session_state.user_queries_st[c].append(new_query_st)
                    save_json(st.session_state.user_queries_st, ST_QUERIES_FILE); st.rerun()

        st.markdown("<br><h3 style='font-size: 1.1rem; font-weight: 600; color: #e2e8f0;'>📋 Database SecurityTrails Queries</h3>", unsafe_allow_html=True)
        for cat, qs in st.session_state.user_queries_st.items():
            st.markdown(f"**📁 {cat}**")
            for idx, q in enumerate(qs):
                c_q, c_b = st.columns([10, 1])
                c_q.markdown(f"<div class='query-box' style='border-left: 4px solid #10b981;'><span>🌐 {q}</span></div>", unsafe_allow_html=True)
                if c_b.button("🗑️", key=f"del_st_{cat}_{idx}"):
                    st.session_state.user_queries_st[cat].remove(q)
                    if not st.session_state.user_queries_st[cat]: del st.session_state.user_queries_st[cat]
                    save_json(st.session_state.user_queries_st, ST_QUERIES_FILE); st.rerun()

    with tab_whois:
        st.markdown("<h3 style='font-size: 1.1rem; font-weight: 600; color: #e2e8f0;'>➕ Tambah Target Typosquatting (Hanya Root Domain)</h3>", unsafe_allow_html=True)
        st.info("💡 Engine ini akan otomatis mengambil kata kunci dari domain Anda (misal 'btn.co.id' menjadi 'btn') dan mencari seluruh domain phishing/tiruan di internet.")
        with st.form("form_whois_logs"):
            c1, c2, c3 = st.columns([3, 5, 2])
            new_cat_whois = c1.text_input("Kategori Target", placeholder="ex: BRAND PROTECT")
            new_query_whois = c2.text_input("Root Domain", placeholder="ex: btn.co.id")
            if c3.form_submit_button("Simpan Target") and new_cat_whois and new_query_whois:
                c = new_cat_whois.upper()
                if c not in st.session_state.user_queries_whois: st.session_state.user_queries_whois[c] = []
                if new_query_whois not in st.session_state.user_queries_whois[c]:
                    st.session_state.user_queries_whois[c].append(new_query_whois)
                    save_json(st.session_state.user_queries_whois, WHOIS_QUERIES_FILE); st.rerun()

        st.markdown("<br><h3 style='font-size: 1.1rem; font-weight: 600; color: #e2e8f0;'>📋 Database Typosquatting Queries</h3>", unsafe_allow_html=True)
        for cat, qs in st.session_state.user_queries_whois.items():
            st.markdown(f"**📁 {cat}**")
            for idx, q in enumerate(qs):
                c_q, c_b = st.columns([10, 1])
                c_q.markdown(f"<div class='query-box' style='border-left: 4px solid #f97316;'><span>🕸️ {q}</span></div>", unsafe_allow_html=True)
                if c_b.button("🗑️", key=f"del_whois_{cat}_{idx}"):
                    st.session_state.user_queries_whois[cat].remove(q)
                    if not st.session_state.user_queries_whois[cat]: del st.session_state.user_queries_whois[cat]
                    save_json(st.session_state.user_queries_whois, WHOIS_QUERIES_FILE); st.rerun()

    with tab_dorks:
        st.markdown("<h3 style='font-size: 1.1rem; font-weight: 600; color: #e2e8f0;'>➕ Tambah Target Google Dork</h3>", unsafe_allow_html=True)
        st.info("💡 **Format Dork:** Gunakan sintaks seperti `site:domain.com ext:pdf` atau `site:domain.com intitle:\"index of\"`")
        with st.form("form_dork_logs"):
            c1, c2, c3 = st.columns([3, 5, 2])
            new_cat_dork = c1.text_input("Kategori Target", placeholder="ex: PDF LEAKS")
            new_query_dork = c2.text_input("Sintaks Dork", placeholder="ex: site:btn.co.id ext:pdf")
            if c3.form_submit_button("Simpan Target") and new_cat_dork and new_query_dork:
                c = new_cat_dork.upper()
                if c not in st.session_state.user_queries_dorks: st.session_state.user_queries_dorks[c] = []
                if new_query_dork not in st.session_state.user_queries_dorks[c]:
                    st.session_state.user_queries_dorks[c].append(new_query_dork)
                    save_json(st.session_state.user_queries_dorks, DORKS_QUERIES_FILE); st.rerun()

        st.markdown("<br><h3 style='font-size: 1.1rem; font-weight: 600; color: #e2e8f0;'>📋 Database Dork Queries</h3>", unsafe_allow_html=True)
        for cat, qs in st.session_state.user_queries_dorks.items():
            st.markdown(f"**📁 {cat}**")
            for idx, q in enumerate(qs):
                c_q, c_b = st.columns([10, 1])
                c_q.markdown(f"<div class='query-box' style='border-left: 4px solid #eab308;'><span>🕵️ {q}</span></div>", unsafe_allow_html=True)
                if c_b.button("🗑️", key=f"del_dork_{cat}_{idx}"):
                    st.session_state.user_queries_dorks[cat].remove(q)
                    if not st.session_state.user_queries_dorks[cat]: del st.session_state.user_queries_dorks[cat]
                    save_json(st.session_state.user_queries_dorks, DORKS_QUERIES_FILE); st.rerun()

    st.markdown("---")
    st.markdown("#### ⚠️ Danger Zone (Master Reset)")
    if st.button("Hapus SEMUA Pengaturan & Database (Factory Reset)", type="primary"):
        st.session_state.crawled_data_ct = pd.DataFrame(); st.session_state.crawled_data_st = pd.DataFrame()
        st.session_state.crawled_data_whois = pd.DataFrame(); st.session_state.crawled_data_dorks = pd.DataFrame()
        for f in [CT_DATA_FILE, ST_DATA_FILE, WHOIS_DATA_FILE, DORKS_DATA_FILE, CT_QUERIES_FILE, ST_QUERIES_FILE, WHOIS_QUERIES_FILE, DORKS_QUERIES_FILE]:
            if os.path.exists(f): os.remove(f)
        st.success("Sistem dikembalikan ke pengaturan pabrik."); time.sleep(1); st.rerun()

# --- REFRESH LOGIC UNTUK TIMER ---
if st.session_state.auto_crawl_enabled:
    time.sleep(2)
    st.rerun()