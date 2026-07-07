-- 법인 기장(회계) PDF 생성 모듈 — 스키마 v2.0
-- 기존 VDP(다국어 동화책) 스키마를 전면 대체합니다.

CREATE TABLE IF NOT EXISTS companies (
  company_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  biz_reg_no TEXT NOT NULL,
  fiscal_year_end_month INT NOT NULL DEFAULT 12,
  dart_corp_code TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
  account_code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  account_type TEXT NOT NULL CHECK (account_type IN ('asset','liability','equity','revenue','expense')),
  normal_balance TEXT NOT NULL CHECK (normal_balance IN ('debit','credit')),
  -- 제조원가명세서 집계용(해당 없으면 NULL): 재료비/노무비/제조경비
  cost_category TEXT CHECK (cost_category IN ('material','labor','overhead')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS journal_entries (
  entry_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  entry_date DATE NOT NULL,
  description TEXT NOT NULL,
  source_type TEXT NOT NULL DEFAULT 'manual' CHECK (source_type IN ('manual','ocr','import')),
  status TEXT NOT NULL DEFAULT 'posted' CHECK (status IN ('draft','posted')),
  voucher_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS journal_lines (
  id SERIAL PRIMARY KEY,
  entry_id TEXT NOT NULL REFERENCES journal_entries(entry_id) ON DELETE CASCADE,
  account_code TEXT NOT NULL REFERENCES accounts(account_code),
  debit NUMERIC(18,2) NOT NULL DEFAULT 0,
  credit NUMERIC(18,2) NOT NULL DEFAULT 0,
  memo TEXT
);

CREATE TABLE IF NOT EXISTS vouchers (
  voucher_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  voucher_type TEXT NOT NULL CHECK (voucher_type IN ('receipt','tax_invoice')),
  file_path TEXT NOT NULL,
  ocr_raw_text TEXT,
  ocr_confidence NUMERIC(5,4),
  extracted_json JSONB,
  status TEXT NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded','ocr_done','ocr_failed','linked')),
  linked_entry_id TEXT REFERENCES journal_entries(entry_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tax_invoices (
  invoice_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  direction TEXT NOT NULL CHECK (direction IN ('sales','purchase')),
  market TEXT NOT NULL DEFAULT 'domestic' CHECK (market IN ('domestic','export')),
  counterparty_name TEXT NOT NULL,
  counterparty_biz_no TEXT,
  supply_amount NUMERIC(18,2) NOT NULL,
  tax_amount NUMERIC(18,2) NOT NULL,
  issue_date DATE NOT NULL,
  item_desc TEXT,
  voucher_id TEXT REFERENCES vouchers(voucher_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fixed_assets (
  asset_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  account_code TEXT NOT NULL REFERENCES accounts(account_code),
  acquisition_date DATE NOT NULL,
  acquisition_cost NUMERIC(18,2) NOT NULL,
  useful_life_years INT NOT NULL,
  salvage_value NUMERIC(18,2) NOT NULL DEFAULT 0,
  depreciation_method TEXT NOT NULL DEFAULT 'straight_line' CHECK (depreciation_method IN ('straight_line')),
  disposed_at DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml_classifications (
  id SERIAL PRIMARY KEY,
  entry_id TEXT NOT NULL REFERENCES journal_entries(entry_id) ON DELETE CASCADE,
  predicted_account_code TEXT REFERENCES accounts(account_code),
  confidence NUMERIC(5,4) NOT NULL,
  model_version TEXT NOT NULL,
  is_override BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml_anomalies (
  id SERIAL PRIMARY KEY,
  entry_id TEXT NOT NULL REFERENCES journal_entries(entry_id) ON DELETE CASCADE,
  score NUMERIC(8,5) NOT NULL,
  reason TEXT,
  model_version TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml_forecasts (
  id SERIAL PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  metric TEXT NOT NULL CHECK (metric IN ('cash_flow','revenue')),
  period TEXT NOT NULL,
  predicted_value NUMERIC(18,2) NOT NULL,
  model_version TEXT NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pdf_reports (
  report_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  report_type TEXT NOT NULL CHECK (report_type IN ('financial_statement','ledger','tax_summary','closing_report','dart_replica','company_dashboard')),
  period_start DATE,
  period_end DATE,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','done','failed')),
  file_path TEXT,
  file_hash TEXT,
  source_snapshot JSONB,
  error_log TEXT,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dart_filings_cache (
  id SERIAL PRIMARY KEY,
  corp_code TEXT NOT NULL,
  corp_name TEXT NOT NULL,
  bsns_year TEXT NOT NULL,
  raw_response JSONB NOT NULL,
  source TEXT NOT NULL DEFAULT 'live' CHECK (source IN ('live','fixture')),
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(corp_code, bsns_year)
);

CREATE INDEX IF NOT EXISTS idx_journal_entries_company_date ON journal_entries(company_id, entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_lines_entry ON journal_lines(entry_id);
CREATE INDEX IF NOT EXISTS idx_journal_lines_account ON journal_lines(account_code);
CREATE INDEX IF NOT EXISTS idx_tax_invoices_company_date ON tax_invoices(company_id, issue_date);
CREATE INDEX IF NOT EXISTS idx_pdf_reports_company ON pdf_reports(company_id);
CREATE INDEX IF NOT EXISTS idx_fixed_assets_company ON fixed_assets(company_id);
