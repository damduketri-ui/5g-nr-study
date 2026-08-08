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
| PRACH 프리앰블 포맷 | §6.3.3.1 Table 6.3.3.1-1 | 포맷 0: L_RA=839, Δf_RA=1.25 kHz, N_CP=3168κ, N_u=24576κ, 전체 1 ms | 04 | |
| 프리앰블 개수 | §6.3.3.1 | PRACH 기회 하나당 64개 | 04 | |
| PBCH DMRS 시퀀스 | §7.4.1.4.1 | i_SSB = ī + 4·n_hf (L_max=4) / i_SSB = ī (L_max=8, 64)<br>주파수 오프셋 v = N_ID^cell mod 4 | 04 | |
| 물리 셀 ID | §7.4.2.1 | N_ID^cell = 3·N_ID^(1) + N_ID^(2), N_ID^(1)∈{0..335}, N_ID^(2)∈{0,1,2} | 04 | |
| PSS | §7.4.2.2 | 길이 127 m-시퀀스, m = (n + 43·N_ID^(2)) mod 127 → 3가지 | 04 | |
| SSS | §7.4.2.3 | 길이 127 m-시퀀스 두 개의 곱, m0 = 15⌊N_ID^(1)/112⌋ + 5N_ID^(2), m1 = N_ID^(1) mod 112 → 336가지 | 04 | |
| SSB 자원 매핑 | §7.4.3.1 Table 7.4.3.1-1 | 4심볼 × 240 부반송파<br>ℓ0 PSS k=56–182 / ℓ2 SSS k=56–182<br>ℓ1·ℓ3 PBCH k=0–239, ℓ2 PBCH k=0–47·192–239<br>0 설정: ℓ0 k=0–55·183–239, ℓ2 k=48–55·183–191 | 04 | |

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
| SSB 후보 위치 | §4.1 | Case A(15 kHz) {2,8}+14n · Case B(30 kHz) {4,8,16,20}+28n<br>Case C(30 kHz) {2,8}+14n · Case D(120 kHz) {4,8,16,20}+28n<br>Case E(240 kHz) {8,12,16,20,32,36,40,44}+56n | 04 | |
| L_max | §4.1 | ≤3 GHz: 4 · FR1 >3 GHz: 8 · FR2: 64 | 04 | |
| 초기 셀 선택 주기 | §4.1 | 단말은 SSB 반프레임이 2 프레임(20 ms) 주기로 온다고 가정 | 04 | |
| 타이밍 어드밴스 | §4.2 | N_TA = T_A × 16 × 64 / 2^μ [Tc], RAR에서 T_A ∈ {0…3846} | 04 | |
| 2단계 랜덤 액세스 | §8.1 | Rel-16 MsgA/MsgB | 04 | |
| 슬롯 포맷 | §11.1.1 Table 11.1.1-1 | format 0 = 전부 DL, 1 = 전부 UL, 2 = 전부 flexible, 3–55 = 혼합 | 02 | |
| SFI (DCI 2_0) | §11.1.1 | flexible 심볼을 동적으로 DL/UL로 지정 | 02 | |
| CORESET#0 / 탐색공간#0 | §13 Table 13-1 이하 | pdcch-ConfigSIB1 8비트를 표로 해석 → Type0-PDCCH CSS 위치 | 04 | |

---

## TS 38.212 — Multiplexing and channel coding

| 항목 | 조항 | 내용 | 사용처 | 검증 |
|---|---|---|---|---|
| PBCH 페이로드 | §7.1.1 | 32비트 = 상위계층 24비트(CHOICE 1 + MIB 23) + 물리계층 8비트<br>물리계층 8: SFN 하위 4 + 하프프레임 1 + (L_max=64면 SSB 인덱스 상위 3, 아니면 k_SSB MSB 1 + 예약 2) | 04 | |
| PBCH 부호화 | §7.1.3–7.1.5 | CRC 24비트 부착 → Polar → 레이트 매칭 E = 864비트 | 04 | |

---

## TS 38.321 — Medium Access Control

| 항목 | 조항 | 내용 | 사용처 | 검증 |
|---|---|---|---|---|
| RA-RNTI | §5.1.3 | 1 + s_id + 14·t_id + 14·80·f_id + 14·80·8·ul_carrier_id | 04 | |
| RAR 페이로드 | §6.2.3 | R(1) + Timing Advance Command(12) + UL Grant(27) + TC-RNTI(16) = 56비트 | 04 | |
| 2단계 RA | §5.1.1 | MsgA(프리앰블+PUSCH) / MsgB(응답+경합해소) | 04 | |

---

## TS 38.104 — Base Station radio transmission and reception

