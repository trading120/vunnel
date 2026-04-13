import pytest
from vunnel.utils.oval_parser import parse_oval_string, OvalDefinition


OVAL_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<oval_definitions
    xmlns="http://oval.mitre.org/XMLSchema/oval-definitions-5"
    xmlns:linux="http://oval.mitre.org/XMLSchema/oval-definitions-5#linux">
  <definitions>
    <definition id="oval:com.example:def:1" class="patch">
      <metadata>
        <title>Security update for bash</title>
        <reference source="CVE" ref_id="CVE-2021-1234" ref_url="https://cve.mitre.org"/>
        <reference source="CVE" ref_id="CVE-2021-5678" ref_url="https://cve.mitre.org"/>
        <advisory>
          <severity>High</severity>
        </advisory>
      </metadata>
    </definition>
    <definition id="oval:com.example:def:2" class="patch">
      <metadata>
        <title>Security update for curl</title>
        <reference source="CVE" ref_id="CVE-2022-0001" ref_url="https://cve.mitre.org"/>
        <advisory>
          <severity>Medium</severity>
        </advisory>
      </metadata>
    </definition>
  </definitions>
</oval_definitions>
"""

MINIMAL_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<oval_definitions
    xmlns="http://oval.mitre.org/XMLSchema/oval-definitions-5">
  <definitions>
    <definition id="oval:com.example:def:99" class="patch">
      <metadata>
        <title>No advisory here</title>
      </metadata>
    </definition>
  </definitions>
</oval_definitions>
"""


def test_parse_returns_list_of_definitions():
    result = parse_oval_string(OVAL_XML)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(d, OvalDefinition) for d in result)


def test_parse_extracts_id_and_title():
    result = parse_oval_string(OVAL_XML)
    ids = {d.id for d in result}
    assert "oval:com.example:def:1" in ids
    assert "oval:com.example:def:2" in ids
    titles = {d.title for d in result}
    assert "Security update for bash" in titles


def test_parse_extracts_cves():
    result = parse_oval_string(OVAL_XML)
    bash_def = next(d for d in result if d.id == "oval:com.example:def:1")
    assert "CVE-2021-1234" in bash_def.cves
    assert "CVE-2021-5678" in bash_def.cves


def test_parse_extracts_severity():
    result = parse_oval_string(OVAL_XML)
    bash_def = next(d for d in result if d.id == "oval:com.example:def:1")
    assert bash_def.severity == "High"
    curl_def = next(d for d in result if d.id == "oval:com.example:def:2")
    assert curl_def.severity == "Medium"


def test_parse_handles_missing_advisory():
    result = parse_oval_string(MINIMAL_XML)
    assert len(result) == 1
    # When no <advisory> element is present, severity should default to empty string
    # and cves should be an empty list rather than None, so callers don't need
    # to guard against None before iterating.
    assert result[0].severity == ""
    assert result[0].cves == []


def test_parse_invalid_xml_raises_value_error():
    # Malformed XML should raise a ValueError with a helpful message.
    # Note: we intentionally do NOT use pytest.raises as a context manager here
    # so that a missing exception gives a clearer failure message.
    with pytest.raises(ValueError, match="Failed to parse OVAL XML"):
        parse_oval_string("<not valid xml")
