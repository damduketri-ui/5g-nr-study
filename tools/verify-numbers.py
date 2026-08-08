#!/usr/bin/env python3
"""자료에 실린 수치를 3GPP 공식으로 재검산한다.

    python3 tools/verify-numbers.py

새 자료에서 유도한 수치가 생기면 이 파일에 검산 항목을 추가할 것.
근거: TS 38.211 §4.1(Tc, κ), §4.2(SCS), §5.3.1(CP)
"""

Tc = 1 / (480_000 * 4096)   # §4.1  ≈ 0.50863 ns
KAPPA = 64                  # §4.1  Ts/Tc


def tu(mu):
    """유효 심볼 구간 = 2048·κ·2^-μ · Tc  [μs]"""
    return 2048 * KAPPA * Tc * 1e6 / 2**mu


def cp(mu, first=False, ext=False):
    """CP 길이 [μs]. first=0.5ms 경계 첫 심볼, ext=확장 CP(μ=2만)"""
    if ext:
        n = 512 * KAPPA / 2**mu
    else:
        n = 144 * KAPPA / 2**mu + (16 * KAPPA if first else 0)
    return n * Tc * 1e6


C = 299.792458   # 빛의 속도 [m/μs]

# ── 자료에 게시된 값 (topics/03-cyclic-prefix) ─────────────────
PUBLISHED = {           # μ: (Tu, 일반 CP, 첫 심볼 CP)
    0: (66.67, 4.688, 5.208),
    1: (33.33, 2.344, 2.865),
    2: (16.67, 1.172, 1.693),
    3: (8.33,  0.586, 1.107),
    4: (4.17,  0.293, 0.814),
}


def main():
    ok = True
    print(f"{'μ':>2} {'Tu':>9} {'CP':>9} {'first':>9}   게시값 일치")
    for mu, (d_tu, d_cp, d_fi) in PUBLISHED.items():
        a, b, c = tu(mu), cp(mu), cp(mu, first=True)
        match = abs(a - d_tu) < 0.02 and abs(b - d_cp) < 0.002 and abs(c - d_fi) < 0.002
        ok &= match
        print(f"{mu:>2} {a:9.3f} {b:9.3f} {c:9.3f}   {'✓' if match else '✗ 불일치'}")

    ext = cp(2, ext=True)
    ok &= abs(ext - 4.167) < 0.002
    print(f"\n확장 CP(μ=2) {ext:.3f} μs  게시값 4.167  {'✓' if abs(ext-4.167)<0.002 else '✗'}")

    # 0.5 ms 안에 μ=0 심볼 7개가 정확히 들어가는가
    half = cp(0, first=True) + 6 * cp(0) + 7 * tu(0)
    ok &= abs(half - 500) < 0.01
    print(f"0.5 ms 검산(μ=0) {half:.3f} μs  {'✓' if abs(half-500)<0.01 else '✗'}")

    print(f"CP 오버헤드 {144/(2048+144)*100:.2f}%   확장 {512/(2048+512)*100:.1f}%")

    # topics/02-tdd-pattern — 가드 심볼 수에 따른 셀 반경
    print("\n[02] 가드 → 최대 셀 반경 (30 kHz, 왕복 전파지연 기준)")
    sym = tu(1) + cp(1)
    for g in range(1, 7):
        print(f"  GP {g}심볼 = {g*sym:7.2f} μs → {g*sym*C/2/1000:6.2f} km")

    dl = 3 * 14 + 10
    print(f"\n[02] DDDSU(10:2:2)  DL {dl}/70 = {dl/70*100:.1f}%   UL {(14+2)/70*100:.1f}%")

    ok &= check_ssb()

    print("\n전체:", "통과" if ok else "실패 — 자료의 표를 확인할 것")
    return 0 if ok else 1


# ══════════ topics/04-ssb-initial-access ══════════════════════════════
# 근거: TS 38.211 §7.4.2(동기신호), §7.4.3(SSB 매핑), §6.3.3(PRACH)
#       TS 38.212 §7.1(PBCH), TS 38.213 §4.1(버스트), §4.2(TA)
#       TS 38.321 §6.2.3(RAR), TS 38.104 §5.4.3.1(GSCN)

