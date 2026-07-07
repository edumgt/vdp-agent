#!/usr/bin/env python3
"""
동적(시계열/이중분개) 샘플 데이터 시드.
정적 기준정보(법인/계정과목/유형자산)는 infra/db/seed/seed.sql 로 이미 적재되어 있다고 가정합니다.
차대변 합계가 항상 일치하도록 파이썬에서 생성해 회계 정합성을 보장합니다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db_util import get_conn  # noqa: E402

STATIC_SEED_SQL = Path(__file__).resolve().parent.parent / "infra" / "db" / "seed" / "seed.sql"
COMPANY_ID = "CORP-0001"

MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]

# (day, description, account_code(차변 or 대변 대상), amount, kind)
# kind: revenue/salary/expense/manufacturing/anomaly


def _entry_id(seq: int) -> str:
    return f"JE-SEED-{seq:04d}"


def build_entries():
    entries = []
    seq = 1

    revenue_base = 3_000_000
    for i, month in enumerate(MONTHS):
        revenue_account = "401" if i % 2 == 0 else "411"
        revenue_amount = revenue_base + i * 400_000  # 우상향 추세(예측 테스트용)
        entries.append({
            "entry_id": _entry_id(seq), "date": f"{month}-15",
            "description": "상품 매출 대금 입금 - ABC상사" if revenue_account == "401" else "용역 계약 대금 입금 - 컨설팅",
            "lines": [{"account_code": "102", "debit": revenue_amount, "credit": 0},
                      {"account_code": revenue_account, "debit": 0, "credit": revenue_amount}],
        })
        seq += 1

        entries.append({
            "entry_id": _entry_id(seq), "date": f"{month}-25",
            "description": f"{i + 1}월 직원 급여 이체",
            "lines": [{"account_code": "801", "debit": 1_500_000, "credit": 0},
                      {"account_code": "102", "debit": 0, "credit": 1_500_000}],
        })
        seq += 1

        entries.append({
            "entry_id": _entry_id(seq), "date": f"{month}-10",
            "description": "KT 통신비 자동이체",
            "lines": [{"account_code": "814", "debit": 180_000, "credit": 0},
                      {"account_code": "102", "debit": 0, "credit": 180_000}],
        })
        seq += 1

        entries.append({
            "entry_id": _entry_id(seq), "date": f"{month}-12",
            "description": "네이버 검색광고 집행비",
            "lines": [{"account_code": "831", "debit": 300_000, "credit": 0},
                      {"account_code": "102", "debit": 0, "credit": 300_000}],
        })
        seq += 1

        entries.append({
            "entry_id": _entry_id(seq), "date": f"{month}-18",
            "description": "거래처 접대 - 한정식당",
            "lines": [{"account_code": "813", "debit": 60_000, "credit": 0},
                      {"account_code": "102", "debit": 0, "credit": 60_000}],
        })
        seq += 1

        # 제조원가 관련(원재료비/노무비/제조경비) - 대시보드 데모용
        entries.append({
            "entry_id": _entry_id(seq), "date": f"{month}-05",
            "description": "원재료 매입 대금 지급",
            "lines": [{"account_code": "501", "debit": 800_000, "credit": 0},
                      {"account_code": "201", "debit": 0, "credit": 800_000}],
        })
        seq += 1
        entries.append({
            "entry_id": _entry_id(seq), "date": f"{month}-28",
            "description": "생산직 노무비 지급",
            "lines": [{"account_code": "504", "debit": 500_000, "credit": 0},
                      {"account_code": "102", "debit": 0, "credit": 500_000}],
        })
        seq += 1
        entries.append({
            "entry_id": _entry_id(seq), "date": f"{month}-28",
            "description": "공장 전기요금 납부",
            "lines": [{"account_code": "507", "debit": 120_000, "credit": 0},
                      {"account_code": "102", "debit": 0, "credit": 120_000}],
        })
        seq += 1

    # 이상거래 탐지 데모용: 3월에 평소(60,000)의 30배 이상인 접대비 발생
    entries.append({
        "entry_id": _entry_id(seq), "date": "2026-03-20",
        "description": "거래처 접대 - 특급호텔 컨퍼런스",
        "lines": [{"account_code": "813", "debit": 1_800_000, "credit": 0},
                  {"account_code": "102", "debit": 0, "credit": 1_800_000}],
    })
    seq += 1

    return entries


def build_tax_invoices():
    invoices = []
    seq = 1
    for i, month in enumerate(MONTHS):
        invoices.append({
            "invoice_id": f"TI-SEED-{seq:04d}", "direction": "sales",
            "market": "export" if i % 3 == 0 else "domestic",
            "counterparty_name": f"해외바이어{i+1}" if i % 3 == 0 else f"국내거래처{i+1}",
            "supply_amount": 2_000_000 + i * 100_000, "tax_amount": (2_000_000 + i * 100_000) * 0.1,
            "issue_date": f"{month}-16", "item_desc": "상품 판매",
        })
        seq += 1
        invoices.append({
            "invoice_id": f"TI-SEED-{seq:04d}", "direction": "purchase", "market": "domestic",
            "counterparty_name": f"원재료공급처{i+1}",
            "supply_amount": 800_000, "tax_amount": 80_000,
            "issue_date": f"{month}-06", "item_desc": "원재료 매입",
        })
        seq += 1
    return invoices


def main():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(STATIC_SEED_SQL.read_text(encoding="utf-8"))
        conn.commit()
        print("[db_seed] 정적 기준정보(법인/계정과목/유형자산) 시드 완료")

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM journal_entries WHERE company_id=%s", (COMPANY_ID,))
            if cur.fetchone()[0] > 0:
                print("[db_seed] 이미 거래 데이터가 시드되어 있어 건너뜁니다. (재시드하려면 journal_entries/tax_invoices를 먼저 비우세요)")
                return

            for entry in build_entries():
                cur.execute(
                    "INSERT INTO journal_entries(entry_id, company_id, entry_date, description, source_type, status) "
                    "VALUES (%s,%s,%s,%s,'manual','posted')",
                    (entry["entry_id"], COMPANY_ID, entry["date"], entry["description"]),
                )
                for line in entry["lines"]:
                    cur.execute(
                        "INSERT INTO journal_lines(entry_id, account_code, debit, credit) VALUES (%s,%s,%s,%s)",
                        (entry["entry_id"], line["account_code"], line["debit"], line["credit"]),
                    )

            for inv in build_tax_invoices():
                cur.execute(
                    "INSERT INTO tax_invoices(invoice_id, company_id, direction, market, counterparty_name, supply_amount, tax_amount, issue_date, item_desc) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (inv["invoice_id"], COMPANY_ID, inv["direction"], inv["market"], inv["counterparty_name"],
                     inv["supply_amount"], inv["tax_amount"], inv["issue_date"], inv["item_desc"]),
                )

            # OCR 데모용 증빙(실제 이미지 파일 없이도 FixtureOcrProvider가 파일명으로 매칭)
            upload_dir = Path(__file__).resolve().parent.parent / "storage" / "uploads"
            cur.execute(
                "INSERT INTO vouchers(voucher_id, company_id, voucher_type, file_path, status) VALUES (%s,%s,%s,%s,'uploaded')",
                ("VCH-SEED-0001", COMPANY_ID, "receipt", str(upload_dir / "receipt_001.png")),
            )
            cur.execute(
                "INSERT INTO vouchers(voucher_id, company_id, voucher_type, file_path, status) VALUES (%s,%s,%s,%s,'uploaded')",
                ("VCH-SEED-0002", COMPANY_ID, "tax_invoice", str(upload_dir / "tax_invoice_001.png")),
            )

        conn.commit()
        print("[db_seed] 거래 데이터 시드 완료: journal_entries/journal_lines/tax_invoices/vouchers")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
