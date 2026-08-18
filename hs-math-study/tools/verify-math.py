#!/usr/bin/env python3
"""자료에 실린 값과 주장을 식으로 되짚어 확인한다.

    python3 tools/verify-math.py

표준 라이브러리만 쓴다(설치 없이 돌아가야 한다).
새 챕터를 쓰면 check_NN_...() 를 만들어 main() 에 등록할 것.

확인 방식은 두 가지다.
  1. 대수 항등식  — 여러 x에 대입해 좌변과 우변이 같은지
  2. 완력 표본    — 최대·최소라고 게시한 값이 정말 그 구간의 최대·최소인지
     (공식을 다시 쓰는 게 아니라, 공식을 안 쓰고 세어 보는 방식이라야 검산이 된다)
"""

import math

TOL = 1e-9


def frange(a, b, n):
    return [a + (b - a) * i / n for i in range(n + 1)]


def ok_mark(hit):
    return '✓' if hit else '✗ 불일치'


# ══════════ 01 이차함수의 최대·최소 ════════════════════════════════
# 근거: 2022 개정 교육과정 「공통수학1」 방정식과 부등식
#       완전제곱식  ax²+bx+c = a(x + b/2a)² − (b²−4ac)/4a   (a ≠ 0)

def vertex(a, b, c):
    """꼭짓점 (−b/2a, −D/4a) — 자료가 유도한 공식 그대로"""
    d = b * b - 4 * a * c
    return -b / (2 * a), -d / (4 * a)


def brute_extreme(a, b, c, lo, hi, n=400_000):
    """공식을 쓰지 않고 구간을 훑어 최대·최소를 찾는다 (검산의 기준선)"""
    best = worst = None
    for x in frange(lo, hi, n):
        y = a * x * x + b * x + c
        if best is None or y > best[1]:
            best = (x, y)
        if worst is None or y < worst[1]:
            worst = (x, y)
    return best, worst


# 자료에 게시된 값 ─────────────────────────────────────────────
PUB_VERTEX = (3.0, -4.0)          # y = x²−6x+5 → (x−3)²−4
PUB_ROOTS = (1.0, 5.0)
PUB_D = 16.0

# (범위, 최댓값, 최댓값의 x, 최솟값, 최솟값의 x)
PUB_RANGES = [
    ((0, 2),  5.0, 0.0, -3.0, 2.0),
    ((2, 6),  5.0, 6.0, -4.0, 3.0),
    ((4, 6),  5.0, 6.0, -3.0, 4.0),
]

# 그림에 손으로 박아 넣은 픽셀 좌표 — 매핑식으로 되짚는다
#   그림1  X(x) = 140 + 30x, Y(y) = 240 − 30y
#   그림3  X(x) =  76 + 30x, Y(y) = 240 − 30y
PUB_PIXELS = [
    ("그림1 꼭짓점 (0,0)",   1, (0, 0),   (140, 240)),
    ("그림1 꼭짓점 (3,−4)",  1, (3, -4),  (230, 360)),
    ("그림1 근 (1,0)",       1, (1, 0),   (170, 240)),
    ("그림1 근 (5,0)",       1, (5, 0),   (290, 240)),
    ("그림1 y절편 (0,5)",    1, (0, 5),   (140, 90)),
    ("그림3 꼭짓점 (3,−4)",  3, (3, -4),  (166, 360)),
    ("그림3 f(0)=5",         3, (0, 5),   (76, 90)),
    ("그림3 f(2)=−3",        3, (2, -3),  (136, 330)),
    ("그림3 f(6)=5",         3, (6, 5),   (256, 90)),
    ("그림3 원점",           3, (0, 0),   (76, 240)),
]


def check_01_identity():
    """① ax²+bx+c 와 완전제곱식이 정말 같은 식인가"""
    ok = True
    print("\n[01] 완전제곱식 항등 확인 — 두 표현이 모든 x에서 같은 값인가")
    cases = [(1, -6, 5), (1, 0, 0), (2, 5, -3), (-1, 4, 1), (-0.5, 3, 7), (3, -7, 2)]
    for a, b, c in cases:
        p, q = vertex(a, b, c)
        worst = max(abs((a * x * x + b * x + c) - (a * (x - p) ** 2 + q))
                    for x in frange(-12, 12, 2000))
        hit = worst < 1e-9
        ok &= hit
        print(f"  a={a:>5} b={b:>5} c={c:>5} → y = {a}(x − {p:.4g})² + {q:.4g}"
              f"   최대오차 {worst:.2e}  {ok_mark(hit)}")
    return ok


def check_01_vertex_is_extreme():
    """② 꼭짓점이 정말 최대·최소인가 — 공식을 안 쓰고 훑어서 확인"""
    ok = True
    print("\n[01] 꼭짓점 = 실수 전체에서의 최대·최소 (완력 표본과 대조)")
    for a, b, c in [(1, -6, 5), (2, 5, -3), (-1, 4, 1), (-0.5, 3, 7)]:
        p, q = vertex(a, b, c)
        best, worst = brute_extreme(a, b, c, p - 20, p + 20, 200_000)
        got = worst if a > 0 else best          # a>0 이면 최소, a<0 이면 최대
        hit = abs(got[0] - p) < 1e-3 and abs(got[1] - q) < 1e-6
        ok &= hit
        kind = '최솟값' if a > 0 else '최댓값'
        print(f"  a={a:>5} b={b:>5} c={c:>5} → 공식 {kind} {q:>9.4f} (x={p:.4f}) / "
              f"표본 {got[1]:>9.4f} (x={got[0]:.4f})  {ok_mark(hit)}")
    return ok