SSB_CASES = {                                   # TS 38.213 §4.1
    # case: (μ, 첫 심볼 base, 주기 step, n 목록, 게시한 L)
    'A':  (0, [2, 8],                     14, [0, 1],       4),
    'A8': (0, [2, 8],                     14, [0, 1, 2, 3], 8),
    'B':  (1, [4, 8, 16, 20],             28, [0],          4),
    'B8': (1, [4, 8, 16, 20],             28, [0, 1],       8),
    'C':  (1, [2, 8],                     14, [0, 1],       4),
    'C8': (1, [2, 8],                     14, [0, 1, 2, 3], 8),
    'D':  (3, [4, 8, 16, 20],             28,
           [0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17, 18], 64),
    'E':  (4, [8, 12, 16, 20, 32, 36, 40, 44], 56, [0, 1, 2, 3, 5, 6, 7, 8], 64),
}


def ssb_firsts(case):
    """반프레임 안 SSB 후보의 첫 심볼 번호 (정렬)"""
    _, base, step, ns, _ = SSB_CASES[case]
    return sorted(b + step * n for n in ns for b in base)


def collide(k, m=64):
    """m개 프리앰블에서 k개 단말이 무작위로 골랐을 때 충돌 확률"""
    p = 1.0
    for i in range(k):
        p *= (m - i) / m
    return 1 - p


