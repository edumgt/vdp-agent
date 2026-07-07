import pytest


@pytest.fixture
def accounts():
    return [
        {"account_code": "101", "name": "현금", "account_type": "asset", "normal_balance": "debit"},
        {"account_code": "102", "name": "보통예금", "account_type": "asset", "normal_balance": "debit"},
        {"account_code": "201", "name": "외상매입금", "account_type": "liability", "normal_balance": "credit"},
        {"account_code": "331", "name": "자본금", "account_type": "equity", "normal_balance": "credit"},
        {"account_code": "401", "name": "상품매출", "account_type": "revenue", "normal_balance": "credit"},
        {"account_code": "801", "name": "급여", "account_type": "expense", "normal_balance": "debit"},
    ]


@pytest.fixture
def journal_lines():
    return [
        # 자본금 출자
        {"entry_id": "E1", "entry_date": "2026-01-05", "description": "자본금 출자", "account_code": "102", "debit": 10_000_000, "credit": 0},
        {"entry_id": "E1", "entry_date": "2026-01-05", "description": "자본금 출자", "account_code": "331", "debit": 0, "credit": 10_000_000},
        # 매출 발생 (보통예금 입금)
        {"entry_id": "E2", "entry_date": "2026-01-15", "description": "상품 매출", "account_code": "102", "debit": 3_000_000, "credit": 0},
        {"entry_id": "E2", "entry_date": "2026-01-15", "description": "상품 매출", "account_code": "401", "debit": 0, "credit": 3_000_000},
        # 급여 지급 (현금)
        {"entry_id": "E3", "entry_date": "2026-01-25", "description": "1월 급여 지급", "account_code": "801", "debit": 1_500_000, "credit": 0},
        {"entry_id": "E3", "entry_date": "2026-01-25", "description": "1월 급여 지급", "account_code": "102", "debit": 0, "credit": 1_500_000},
        # 외상매입 발생
        {"entry_id": "E4", "entry_date": "2026-02-02", "description": "사무용품 외상매입", "account_code": "801", "debit": 200_000, "credit": 0},
        {"entry_id": "E4", "entry_date": "2026-02-02", "description": "사무용품 외상매입", "account_code": "201", "debit": 0, "credit": 200_000},
    ]
