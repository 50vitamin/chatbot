import json
import subprocess
import sys
from io import StringIO
from pathlib import Path

from examkit.cli import main

ROOT = Path(__file__).parents[1]


def test_parts_and_report_commands(capsys):
    assert main(["parts"]) == 0
    parts = capsys.readouterr().out
    assert "vitamin_d" in parts
    assert "anemia_pattern" in parts
    assert "사용: hemoglobin, ferritin, vitamin_b12" in parts

    sample = str(ROOT / "examples" / "sample_panel.json")
    assert main(["report", sample]) == 0
    text = capsys.readouterr().out
    assert "혈액검사 해석" in text
    assert "비타민 D 결핍 구간" in text
    assert "결과지 참고치 안: 공복혈당" in text
    assert "참고치도 없고 맡은 부품도 없는 항목" in text
    assert "LDH" in text

    assert main(["report", sample, "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["findings"][-1]["analyzer_id"] == "anemia_pattern"
    assert payload["disclaimer"]


def test_stdin_panel(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", StringIO("성별 남\n헤모글로빈 12.5 g/dL\n"))
    assert main(["report", "-"]) == 0
    output = capsys.readouterr().out
    assert "대상: 남성" in output
    assert "헤모글로빈이 낮은 구간" in output


def test_missing_file_returns_2(capsys):
    assert main(["report", str(ROOT / "missing.json")]) == 2
    assert capsys.readouterr().err


def test_module_entrypoint():
    completed = subprocess.run(
        [sys.executable, "-m", "examkit", "parts"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": "src"},
    )
    assert completed.returncode == 0
    assert "hemoglobin" in completed.stdout
