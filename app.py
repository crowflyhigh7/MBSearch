import json
import streamlit as st
import streamlit.components.v1 as components
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
    "cat_submodel": "세부모델", "cat_grade": "등급", "cat_subgrade": "세부등급",
    "platenumber": "차량번호", "modelyear": "연식", "reg_year": "등록연도",
    "reg_month": "등록월", "reg_date": "등록일", "mileage": "주행거리",
    "fuel": "연료", "status": "상태", "ownerprice": "오너가", "mbprice": "MB가",
}

# ─────────────────────────────────────────────────────────────────────────────
# 카드 HTML 템플릿 (이전비 버튼 클릭 → 새 창 오픈)
# ─────────────────────────────────────────────────────────────────────────────
CARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
.card {
  background: #1e1e2e; border-radius: 12px; padding: 14px 18px;
  border-left: 4px solid #e63946; box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.card-title  { font-size: 15px; font-weight: 700; color: #cdd6f4; }
.btn-group   { display: flex; gap: 6px; align-items: center; flex-shrink: 0; }
.icon-btn {
  width: 28px; height: 28px; background: #313244; border: none; border-radius: 6px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.15s; flex-shrink: 0;
}
.icon-btn:hover { background: #45475a; }
.icon-btn svg { width: 14px; height: 14px; stroke: #cba6f7; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.fee-icon { font-size: 14px; line-height: 1; }
.row   { display: flex; flex-wrap: wrap; gap: 6px 16px; margin-bottom: 6px; align-items: center; }
.label { color: #888; font-size: 11px; }
.val   { color: #cdd6f4; font-size: 13px; }
.plate {
  background: #313244; border-radius: 6px; padding: 3px 10px;
  font-weight: 700; font-size: 15px; color: #cba6f7;
  cursor: pointer; user-select: none; display: inline-block; transition: opacity 0.15s;
}
.plate:active { opacity: 0.6; }
.owner   { color: #a6adc8; font-size: 14px; }
.mbprice { color: #e63946; font-weight: 900; font-size: 22px; }
.call-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: #313244; border-radius: 6px; padding: 5px 12px;
  color: #a6e3a1; font-size: 13px; font-weight: 600;
  text-decoration: none; transition: background 0.15s;
}
.call-btn:hover { background: #45475a; }
</style>
</head>
<body>
<div class="card">
  <div class="card-header">
    <div class="card-title">__CARD_TITLE__</div>
    <div class="btn-group">
      <button class="icon-btn" onclick="openFeeWindow()" title="이전비 내역서">
        <span class="fee-icon">📋</span>
      </button>
      <button class="icon-btn" onclick="(function(){
          var url='https://www.mobettercar.kr/detail?id=__STOCK_ID__';
          window.open(url,'_blank');
          if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(url);}
          else{var t=document.createElement('textarea');t.value=url;t.style.cssText='position:fixed;opacity:0;';document.body.appendChild(t);t.focus();t.select();try{document.execCommand('copy');}catch(e){}document.body.removeChild(t);}
        })()" title="매물 상세 보기">
        <svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
      </button>
    </div>
  </div>
  <div class="row">
    <span class="plate" onclick="copyPlate()">__PLATE__</span>
    <span class="val"><span class="label">연식 </span>__MODELYEAR__</span>
    <span class="val"><span class="label">등록 </span>__REG_INFO__</span>
  </div>
  <div class="row">
    <span class="val"><span class="label">주행 </span>__MILEAGE__</span>
    <span class="val"><span class="label">연료 </span>__FUEL__</span>
    <span class="val"><span class="label">상태 </span>__STATUS__</span>
  </div>
  <div class="row" style="margin-top:8px;align-items:baseline;gap:14px;">
    <span class="owner">오너가 __OWNER_PRICE__</span>
    <span class="mbprice">MB __MB_PRICE__</span>
  </div>
  __CALL_BTN__
</div>

<script id="fee-data" type="application/json">__FEE_DATA_JSON__</script>

<script>
function openFeeWindow() {
  var html = JSON.parse(document.getElementById('fee-data').textContent);
  var blob = new Blob([html], { type: 'text/html; charset=utf-8' });
  var url  = URL.createObjectURL(blob);
  window.open(url, '_blank');
  setTimeout(function() { URL.revokeObjectURL(url); }, 60000);
}

// iframe 높이를 카드 실제 높이에 맞게 자동 조절
document.addEventListener('DOMContentLoaded', function() {
  try {
    window.frameElement.style.height = document.body.scrollHeight + 'px';
  } catch(e) {}
});

function copyPlate() {
  var txt  = '__PLATE__';
  var el   = document.querySelector('.plate');
  var prev = el.innerText;
  function done() { el.innerText = '✓ 복사됨'; setTimeout(function(){ el.innerText = prev; }, 1400); }
  function fb() {
    var t = document.createElement('textarea');
    t.value = txt; t.setAttribute('readonly','');
    t.style.cssText = 'position:fixed;top:0;left:0;width:2em;height:2em;opacity:0;';
    document.body.appendChild(t); t.focus(); t.select();
    try { document.execCommand('copy'); done(); } catch(e) {}
    document.body.removeChild(t);
  }
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(txt).then(done, fb);
  else fb();
}
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
# 이전비 내역서 새 창 HTML 템플릿
# ─────────────────────────────────────────────────────────────────────────────
FEE_WINDOW_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>이전비 내역서</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: '맑은 고딕', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  background: #f0f0f0; padding: 14px;
}

/* ── 버튼 ── */
.ctrl { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.fbtn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; font-family: inherit; }
.fbtn:hover { opacity: 0.8; }
.fbtn-img { background: #e63946; color: #fff; }
.fbtn-dl  { background: #28a745; color: #fff; }

/* ── PC 테이블 ── */
#fee-pc { background: #fff; border: 1px solid #aaa; padding: 8px; max-width: 760px; }
.ft { width: 100%; border-collapse: collapse; }
.ft td { border: 1px solid #555; padding: 5px 8px; vertical-align: middle; }
.ft-title { text-align: center; font-size: 22px; font-weight: bold; padding: 12px 8px; letter-spacing: 8px; }
.ft-lbl   { text-align: center; font-size: 12px; background: #f0f0e0; white-space: nowrap; width: 1%; }
.ft-amt   { text-align: center; width: 20%; }
.ft-note  { font-size: 11px; color: #222; line-height: 1.5; }
.ft-big   { text-align: center; font-size: 18px; font-weight: bold; }
.ft-total { text-align: center; font-size: 18px; font-weight: bold; display: flex; align-items: baseline; justify-content: center; gap: 3px; }
/* 원 단위 */
.amt-wrap { display: flex; align-items: baseline; gap: 3px; }
.amt-wrap > input { flex: 1; min-width: 0; width: auto; }
.won    { font-size: 10px; color: #444; white-space: nowrap; flex-shrink: 0; }
.won-lg { font-size: 13px; color: #444; white-space: nowrap; flex-shrink: 0; }
.ft-acct td { background: #e8f0e0; font-weight: bold; }
.ft-co td   { text-align: center; font-size: 16px; font-weight: bold; padding: 8px; }

.fee-input {
  width: 100%; min-width: 80px; border: 1px solid #bbb; border-radius: 3px;
  padding: 3px 6px; text-align: right; font-size: 13px;
  font-family: '맑은 고딕', 'Malgun Gothic', sans-serif; background: #fafff0;
}
.fee-input:focus { outline: 2px solid #e63946; border-color: #e63946; }
.fee-input-big  { font-size: 18px; font-weight: bold; text-align: center; }
.ev-area { display: flex; align-items: center; gap: 6px; font-size: 11px; }
.ev-area label { cursor: pointer; }
.ev-area input[type=checkbox] { width: 15px; height: 15px; cursor: pointer; }

/* ── 모바일 ── */
#fee-mobile { display: none; }
@media (max-width: 600px) {
  #fee-pc     { display: none; }
  #fee-mobile { display: block; }
  body { padding: 8px; }
}
.mob-doc   { background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.15); }
.mob-title { text-align: center; font-size: 18px; font-weight: bold; padding: 14px 12px; border-bottom: 2px solid #333; letter-spacing: 4px; }
.mob-car-row  { display: flex; border-bottom: 1px solid #ddd; }
.mob-car-cell { flex: 1; padding: 9px 10px; border-right: 1px solid #ddd; }
.mob-car-cell:last-child { border-right: none; }
.mob-car-lbl { font-size: 10px; color: #888; }
.mob-car-val { font-weight: bold; font-size: 14px; }
.mob-tbl { width: 100%; border-collapse: collapse; }
.mob-tbl tr { border-bottom: 1px solid #eee; }
.mob-tbl td { padding: 10px 10px; vertical-align: middle; }
.mob-lbl { font-size: 13px; color: #222; width: 35%; }
.mob-val { text-align: right; }
.mob-input {
  width: 100%; border: none; border-bottom: 1px solid #ccc;
  text-align: right; font-size: 15px; font-family: sans-serif;
  background: transparent; padding: 2px 0;
}
.mob-input:focus { outline: none; border-bottom-color: #e63946; }
.mob-ev-row td  { background: #f8f8ff; }
.mob-ev-area    { display: flex; align-items: center; gap: 6px; font-size: 12px; justify-content: flex-end; }
.mob-ev-area label { cursor: pointer; }
.mob-total-row  { background: #fff0f0; }
.mob-total-lbl  { font-size: 13px; font-weight: bold; color: #333; }
.mob-total-val  { font-size: 18px; font-weight: bold; color: #e63946; text-align: right; }
.mob-acct { background: #e8f0e0; padding: 13px 10px; font-size: 12px; font-weight: bold; text-align: center; border-top: 1px solid #ccc; }

/* ── 이미지 결과 ── */
#img-result { display: none; margin-top: 16px; }
#img-result img { max-width: 100%; border: 1px solid #ddd; border-radius: 4px; display: block; }
</style>
</head>
<body>

<div class="ctrl" id="ctrl-bar">
  <button class="fbtn fbtn-img" onclick="convertToImage()">🖼️ 이미지로 변환</button>
</div>

<!-- ══ PC 레이아웃 ══ -->
<div id="fee-pc">
<table class="ft">
  <tr><td colspan="3" class="ft-title">이전비  내역서</td></tr>
  <tr>
    <td class="ft-lbl" style="padding:6px 14px;">차&nbsp;&nbsp;&nbsp;&nbsp;명</td>
    <td style="text-align:center;font-weight:bold;font-size:15px;">__FEE_CAR_NAME__</td>
    <td>
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="border:none;text-align:center;font-size:12px;border-right:1px solid #555;padding:4px 10px;">년&nbsp;&nbsp;식</td>
          <td style="border:none;text-align:center;font-weight:bold;font-size:15px;padding:4px 10px;">__FEE_MODELYEAR__</td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td class="ft-lbl">과세표준액</td>
    <td colspan="2" class="ft-big">
      <input class="fee-input fee-input-big" id="tax_base" value="__FEE_TAX_BASE__"
             onchange="recalcFromBase()" oninput="recalcFromBase()">
    </td>
  </tr>
  <tr>
    <td class="ft-lbl">취&nbsp;&nbsp;득&nbsp;&nbsp;세</td>
    <td class="ft-amt">
      <input class="fee-input" id="acq_tax" value="__FEE_ACQ_TAX__" oninput="recalcTotal()">
    </td>
    <td class="ft-note">
      <div class="ev-area">
        <input type="checkbox" id="ev_check" onchange="applyEV()">
        <label for="ev_check">※ 전기차 취득세 140만원 감면</label>
      </div>
    </td>
  </tr>
  <tr>
    <td class="ft-lbl">공&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;채</td>
    <td class="ft-amt">
      <input class="fee-input" id="bond" value="__FEE_BOND__" oninput="recalcTotal()">
    </td>
    <td class="ft-note">※ 차액 반환해드립니다</td>
  </tr>
  <tr>
    <td class="ft-lbl">등록대행수수료</td>
    <td class="ft-amt" rowspan="4">
      <input class="fee-input" id="reg_fee" value="450,000" oninput="recalcTotal()">
    </td>
    <td class="ft-note">근거 1) 자동차관리법시행규칙 제122조 대행수수료.<br>2) 등록신청대행에 소요되는 실제비용</td>
  </tr>
  <tr>
    <td class="ft-lbl">계약서비</td>
    <td class="ft-note"></td>
  </tr>
  <tr>
    <td class="ft-lbl">매도비</td>
    <td class="ft-note" style="font-size:10.5px;">
      근거 1) 자동차관리법시행규칙 제 122조 관리비용<br>
      2) 매매용자동차의 보관·관리에 소요되는 실제비용.<br>
      다만, 그 금액은 당해지역의 공영주차장의 주차요금을 초과할 수 없다.
    </td>
  </tr>
  <tr>
    <td class="ft-lbl">인증지대</td>
    <td class="ft-note"></td>
  </tr>
  <tr>
    <td class="ft-lbl">탁송료</td>
    <td class="ft-amt">
      <input class="fee-input" id="delivery" value="100,000" oninput="recalcTotal()">
    </td>
    <td class="ft-note"></td>
  </tr>
  <tr>
    <td class="ft-lbl">매매알선수수료</td>
    <td class="ft-amt">
      <input class="fee-input" id="brokerage" value="300,000" oninput="recalcTotal()">
    </td>
    <td class="ft-note">근거 1) 자동차관리법시행규칙 제 122조 매매 알선수수료<br>2) 매매알선에 소요되는 실제비용</td>
  </tr>
  <tr>
    <td class="ft-lbl">성능상태<br>책임보험료</td>
    <td class="ft-amt">
      <input class="fee-input" id="insurance" value="__FEE_INSURANCE__" oninput="recalcTotal()">
    </td>
    <td class="ft-note">근거 1) 자동차관리법 제58조의 4에 의해 의무적으로 발생하는 비용</td>
  </tr>
  <tr>
    <td class="ft-lbl">합&nbsp;&nbsp;&nbsp;&nbsp;계</td>
    <td colspan="2" class="ft-total"><span id="pc_total">__FEE_TOTAL__</span><span class="won-lg">원</span></td>
  </tr>
  <tr class="ft-acct">
    <td class="ft-lbl">계좌번호</td>
    <td colspan="2" style="text-align:center;font-size:14px;">국민은행 : 658101 - 01 - 671081 (예금주 : 카스갤러리)</td>
  </tr>
  <tr>
    <td colspan="3" style="text-align:center;padding:8px;font-size:13px;">상기 이전비 내역을 고지함</td>
  </tr>
  <tr>
    <td class="ft-lbl">매수인</td>
    <td colspan="2" style="text-align:center;">(인)</td>
  </tr>
  <tr>
    <td colspan="3" style="font-size:10.5px;padding:5px 8px;line-height:1.6;">
      ▶ 지방세법 제12조(부동산외 취득의 세율) 제1항 제2호, 자동차 관리법시행 규칙 제 122조<br>
      &nbsp;&nbsp;(매매알선수수료등) 및 공채발행에 관한 지방자치법규 조례에 의합니다.
    </td>
  </tr>
  <tr>
    <td class="ft-lbl">전화번호</td>
    <td style="text-align:center;font-size:13px;">032 - 266 - 7900</td>
    <td style="font-size:13px;padding:5px 12px;">
      <span style="margin-right:16px;color:#444;">팩스번호</span>
      <span>070 - 7816 - 7900</span>
    </td>
  </tr>
  <tr class="ft-co">
    <td colspan="3">엠파크 허브&nbsp;&nbsp;&nbsp;&nbsp;(주)카스갤러리</td>
  </tr>
</table>
</div>

<!-- ══ 모바일 레이아웃 ══ -->
<div id="fee-mobile">
<div class="mob-doc">
  <div class="mob-title">이전비 내역서</div>
  <div class="mob-car-row">
    <div class="mob-car-cell">
      <div class="mob-car-lbl">차 명</div>
      <div class="mob-car-val">__FEE_CAR_NAME__</div>
    </div>
    <div class="mob-car-cell">
      <div class="mob-car-lbl">년 식</div>
      <div class="mob-car-val">__FEE_MODELYEAR__</div>
    </div>
  </div>
  <table class="mob-tbl">
    <tr>
      <td class="mob-lbl">과세표준액</td>
      <td class="mob-val">
        <input class="mob-input" id="m_tax_base" value="__FEE_TAX_BASE__"
               style="font-size:16px;font-weight:bold;"
               onchange="mobRecalcFromBase()" oninput="mobRecalcFromBase()">
      </td>
    </tr>
    <tr>
      <td class="mob-lbl">취득세</td>
      <td class="mob-val">
        <input class="mob-input" id="m_acq_tax" value="__FEE_ACQ_TAX__" oninput="mobRecalcTotal()">
      </td>
    </tr>
    <tr class="mob-ev-row">
      <td colspan="2" style="padding:5px 10px;">
        <div class="mob-ev-area">
          <input type="checkbox" id="m_ev_check" onchange="mobApplyEV()">
          <label for="m_ev_check">전기차 취득세 140만원 감면</label>
        </div>
      </td>
    </tr>
    <tr>
      <td class="mob-lbl">공채</td>
      <td class="mob-val">
        <input class="mob-input" id="m_bond" value="__FEE_BOND__" oninput="mobRecalcTotal()">
      </td>
    </tr>
    <tr>
      <td class="mob-lbl">등록대행수수료<br><span style="color:#888;font-size:11px;">+계약서비·매도비·인증지대</span></td>
      <td class="mob-val">
        <input class="mob-input" id="m_reg_fee" value="450,000" oninput="mobRecalcTotal()">
      </td>
    </tr>
    <tr>
      <td class="mob-lbl">탁송료</td>
      <td class="mob-val">
        <input class="mob-input" id="m_delivery" value="100,000" oninput="mobRecalcTotal()">
      </td>
    </tr>
    <tr>
      <td class="mob-lbl">매매알선수수료</td>
      <td class="mob-val">
        <input class="mob-input" id="m_brokerage" value="300,000" oninput="mobRecalcTotal()">
      </td>
    </tr>
    <tr>
      <td class="mob-lbl">성능상태책임보험료</td>
      <td class="mob-val">
        <input class="mob-input" id="m_insurance" value="__FEE_INSURANCE__" oninput="mobRecalcTotal()">
      </td>
    </tr>
    <tr class="mob-total-row">
      <td class="mob-total-lbl">합 계</td>
      <td class="mob-total-val"><span id="mob_total">__FEE_TOTAL__</span><span class="won-lg" style="font-size:12px;color:#e63946;"> 원</span></td>
    </tr>
  </table>
  <div class="mob-acct">계좌번호 : 국민은행 658101-01-671081<br>(예금주 : 카스갤러리)</div>
</div>
</div>

<!-- ══ 이미지 결과 ══ -->
<div id="img-result">
  <img id="out-img" src="" alt="">
  <br><br>
  <button class="fbtn fbtn-dl" onclick="downloadImg()">⬇️ 이미지 다운로드</button>
</div>

<script>
function parseNum(v) { return parseInt(String(v).replace(/,/g, '')) || 0; }
function fmt(n)      { return Math.round(n).toLocaleString('ko-KR'); }
function isMobile()  { return window.innerWidth <= 600; }

function recalcFromBase() {
  var base = parseNum(document.getElementById('tax_base').value);
  var isEV = document.getElementById('ev_check').checked;
  var acq  = Math.round(base * 0.07);
  if (isEV) acq = Math.max(0, acq - 1400000);
  document.getElementById('acq_tax').value = fmt(acq);
  document.getElementById('bond').value    = fmt(Math.round(base * 0.005));
  recalcTotal();
}
function applyEV() { recalcFromBase(); }
function recalcTotal() {
  var t = parseNum(document.getElementById('acq_tax').value)
        + parseNum(document.getElementById('bond').value)
        + parseNum(document.getElementById('reg_fee').value)
        + parseNum(document.getElementById('delivery').value)
        + parseNum(document.getElementById('brokerage').value)
        + parseNum(document.getElementById('insurance').value);
  document.getElementById('pc_total').textContent = fmt(t);
  syncPCtoMob();
}

function mobRecalcFromBase() {
  var base = parseNum(document.getElementById('m_tax_base').value);
  var isEV = document.getElementById('m_ev_check').checked;
  var acq  = Math.round(base * 0.07);
  if (isEV) acq = Math.max(0, acq - 1400000);
  document.getElementById('m_acq_tax').value = fmt(acq);
  document.getElementById('m_bond').value    = fmt(Math.round(base * 0.005));
  mobRecalcTotal();
}
function mobApplyEV() { mobRecalcFromBase(); }
function mobRecalcTotal() {
  var t = parseNum(document.getElementById('m_acq_tax').value)
        + parseNum(document.getElementById('m_bond').value)
        + parseNum(document.getElementById('m_reg_fee').value)
        + parseNum(document.getElementById('m_delivery').value)
        + parseNum(document.getElementById('m_brokerage').value)
        + parseNum(document.getElementById('m_insurance').value);
  document.getElementById('mob_total').textContent = fmt(t);
  syncMobToPC();
}

var PAIRS = [
  ['acq_tax','m_acq_tax'], ['bond','m_bond'], ['reg_fee','m_reg_fee'],
  ['delivery','m_delivery'], ['brokerage','m_brokerage'], ['insurance','m_insurance']
];
function syncPCtoMob() {
  PAIRS.forEach(function(p) {
    var s = document.getElementById(p[0]), d = document.getElementById(p[1]);
    if (s && d) d.value = s.value;
  });
  var t = document.getElementById('pc_total'), m = document.getElementById('mob_total');
  if (t && m) m.textContent = t.textContent;
}
function syncMobToPC() {
  PAIRS.forEach(function(p) {
    var s = document.getElementById(p[1]), d = document.getElementById(p[0]);
    if (s && d) d.value = s.value;
  });
  var t = document.getElementById('mob_total'), p2 = document.getElementById('pc_total');
  if (t && p2) p2.textContent = t.textContent;
}

function convertToImage() {
  var docEl = isMobile() ? document.getElementById('fee-mobile') : document.getElementById('fee-pc');
  var ctrl  = document.getElementById('ctrl-bar');
  ctrl.style.display = 'none';
  html2canvas(docEl, {
    scale: 2, useCORS: true, backgroundColor: '#ffffff',
    onclone: function(clonedDoc) {
      clonedDoc.querySelectorAll('input[type="checkbox"]').forEach(function(inp) {
        var s = clonedDoc.createElement('span');
        s.textContent = inp.checked ? '☑' : '☐';
        s.style.cssText = 'font-size:15px;margin-right:4px;vertical-align:middle;';
        inp.parentNode.replaceChild(s, inp);
      });
      clonedDoc.querySelectorAll('input').forEach(function(inp) {
        var s = clonedDoc.createElement('span');
        s.textContent = inp.value;
        var big = inp.className.indexOf('big') >= 0;
        var mob = inp.className.indexOf('mob') >= 0;
        var fs  = big ? '18px' : (mob ? '15px' : '13px');
        s.style.cssText = big
          ? 'font-size:18px;font-weight:bold;display:block;text-align:center;flex:1;min-width:0;'
          : 'font-size:' + fs + ';display:block;text-align:right;padding:3px 6px;flex:1;min-width:0;';
        inp.parentNode.replaceChild(s, inp);
      });
    }
  }).then(function(canvas) {
    ctrl.style.display = 'flex';
    var img = document.getElementById('out-img');
    img.src = canvas.toDataURL('image/png');
    document.getElementById('img-result').style.display = 'block';
    document.getElementById('img-result').scrollIntoView({ behavior: 'smooth' });
  });
}
function downloadImg() {
  var a = document.createElement('a');
  a.href = document.getElementById('out-img').src;
  a.download = '이전비내역서.png';
  a.click();
}

// 모든 금액 입력 뒤에 '원' 단위 추가
document.querySelectorAll('.fee-input, .mob-input').forEach(function(inp) {
  var wrap = document.createElement('div');
  wrap.className = 'amt-wrap';
  inp.parentNode.insertBefore(wrap, inp);
  wrap.appendChild(inp);
  var won = document.createElement('span');
  won.className = inp.classList.contains('fee-input-big') ? 'won-lg' : 'won';
  won.textContent = '원';
  wrap.appendChild(won);
});

// input 변경 시 attribute 동기화 (html2canvas 대응)
document.querySelectorAll('input').forEach(function(inp) {
  inp.addEventListener('input', function() {
    this.setAttribute('value', this.value);
    if (this.type === 'checkbox') {
      if (this.checked) this.setAttribute('checked', '');
      else this.removeAttribute('checked');
    }
  });
});
</script>
</body>
</html>"""


st.set_page_config(page_title="MB 매물 조회", page_icon="🚗", layout="centered")

st.markdown("""
<style>
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #1e1e2e !important;
        border-left: 4px solid #e63946 !important;
        border-top: 1px solid #313244 !important;
        border-right: 1px solid #313244 !important;
        border-bottom: 1px solid #313244 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4) !important;
        margin-bottom: 10px;
    }
    .result-count { color: #a6adc8; font-size: 13px; margin-bottom: 10px; }
    /* components.html iframe 컨테이너 여백 제거 */
    [data-testid="stHtml"], [data-testid="stCustomComponentV1"] {
        margin: 0 !important; padding: 0 !important; line-height: 0 !important;
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
    submodel  = row.get("cat_submodel", "")
    grade     = row.get("cat_grade", "")
    subgrade  = row.get("cat_subgrade", "")
    plate     = str(row.get("platenumber", ""))
    stock_id  = str(row.get("stock_id", "")).strip()
    modelyear = str(row.get("modelyear", ""))
    reg_year  = row.get("reg_year", "")
    reg_month = row.get("reg_month", "")
    reg_date  = row.get("reg_date", "")
    mileage_raw = row.get("mileage", "")
    try:
        mileage = f"{int(str(mileage_raw).replace(',','').replace(' ','')):,} km"
    except (ValueError, TypeError):
        mileage = str(mileage_raw)
    fuel        = str(row.get("fuel", ""))
    status      = str(row.get("status", ""))
    ownerprice  = format_number(row.get("ownerprice", ""))
    mbprice_fmt = format_number(row.get("mbprice", ""))
    owner_name  = str(row.get("owner_name", "")).strip()
    owner_phone = str(row.get("owner_phone", "")).strip()

    title    = " ".join(filter(None, [str(submodel), str(grade), str(subgrade)]))
    reg_info = "/".join(filter(None, [str(reg_year), str(reg_month), str(reg_date)]))
    car_name = title

    try:
        mbprice_num = int(str(row.get("mbprice", "0")).replace(",", "").replace(" ", ""))
    except (ValueError, TypeError):
        mbprice_num = 0
    acq_tax = round(mbprice_num * 0.07)
    bond    = round(mbprice_num * 0.005)
    try:
        insurance = int(str(row.get("insur", "")).replace(",", "").replace(" ", "")) or 100000
    except (ValueError, TypeError):
        insurance = 100000
    total = acq_tax + bond + 450000 + 100000 + 300000 + insurance

    def fmt(n):
        return f"{n:,}"

    phone_svg = ('<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
                 'stroke="#a6e3a1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
                 '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07'
                 'A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.4 2 2 0 0 1 3.6 1.22h3'
                 'a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.82'
                 'a16 16 0 0 0 6.29 6.29l.97-.97a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7'
                 'A2 2 0 0 1 22 16.92z"/></svg>')
    if owner_phone:
        call_btn_html = (f'<div class="row" style="margin-top:6px;">'
                         f'<a class="call-btn" href="tel:{owner_phone}">'
                         f'{phone_svg} {owner_name} / {owner_phone}</a></div>')
    else:
        call_btn_html = ""

    # 이전비 내역서 HTML 생성 후 JSON 인코딩 (새 창용)
    fee_html = (FEE_WINDOW_HTML
                .replace("__FEE_CAR_NAME__",  car_name)
                .replace("__FEE_MODELYEAR__", modelyear)
                .replace("__FEE_TAX_BASE__",  fmt(mbprice_num))
                .replace("__FEE_ACQ_TAX__",   fmt(acq_tax))
                .replace("__FEE_BOND__",       fmt(bond))
                .replace("__FEE_INSURANCE__",  fmt(insurance))
                .replace("__FEE_TOTAL__",      fmt(total)))
    # json.dumps 후 </script> 가 HTML 파서에 의해 script 블록을 조기 종료시키는 것을 방지
    fee_json = json.dumps(fee_html).replace("</", "<\\/")

    html = (CARD_HTML
            .replace("__CARD_TITLE__",   title)
            .replace("__STOCK_ID__",     stock_id)
            .replace("__PLATE__",        plate)
            .replace("__MODELYEAR__",    modelyear)
            .replace("__REG_INFO__",     reg_info)
            .replace("__MILEAGE__",      mileage)
            .replace("__FUEL__",         fuel)
            .replace("__STATUS__",       status)
            .replace("__OWNER_PRICE__",  str(ownerprice))
            .replace("__MB_PRICE__",     str(mbprice_fmt))
            .replace("__CALL_BTN__",     call_btn_html)
            .replace("__FEE_DATA_JSON__", fee_json))

    card_height = 210 if owner_phone else 185
    components.html(html, height=card_height)


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