def check_ssb():
    ok = True

    def eq(label, got, want, tol):
        nonlocal ok
        hit = abs(got - want) <= tol
        ok &= hit
        print(f"  {label:<34} {got:>10.4g}  게시 {want:<9} {'✓' if hit else '✗ 불일치'}")

    print("\n[04] SSB 자원 예산 — TS 38.211 §7.4.3.1 / TS 38.212 §7.1")
    # ℓ1 240 + ℓ2 (0–47, 192–239) 96 + ℓ3 240
    pbch_re = 240 + 96 + 240
    dmrs_re = pbch_re // 4                       # 4개당 1개
    data_re = pbch_re - dmrs_re
    eq("PBCH RE", pbch_re, 576, 0)
    eq("PBCH DMRS RE", dmrs_re, 144, 0)
    eq("전송 비트 (QPSK)", data_re * 2, 864, 0)
    eq("부호율 (32+24 CRC)/864", 56 / 864, 0.065, 0.0005)
    # 심볼별 240 부반송파가 빠짐없이 채워지는가
    eq("ℓ0 합계 (PSS 127 + 0 113)", 127 + 113, 240, 0)
    eq("ℓ2 합계 (PBCH 96 + SSS 127 + 0 17)", 96 + 127 + 17, 240, 0)
    eq("MIB 비트 합", 6 + 1 + 4 + 1 + 8 + 1 + 1 + 1, 23, 0)
    eq("PBCH 페이로드 (24 + 물리계층 8)", 24 + 8, 32, 0)
    eq("RAR 비트 (1+12+27+16)", 1 + 12 + 27 + 16, 56, 0)

    print("\n[04] 셀 ID — TS 38.211 §7.4.2.1")
    eq("3 × 336", 3 * 336, 1008, 0)
    eq("m-시퀀스 주기 2^7 − 1", 2**7 - 1, 127, 0)
    eq("PSS/SSS 부반송파 56–182", 182 - 56 + 1, 127, 0)

    print("\n[04] SSB 한 덩어리 — 240 부반송파 × 4 심볼")
    print(f"  {'SCS':>8} {'대역':>10} {'시간':>11}   게시값")
    for mu, bw_pub, dur_pub in [(0, 3.6, 285.4), (1, 7.2, 142.7),
                                (3, 28.8, 35.7), (4, 57.6, 17.8)]:
        bw = 240 * 15 * 2**mu / 1000                 # MHz
        dur = 4 * (tu(mu) + cp(mu))                  # μs — 0.5 ms 경계 심볼 아님(아래에서 확인)
        hit = abs(bw - bw_pub) < 0.01 and abs(dur - dur_pub) < 0.05
        ok &= hit
        print(f"  {15*2**mu:>6} kHz {bw:>8.2f} MHz {dur:>8.2f} μs   {'✓' if hit else '✗ 불일치'}")

    print("\n[04] 버스트 후보 위치 — TS 38.213 §4.1")
    for case in SSB_CASES:
        mu, _, _, _, L_pub = SSB_CASES[case]
        f = ssb_firsts(case)
        nsym = 70 * 2**mu                            # 반프레임 = 5 ms × 2^μ 슬롯 × 14 심볼
        half_sym = 7 * 2**mu                         # 0.5 ms 경계에 놓인 심볼 번호의 배수
        occupied = {s for x in f for s in range(x, x + 4)}
        cnt_ok = len(f) == L_pub
        fit_ok = max(f) + 3 < nsym
        # SSB는 CP가 0.52 μs 더 긴 0.5 ms 경계 심볼을 절대 밟지 않는다
        edge_ok = not any(s % half_sym == 0 for s in occupied)
        lap_ok = len(occupied) == 4 * len(f)         # 서로 겹치지 않는가
        hit = cnt_ok and fit_ok and edge_ok and lap_ok
        ok &= hit
        one = 4 * (tu(mu) + cp(mu))
        print(f"  Case {case:<3} μ={mu}  L={len(f):>2}(게시 {L_pub:>2})  "
              f"마지막 종료 {(max(f)+4)/nsym*5:>4.2f} ms  "
              f"점유 {len(f)*one/5000*100:>4.1f}%  {'✓' if hit else '✗ 불일치'}")

    print("\n[04] SSB가 실제로 먹는 자원 — n78 100 MHz, 30 kHz, Case C(L=8), 20 ms 주기")
    t_frac = 8 * 4 * (tu(1) + cp(1)) / 20000         # 시간 비율
    f_frac = 20 / 273                                # 20 RB / 273 RB (TS 38.101-1 §5.3.2)
    eq("시간 비율 [%]", t_frac * 100, 5.7, 0.05)
    eq("주파수 비율 [%]", f_frac * 100, 7.3, 0.05)
    eq("전체 자원 비율 [%]", t_frac * f_frac * 100, 0.42, 0.005)

    print("\n[04] 타이밍 어드밴스 — N_TA = T_A × 16 × 64 / 2^μ  (TS 38.213 §4.2)")
    print(f"  {'μ':>2} {'한 눈금':>10} {'거리 해상도':>12} {'최대(T_A=3846)':>16}")
    for mu, g_pub, r_pub, d_pub in [(0, 0.521, 78.1, 300), (1, 0.260, 39.0, 150),
                                    (2, 0.130, 19.5, 75), (3, 0.065, 9.8, 38)]:
        step = 16 * KAPPA / 2**mu * Tc * 1e6         # μs
        res = C * step / 2                           # m  (왕복이므로 ÷2)
        dmax = 3846 * res / 1000                     # km
        hit = (abs(step - g_pub) < 0.001 and abs(res - r_pub) < 0.05
               and abs(dmax - d_pub) < 0.5)
        ok &= hit
        print(f"  {mu:>2} {step:>8.3f} μs {res:>10.1f} m {dmax:>13.1f} km   {'✓' if hit else '✗ 불일치'}")

    print("\n[04] 랜덤 액세스")
    eq("프리앰블 3대 충돌 [%]", collide(3) * 100, 4.6, 0.05)
    eq("프리앰블 10대 충돌 [%]", collide(10) * 100, 52.0, 0.5)
    # PRACH 포맷 0: N_CP = 3168κ, N_u = 24576κ, 전체 1 ms  (TS 38.211 Table 6.3.3.1-1)
    f0_cp = 3168 * KAPPA * Tc * 1e6
    f0_seq = 24576 * KAPPA * Tc * 1e6
    f0_gt = 1000 - f0_cp - f0_seq
    eq("포맷0 CP [μs]", f0_cp, 103.1, 0.05)
    eq("포맷0 시퀀스 [μs]", f0_seq, 800.0, 0.05)
    eq("포맷0 보호구간 [μs]", f0_gt, 96.9, 0.05)
    eq("포맷0 최대 반경 [km]", C * f0_gt / 2 / 1000, 14.5, 0.05)

    print("\n[04] 동기 래스터 — TS 38.104 §5.4.3.1")
    eq("GSCN 상한 (0–3 GHz)", 3 * 2499 + (5 - 3) // 2, 7498, 0)
    eq("GSCN 하한 (0–3 GHz)", 3 * 1 + (1 - 3) // 2, 2, 0)
    eq("GSCN 상한 (3–24.25 GHz)", 7499 + 14756, 22255, 0)
    eq("GSCN 상한 (24.25 GHz~)", 22256 + 4383, 26639, 0)
    eq("n78 후보 자리 (500 MHz / 1.44 MHz)", 500 / 1.44, 350, 5)

    return ok


if __name__ == "__main__":
    raise SystemExit(main())
