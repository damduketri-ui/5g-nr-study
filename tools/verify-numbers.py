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

    print("\n전체:", "통과" if ok else "실패 — 자료의 표를 확인할 것")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
