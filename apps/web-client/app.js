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

async function uploadVoucher() {
  try {
    const fileInput = document.getElementById('voucherFile');
    if (!fileInput.files[0]) throw new Error('파일을 선택하세요');
    const fd = new FormData();
    fd.append('company_id', companyId());
    fd.append('voucher_type', document.getElementById('voucherType').value);
    fd.append('file', fileInput.files[0]);
    const r = await api('/api/vouchers', { method: 'POST', body: fd });
    showMsg('voucherMsg', `업로드 완료: ${r.voucher_id} (OCR 처리 중입니다. 잠시 후 조회해 주세요)`);
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
    showMsg('reportMsg', `요청됨: ${r.report_id}`);
    document.getElementById('reportLookupId').value = r.report_id;
  } catch (e) { showMsg('reportMsg', e.message, true); }
}
async function checkStatus() {
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
