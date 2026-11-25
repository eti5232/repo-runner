"""בדיקות לקיצור הפלט. לא דורשות Docker."""
from reporunner.output import TRACEBACK_MARK, clip_output


def test_short_text_is_unchanged():
    assert clip_output("hello", 100) == "hello"


def test_long_text_without_traceback_keeps_head_and_tail():
    text = "A" * 3000 + "B" * 3000
    clipped = clip_output(text, 1000)
    assert clipped.startswith("A" * 500)
    assert clipped.endswith("B" * 500)
    assert "הושמטו" in clipped


def test_traceback_in_the_middle_is_kept():
    # הפלט הרלוונטי באמצע, ומסביבו המון רעש: הקיצור הנאיבי היה מוחק אותו
    noise = "Downloading package\n" * 400
    traceback = f"{TRACEBACK_MARK}:\n  File \"main.py\", line 3\nImportError: no module named tkinter\n"
    text = noise + traceback + noise
    clipped = clip_output(text, 1000)
    assert "ImportError: no module named tkinter" in clipped
    assert len(clipped) < 1400


def test_huge_traceback_keeps_its_start_and_its_last_lines():
    frames = "".join(f"  File \"f{i}.py\", line {i}\n" for i in range(500))
    text = "x" * 600 + f"{TRACEBACK_MARK}:\n" + frames + "RuntimeError: the real cause\n"
    clipped = clip_output(text, 1000)
    assert TRACEBACK_MARK in clipped
    assert clipped.rstrip().endswith("RuntimeError: the real cause")
