from accounting_engine.company_dashboard import build_company_dashboard


def test_company_dashboard_combines_all_sections():
    accounts = [
        {"account_code": "501", "name": "원재료비", "account_type": "expense", "normal_balance": "debit", "cost_category": "material"},
        {"account_code": "172", "name": "비품", "account_type": "asset", "normal_balance": "debit", "cost_category": None},
    ]
    journal_lines = [
        {"entry_id": "M1", "entry_date": "2026-01-05", "description": "원재료 매입", "account_code": "501", "debit": 1_000_000, "credit": 0},
    ]
    tax_invoices = [
        {"direction": "sales", "market": "export", "supply_amount": 400_000},
        {"direction": "sales", "market": "domestic", "supply_amount": 600_000},
    ]
    fixed_assets = [
        {"asset_id": "FA1", "name": "노트북", "account_code": "172", "acquisition_date": "2024-01-01", "acquisition_cost": 2_000_000, "useful_life_years": 4, "salvage_value": 0},
    ]

    result = build_company_dashboard(
        company_name="테스트법인",
        as_of_date="2026-06-30",
        bs_summary={"asset_total": 10_000_000, "liability_total": 2_000_000, "equity_total": 8_000_000},
        is_summary={"revenue_total": 5_000_000, "expense_total": 3_000_000, "net_income": 2_000_000},
        tax_invoices=tax_invoices,
        accounts=accounts,
        journal_lines=journal_lines,
        fixed_assets=fixed_assets,
    )

    assert result["summary"]["export_ratio_pct"] == 40.0
    assert result["summary"]["manufacturing"]["cost_by_category"]["material"] == 1_000_000
    assert result["summary"]["fixed_assets"]["total_cost"] == 2_000_000
    # page1: 대시보드 요약, page2: 제조원가명세서, page3: 유형자산목록
    assert len(result["render_tree"]["pages"]) == 3