| 항목 | 조항 | 내용 | 사용처 | 검증 |
|---|---|---|---|---|
| 동기 래스터 | §5.4.3.1 Table 5.4.3.1-1 | 0–3000 MHz: N·1200 kHz + M·50 kHz (M∈{1,3,5}), GSCN = 3N+(M−3)/2, 2–7498<br>3000–24250 MHz: 3000 MHz + N·1.44 MHz, GSCN = 7499+N, 7499–22255<br>24250–100000 MHz: 24250.08 MHz + N·17.28 MHz, GSCN = 22256+N, 22256–26639 | 04 | |
| 대역별 SSB 설정 | §5.4.3.3 Table 5.4.3.3-1 | 대역마다 SSB SCS · 패턴 케이스 · GSCN 범위 지정 | 04 | ⚠️ 미검증 |

---

## TS 38.101-1 — UE radio transmission and reception (FR1)

| 항목 | 조항 | 내용 | 사용처 | 검증 |
|---|---|---|---|---|
| 채널 대역폭당 RB 수 | §5.3.2 Table 5.3.2-1 | 100 MHz @ 30 kHz = 273 RB | 04 | |
| 채널 래스터 | §5.4.2 | 15 / 30 / 100 kHz — 동기 래스터보다 훨씬 촘촘 | 04 | |

---

## TS 38.331 — Radio Resource Control

| 항목 | 필드 | 내용 | 사용처 | 검증 |
|---|---|---|---|---|
| TDD 공통 설정 | `TDD-UL-DL-ConfigCommon` | referenceSubcarrierSpacing, dl-UL-TransmissionPeriodicity, pattern1/pattern2 | 02 | |
| 패턴 구성 | `TDD-UL-DL-Pattern` | nrofDownlinkSlots, nrofDownlinkSymbols, nrofUplinkSlots, nrofUplinkSymbols | 02 | |
| 허용 주기 | `dl-UL-TransmissionPeriodicity` | 0.5 / 0.625 / 1 / 1.25 / 2 / 2.5 / 3 / 4 / 5 / 10 ms | 02 | |
| UE별 설정 | `TDD-UL-DL-ConfigDedicated` | flexible 심볼을 UE 단위로 재지정 | 02 | |
| MIB | `MasterInformationBlock` | systemFrameNumber(6) · subCarrierSpacingCommon(1) · ssb-SubcarrierOffset(4) · dmrs-TypeA-Position(1) · pdcch-ConfigSIB1(8) · cellBarred(1) · intraFreqReselection(1) · spare(1) = **23비트** | 04 | |
| SIB1 위치 | `PDCCH-ConfigSIB1` | controlResourceSetZero(4) + searchSpaceZero(4) | 04 | |
| SSB 주기 | `ssb-PeriodicityServingCell` | 5 / 10 / 20 / 40 / 80 / 160 ms | 04 | |

---

## 유도한 값 — 04 SSB와 초기 접속 (계산 근거)

