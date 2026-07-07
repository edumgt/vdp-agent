-- 정적 기준정보(법인/계정과목)만 SQL로 시드합니다.
-- 분개/증빙/세금계산서 등 시계열·이중분개 검증이 필요한 거래 데이터는
-- scripts/db_seed.py 가 파이썬으로 생성합니다(차대변 합계 일치 보장 목적).

INSERT INTO companies(company_id, name, biz_reg_no, fiscal_year_end_month, dart_corp_code)
VALUES ('CORP-0001', '주식회사 조이아컴퍼니', '123-45-67890', 12, NULL)
ON CONFLICT (company_id) DO NOTHING;

INSERT INTO accounts(account_code, name, account_type, normal_balance, cost_category) VALUES
  ('101', '현금', 'asset', 'debit', NULL),
  ('102', '보통예금', 'asset', 'debit', NULL),
  ('108', '외상매출금', 'asset', 'debit', NULL),
  ('131', '선급금', 'asset', 'debit', NULL),
  ('150', '상품', 'asset', 'debit', NULL),
  ('172', '비품', 'asset', 'debit', NULL),
  ('208', '차량운반구', 'asset', 'debit', NULL),
  ('201', '외상매입금', 'liability', 'credit', NULL),
  ('254', '예수금', 'liability', 'credit', NULL),
  ('261', '미지급금', 'liability', 'credit', NULL),
  ('293', '장기차입금', 'liability', 'credit', NULL),
  ('331', '자본금', 'equity', 'credit', NULL),
  ('375', '이익잉여금', 'equity', 'credit', NULL),
  ('401', '상품매출', 'revenue', 'credit', NULL),
  ('411', '용역매출', 'revenue', 'credit', NULL),
  ('501', '원재료비', 'expense', 'debit', 'material'),
  ('504', '노무비', 'expense', 'debit', 'labor'),
  ('507', '제조경비', 'expense', 'debit', 'overhead'),
  ('801', '급여', 'expense', 'debit', NULL),
  ('811', '복리후생비', 'expense', 'debit', NULL),
  ('813', '접대비', 'expense', 'debit', NULL),
  ('814', '통신비', 'expense', 'debit', NULL),
  ('815', '수도광열비', 'expense', 'debit', NULL),
  ('817', '세금과공과', 'expense', 'debit', NULL),
  ('818', '감가상각비', 'expense', 'debit', NULL),
  ('819', '임차료', 'expense', 'debit', NULL),
  ('822', '차량유지비', 'expense', 'debit', NULL),
  ('824', '운반비', 'expense', 'debit', NULL),
  ('826', '도서인쇄비', 'expense', 'debit', NULL),
  ('830', '소모품비', 'expense', 'debit', NULL),
  ('831', '광고선전비', 'expense', 'debit', NULL),
  ('833', '지급수수료', 'expense', 'debit', NULL),
  ('848', '잡비', 'expense', 'debit', NULL)
ON CONFLICT (account_code) DO NOTHING;

-- 유형자산 대장 샘플
INSERT INTO fixed_assets(asset_id, company_id, name, account_code, acquisition_date, acquisition_cost, useful_life_years, salvage_value, depreciation_method) VALUES
  ('FA-0001', 'CORP-0001', '사무용 노트북 15대', '172', '2025-03-01', 15_000_000, 4, 0, 'straight_line'),
  ('FA-0002', 'CORP-0001', '사무실 책상/의자 세트', '172', '2025-01-10', 6_000_000, 5, 0, 'straight_line'),
  ('FA-0003', 'CORP-0001', '법인 승합차', '208', '2024-06-15', 32_000_000, 5, 2_000_000, 'straight_line')
ON CONFLICT (asset_id) DO NOTHING;
