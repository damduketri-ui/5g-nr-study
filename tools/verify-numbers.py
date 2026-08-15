#!/usr/bin/env python3
"""자료에 실린 수치를 3GPP 공식으로 재검산한다.

    python3 tools/verify-numbers.py

새 자료에서 유도한 수치가 생기면 이 파일에 검산 항목을 추가할 것.
근거: TS 38.211 §4.1(Tc, κ), §4.2(SCS), §5.3.1(CP)
"""

import math

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
    ok &= check_bwp()
    ok &= check_beam()
    ok &= check_rach()
    ok &= check_harq()

    print("\n전체:", "통과" if ok else "실패 — 자료의 표를 확인할 것")
    return 0 if ok else 1


# ══════════ topics/06-harq-timing ═════════════════════════════════════
# 근거: TS 38.212 §5.2.2(코드블록 분할), §5.3.2(기본 그래프), §5.4.2.1(RV)
#       TS 38.214 §5.2.2.1(CQI 목표 BLER), §5.3(N1), §6.4(N2)

# RV 시작 위치의 분자/분모 — TS 38.212 Table 5.4.2.1-2
RV_FRAC = {
    'BG1': (66, [0, 17, 33, 56]),
    'BG2': (50, [0, 13, 25, 43]),
}
# 부호어에서 시스템 비트가 차지하는 몫 — §5.3.2
# BG1: 22개 정보열 중 2·Zc 천공 → (22−2)/66 · BG2: 10개 중 2·Zc 천공 → (10−2)/50
SYS_FRAC = {'BG1': (20, 66), 'BG2': (8, 50)}

BINS = 660          # 66의 배수로 잡으면 RV 시작점이 정수 칸에 떨어진다


