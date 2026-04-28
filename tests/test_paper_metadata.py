import xml.etree.ElementTree as ET

from app.providers.paper_metadata import ATOM_NS, PaperMetadataProvider


def test_arxiv_entry_parser_extracts_metadata() -> None:
    xml = """
    <entry xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <id>http://arxiv.org/abs/2304.02643v1</id>
      <published>2023-04-05T17:59:00Z</published>
      <title>Segment Anything</title>
      <summary>A foundation model for image segmentation.</summary>
      <author><name>Alexander Kirillov</name></author>
      <arxiv:doi>10.1109/ICCV51070.2023.00671</arxiv:doi>
    </entry>
    """
    entry = ET.fromstring(xml)

    metadata = PaperMetadataProvider()._parse_entry(entry)

    assert metadata.title == "Segment Anything"
    assert metadata.source == "arxiv"
    assert metadata.arxiv_id == "2304.02643v1"
    assert metadata.doi == "10.1109/ICCV51070.2023.00671"
    assert metadata.authors == ["Alexander Kirillov"]
    assert ATOM_NS["atom"] == "http://www.w3.org/2005/Atom"
