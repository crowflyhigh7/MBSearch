import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

SPREADSHEET_ID = "1qis9zW7EHPgBRQLAIuOhEas3vJOzdX0tqXCwh1CScWE"
PASSWORD = "mb1234"

SEARCH_COLS = ["cat_make", "cat_model", "cat_submodel", "cat_grade", "cat_subgrade", "platenumber"]
DISPLAY_COLS = [
    "cat_submodel", "cat_grade", "cat_subgrade", "platenumber",
    "modelyear", "reg_year", "reg_month", "reg_date",
    "mileage", "fuel", "status", "ownerprice", "mbprice"
]

LABELS = {
    "cat_submodel": "세부모델",
    "cat_grade": "등급",
    "cat_subgrade": "세부등급",
    "platenumber": "차량번호",
    "modelyear": "연식",
    "reg_year": "등록연도",
    "reg_month": "등록월",
    "reg_date": "등록일",
    "mileage": "주행거리",
    "fuel": "연료",
    "status": "상태",
    "ownerprice": "오너가",
    "mbprice": "MB가",
}

st.set_page_config(page_title="MB 매물 조회", page_icon="🚗", layout="centered")

st.markdown("""
<style>
    .card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        border-left: 4px solid #e63946;
    }
    .card-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px 18px;
        margin-bottom: 4px;
    }
    .card-item {
        font-size: 13px;
        color: #cdd6f4;
    }
    .card-label {
        color: #888;
        font-size: 11px;
    }
    .mb-price {
        color: #e63946;
        font-weight: 900;
        font-size: 22px;
    }
    .owner-price {
        color: #a6adc8;
        font-size: 14px;
    }
    .plate {
        background: #313244;
        border-radius: 6px;
        padding: 2px 8px;
        font-weight: 700;
        font-size: 15px;
        color: #cba6f7;
        cursor: pointer;
        user-select: none;
        transition: opacity 0.15s;
    }
    .plate:active { opacity: 0.6; }
    .card-title {
        font-size: 16px;
        font-weight: 700;
        color: #cdd6f4;
        margin-bottom: 10px;
    }
    .result-count {
        color: #a6adc8;
        font-size: 13px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚗 MB 매물 조회")


def format_number(val):
    try:
        n = int(str(val).replace(",", "").replace(" ", ""))
        return f"{n:,}"
    except Exception:
        return val


@st.cache_data(ttl=120)
def load_data():
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
    except (KeyError, FileNotFoundError):
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet("st_stocklist")
    rows = sheet.get_all_values()
    if not rows:
        raise ValueError("시트에 데이터가 없습니다.")
    headers = [h.strip() for h in rows[0]]
    df = pd.DataFrame(rows[1:], columns=headers)
    df.columns = df.columns.str.strip()
    return df


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        with st.form("login_form"):
            pw = st.text_input("비밀번호를 입력하세요", type="password", placeholder="Password")
            submitted = st.form_submit_button("확인")
            if submitted:
                if pw == PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("비밀번호가 틀렸습니다.")
        return False
    return True


def render_card(row):
    submodel = row.get("cat_submodel", "")
    grade = row.get("cat_grade", "")
    subgrade = row.get("cat_subgrade", "")
    plate = row.get("platenumber", "")
    modelyear = row.get("modelyear", "")
    reg_year = row.get("reg_year", "")
    reg_month = row.get("reg_month", "")
    reg_date = row.get("reg_date", "")
    mileage_raw = row.get("mileage", "")
    try:
        mileage = f"{int(str(mileage_raw).replace(',', '').replace(' ', '')):,} km"
    except (ValueError, TypeError):
        mileage = mileage_raw
    fuel = row.get("fuel", "")
    status = row.get("status", "")
    ownerprice = format_number(row.get("ownerprice", ""))
    mbprice = format_number(row.get("mbprice", ""))

    title = " ".join(filter(None, [str(submodel), str(grade), str(subgrade)]))
    reg_info = "/".join(filter(None, [str(reg_year), str(reg_month), str(reg_date)]))

    st.markdown(f"""
    <div class="card">
        <div class="card-title">{title}</div>
        <div class="card-row">
            <span class="plate" onclick="(function(el, txt){{
                var prev = el.innerText;
                if(navigator.clipboard && navigator.clipboard.writeText){{
                    navigator.clipboard.writeText(txt).then(function(){{
                        el.innerText = '✓ 복사됨';
                        setTimeout(function(){{ el.innerText = prev; }}, 1200);
                    }});
                }} else {{
                    var ta = document.createElement('textarea');
                    ta.value = txt; document.body.appendChild(ta);
                    ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
                    el.innerText = '✓ 복사됨';
                    setTimeout(function(){{ el.innerText = prev; }}, 1200);
                }}
            }})(this, '{plate}')">{plate}</span>
            <span class="card-item"><span class="card-label">연식 </span>{modelyear}</span>
            <span class="card-item"><span class="card-label">등록 </span>{reg_info}</span>
        </div>
        <div class="card-row">
            <span class="card-item"><span class="card-label">주행 </span>{mileage}</span>
            <span class="card-item"><span class="card-label">연료 </span>{fuel}</span>
            <span class="card-item"><span class="card-label">상태 </span>{status}</span>
        </div>
        <div class="card-row" style="margin-top:10px; align-items:baseline; gap:14px;">
            <span class="owner-price">오너가 {ownerprice}</span>
            <span class="mb-price">MB {mbprice}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


if check_password():
    query = st.text_input("🔍 검색", placeholder="차량명, 번호판, 등급 등으로 검색...")

    with st.spinner("데이터 불러오는 중..."):
        try:
            df = load_data()
        except Exception as e:
            st.exception(e)
            st.stop()

    if query:
        q = query.strip().lower()
        mask = pd.Series([False] * len(df), index=df.index)
        for col in SEARCH_COLS:
            if col in df.columns:
                mask |= df[col].astype(str).str.lower().str.contains(q, na=False, regex=False)
        result = df[mask]
    else:
        result = df

    st.markdown(f'<div class="result-count">총 {len(result)}건</div>', unsafe_allow_html=True)

    if result.empty:
        st.info("검색 결과가 없습니다.")
    else:
        for _, row in result.iterrows():
            render_card(row)