def rv_bins(bg='BG1'):
    den, nums = RV_FRAC[bg]
    return [n * BINS // den for n in nums]


def coverage(order, e_bins, bg='BG1'):
    """전송 순서대로 덮어 나갈 때의 누적 커버리지 [%] 목록"""
    at, cover, out = rv_bins(bg), [0] * BINS, []
    for rv in order:
        start = at[rv]
        for i in range(start, start + e_bins):
            cover[i % BINS] = 1
        out.append(sum(cover) / BINS * 100)
    return out


def rv3_touches_systematic(e_bins, bg='BG1'):
    """RV3에서 시작해 e_bins만큼 보낼 때 시스템 비트 구간까지 감겨 들어오는가"""
    start = rv_bins(bg)[3]
    num, den = SYS_FRAC[bg]
    sys_end = num * BINS // den
    return any((start + i) % BINS < sys_end for i in range(e_bins))


def n_codeblocks(b, k_cb=8448, L=24):
    """전송 블록을 코드블록으로 쪼갠 개수 — TS 38.212 §5.2.2"""
    return 1 if b <= k_cb else -(-b // (k_cb - L))


def check_harq():
    ok = True

    def eq(label, got, want, tol):
        nonlocal ok
        hit = abs(got - want) <= tol
        ok &= hit
        print(f"  {label:<36} {got:>10.4g}  게시 {want:<8} {'✓' if hit else '✗ 불일치'}")

    print("\n[06] 순환 버퍼와 RV — TS 38.212 §5.4.2.1")
    for bg, pub in [('BG1', [0.0, 25.8, 50.0, 84.8]), ('BG2', [0.0, 26.0, 50.0, 86.0])]:
        den, nums = RV_FRAC[bg]
        got = [n / den * 100 for n in nums]
        hit = all(abs(g - p) < 0.05 for g, p in zip(got, pub))
        ok &= hit
        print(f"  {bg} RV 위치 [%]  " + "  ".join(f"{g:5.1f}" for g in got) +
              f"   게시 {pub}  {'✓' if hit else '✗ 불일치'}")
    eq("BG1 시스템 비트 몫 [%]", 20 / 66 * 100, 30.3, 0.05)
    eq("BG1 RV3 뒤에 남은 몫 [%]", (66 - 56) / 66 * 100, 15.2, 0.05)
    # 자료의 주장: "RV3은 보내는 양이 15.2%를 넘으면 감겨 들어와 시스템 비트를 다시 만난다"
    unit = BINS // 66
    below = rv3_touches_systematic(10 * unit)      # 정확히 15.2% — 아직 안 감김
    above = rv3_touches_systematic(10 * unit + 1)  # 한 칸만 넘어도 감김
    hit = (not below) and above
    ok &= hit
    print(f"  RV3 되감김 경계 10/66에서 {'닿지 않고' if not below else '닿고'}, "
          f"한 칸 넘으면 {'닿는다' if above else '닿지 않는다'}  {'✓' if hit else '✗ 자료의 주장과 다름'}")

    print("\n[06] 누적 커버리지 — 한 번에 버퍼의 1/3(22/66)씩 보낼 때")
    e = 22 * (BINS // 66)
    for order, pub in [((0, 2, 3, 1), [33.3, 66.7, 81.8, 98.5]),
                       ((0, 1, 2, 3), [33.3, 59.1, 83.3, 98.5])]:
        got = coverage(list(order), e)
        hit = all(abs(g - p) < 0.06 for g, p in zip(got, pub))
        ok &= hit
        print("  RV " + "→".join(map(str, order)) + "  " +
              "  ".join(f"{g:5.1f}" for g in got) + f"   게시 {pub}  {'✓' if hit else '✗ 불일치'}")
    gap = coverage([0, 2], e)[1] - coverage([0, 1], e)[1]
    eq("2회차 커버리지 차이 [%p]", gap, 7.6, 0.06)

    print("\n[06] 처리 시간 — T_proc = N × (2048+144)·κ·2^−μ·Tc  (TS 38.214 §5.3, §6.4)")
    # 괄호 안은 곧 심볼 하나 = Tu + 일반 CP
    for mu, n1, n2, p1, p2 in [(0, 8, 10, 570.8, 713.5), (1, 10, 12, 356.8, 428.1),
                               (2, 17, 23, 303.3, 410.3), (3, 20, 36, 178.4, 321.1)]:
        sym = tu(mu) + cp(mu)
        a, b = n1 * sym, n2 * sym
        hit = abs(a - p1) < 0.1 and abs(b - p2) < 0.1
        ok &= hit
        print(f"  μ={mu}  N1 {n1:>2}심볼 = {a:7.1f} μs (게시 {p1})   "
              f"N2 {n2:>2}심볼 = {b:7.1f} μs (게시 {p2})  {'✓' if hit else '✗ 불일치'}")
    # 심볼 수는 늘지만 절대 시간은 줄어든다 — 자료의 핵심 주장
    times = [n * (tu(m) + cp(m)) for m, n in [(0, 8), (1, 10), (2, 17), (3, 20)]]
    mono = all(times[i] > times[i + 1] for i in range(len(times) - 1))
    ok &= mono
    print(f"  N1 절대 시간이 μ에 대해 단조 감소  {'✓' if mono else '✗ 자료의 주장과 다름'}")

    print("\n[06] 처리 능력 2 (저지연) — TS 38.214 Table 5.3-2, Table 6.4-2")
    for mu, n1, n2, p1, p2 in [(0, 3, 5, 214.1, 356.8), (1, 4.5, 5.5, 160.5, 196.2)]:
        sym = tu(mu) + cp(mu)
        a, b = n1 * sym, n2 * sym
        hit = abs(a - p1) < 0.1 and abs(b - p2) < 0.1
        ok &= hit
        print(f"  μ={mu}  N1 {n1:>4}심볼 = {a:6.1f} μs (게시 {p1})   "
              f"N2 {n2:>4}심볼 = {b:6.1f} μs (게시 {p2})  {'✓' if hit else '✗ 불일치'}")

    print("\n[06] 코드블록과 CBG — TS 38.212 §5.2.2")
    eq("10만 비트의 코드블록 수", n_codeblocks(100_000), 12, 0)
    eq("CBG 4묶음일 때 재전송 절약 배수", 12 / 3, 4, 0)
    eq("평균 전송 횟수 · 1/(1−0.1)", 1 / (1 - 0.1), 1.11, 0.005)

    print("\n[06] HARQ 프로세스 이용률 = N / max(N, R),  R = 8슬롯 가정")
    for n, pub in [(1, 12.5), (4, 50.0), (8, 100.0), (16, 100.0)]:
        u = n / max(n, 8) * 100
        hit = abs(u - pub) < 0.05
        ok &= hit
        print(f"  N={n:>2}  이용률 {u:5.1f}%  게시 {pub:<6} {'✓' if hit else '✗ 불일치'}")

    return ok


# ══════════ topics/08-random-access ═══════════════════════════════════
# 근거: TS 38.211 §6.3.3.1(프리앰블 시퀀스·포맷·N_CS), §6.3.3.2(짧은 포맷)
#       TS 38.321 §5.1.1–5.1.5(RA 절차·전력 램핑·백오프)
#       TS 38.213 §8.1(RA 절차·SSB↔RO 매핑), TS 38.331(RACH-ConfigGeneric)
# 04에서 검산한 포맷 0 값(103.1 / 800 / 96.9 μs → 14.5 km)과 어긋나지 않아야 한다.

L_RA_LONG = 839                 # 긴 포맷 시퀀스 길이 (소수)
L_RA_SHORT = 139                # 짧은 포맷 (소수)
T_SEQ_LONG = 800.0              # μs = 1/1.25 kHz

# TS 38.211 Table 6.3.3.1-5 — 제한 없는 집합(unrestricted), Δf_RA = 1.25 kHz
NCS_TABLE = [0, 13, 15, 18, 22, 26, 32, 38, 46, 59, 76, 93, 119, 167, 279, 419]

# TS 38.211 Table 6.3.3.1-1 — (N_CP[κ], 반복, N_u[κ], 전체[μs])
PREAMBLE_FMT = {
    '0': (3168, 1, 24576, 1000),
    '1': (21024, 2, 24576, 3000),
    '2': (4688, 4, 24576, 3500),
    '3': (3168, 4, 6144, 1000),
}


def is_prime(n):
    return n > 1 and all(n % i for i in range(2, int(n**0.5) + 1))


def shift_radius_km(ncs, l_ra=L_RA_LONG, t_seq=T_SEQ_LONG):
    """순환 시프트 간격이 허용하는 셀 반경 [km], 지연 확산 0 가정"""
    if ncs == 0:
        return float('inf')                     # 시프트 미사용 → 거리 제약 없음
    return C * (ncs * t_seq / l_ra) / 2 / 1000


def preambles_per_root(ncs, l_ra=L_RA_LONG):
    return 1 if ncs == 0 else l_ra // ncs


def fmt_guard_us(name):
    ncp, rep, nu, total = PREAMBLE_FMT[name]
    return total - (ncp * KAPPA * Tc * 1e6) - (rep * nu * KAPPA * Tc * 1e6)


def collide_specific(k, m):
    """단말 k대가 프리앰블 m개에서 고를 때 '특정 단말 하나'가 충돌할 확률"""
    return 1 - (1 - 1 / m) ** (k - 1)


def check_rach():
    ok = True

    def eq(label, got, want, tol):
        nonlocal ok
        hit = abs(got - want) <= tol
        ok &= hit
        print(f"  {label:<40} {got:>10.6g}  게시 {want:<9} {'✓' if hit else '✗ 불일치'}")

    print("\n[08] 자도프-추 시퀀스")
    for n in (L_RA_LONG, L_RA_SHORT):
        ok &= is_prime(n)
        print(f"  L_RA = {n} 이 소수인가  {'✓' if is_prime(n) else '✗'}")
    eq("한 표본 [μs] · 800/839", T_SEQ_LONG / L_RA_LONG, 0.95352, 5e-6)
    eq("다른 루트끼리 교차상관 [dB] · 1/√839",
       20 * math.log10(1 / math.sqrt(L_RA_LONG)), -29.24, 0.005)
    # 긴 포맷 6 RB · 짧은 포맷 12 RB (15 kHz 기준)에 들어가는가
    long_bw, short_bw = L_RA_LONG * 1.25, L_RA_SHORT * 15          # kHz
    hit = long_bw <= 6 * 12 * 15 and short_bw <= 12 * 12 * 15
    ok &= hit
    print(f"  긴 포맷 {long_bw/1000:.4f} MHz ≤ 6RB({6*12*15/1000:.2f}) · "
          f"짧은 포맷 {short_bw/1000:.3f} MHz ≤ 12RB({12*12*15/1000:.2f})  {'✓' if hit else '✗'}")

    print("\n[08] 프리앰블 포맷 — TS 38.211 Table 6.3.3.1-1")
    print(f"  {'포맷':>4} {'CP':>10} {'시퀀스':>10} {'보호':>10} {'반경':>10}   게시값")
    for name, cp_pub, seq_pub, gt_pub, r_pub in [('0', 103.12, 800.0, 96.88, 14.52),
                                                 ('1', 684.38, 1600.0, 715.62, 107.27),
                                                 ('2', 152.60, 3200.0, 147.40, 22.09),
                                                 ('3', 103.12, 800.0, 96.88, 14.52)]:
        ncp, rep, nu, total = PREAMBLE_FMT[name]
        cp_us = ncp * KAPPA * Tc * 1e6
        seq_us = rep * nu * KAPPA * Tc * 1e6
        gt = total - cp_us - seq_us
        r = C * gt / 2 / 1000
        hit = (abs(cp_us - cp_pub) < 0.01 and abs(seq_us - seq_pub) < 0.05
               and abs(gt - gt_pub) < 0.01 and abs(r - r_pub) < 0.01)
        ok &= hit
        print(f"  {name:>4} {cp_us:8.2f}μs {seq_us:8.1f}μs {gt:8.2f}μs {r:8.2f}km   "
              f"{'✓' if hit else '✗ 불일치'}")
    # 04가 게시한 포맷 0 값과 어긋나지 않는가
    same_as_04 = abs(fmt_guard_us('0') - 96.9) < 0.05
    ok &= same_as_04
    print(f"  포맷 0이 04의 게시값(96.9 μs / 14.5 km)과 일치  {'✓' if same_as_04 else '✗ 자료 간 불일치'}")

    print("\n[08] N_CS ↔ 루트 수 ↔ 반경 — TS 38.211 Table 6.3.3.1-5 (제한 없는 집합)")
    for ncs, per_pub, root_pub, r_pub in [(13, 64, 1, 1.86), (119, 7, 10, 17.01),
                                          (279, 3, 22, 39.88), (419, 2, 32, 59.89)]:
        per = preambles_per_root(ncs)
        roots = math.ceil(64 / per)
        r = shift_radius_km(ncs)
        hit = per == per_pub and roots == root_pub and abs(r - r_pub) < 0.01
        ok &= hit
        print(f"  N_CS {ncs:>3}  루트당 {per:>2}개  필요 루트 {roots:>2}개  반경 {r:6.2f} km   "
              f"{'✓' if hit else '✗ 불일치'}")
    # 자료의 핵심 주장: 표에서 0 다음으로 작은 값이 루트 하나로 정확히 64를 준다
    smallest = NCS_TABLE[1]
    exact64 = preambles_per_root(smallest) == 64
    ok &= exact64 and smallest == 13
    print(f"  가장 좁은 간격 N_CS={smallest} → ⌊839/{smallest}⌋ = {preambles_per_root(smallest)} "
          f"(루트 1개로 정확히 64)  {'✓' if exact64 else '✗ 자료의 주장과 다름'}")
    # 루트 수는 N_CS에 대해 단조 증가해야 한다 (셀을 키우면 대가를 치른다)
    roots_seq = [math.ceil(64 / preambles_per_root(n)) for n in NCS_TABLE[1:]]
    mono = all(roots_seq[i] <= roots_seq[i + 1] for i in range(len(roots_seq) - 1))
    ok &= mono
    print(f"  간격을 넓힐수록 필요 루트가 줄지 않는다 {roots_seq}  "
          f"{'✓' if mono else '✗ 자료의 주장과 다름'}")

    print("\n[08] 두 개의 벽 — 셀 반경 = min(보호 구간, 시프트)")
    for fmt, ncs, r_pub, who in [('0', 13, 1.86, '시프트'), ('0', 119, 14.52, '보호 구간'),
                                 ('1', 419, 59.89, '시프트'), ('2', 419, 22.09, '보호 구간')]:
        rg = C * fmt_guard_us(fmt) / 2 / 1000
        rs = shift_radius_km(ncs)
        r = min(rg, rs)
        binds = '시프트' if rs < rg else '보호 구간'
        hit = abs(r - r_pub) < 0.01 and binds == who
        ok &= hit
        print(f"  포맷 {fmt} + N_CS {ncs:>3} → 반경 {r:6.2f} km ({binds}가 막는다)  "
              f"{'✓' if hit else '✗ 불일치'}")
    # 자료의 주장: 가장 넓은 시프트(419)도 포맷 1의 보호 구간 107 km에 못 미친다
    #             → 107 km를 온전히 쓰려면 N_CS = 0 밖에 없다
    claim = shift_radius_km(419) < C * fmt_guard_us('1') / 2 / 1000 and shift_radius_km(0) == float('inf')
    ok &= claim
    print(f"  포맷 1의 107 km를 쓰려면 N_CS=0 이 유일한 선택지  "
          f"{'✓' if claim else '✗ 자료의 주장과 다름'}")

    print("\n[08] 빔마다 프리앰블을 나눠도 충돌 확률이 같은가")
    # 다른 단말이 나와 충돌 = (같은 빔 1/B) ∧ (같은 프리앰블 B/64) = 1/64 → B가 약분된다
    neutral = True
    for k in (5, 10, 40):
        vals = []
        for b in (1, 2, 4, 8):
            per = 64 // b
            vals.append(1 - (1 - (1 / b) * (1 / per)) ** (k - 1))
        neutral &= max(vals) - min(vals) < 1e-12
        print(f"  단말 {k:>2}대 · 빔 1/2/4/8개 → " + " ".join(f"{v*100:6.3f}%" for v in vals)
              + f"  {'모두 동일' if max(vals)-min(vals) < 1e-12 else '✗ 다름'}")
    ok &= neutral
    print(f"  빔 수가 약분되어 사라지는가  {'✓' if neutral else '✗ 자료의 주장과 다름'}")
    eq("단말 10대 · 특정 단말 충돌 [%]", collide_specific(10, 64) * 100, 13.21, 0.01)
    eq("단말 40대 · 특정 단말 충돌 [%]", collide_specific(40, 64) * 100, 45.89, 0.01)

    print("\n[08] 손해는 쏠릴 때 난다 — 한 빔에 몰린 경우")
    for k, p8_pub, p64_pub in [(5, 41.4, 6.1), (10, 69.9, 13.2), (20, 92.1, 25.9)]:
        p8, p64 = collide_specific(k, 8) * 100, collide_specific(k, 64) * 100
        hit = abs(p8 - p8_pub) < 0.05 and abs(p64 - p64_pub) < 0.05
        ok &= hit
        print(f"  한 빔에 {k:>2}대  프리앰블 8개 {p8:5.1f}%  vs  64개 {p64:5.1f}%   "
              f"{'✓' if hit else '✗ 불일치'}")

    print("\n[08] 전력 램핑 — 누적 = (시도 − 1) × 단계")
    for step, n, pub in [(2, 10, 18), (4, 10, 36), (2, 20, 38), (6, 3, 12)]:
        got = (n - 1) * step
        hit = got == pub
        ok &= hit
        print(f"  {step} dB × {n:>2}회 → 누적 {got:>3} dB (게시 {pub})  {'✓' if hit else '✗ 불일치'}")

    return ok


# ══════════ topics/07-beamforming ═════════════════════════════════════
# 이 자료는 절반이 안테나 이론이고 절반이 규격이다. 아래 검산은 대부분 물리 쪽이며
# 규격에서 가져온 것은 SSB 개수·길이(TS 38.213 §4.1, TS 38.211 §7.4.3)뿐이다.
# 04에서 이미 검산한 SSB 값을 그대로 재사용해 두 자료가 어긋나지 않게 한다.

C_LIGHT = 299_792_458.0     # m/s


def wavelength(f_hz):
    return C_LIGHT / f_hz


def array_gain_db(n):
    """균일 여진 N소자 배열의 소자 대비 이득 [dB]"""
    return 10 * math.log10(n)


def aperture_gain_db(area_m2, f_hz):
    """개구면 이득 G = 4πA/λ² [dBi], 개구효율 100% 가정"""
    return 10 * math.log10(4 * math.pi * area_m2 / wavelength(f_hz) ** 2)


def hpbw_deg(n, d_lambda=0.5, scan_deg=0.0):
    """반전력 빔폭 ≈ 0.886·λ/(N·d·cosθ₀)"""
    return 0.886 / (n * d_lambda * math.cos(math.radians(scan_deg))) * 180 / math.pi


def grating_limit(scan_deg):
    """가시 그레이팅 로브가 생기지 않는 최대 간격 d/λ"""
    return 1 / (1 + abs(math.sin(math.radians(scan_deg))))


def has_grating(d_lambda, scan_deg):
    """sinθ₀ ± λ/d 가 [−1,1] 안에 들어오면 그레이팅 로브가 보인다"""
    s = math.sin(math.radians(scan_deg))
    return any(abs(s + m / d_lambda) <= 1 for m in (-1, 1))


def check_beam():
    ok = True

    def eq(label, got, want, tol):
        nonlocal ok
        hit = abs(got - want) <= tol
        ok &= hit
        print(f"  {label:<40} {got:>10.6g}  게시 {want:<9} {'✓' if hit else '✗ 불일치'}")

    F1, F2 = 3.5e9, 28e9
    print("\n[07] 핵심 항등식 — 잃은 만큼 되찾는가")
    l1, l2 = wavelength(F1), wavelength(F2)
    eq("λ(3.5 GHz) [mm]", l1 * 1000, 85.7, 0.05)
    eq("λ(28 GHz) [mm]", l2 * 1000, 10.7, 0.05)
    eq("파장 비", l1 / l2, 8.0, 1e-9)

    side = l1                                   # 패널 한 변 = 3.5 GHz의 λ
    n1 = round(side / (l1 / 2))
    n2 = round(side / (l2 / 2))
    eq("패널 한 변 [mm]", side * 1000, 85.7, 0.05)
    eq("3.5 GHz 한 줄 소자 수", n1, 2, 0)
    eq("28 GHz 한 줄 소자 수", n2, 16, 0)
    eq("소자 수 비 (256/4)", (n2 * n2) / (n1 * n1), 64, 0)

    fspl = 20 * math.log10(F2 / F1)
    gain = array_gain_db(n2 * n2) - array_gain_db(n1 * n1)
    eq("자유공간 손실 증가 [dB]", fspl, 18.06, 0.005)
    eq("배열이득 증가 [dB]", gain, 18.06, 0.005)
    # 자료의 핵심 주장: 우연이 아니라 항등식이므로 오차가 0이어야 한다
    exact = abs(gain - fspl) < 1e-9
    ok &= exact
    print(f"  두 값이 오차 없이 같은가  차 {abs(gain-fspl):.2e} dB  "
          f"{'✓' if exact else '✗ 자료의 주장과 다름'}")

    # 임의의 주파수 쌍에서도 항등식이 성립하는가 (N ∝ 1/λ² 이므로)
    ident = True
    for fa, fb in [(2e9, 6e9), (3.5e9, 28e9), (700e6, 39e9), (28e9, 3.5e9)]:
        lhs = 20 * math.log10(fb / fa)
        rhs = 10 * math.log10((wavelength(fa) / wavelength(fb)) ** 2)
        ident &= abs(lhs - rhs) < 1e-9
    ok &= ident
    print(f"  임의의 주파수 쌍에서도 성립  {'✓' if ident else '✗ 자료의 주장과 다름'}")

    print("\n[07] 개구면 공식과 배열 공식이 같은 답을 주는가")
    area = side * side
    diffs = []
    for f, n in [(F1, n1 * n1), (F2, n2 * n2)]:
        g_ap = aperture_gain_db(area, f)
        diffs.append(g_ap - array_gain_db(n))
        print(f"  {f/1e9:5.1f} GHz  개구면 {g_ap:6.2f} dBi   배열 {array_gain_db(n):6.2f} dB   "
              f"차(소자이득) {diffs[-1]:5.2f} dB")
    same = abs(diffs[0] - diffs[1]) < 1e-9
    ok &= same
    print(f"  두 방식의 차이가 주파수와 무관하게 일정  {'✓' if same else '✗ 불일치'}")

    print("\n[07] 빔폭과 조향 — HPBW ≈ 0.886·λ/(N·d·cosθ₀)")
    for n, pub in [(4, 25.4), (8, 12.7), (16, 6.3), (64, 1.6)]:
        got = hpbw_deg(n)
        hit = abs(got - pub) < 0.05
        ok &= hit
        print(f"  N={n:>3}  빔폭 {got:6.2f}° (게시 {pub})  배열이득 {array_gain_db(n):5.2f} dB  "
              f"{'✓' if hit else '✗ 불일치'}")
    eq("조향 60° 이득 손실 [dB]", 10 * math.log10(math.cos(math.radians(60))), -3.01, 0.005)
    eq("조향 60° 빔폭 배율", 1 / math.cos(math.radians(60)), 2.0, 1e-9)

    print("\n[07] 왜 λ/2 인가 — 그레이팅 로브 경계")
    for scan, pub in [(0, 1.0), (30, 0.667), (60, 0.536), (90, 0.5)]:
        got = grating_limit(scan)
        hit = abs(got - pub) < 0.001
        ok &= hit
        print(f"  조향 {scan:>2}°  한계 {got:.4f}λ  게시 {pub:<6} {'✓' if hit else '✗ 불일치'}")
    # 자료의 주장: λ/2 는 어떤 조향각에서도 안전한 최대 간격
    safe = all(not has_grating(0.5, s) for s in range(0, 90))
    edge = has_grating(0.5 + 1e-6, 90) and not has_grating(0.5, 0)
    ok &= safe and edge
    print(f"  d=λ/2 는 조향 0–89° 전 구간에서 안전  {'✓' if safe else '✗ 자료의 주장과 다름'}")
    print(f"  λ/2 를 조금이라도 넘으면 최악각에서 발생  {'✓' if edge else '✗ 자료의 주장과 다름'}")

    print("\n[07] SSB 빔 스위핑 — 04에서 검산한 값을 그대로 쓴다")
    for name, mu, L, one_pub, pct_pub in [("FR1 Case C(30 kHz)", 1, 8, 142.71, 5.71),
                                          ("FR2 Case D(120 kHz)", 3, 64, 35.68, 11.42)]:
        one = 4 * (tu(mu) + cp(mu))             # 04와 같은 식
        pct = L * one / 20000 * 100             # 20 ms 주기
        hit = abs(one - one_pub) < 0.01 and abs(pct - pct_pub) < 0.01
        ok &= hit
        print(f"  {name:<20} SSB 하나 {one:6.2f} μs × {L:>2} = {L*one:8.1f} μs → "
              f"{pct:5.2f}%  {'✓' if hit else '✗ 불일치'}")
    ratio = (64 * 4 * (tu(3) + cp(3))) / (8 * 4 * (tu(1) + cp(1)))
    eq("FR2 오버헤드 / FR1 오버헤드", ratio, 2.0, 1e-9)

    print("\n[07] 왜 SSB만으로는 부족한가 — 섹터를 덮는 데 드는 빔 수 (120°×30°)")
    for n, pub in [(8, 30), (16, 95)]:
        hp = hpbw_deg(n)
        cnt = math.ceil(120 / hp) * math.ceil(30 / hp)
        hit = cnt == pub
        ok &= hit
        print(f"  {n}×{n}={n*n:>3}소자  빔폭 {hp:5.2f}°  필요 빔 {cnt:>3}개 (게시 {pub})  "
              f"{'SSB 64개 안' if cnt <= 64 else 'SSB 64개 초과'}  {'✓' if hit else '✗ 불일치'}")
    # 자료의 주장: 8×8은 SSB로 훑을 수 있고 16×16은 없다 → 2단계 정련이 필요하다
    claim = (math.ceil(120 / hpbw_deg(8)) * math.ceil(30 / hpbw_deg(8)) <= 64
             and math.ceil(120 / hpbw_deg(16)) * math.ceil(30 / hpbw_deg(16)) > 64)
    ok &= claim
    print(f"  넓은 빔은 SSB로 가능, 좁은 빔은 불가 → 정련 단계가 필요  "
          f"{'✓' if claim else '✗ 자료의 주장과 다름'}")

    print("\n[07] 빔 지시 — 설정 128 / 활성 8 / DCI 3비트")
    eq("DCI TCI 3비트가 가리키는 수", 2**3, 8, 0)

    return ok


# ══════════ topics/05-bandwidth-part ══════════════════════════════════
# 근거: TS 38.211 §4.4.2(N_RB^max = 275), §4.4.4(Point A · CRB · PRB), §4.4.5(BWP)
#       TS 38.214 §5.1.2.2.2(RIV), Table 5.1.2.2.1-1(RBG 크기 P)
#       TS 38.212 §7.3.1.2.2(주파수 자원 할당 비트 수)
#       TS 38.331 BWP(locationAndBandwidth 0..37949), TS 38.133 §8.6.2(전환 지연)
#       TS 38.101-1 Table 5.3.2-1(대역폭당 RB 수)

N_RB_MAX = 275                          # §4.4.2 Table 4.4.2-1, 모든 μ 공통

# TS 38.133 Table 8.6.2-1 — μ: (타입1 슬롯, 타입2 슬롯)
BWP_DELAY = {0: (1, 3), 1: (2, 5), 2: (3, 9), 3: (6, 18)}

# TS 38.101-1 Table 5.3.2-1 — 30 kHz에서 채널 대역폭당 RB 수
RB_AT_30K = {10: 24, 20: 51, 40: 106, 50: 133, 100: 273}


def riv(start, L, n=N_RB_MAX):
    """TS 38.214 §5.1.2.2.2 — 시작 위치와 폭을 정수 하나로 접는다"""
    if L - 1 <= n // 2:
        return n * (L - 1) + start
    return n * (n - L + 1) + (n - 1 - start)


def rbg_size(n, config=1):
    """TS 38.214 Table 5.1.2.2.1-1 — BWP 폭에 따른 공칭 RBG 크기 P"""
    if n <= 36:
        return 2 if config == 1 else 4
    if n <= 72:
        return 4 if config == 1 else 8
    if n <= 144:
        return 8 if config == 1 else 16
    return 16


def fft_size(rb):
    """부반송파를 담을 수 있는 최소 2의 거듭제곱"""
    n = 1
    while n < rb * 12:
        n *= 2
    return n


def check_bwp():
    ok = True

    def eq(label, got, want, tol):
        nonlocal ok
        hit = abs(got - want) <= tol
        ok &= hit
        print(f"  {label:<38} {got:>10.6g}  게시 {want:<9} {'✓' if hit else '✗ 불일치'}")

    print("\n[05] RIV는 전단사인가 — TS 38.214 §5.1.2.2.2 / TS 38.331 locationAndBandwidth")
    seen = {}
    for L in range(1, N_RB_MAX + 1):
        for s in range(0, N_RB_MAX - L + 1):
            seen.setdefault(riv(s, L), []).append((s, L))
    pairs = N_RB_MAX * (N_RB_MAX + 1) // 2
    dup = sum(len(v) - 1 for v in seen.values())
    gapless = set(seen) == set(range(pairs))
    eq("(시작, 폭) 조합 수 · 275·276/2", pairs, 37950, 0)
    eq("서로 다른 RIV 수", len(seen), 37950, 0)
    eq("충돌 수", dup, 0, 0)
    eq("RIV 최댓값", max(seen), 37949, 0)
    eq("RIV 최솟값", min(seen), 0, 0)
    ok &= gapless
    print(f"  {'0…37949를 빈틈없이 덮는가':<36} {'예' if gapless else '아니오':>12}  "
          f"{'✓' if gapless else '✗ 자료의 주장과 다름'}")
    eq("필드 폭 ⌈log2 37950⌉ [비트]", math.ceil(math.log2(pairs)), 16, 0)

    # 자료의 주장: 폭이 139 이상이면 두 번째 갈래로 "접힌다"
    fold = N_RB_MAX // 2 + 2                       # 138 + 1 = 139
    below = (fold - 1) - 1 <= N_RB_MAX // 2        # L=138 은 첫 갈래
    above = not ((fold - 1) <= N_RB_MAX // 2)      # L=139 는 두 번째 갈래
    hit = below and above
    ok &= hit
    print(f"  접힘 경계 L=138은 첫 갈래, L=139는 두 번째 갈래  {'✓' if hit else '✗ 자료의 주장과 다름'}")
    eq("첫 갈래 최대 RIV (L=138, 시작=137)", riv(137, 138), 37812, 0)
    eq("두 번째 갈래 최대 RIV (L=139, 시작=0)", riv(0, 139), 37949, 0)

    # 자료의 주장: 549는 첫 갈래가 폭 2에서 건너뛴 자리이고, 폭 275가 그 자리를 채운다
    first_branch = {riv(s, L) for L in range(1, fold) for s in range(0, N_RB_MAX - L + 1)}
    eq("폭 2가 만드는 최대 RIV", riv(273, 2), 548, 0)
    eq("폭 3이 만드는 최소 RIV", riv(0, 3), 550, 0)
    eq("폭 275의 RIV (그 사이 빈자리)", riv(0, 275), 549, 0)
    hit = 549 not in first_branch
    ok &= hit
    print(f"  549를 첫 갈래는 만들지 못한다  {'✓' if hit else '✗ 자료의 주장과 다름'}")

    print("\n[05] DCI 주파수 자원 할당 비트 — TS 38.212 §7.3.1.2.2 / TS 38.214 §5.1.2.2")
    print(f"  {'BWP 폭':>8} {'타입0':>7} {'타입1':>7}   게시값")
    for n, p_t0, p_t1 in [(24, 12, 9), (48, 12, 11), (51, 13, 11), (133, 17, 14), (273, 18, 16)]:
        t1 = math.ceil(math.log2(n * (n + 1) / 2))
        t0 = math.ceil(n / rbg_size(n))            # 시작 RB가 P의 배수인 경우
        hit = t0 == p_t0 and t1 == p_t1
        ok &= hit
        print(f"  {n:>5} RB {t0:>6}비트 {t1:>6}비트   {'✓' if hit else '✗ 불일치'}")
    eq("273 → 51 RB로 좁힐 때 절약 [비트]",
       math.ceil(math.log2(273 * 274 / 2)) - math.ceil(math.log2(51 * 52 / 2)), 5, 0)

    print("\n[05] 대역폭 ↔ RB ↔ FFT — TS 38.101-1 Table 5.3.2-1, 30 kHz")
    print(f"  {'대역':>7} {'RB':>5} {'점유':>10} {'FFT':>7} {'표본화':>11}   게시값")
    for bw, occ_pub, fft_pub, fs_pub in [(10, 8.64, 512, 15.36), (20, 18.36, 1024, 30.72),
                                         (50, 47.88, 2048, 61.44), (100, 98.28, 4096, 122.88)]:
        rb = RB_AT_30K[bw]
        occ = rb * 12 * 30 / 1000                  # MHz
        nfft = fft_size(rb)
        fs = nfft * 30 / 1000                      # MHz
        hit = (abs(occ - occ_pub) < 0.005 and nfft == fft_pub and abs(fs - fs_pub) < 0.005
               and occ < bw)                       # 점유 대역이 채널을 넘지 않는가
        ok &= hit
        print(f"  {bw:>4} MHz {rb:>5} {occ:>8.2f} MHz {nfft:>7} {fs:>8.2f} MHz   {'✓' if hit else '✗ 불일치'}")

    # 자료의 주장: 대역은 5.35배 줄었는데 표본화율은 4배만 줄어든다 (FFT가 2의 거듭제곱이라)
    wide, narrow = fft_size(273), fft_size(51)
    eq("표본화율 비 100→20 MHz", wide / narrow, 4.0, 0.005)
    eq("FFT 일감 비 N·log2N", (wide * math.log2(wide)) / (narrow * math.log2(narrow)), 4.8, 0.005)
    eq("RB 비 273/51", 273 / 51, 5.35, 0.005)
    ok &= (273 / 51) > (wide / narrow)
    print(f"  RB 비가 표본화율 비보다 크다(2의 거듭제곱 계단)  "
          f"{'✓' if (273/51) > (wide/narrow) else '✗ 자료의 주장과 다름'}")

    print("\n[05] BWP 전환 지연 — TS 38.133 §8.6.2 Table 8.6.2-1")
    print(f"  {'μ':>2} {'슬롯':>9} {'타입1':>16} {'타입2':>16}   게시값")
    for mu, (t1_pub_ms, t2_pub_ms) in [(0, (1.00, 3.00)), (1, (1.00, 2.50)),
                                       (2, (0.75, 2.25)), (3, (0.75, 2.25))]:
        slot = 1 / 2**mu
        n1, n2 = BWP_DELAY[mu]
        a, b = n1 * slot, n2 * slot
        hit = abs(a - t1_pub_ms) < 0.005 and abs(b - t2_pub_ms) < 0.005
        ok &= hit
        print(f"  {mu:>2} {slot:>7.3f}ms {n1:>7}슬롯 {a:>5.2f}ms {n2:>7}슬롯 {b:>5.2f}ms   "
              f"{'✓' if hit else '✗ 불일치'}")

    # 자료의 핵심 주장: 슬롯 수는 μ에 따라 늘지만 실제 시간은 바닥을 친다 (06의 N1과 반대)
    for typ, floor_pub in [(1, 0.75), (2, 2.25)]:
        idx = 0 if typ == 1 else 1
        times = [BWP_DELAY[mu][idx] / 2**mu for mu in sorted(BWP_DELAY)]
        slots = [BWP_DELAY[mu][idx] for mu in sorted(BWP_DELAY)]
        rising = all(slots[i] < slots[i + 1] for i in range(len(slots) - 1))
        flat = abs(times[-1] - times[-2]) < 1e-9        # μ=2와 μ=3이 같은 시간
        hit = rising and flat and abs(min(times) - floor_pub) < 1e-9
        ok &= hit
        print(f"  타입{typ}: 슬롯 수 단조 증가 {slots} · 시간 바닥 {min(times):.2f} ms "
              f"(게시 {floor_pub}) · μ=2,3 동일  {'✓' if hit else '✗ 자료의 주장과 다름'}")

    print("\n[05] 설정 개수와 초기 BWP")
    # maxNrofBWPs = 4 와 DCI BWP 지시자 2비트가 서로 맞는가 (TS 38.331 / TS 38.212 §7.3.1)
    eq("BWP 지시자 2비트가 가리키는 수", 2**2, 4, 0)
    # CORESET#0 폭(24·48·96 RB)이 275 격자 안의 창문으로 성립하는가 — 초기 BWP가 여기서 나온다
    fits = all(1 <= n <= N_RB_MAX and 0 <= riv(0, n) <= 37949 for n in (24, 48, 96))
    ok &= fits
    print(f"  CORESET#0 폭 24·48·96 RB가 275 격자 위 창문으로 성립  {'✓' if fits else '✗'}")

    return ok


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
