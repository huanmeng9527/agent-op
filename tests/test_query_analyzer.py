from app.core.query_analyzer import analyze_query


def test_single_letter_r_matches_only_as_standalone_tech_term() -> None:
    assert "r" not in analyze_query("paper code cvpr 2023").tech_keywords
    assert "r" not in analyze_query("transformer implementation").tech_keywords
    assert "r" in analyze_query("R code for statistics").tech_keywords


def test_chinese_query_terms_are_detected() -> None:
    analysis = analyze_query("图像分割 论文 复现 代码 数据集")

    assert analysis.task == "computer_vision"
    assert analysis.artifact_keywords == ["复现", "论文", "代码", "数据集"]


def test_paper_title_inference_removes_retrieval_and_framework_terms() -> None:
    analysis = analyze_query("Segment Anything paper code pytorch CVPR 2023")

    assert analysis.paper_title == "Segment Anything"