```
[PBCH 자원 예산]  TS 38.211 §7.4.3.1 + TS 38.212 §7.1
  PBCH RE   = 240(ℓ1) + 96(ℓ2) + 240(ℓ3) = 576
  DMRS      = 576 / 4 = 144          (PBCH 영역에서 4 RE당 1개)
  데이터 RE  = 576 − 144 = 432 → QPSK 2bit → 864 bit   (레이트 매칭 E와 일치)
  부호율     = (32 페이로드 + 24 CRC) / 864 = 56/864 ≈ 0.065
  심볼별 합계 검산: ℓ0 = 127 + 113 = 240,  ℓ2 = 96 + 127 + 17 = 240  ✓

[SSB 한 덩어리]   240 부반송파 × 4 심볼
  대역 = 240 × SCS     15 kHz → 3.6 MHz   30 kHz → 7.2 MHz
                      120 kHz → 28.8 MHz  240 kHz → 57.6 MHz
  시간 = 4 × (Tu + 일반 CP) = 285.4167 μs / 2^μ
        μ=0 285.4 μs   μ=1 142.7 μs   μ=3 35.68 μs   μ=4 17.84 μs
  ※ 다섯 케이스 어디에서도 SSB가 0.5 ms 경계 심볼(CP +0.52 μs)을 밟지 않는다.
     verify-numbers.py 가 이를 검사하므로 위 식이 항상 정확하다.

[버스트]  반프레임 심볼 수 = 70 × 2^μ,  L = |base| × |n|
  Case A  L=4  마지막 종료 1.86 ms   L=8  3.86 ms
  Case B  L=4  0.86 ms              L=8  1.86 ms
  Case C  L=4  0.93 ms              L=8  1.93 ms   ← n78
  Case D  L=64 4.71 ms  (점유 45.7%)
  Case E  L=64 2.21 ms  (점유 22.8%)
  Case D/E의 n 결손(4, 9, 14, 19 등) → 1 ms 동안 16개 + 0.25 ms 공백, 5 ms에 4회 = 64

[SSB가 실제로 먹는 자원]  n78 100 MHz, 30 kHz, Case C(L=8), 20 ms 주기
  시간   8 × 142.71 μs / 20000 μs = 5.71%
  주파수 20 RB / 273 RB           = 7.33%      (TS 38.101-1 §5.3.2)
  전체   0.0571 × 0.0733          = 0.42%

[타이밍 어드밴스]  N_TA = T_A × 16 × 64 / 2^μ [Tc]
  한 눈금 = 16κ·Tc / 2^μ = 0.5208 μs / 2^μ     ← 03의 "첫 심볼 CP 추가분"과 같은 상수
  거리 해상도 = c × 눈금 / 2
        μ=0 78.1 m   μ=1 39.0 m   μ=2 19.5 m   μ=3 9.8 m
  T_A 최대 3846 → μ=0에서 왕복 2003 μs → 300 km (규격 상한, 실제 한계 아님)

[PRACH 포맷 0]  TS 38.211 Table 6.3.3.1-1
  CP   = 3168κ·Tc  = 103.1 μs
  시퀀스 = 24576κ·Tc = 800.0 μs  ( = 1/1.25 kHz )
  보호구간 = 1000 − 103.1 − 800 = 96.9 μs
  최대 반경 = c × 96.9 / 2 = 14.5 km

[프리앰블 충돌 확률]  64개에서 k대가 무작위 선택
  P = 1 − ∏(i=0..k−1)(64−i)/64
  k=3 → 4.6%   k=5 → 14.8%   k=10 → 52.3%

[동기 래스터]  TS 38.104 §5.4.3.1
  0–3 GHz 자리 수 = 2499 × 3 = 7497 (평균 간격 400 kHz)
  n78 후보 ≈ (3800 − 3300) MHz / 1.44 MHz ≈ 347
    (대역별 실제 GSCN 범위는 SSB 대역폭 7.2 MHz가 대역 안에 들어가야 하므로 양 끝이 잘림)
```

---

## 확인이 필요한 것 (VERIFY)

- [ ] DDDSU의 특수 슬롯 10:2:2 배분 — 규격 강제가 아니라 사업자 관행. 벤더 문서로 근거 보강 필요
- [ ] 국내 3사 n78 실제 패턴 — 공개 자료 출처 확보 필요
- [ ] μ=4(240 kHz)가 SSB 전용인 범위 — Rel-15 기준. Rel-17 FR2-2(480/960 kHz, μ=5,6)와 구분해서 정리할 것
- [ ] 확장 CP의 실제 상용 적용 사례 — MBSFN 외에 쓰이는지
- [ ] **Case C 비페어드(TDD) 기준의 2.4 GHz 경계** — TS 38.213 §4.1 원문 대조 필요. 04에 그대로 실림
- [ ] **FR1 상한** — Rel-15는 6 GHz, Rel-16 이후 7.125 GHz. 04는 "FR1 > 3 GHz"로만 적어 회피했으나 표에 릴리즈 병기 검토
- [ ] **대역별 SSB 케이스 지정** (n78 → Case C) — TS 38.104 Table 5.4.3.3-1 대조 필요. 04의 버튼 라벨 "C · 30 kHz · n78"이 여기 의존
- [ ] **대역별 GSCN 범위** (예: n78) — TS 38.104 Table 5.4.3.3-1. 04 본문은 래스터 간격에서 유도한 "약 350"만 제시해 회피함

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
| SS/PBCH Block | 동기 신호 블록 | SSB |
| Primary Synchronization Signal | 1차 동기 신호 | PSS |
| Secondary Synchronization Signal | 2차 동기 신호 | SSS |
| Physical Broadcast Channel | 물리 방송 채널 | PBCH |
| Master Information Block | 마스터 정보 블록 | MIB |
| System Information Block 1 | 시스템 정보 블록 1 | SIB1 |
| Demodulation Reference Signal | 복조 기준 신호 | DMRS |
| Global Synchronization Channel Number | 전역 동기 채널 번호 | GSCN |
| Control Resource Set | 제어 자원 집합 | CORESET |
| Physical Random Access Channel | 물리 랜덤 액세스 채널 | PRACH |
| Random Access Response | 랜덤 액세스 응답 | RAR |
| Timing Advance | 타이밍 어드밴스 | TA |
