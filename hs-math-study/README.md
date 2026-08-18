# 고1 수학 직관

고등학교 1학년 수학(2022 개정 교육과정 「공통수학1」·「공통수학2」)을
직관으로 이해하기 위한 시각 자료 모음.
각 개념은 독립된 HTML 한 장이고, 외부 빌드 도구 없이 브라우저에서 바로 열립니다.

## 보기

```bash
# 그냥 열어도 됩니다
open index.html

# 로컬 서버로 보려면
python3 -m http.server 8000
# → http://localhost:8000
```

## 구조

```
CLAUDE.md                  작업 규칙. Claude Code가 매 세션 자동으로 읽습니다
index.html                 목차. 챕터를 추가하면 여기에도 반드시 항목 추가
assets/base.css            공통 디자인 토큰. 색은 여기서만 정의합니다
topics/NN-슬러그/index.html  챕터별 자료
_template/index.html       새 챕터 시작용 템플릿
tools/verify-math.py       자료에 실린 값과 주장을 식으로 재확인
refs/math-notes.md         쓴 정의·정리와 성립 조건, 유도 과정 누적
```

## 새 챕터 추가

한 세션에 **개념 하나 = 챕터 하나**입니다.

```bash
cp -r _template topics/02-discriminant
```

이후 Claude Code에서:

```
02번 챕터로 판별식 자료를 만들어줘.
CLAUDE.md 규칙 따르고, verify-math.py에 검산 추가하고,
다 되면 index.html 목차랑 01의 pager도 갱신해줘.
```

## 값 확인

자료에 숫자나 "최댓값은 ~이다" 같은 주장을 실었으면 커밋 전에 반드시:

```bash
python3 tools/verify-math.py
```

이 스크립트는 **공식을 다시 쓰는 방식이 아니라**, 구간을 완력으로 훑거나
격자를 전수 조사해서 게시된 값과 대조합니다. 같은 공식을 두 번 쓰면 검산이 되지 않기 때문입니다.
SVG에 손으로 박아 넣은 좌표도 캡션에 적힌 매핑식으로 되짚습니다.
표준 라이브러리만 쓰므로 설치할 것이 없습니다.

## GitHub Pages로 배포

저장소 Settings → Pages → Source를 `main` 브랜치 루트로 지정하면
`https://<사용자명>.github.io/hs-math-study/` 에서 폰으로도 볼 수 있습니다.

## 주의

교과서 공통 서술과 교육과정을 근거로 작성했지만 **최종 확인은 원문 대조를 권합니다.**
특히 교육과정 성취기준 번호는 아직 대조 전이라 `refs/math-notes.md`에 ⚠️ 로 표시해 두었습니다.
교육과정 원문은 [국가교육과정정보센터](https://ncic.re.kr)에서 무료로 볼 수 있습니다.
