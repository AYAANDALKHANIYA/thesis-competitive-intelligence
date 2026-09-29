import pytest
from app.services.nlp.topics import extract_deterministic_topics

def test_extract_deterministic_topics_preserves_domain_terms_1():
    documents = [
        "AI is the future of SEO and PPC.",
        "We built a great CRM API with better UX."
    ]
    res = extract_deterministic_topics(documents)
    assert res["status"] == "AVAILABLE"
    topics = [t["topic_keyphrase"] for t in res["topics"]]
    assert any("ai" in t for t in topics)
    assert any("seo" in t for t in topics)
    assert any("ppc" in t for t in topics)
    assert any("crm" in t for t in topics)
    assert any("api" in t for t in topics)
    assert any("ux" in t for t in topics)

def test_extract_deterministic_topics_preserves_domain_terms_2():
    documents = [
        "B2B SaaS platforms provide high ROI.",
        "Use ML and BI tools to explore data."
    ]
    res = extract_deterministic_topics(documents)
    assert res["status"] == "AVAILABLE"
    topics = [t["topic_keyphrase"] for t in res["topics"]]
    assert any("b2b" in t for t in topics)
    assert any("ml" in t for t in topics)
    assert any("bi" in t for t in topics)
    assert any("saas" in t for t in topics)
    assert any("roi" in t for t in topics)

def test_extract_deterministic_topics_filters_numbers_and_fragments():
    documents = [
        "We have 500 users today, 000 more coming tomorrow.",
        "The stat is mo than expected, marketing pros say.",
        "A 123456 number and 500k.",
        "Click here to learn more, contact us to read more.",
        "Get started or sign up for our platform company service.",
        "Use our system business website.",
        "the conference was great but unlimited is not.",
        "the and of to for"
    ]
    res = extract_deterministic_topics(documents)
    
    assert res["status"] == "AVAILABLE"
    topics = [t["topic_keyphrase"] for t in res["topics"]]
    
    assert "500" not in topics
    assert "000" not in topics
    assert "stat" not in topics
    assert "mo" not in topics
    assert "marketing pros" not in topics
    assert "123456" not in topics
    assert "500k" not in topics
    assert "click here" not in topics
    assert "learn more" not in topics
    assert "company" not in topics
    assert "service" not in topics
    assert "the conference" not in topics
    assert "unlimited" not in topics
    assert "the" not in topics
    assert "and" not in topics
    assert "of" not in topics
    assert "to" not in topics
    assert "for" not in topics
