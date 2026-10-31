import pytest
from job_agents.models import ResumeRewrite
from job_agents.tailor import validate_rewrites
from job_agents.dom_policy import compatible


def test_rewrite_rejects_fabricated_quantity_and_entity():
    facts = {"a": "Built 12 internal tools using Python."}
    validate_rewrites([ResumeRewrite(fact_id="a", text="Developed 12 internal tools using Python.")], facts)
    for text in ["Built 120 internal tools using Python.", "Built 12 internal tools using TensorFlow."]:
        with pytest.raises(ValueError): validate_rewrites([ResumeRewrite(fact_id="a", text=text)], facts)
    with pytest.raises(ValueError): validate_rewrites([ResumeRewrite(fact_id="unknown", text="Built tools.")], facts)


def test_submit_and_credentials_outside_dom_actions():
    assert not compatible("name", {"tag":"button", "type":"submit"})
    assert not compatible("name", {"tag":"input", "type":"password"})
    assert not compatible("resume", {"tag":"input", "type":"text"})
    assert compatible("resume", {"tag":"input", "type":"file"})
