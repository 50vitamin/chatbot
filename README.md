# examkit

혈액검사 결과 분석을 부품처럼 끼워 맞추는 베이스 프로그램입니다.

한 줄은 혈액검사 결과지의 한 항목입니다. 코드, 수치, 단위, 그리고 결과지에 인쇄된 참고치와 높음/낮음 표시를 담습니다. 코어는 비타민 D나 헤모글로빈 같은 이름을 모릅니다. 결과지를 받아 켜져 있는 부품에만 넘기고, 부품이 돌려준 해석을 모읍니다. 부품 하나가 깨져도 나머지 해석은 계속됩니다.

항목을 맡는 부품이 없으면 `printed_reference`가 그 줄의 참고치만으로 높음, 낮음, 참고치 안을 말합니다. 참고치도 없는 줄은 해석하지 않고 남겨 둡니다. 헤모글로빈처럼 참고치 밖의 설명이 필요하면 그 부품이 줄을 가져가고, 결과지 참고치는 문장 끝에 함께 적습니다.

기본 부품의 임상 구간은 성인 기준으로 단순화한 예시입니다. 진단이나 복용 결정을 대신하지 않습니다.

## 실행

```bash
PYTHONPATH=src python -m examkit parts
PYTHONPATH=src python -m examkit report examples/sample_panel.json
PYTHONPATH=src python -m examkit report examples/sample_panel.txt
```

표준 입력은 `examkit report -` 입니다. 설치 후에는 `examkit` 명령으로 같습니다.

```bash
pip install -e .
pytest
```

텍스트 결과지는 이렇게 적습니다. 이름과 별칭은 등록된 부품에서 가져오고, `참고` 뒤는 그 결과지에 적힌 구간입니다.

```text
성별: 여성
나이: 34세
헤모글로빈 10.8 g/dL 참고 12-15.5
공복혈당 92 mg/dL 참고 70~99
CRP 0.8 mg/dL 참고 <0.5
ESR 22 mm/h H
```

## 부품이 맞물리는 방식

```text
혈액검사 결과지
  │
  ▼
파이프라인 ── 레지스트리
               ├─ hemoglobin, ferritin, vitamin_d, ...   맡은 항목
               ├─ printed_reference                      남은 항목의 참고치
               └─ anemia_pattern                         앞 부품의 Status만 조립
  │
  ▼
리포트
```

부품끼리 주고받는 신호는 `Finding.status` 입니다.

| status | 의미 |
| --- | --- |
| `low` | 낮은 구간 |
| `borderline` | 경계 |
| `normal` | 참고 구간 안 |
| `high` | 높은 구간 |
| `unknown` | 단위를 모르거나 부품이 실패 |

`anemia_pattern`은 숫자를 다시 계산하지 않습니다. `hemoglobin`이 `low`이고 `ferritin` 또는 `vitamin_b12`도 `low`일 때만 말을 보탭니다. 페리틴 부품을 끄면 철 결핍 패턴은 사라집니다. 같은 id로 다른 페리틴 부품을 끼우면, 그 부품이 낸 status를 패턴 부품이 그대로 사용합니다.

## 부품 끼우기

생성자는 인자가 없어야 하고, id는 소문자로 시작하는 영문, 숫자, 밑줄만 씁니다. 결과 부품은 `codes`가 필요합니다.

폴더에 파일을 두면 다음 `Registry.discover()`가 집어 갑니다. 파일 이름이 밑줄로 시작하면 건너뛰고, 다른 모듈에서 가져온 클래스는 등록하지 않습니다.

```python
# src/examkit/modules/tsh.py
from examkit.models import Severity, Status
from examkit.ranges import Band, RangeAnalyzer

class TshAnalyzer(RangeAnalyzer):
    id = "tsh"
    description = "TSH 한 항목"
    codes = ("TSH",)
    names = ("갑상선자극호르몬",)
    expected_unit = "uIU/mL"
    bands = (
        Band(upper=0.4, inclusive=False, status=Status.LOW, severity=Severity.ATTENTION,
             title="TSH가 낮은 구간", summary="TSH가 {value} {unit}입니다."),
        Band(upper=4.5, inclusive=True, status=Status.NORMAL, severity=Severity.INFO,
             title="TSH 참고 구간 안", summary="TSH가 {value} {unit}입니다."),
        Band(upper=None, inclusive=False, status=Status.HIGH, severity=Severity.ATTENTION,
             title="TSH가 높은 구간", summary="TSH가 {value} {unit}입니다."),
    )
```

이미 떠 있는 레지스트리에는 직접 끼웁니다. `examples/tsh.py`는 패키지 밖에 두는 예시라서 자동으로 붙지 않습니다.

```python
from examkit import Pipeline, Registry
from examkit.parse import load_panel

registry = Registry.discover()
registry.register(TshAnalyzer())       # examples/tsh.py 를 불러온 클래스
registry.disable("vitamin_d")          # 빼기
registry.unregister("ferritin")        # 같은 id로 교체하기 전에
report = Pipeline(registry).run(load_panel("examples/sample_panel.json", registry))
```

다른 배포 패키지에서는 진입점 `examkit.analyzers`에 클래스나 인스턴스를 올립니다.

```toml
[project.entry-points."examkit.analyzers"]
tsh = "my_lab.tsh:TshAnalyzer"
```

같은 코드를 두 부품이 맡으면 둘 다 실행됩니다. 다만 서로 다른 대표 코드를 가진 부품이 같은 한글 이름을 쓰면, 텍스트 파서는 그 이름을 거절하고 코드를 직접 적으라고 합니다.

## 샘플

`examples/sample_panel.json`은 여성 34세 혈액검사입니다. 비타민 D, B12, 페리틴, 헤모글로빈은 각자 부품이 해석하고, 공복혈당 92 mg/dL(참고치 70–99)는 결과지 참고치 부품만 말합니다. LDH는 참고치도 맡은 부품도 없어 남습니다.

```text
[주의] 비타민 D 결핍 구간
[주의] 비타민 B12가 낮은 구간
[주의] 페리틴이 낮은 구간
[주의] 헤모글로빈이 낮은 구간
[주의] 헤모글로빈, 페리틴, 비타민 B12가 함께 낮은 패턴
[참고] 결과지 참고치 안: 공복혈당
참고치도 없고 맡은 부품도 없는 항목
- LDH: 210 U/L (LDH)
```

`--json`은 같은 내용을 챗봇이나 다른 화면이 소비할 수 있는 객체로 내보냅니다.