def check_01_discriminant():
    """③ q = −D/4a 이고, D의 부호가 x축과의 교점 수를 그대로 말하는가"""
    ok = True
    print("\n[01] 꼭짓점 y좌표와 판별식 — q = −D/4a,  a>0이면 (D>0 ⟺ q<0)")
    bad = 0
    for a in [x / 4 for x in range(-8, 9)]:
        if a == 0:
            continue
        for b in range(-6, 7):
            for c in range(-6, 7):
                d = b * b - 4 * a * c
                p, q = vertex(a, b, c)
                if abs(q - (-d / (4 * a))) > TOL:
                    bad += 1
                # a>0: 접시 바닥이 x축 아래(q<0) ⟺ 두 점에서 만난다(D>0)
                if a > 0 and (d > TOL) != (q < -TOL):
                    bad += 1
                if a < 0 and (d > TOL) != (q > TOL):
                    bad += 1
    hit = bad == 0
    ok &= hit
    print(f"  a·b·c 격자 {17 * 13 * 13 - 13 * 13}가지 전수 확인, 어긋난 경우 {bad}건  {ok_mark(hit)}")

    p, q = vertex(1, -6, 5)
    d = (-6) ** 2 - 4 * 1 * 5
    r = [(6 - math.sqrt(d)) / 2, (6 + math.sqrt(d)) / 2]
    for lab, got, want in [("게시 꼭짓점 x", p, PUB_VERTEX[0]),
                           ("게시 꼭짓점 y", q, PUB_VERTEX[1]),
                           ("게시 D", d, PUB_D),
                           ("게시 근 작은쪽", r[0], PUB_ROOTS[0]),
                           ("게시 근 큰쪽", r[1], PUB_ROOTS[1])]:
        h = abs(got - want) < 1e-9
        ok &= h
        print(f"  {lab:<16} {got:>8.4f}  게시 {want:<8} {ok_mark(h)}")
    return ok


def check_01_restricted():
    """④ 범위가 잘렸을 때의 표 — 게시한 최대·최소가 정말 그 구간의 값인가"""
    ok = True
    print("\n[01] 제한된 범위에서의 최대·최소 (y = x²−6x+5, 완력 표본과 대조)")
    for (lo, hi), pmax, pxmax, pmin, pxmin in PUB_RANGES:
        best, worst = brute_extreme(1, -6, 5, lo, hi, 400_000)
        hit = (abs(best[1] - pmax) < 1e-6 and abs(best[0] - pxmax) < 1e-4 and
               abs(worst[1] - pmin) < 1e-6 and abs(worst[0] - pxmin) < 1e-4)
        ok &= hit
        inside = lo <= PUB_VERTEX[0] <= hi
        print(f"  {lo} ≤ x ≤ {hi}  꼭짓점 {'안' if inside else '밖'}   "
              f"최대 {best[1]:>6.3f}(x={best[0]:.3f}) 게시 {pmax}(x={pxmax})   "
              f"최소 {worst[1]:>6.3f}(x={worst[0]:.3f}) 게시 {pmin}(x={pxmin})  {ok_mark(hit)}")

    # 자료의 주장: [0,2]와 [4,6]은 대칭축 x=3에 대해 거울상이라 값이 같다
    a1 = brute_extreme(1, -6, 5, 0, 2, 200_000)
    a2 = brute_extreme(1, -6, 5, 4, 6, 200_000)
    mirror = (abs(a1[0][1] - a2[0][1]) < 1e-6 and abs(a1[1][1] - a2[1][1]) < 1e-6 and
              abs((3 - a1[0][0]) - (a2[0][0] - 3)) < 1e-3)
    ok &= mirror
    print(f"  [0,2]와 [4,6]은 x=3에 대한 거울상 — 값 같고 위치 뒤바뀜  {ok_mark(mirror)}")

    # 자료의 주장: 꼭짓점이 범위 밖이면 답은 반드시 양 끝점에서 나온다
    off = 0
    for lo in range(-2, 3):
        for w in (1, 2, 3):
            hi = lo + w
            if lo <= 3 <= hi:
                continue
            best, worst = brute_extreme(1, -6, 5, lo, hi, 100_000)
            for x, _ in (best, worst):
                if min(abs(x - lo), abs(x - hi)) > 1e-4:
                    off += 1
    ok &= off == 0
    print(f"  꼭짓점 밖 구간에서 최대·최소는 항상 양 끝점 — 예외 {off}건  {ok_mark(off == 0)}")
    return ok


def check_01_pixels():
    """⑤ 그림에 박아 넣은 픽셀 좌표가 캡션의 매핑식과 맞는가"""
    ok = True
    print("\n[01] SVG 좌표 검산 — 그림1 X=140+30x · 그림3 X=76+30x · 공통 Y=240−30y")
    for lab, fig, (x, y), (px, py) in PUB_PIXELS:
        gx = (140 if fig == 1 else 76) + 30 * x
        gy = 240 - 30 * y
        hit = abs(gx - px) < 0.5 and abs(gy - py) < 0.5
        ok &= hit
        print(f"  {lab:<20} 계산 ({gx:>6.1f},{gy:>6.1f})  게시 ({px},{py})  {ok_mark(hit)}")
    return ok


def main():
    print("고1 수학 직관 — 수치·주장 검산")
    ok = True
    ok &= check_01_identity()
    ok &= check_01_vertex_is_extreme()
    ok &= check_01_discriminant()
    ok &= check_01_restricted()
    ok &= check_01_pixels()
    print("\n전체:", "통과" if ok else "실패 — 자료의 값을 확인할 것")
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
