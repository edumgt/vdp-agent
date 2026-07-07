from ml_pipeline.classifier import AccountClassifier, load_labeled_data


def test_load_labeled_data_has_examples():
    data = load_labeled_data()
    assert len(data) >= 50
    assert all("text" in e and "account_code" in e for e in data)


def test_classifier_predicts_seen_category_correctly():
    clf = AccountClassifier.train(load_labeled_data())
    result = clf.predict("KT 통신비 자동이체")
    assert result["account_code"] == "814"
    assert 0 <= result["confidence"] <= 1
    assert result["model_version"]


def test_classifier_predicts_payroll():
    clf = AccountClassifier.train(load_labeled_data())
    result = clf.predict("직원 급여 이체 - 전직원")
    assert result["account_code"] == "801"


def test_classifier_distribution_sums_close_to_one():
    clf = AccountClassifier.train(load_labeled_data())
    result = clf.predict("네이버클라우드 서버 이용료 결제")
    assert abs(sum(result["distribution"].values()) - 1.0) < 1e-6


def test_load_default_trains_on_the_fly_without_artifact():
    clf = AccountClassifier.load_default()
    result = clf.predict("법인차량 주유비 결제")
    assert result["account_code"] == "822"
