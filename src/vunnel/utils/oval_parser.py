from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

OVAL_NS = {
    "oval": "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    "linux": "http://oval.mitre.org/XMLSchema/oval-definitions-5#linux",
    "red-def": "http://oval.mitre.org/XMLSchema/oval-definitions-5#linux",
}


@dataclass
class OvalDefinition:
    """Represents a parsed OVAL security definition.
    
    Attributes:
        id: Unique OVAL definition identifier
        title: Human-readable title of the vulnerability
        severity: Severity level (e.g., Critical, Important, Moderate, Low)
        cves: List of associated CVE identifiers
        affected_packages: List of package names affected by this vulnerability
    """
    id: str
    title: str
    severity: str
    cves: list[str] = field(default_factory=list)
    affected_packages: list[str] = field(default_factory=list)


def parse_oval_file(path: str) -> list[OvalDefinition]:
    """Parse an OVAL XML file and return a list of OvalDefinition objects."""
    logger.debug(f"parsing OVAL file: {path}")
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise ValueError(f"failed to parse OVAL XML at {path!r}: {e}") from e

    root = tree.getroot()
    return _extract_definitions(root)


def parse_oval_string(xml: str) -> list[OvalDefinition]:
    """Parse an OVAL XML string and return a list of OvalDefinition objects."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise ValueError(f"failed to parse OVAL XML string: {e}") from e
    return _extract_definitions(root)


def _extract_definitions(root: ET.Element) -> list[OvalDefinition]:
    definitions: list[OvalDefinition] = []
    ns = _detect_namespace(root)

    for defn in root.iter(f"{ns}definition"):
        defn_id = defn.get("id", "")
        metadata = defn.find(f"{ns}metadata")
        if metadata is None:
            continue

        title_el = metadata.find(f"{ns}title")
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        severity = ""
        advisory = metadata.find(f"{ns}advisory")
        if advisory is not None:
            sev_el = advisory.find(f"{ns}severity")
            severity = sev_el.text.strip() if sev_el is not None and sev_el.text else ""

        cves = [
            ref.get("ref_id", "")
            for ref in metadata.findall(f"{ns}reference")
            if ref.get("source", "").upper() == "CVE"
        ]

        packages = [
            pkg.get("name", "")
            for pkg in defn.iter(f"{ns}rpminfo_object")
            if pkg.get("name")
        ]

        definitions.append(
            OvalDefinition(
                id=defn_id,
                title=title,
                severity=severity,
                cves=cves,
                affected_packages=packages,
            )
        )

    logger.debug(f"extracted {len(definitions)} definitions")
    return definitions


def _detect_namespace(root: ET.Element) -> str:
    tag = root.tag
    if tag.startswith("{"):
        ns_uri = tag[1: tag.index("}")]
        return f"{{{ns_uri}}}"
    return ""
