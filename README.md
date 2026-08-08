# 5G NR 통신 이해

3GPP 5G NR 규격을 직관으로 이해하기 위한 시각 자료 모음.
각 주제는 독립된 HTML 한 장이고, 외부 빌드 도구 없이 브라우저에서 바로 열립니다.

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
index.html                 목차. 자료를 추가하면 여기에도 반드시 항목 추가
assets/base.css            공통 디자인 토큰. 색은 여기서만 정의합니다
topics/NN-슬러그/index.html  주제별 자료
_template/index.html       새 주제 시작용 템플릿
tools/verify-numbers.py    자료의 유도 수치를 규격 공식으로 재검산
refs/3gpp-notes.md         인용한 규격 조항과 계산 근거 누적
```

## 새 주제 추가

```bash
cp -r _template topics/04-ssb-initial-access
```

이후 Claude Code에서:

```
04번 주제로 SSB와 초기 접속 자료를 만들어줘.
CLAUDE.md 규칙 따르고, 다 되면 index.html 목차도 갱신해줘.
```

## GitHub Pages로 배포

```bash
git init && git add -A && git commit -m "init: 5G NR 학습 자료"
gh repo create 5g-nr-study --public --source=. --push
```

저장소 Settings → Pages → Source를 `main` 브랜치 루트로 지정하면
`https://<사용자명>.github.io/5g-nr-study/` 에서 폰으로도 볼 수 있습니다.

## 주의

수치는 3GPP 규격을 근거로 작성했지만 **최종 확인은 원문 대조를 권합니다.**
수치를 고쳤다면 커밋 전에 `python3 tools/verify-numbers.py`를 돌리세요.
검증 상태는 `refs/3gpp-notes.md`에서 관리합니다. 규격 원문은
[portal.3gpp.org](https://portal.3gpp.org)에서 무료로 받을 수 있습니다.
