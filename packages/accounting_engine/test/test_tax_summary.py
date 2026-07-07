from accounting_engine.tax_summary import build_tax_summary, compute_tax_summary


def _invoices():
    return [
        {"invoice_id": "T1", "direction": "sales", "counterparty_name": "A상사", "supply_amount": 1_000_000, "tax_amount": 100_000, "issue_date": "2026-01-10"},
        {"invoice_id": "T2", "direction": "sales", "counterparty_name": "B상사", "supply_amount": 500_000, "tax_amount": 50_000, "issue_date": "2026-01-20"},
        {"invoice_id": "T3", "direction": "purchase", "counterparty_name": "C상사", "supply_amount": 300_000, "tax_amount": 30_000, "issue_date": "2026-01-15"},
    ]


def test_compute_tax_summary_totals():
    summary = compute_tax_summary(_invoices())
    assert summary["sales_supply"] == 1_500_000
    assert summary["sales_tax"] == 150_000
    assert summary["purchase_supply"] == 300_000
    assert summary["purchase_tax"] == 30_000
    assert summary["vat_payable"] == 120_000


def test_build_tax_summary_render_tree():
    result = build_tax_summary(_invoices(), "2026-01-01", "2026-01-31")
    assert result["render_tree"]["pages"][0]["nodes"][1]["type"] == "table"
