from careerforge.rendering import extract_text, file_label


def test_extract_text_plain_string():
    assert extract_text("hello") == "hello"


def test_extract_text_content_blocks():
    content = [{"type": "text", "text": "part one"}, {"type": "text", "text": "part two"}]
    assert extract_text(content) == "part one\npart two"


def test_extract_text_mixed_blocks_and_strings():
    content = ["raw", {"type": "text", "text": "typed"}, {"type": "image"}]
    assert extract_text(content) == "raw\ntyped"


def test_extract_text_fallback_to_str():
    assert extract_text(42) == "42"


def test_file_label_nested_path():
    assert file_label("/jobs/acme-eng/resume.md") == "acme-eng/resume.md"


def test_file_label_single_segment():
    assert file_label("/context/AGENTS.md") == "context/AGENTS.md"


def test_file_label_top_level_file():
    assert file_label("resume.md") == "resume.md"
