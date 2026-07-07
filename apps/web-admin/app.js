function apiBase() {
  return document.getElementById('apiBase').value.replace(/\/$/, '');
}
function companyId() {
  return document.getElementById('companyId').value.trim();
}
function showMsg(id, text, isError) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = 'msg' + (isError ? ' error' : '');
}
function showOut(id, obj) {
  document.getElementById(id).textContent = JSON.stringify(obj, null, 2);
}

async function api(path, opts) {
  const res = await fetch(apiBase() + path, opts);
  let body;
  try { body = await res.json(); } catch (e) { body = { error: 'invalid json response' }; }
  if (!res.ok) throw Object.assign(new Error(body.error || 'request failed'), { body });
  return body;
}

// 1) 회사
async function createCompany() {
  try {
    const name = document.getElementById('corpName').value;
    const biz_reg_no = document.getElementById('corpBizNo').value;
    const r = await api('/api/companies', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, biz_reg_no }) });
    showMsg('companiesMsg', `생성됨: ${r.company_id}`);
    document.getElementById('companyId').value = r.company_id;
  } catch (e) { showMsg('companiesMsg', e.message, true); }
}
async function listCompanies() {
  try {
    const r = await api('/api/companies');
    showOut('companiesOut', r);
  } catch (e) { showMsg('companiesMsg', e.message, true); }
}

// 2) 계정과목
async function listAccounts() {
  try {
    const r = await api('/api/accounts');
    showOut('accountsOut', r);
  } catch (e) { showOut('accountsOut', { error: e.message }); }
}

// 3) 분개
async function suggestAccount() {
  try {
    const description = document.getElementById('jeDesc').value;
    const r = await api('/api/ml/classify-preview', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ description }) });
    document.getElementById('jeDebitAccount').value = r.account_code;
    showMsg('journalMsg', `추천 계정: ${r.account_code} (신뢰도 ${(r.confidence * 100).toFixed(1)}%)`);
  } catch (e) { showMsg('journalMsg', e.message, true); }
}
async function createJournalEntry() {
  try {
    const lines = [
      { account_code: document.getElementById('jeDebitAccount').value, debit: Number(document.getElementById('jeDebitAmount').value || 0), credit: 0 },
      { account_code: document.getElementById('jeCreditAccount').value, debit: 0, credit: Number(document.getElementById('jeCreditAmount').value || 0) },
    ];
    const body = { company_id: companyId(), entry_date: document.getElementById('jeDate').value, description: document.getElementById('jeDesc').value, lines };
    const r = await api('/api/journal-entries', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    showMsg('journalMsg', `등록됨: ${r.entry_id} (계정과목 자동분류가 비동기로 실행됩니다)`);
  } catch (e) { showMsg('journalMsg', e.message, true); }
}
async function listJournalEntries() {
  try {
    const r = await api(`/api/journal-entries?company_id=${encodeURIComponent(companyId())}`);
    showOut('journalOut', r);
  } catch (e) { showMsg('journalMsg', e.message, true); }
}
async function getJournalEntry() {
  try {
    const id = document.getElementById('jeLookupId').value;
    const r = await api(`/api/journal-entries/${encodeURIComponent(id)}`);
    showOut('journalOut', r);
  } catch (e) { showMsg('journalMsg', e.message, true); }
}

// 4) 증빙
async function uploadVoucher() {
  try {
    const fileInput = document.getElementById('voucherFile');
    if (!fileInput.files[0]) throw new Error('파일을 선택하세요');
    const fd = new FormData();
    fd.append('company_id', companyId());
    fd.append('voucher_type', document.getElementById('voucherType').value);
    fd.append('file', fileInput.files[0]);
    const r = await api('/api/vouchers', { method: 'POST', body: fd });
    showMsg('voucherMsg', `업로드됨: ${r.voucher_id} (OCR 비동기 처리 중)`);
    document.getElementById('voucherLookupId').value = r.voucher_id;
  } catch (e) { showMsg('voucherMsg', e.message, true); }
}
async function getVoucher() {
  try {
    const id = document.getElementById('voucherLookupId').value;
    const r = await api(`/api/vouchers/${encodeURIComponent(id)}`);
    showOut('voucherOut', r);
  } catch (e) { showMsg('voucherMsg', e.message, true); }
}

// 5/6) ML
async function loadAnomalies() {
  try {
    const r = await api(`/api/ml/anomalies?company_id=${encodeURIComponent(companyId())}`);
    showOut('anomaliesOut', r);
  } catch (e) { showOut('anomaliesOut', { error: e.message }); }
}
async function loadForecast() {
  try {
    const metric = document.getElementById('forecastMetric').value;
    const r = await api(`/api/ml/forecast?company_id=${encodeURIComponent(companyId())}&metric=${metric}&periods_ahead=3`);
    showOut('forecastOut', r);
  } catch (e) { showOut('forecastOut', { error: e.message }); }
}

// 7) 보고서
async function generateReport() {
  try {
    const body = {
      company_id: companyId(),
      report_type: document.getElementById('reportType').value,
      period_start: document.getElementById('reportStart').value,
      period_end: document.getElementById('reportEnd').value,
      as_of_date: document.getElementById('reportEnd').value,
    };
    const r = await api('/api/reports/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    showMsg('reportMsg', `생성 요청됨: ${r.report_id} (잠시 후 상태 조회)`);
    document.getElementById('reportLookupId').value = r.report_id;
  } catch (e) { showMsg('reportMsg', e.message, true); }
}
async function getReport() {
  try {
    const id = document.getElementById('reportLookupId').value;
    const r = await api(`/api/reports/${encodeURIComponent(id)}`);
    showOut('reportOut', r);
  } catch (e) { showMsg('reportMsg', e.message, true); }
}
function downloadReport() {
  const id = document.getElementById('reportLookupId').value;
  window.open(`${apiBase()}/api/reports/${encodeURIComponent(id)}/pdf`, '_blank');
}

// 8) 대시보드
async function loadDashboard() {
  try {
    const r = await api(`/api/companies/${encodeURIComponent(companyId())}/dashboard`);
    showOut('dashboardOut', r);
  } catch (e) { showOut('dashboardOut', { error: e.message }); }
}

// 9) DART
async function searchDart() {
  try {
    const name = document.getElementById('dartName').value;
    const r = await api(`/api/dart/search?name=${encodeURIComponent(name)}`);
    showOut('dartOut', r);
    if (r.matches && r.matches[0]) {
      document.getElementById('dartCorpCode').value = r.matches[0].corp_code;
      document.getElementById('dartCorpName').value = r.matches[0].corp_name;
    }
    showMsg('dartMsg', `${r.source === 'live' ? '실시간 OpenDART' : '오프라인 fixture'} 데이터 - ${r.matches.length}건 검색됨`);
  } catch (e) { showMsg('dartMsg', e.message, true); }
}
async function regenerateDart() {
  try {
    const corpCode = document.getElementById('dartCorpCode').value;
    const body = { company_id: companyId(), corp_name: document.getElementById('dartCorpName').value, bsns_year: document.getElementById('dartYear').value };
    const r = await api(`/api/dart/companies/${encodeURIComponent(corpCode)}/regenerate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    showMsg('dartMsg', `재현 요청됨: ${r.report_id} (완료 후 상단 7번 섹션에서 PDF 다운로드 가능)`);
    document.getElementById('reportLookupId').value = r.report_id;
  } catch (e) { showMsg('dartMsg', e.message, true); }
}
