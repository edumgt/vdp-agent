from accounting_engine.manufacturing_cost import build_manufacturing_cost_statement, compute_manufacturing_cost_summary


def _accounts():
    return [
        {"account_code": "501", "name": "원재료비", "account_type": "expense", "normal_balance": "debit", "cost_category": "material"},
        {"account_code": "504", "name": "노무비", "account_type": "expense", "normal_balance": "debit", "cost_category": "labor"},
        {"account_code": "507", "name": "제조경비", "account_type": "expense", "normal_balance": "debit", "cost_category": "overhead"},
        {"account_code": "801", "name": "급여", "account_type": "expense", "normal_balance": "debit", "cost_category": None},
    ]


def _journal_lines():
    return [
        {"entry_id": "M1", "entry_date": "2026-01-05", "description": "원재료 매입", "account_code": "501", "debit": 5_000_000, "credit": 0},
        {"entry_id": "M2", "entry_date": "2026-01-10", "description": "생산직 노무비", "account_code": "504", "debit": 3_000_000, "credit": 0},
        {"entry_id": "M3", "entry_date": "2026-01-15", "description": "공장 전기료", "account_code": "507", "debit": 500_000, "credit": 0},
        {"entry_id": "M4", "entry_date": "2026-01-20", "description": "본사 관리직 급여", "account_code": "801", "debit": 2_000_000, "credit": 0},
    ]


def test_manufacturing_cost_summary_excludes_non_manufacturing_accounts():
    summary = compute_manufacturing_cost_summary(_accounts(), _journal_lines(), beginning_wip=1_000_000, ending_wip=800_000)
    assert summary["cost_by_category"]["material"] == 5_000_000
    assert summary["cost_by_category"]["labor"] == 3_000_000
    assert summary["cost_by_category"]["overhead"] == 500_000
    assert summary["total_manufacturing_cost"] == 8_500_000
    # 기초재공품 + 당기총제조비용 - 기말재공품
    assert summary["cost_of_goods_manufactured"] == 1_000_000 + 8_500_000 - 800_000


def test_build_manufacturing_cost_statement_render_tree():
    result = build_manufacturing_cost_statement(_accounts(), _journal_lines())
    assert result["render_tree"]["pages"][0]["nodes"][1]["type"] == "table"
