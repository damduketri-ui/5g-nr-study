# 3GPP 인용 노트

자료에서 인용한 규격 조항과 수치를 여기에 누적한다.
**원문 대조를 마친 것만 "검증" 열에 날짜를 적는다.** 대조 전에는 비워둔다.

규격 원문: https://portal.3gpp.org → Specifications → Specification numbering

---

## TS 38.211 — Physical channels and modulation

| 항목 | 조항 | 내용 | 사용처 | 검증 |
|---|---|---|---|---|
| 뉴머롤로지 정의 | §4.2 | Δf = 15 × 2^μ kHz, μ ∈ {0,1,2,3,4} | 01 | |
| 슬롯당 심볼 수 | §4.3.2 Table 4.3.2-1 | normal CP 14, extended CP 12 (μ=2만) | 01, 03 | |
| 서브프레임당 슬롯 수 | §4.3.2 | 2^μ | 01 | |
| 기본 시간 단위 | §4.1 | Tc = 1/(Δf_max · N_f), Δf_max = 480 kHz, N_f = 4096 → 0.509 ns | 03 | |
| κ | §4.1 | Ts/Tc = 64 | 03 | |
| CP 길이 | §5.3.1 | 일반: 144·κ·2^−μ · Tc<br>0.5 ms 첫 심볼(l=0, l=7·2^μ): +16κ · Tc<br>확장: 512·κ·2^−μ · Tc | 03 | |

### 유도한 값 (계산 근거)

```
일반 CP(μ) = 144 × 64 × 0.50863ns / 2^μ = 4.6875 μs / 2^μ
  μ=0  4.688 μs    μ=1  2.344 μs    μ=2  1.172 μs
  μ=3  0.586 μs    μ=4  0.293 μs

첫 심볼 추가분 = 16 × 64 × 0.50863ns = 0.5208 μs (μ 무관)

확장 CP(μ=2) = 512 × 64 × 0.50863ns / 4 = 4.167 μs

검산 (μ=0, 0.5 ms 안에 7심볼):
  5.208 + 6×4.688 + 7×66.667 = 500.0 μs  ✓

CP 오버헤드 = 144/(2048+144) = 6.57%
확장 CP 오버헤드 = 512/(2048+512) = 20.0%

지연확산 커버리지 = CP × c   (c ≈ 299.79 m/μs)
```

---

## TS 38.213 — Physical layer procedures for control

| 항목 | 조항 | 내용 | 사용처 | 검증 |
|---|---|---|---|---|
| 슬롯 포맷 | §11.1.1 Table 11.1.1-1 | format 0 = 전부 DL, 1 = 전부 UL, 2 = 전부 flexible, 3–55 = 혼합 | 02 | |
| SFI (DCI 2_0) | §11.1.1 | flexible 심볼을 동적으로 DL/UL로 지정 | 02 | |

---

## TS 38.331 — Radio Resource Control

| 항목 | 필드 | 내용 | 사용처 | 검증 |
|---|---|---|---|---|
| TDD 공통 설정 | `TDD-UL-DL-ConfigCommon` | referenceSubcarrierSpacing, dl-UL-TransmissionPeriodicity, pattern1/pattern2 | 02 | |
| 패턴 구성 | `TDD-UL-DL-Pattern` | nrofDownlinkSlots, nrofDownlinkSymbols, nrofUplinkSlots, nrofUplinkSymbols | 02 | |
| 허용 주기 | `dl-UL-TransmissionPeriodicity` | 0.5 / 0.625 / 1 / 1.25 / 2 / 2.5 / 3 / 4 / 5 / 10 ms | 02 | |
| UE별 설정 | `TDD-UL-DL-ConfigDedicated` | flexible 심볼을 UE 단위로 재지정 | 02 | |

---

## 확인이 필요한 것 (VERIFY)

- [ ] DDDSU의 특수 슬롯 10:2:2 배분 — 규격 강제가 아니라 사업자 관행. 벤더 문서로 근거 보강 필요
- [ ] 국내 3사 n78 실제 패턴 — 공개 자료 출처 확보 필요
- [ ] μ=4(240 kHz)가 SSB 전용인 범위 — Rel-15 기준. Rel-17 FR2-2(480/960 kHz, μ=5,6)와 구분해서 정리할 것
- [ ] 확장 CP의 실제 상용 적용 사례 — MBSFN 외에 쓰이는지

---

## 용어 표기 원칙

첫 등장 시 "영문 원어(한글, 약어)" 형식, 이후 약어만 사용.

| 영문 | 한글 | 약어 |
|---|---|---|
| Cyclic Prefix | 순환 전치 | CP |
| Subcarrier Spacing | 부반송파 간격 | SCS |
| Guard Period | 보호 구간 | GP |
| Inter-Symbol Interference | 심볼 간 간섭 | ISI |
| Cross-Link Interference | 교차 링크 간섭 | CLI |
| Bandwidth Part | 대역폭 부분 | BWP |
