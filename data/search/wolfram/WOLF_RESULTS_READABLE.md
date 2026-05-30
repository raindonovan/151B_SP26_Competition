# WOLF_RESULTS_READABLE.md — Readable log of all processed items
**Rows**: 316 processed (272 verified/DONE, 43 inconclusive, 1 disputed) across batches B1-B18 + WEBSEARCH.
Readable companion to `WOLF_RESULTS.csv` (the full machine-readable scorecard for all 943).

| ID | Batch | Confidence | Answer (truncated) | Notes |
|-------|-------|------------|---------------------|-------|
| 0005 | B2 | HIGH | 541.3, 63.25, 135.325, 4.2167, 32.09 | ANOVA 5-tuple; under-count |
| 0009 | B1 | HIGH | L-8x, 6F | 2-slot numerator/denominator split; format risk |
| 0012 | B2 | HIGH | 2c + 4p = 70, 11 | equation+value; string-match risk on equation form |
| 0068 | B2 | HIGH | -2.857, 6.986, -1.082, 3.707, -3.707, A, -12.647,  | 8-slot paired t-test; slot1 was completely wrong (5.443) |
| 0134 | B2 | HIGH | 1, 5, 12, 20, 26, 30, 31, 27.63 | 7 cumulative freqs + median; severe under-count |
| 0192 | B2 | HIGH | 1.06, (1.88, infty), 0.1449, A | z-test 4-slot; note infty notation |
| 0257 | B2 | HIGH | 2.52, 3.00, A | CI + MCQ 3-slot |
| 0353 | B3 | HIGH | 8, C, 5 and 7, D | table lookup; format risk on '5 and 7' vs '5, 7' |
| 0385 | B3 | HIGH | A, A, A | 3-slot sampling design MCQ; all answers A |
| 0413 | B3 | HIGH | 0.89, (1.83, infty), 0.2008, A | paired t 4-slot; watch LaTeX \text{A} wrap risk |
| 0435 | B1 | HIGH | 0.4457, 0.5368, A | CI bounds + MCQ; under-count missing letter |
| 0469 | B3 | HIGH | s^2, 0.1575A, 0.1575s^2, C, 81, square feet, 14.17 | 10-slot composition; includes units-as-slots |
| 0479 | B1 | HIGH | 40.36, 43.64, 40.01, 43.99 | 90%+95% CI 4-slot; model emitted only 95% bounds |
| 0487 | B3 | HIGH | -21.1, -0.9636 | covariance + correlation 2-slot |
| 0495 | B3 | HIGH | 100, 100, 200, 0.255, 5.991, B | chi-sq GoF 6-slot |
| 0499 | B4 | HIGH | 36.9, 0.3225, 32.25, 2.149 | exponential growth 4-slot |
| 0519 | B4 | HIGH | 426.3, 5090, 98.30 | population model 3-slot |
| 0548 | B1 | HIGH | 1.20x = 144, $120.00 | equation+value; risk on equation string form |
| 0578 | B1 | HIGH | 7.62, 9.00, 95.44 | CI+confidence 3-slot |
| 0585 | B4 | PARTIAL | -0.2235, 2.262, -2.262, No | slot 5 unknown (interpretation phrase) |
| 0587 | B4 | HIGH | B, C, D, E, F, J, C, A, B, B | 4 sub-parts multi-select; last slot = B (centring effect) |
| 0591 | B4 | HIGH | 1.081, 1.683, 1.819, -0.832, 3.162, -0.322, 4.123, | trig identity expansion 8-slot; note negative slot 4 |
| 0622 | B4 | PARTIAL | 3.854, 2.567, Yes | slot 4 unknown (interpretation phrase) |
| 0633 | B5 | HIGH | B, D, 8 | multi-select + value 3-slot |
| 0638 | B5 | HIGH | 0.15, (-infty, -1.75)U(1.75, infty), 0.88, D | proportion z-test 4-slot |
| 0657 | B5 | HIGH | 172.52, 187.48, 172.87, 187.13, 0, 5.167, -10.33,  | difference of means 8-slot |
| 0715 | B5 | HIGH | 5, 7, 9, 13, 8.5, 6, 7, 8, 9, 10, 11, 8.5 | sampling distribution 4-slot (lists as slots); format risk |
| 0721 | B5 | HIGH | D, A, A | 3-slot CLT/sampling MCQ |
| 0748 | B5 | HIGH | 222.51, 186.49, 79.43, 66.57, 50.05, 41.95, 31.01, | chi-sq independence 12-slot |
| 0749 | B6 | PARTIAL | 5, 5, 5, 5, 5, is, 14/9, 19/14, 24/19, 29/24, 34/2 | format uncertain; 6 ANS slots but exact slot boundaries uncl |
| 0787 | B1 | MEDIUM | 148,178,452, 41.55, 46.97 | discrete geometric 3-slot; format ambiguity on units |
| 0793 | B6 | HIGH | 1.35, (1.49, inf), 0.0895, D | t-test 4-slot; note 'inf' not 'infty' in notation |
| 0858 | B6 | PARTIAL | 2.300, 1.691, Yes | slot 4 unknown (interpretation phrase) |
| 0886 | B6 | HIGH | A, C | 2-slot ME scaling + n_req |
| 0894 | B6 | MEDIUM | 0.008, 1.783, 2.013, -0.091, 0.283, -0.100, 0.272, | regression PI 8-slot; question hints 9, verified 10 |
| 0917 | B6 | HIGH | 189.8, 246.4, 43 | CI + n_req 3-slot |
| 0924 | B7 | HIGH | n = 55 + 0.2t, 2010 | linear model + year 2-slot |
| 0929 | B7 | HIGH | 5.860, (-0.78, 3.18), A | pooled t CI + MCQ 3-slot; nB=11 (13-2 excluded) |
| 0011 | B8 | consensus-only | 0.939 | truncated problem text; verify against source |
| 0040 | B8 | HIGH | D = 800 - 50d | missing LHS prefix; Qwen failure=missing-prefix |
| 0067 | B8 | HIGH | 7.6(1.09)^t, 13.9, 5.4 | exponential growth 3-slot; Qwen under-counted |
| 0072 | B8 | HIGH | -0.8352, -0.9187, 0.3950, -2.3258, Quadrant IV | trig 5-slot; full label required |
| 0089 | B8 | HIGH | \frac{326}{7} | fraction vs decimal |
| 0100 | B8 | HIGH | \frac{180}{7} | fraction vs decimal |
| 0103 | B8 | HIGH | 8\sqrt{2} | exact form vs decimal |
| 0106 | B8 | HIGH | \frac{13}{6} | fraction vs decimal |
| 0118 | B8 | HIGH | \frac{18}{5} | fraction vs decimal |
| 0124 | B8 | HIGH | H | Putnam 2018 A2; Qwen=G missed z=1 edge case |
| 0167 | B8 | HIGH | Negative, Negative, Positive, Negative | words not letters; Qwen failure=letter-vs-word |
| 0181 | B8 | HIGH | A | symmetry proof; only symmetric matrix; Qwen=B wrong |
| 0218 | B8 | HIGH | \arcsin\!(\frac{7}{10}) | exact form vs decimal |
| 0233 | B8 | HIGH | 1.96, -1.96, -5.18, B | hypothesis test 4-slot; Qwen under-counted |
| 0247 | B8 | HIGH | \frac{2409}{65}, \frac{2474}{1+\frac{2409}{65}e^{- | logistic 3-slot; Qwen under-counted |
| 0317 | B8 | HIGH | D | dataset quirk — D and H identical; only D accepted |
| 0395 | B8 | HIGH | \frac{85}{3}, -\frac{95}{4}, -\frac{10}{7} | rate-of-change fractions |
| 0454 | B8 | HIGH | 1.5, 0.9375 | GPA trailing zeros |
| 0496 | B8 | HIGH | 9.594^\circ | bearing; degree symbol required |
| 0506 | B8 | HIGH | J | balanced primes MCQ |
| 0584 | B8 | HIGH | 7z, 6w | symbolic form; Qwen substituted z=w=1 |
| 0884 | B8 | HIGH | g(x)=(x-59)^2+74 | prefix required; g(x)= form |
| 0902 | B8 | HIGH | 9, 6 | simplified radical ratio |
| 0041 | WEBSEARCH | HIGH | 2112 | IMO 2025 P6 (Matilda tiles). ALL 5 teachers wrong (3986/4048 |
| 0117 | WEBSEARCH | HIGH | B | Putnam 2021 A5. Answer = 2020 = option B. All 5 teachers agr |
| 0120 | WEBSEARCH | HIGH | 8 | Polya theorem on fixed divisors. 4/5 teachers agreed. Free-f |
| 0125 | WEBSEARCH | HIGH | G | Putnam 2016 A1; value=8 confirmed; MCQ option G (index 6 of  |
| 0141 | WEBSEARCH | DISPUTED | 0 | Putnam 1989 A-1 base-7 variant: math gives 0 primes but 0 is |
| 0000 | B9 | HIGH | 4, 16 | order-of-ops 2-slot; best=16 is undercount |
| 0002 | B9 | HIGH | -1.461, 1.645, A | z-prop-test 3-slot; z=-1.461 confirmed; best/teacher ag |
| 0004 | B9 | HIGH | -7/sqrt(149), 10/sqrt(149), -7/10 | trig on terminal point; exact form; best(decimals)=teac |
| 0016 | B9 | INCONCLUSIVE | INCONCLUSIVE | game theory on 1001-gon; not Wolfram-computable; teache |
| 0017 | B9 | HIGH | 181 | least odd prime of a(2015); mod181=0 confirmed; mod3,5, |
| 0020 | B9 | HIGH | 228, 229, 250 | mean/median/mode; Wolfram confirmed; best=229 is 2-slot |
| 0024 | B9 | HIGH | 1 | sum squared residuals=1; teacher correct; best=2 is wro |
| 0025 | B9 | HIGH | 8/63, 2/21, 11/63, 17/63, 13/63, 8/63, 8, 14, 25, 42, 5 | rel-freq+cumul-freq 12-slot; best=6 slots (cumul only), |
| 0029 | B9 | HIGH | 38.2 | yellow tint pct: 26/68=38.24% rounded to 1dp=38.2; best |
| 0032 | B9 | HIGH | sqrt(101), -1, -7/2 | distance=sqrt(101), midpoint=(-1,-7/2); best(decimals)  |
| 0049 | B9 | HIGH | 0.0143 | type-II error beta; P(Z>=2.189)=0.01430; best=0.01433 a |
| 0058 | B9 | INCONCLUSIVE | INCONCLUSIVE | functional-equation competition problem; not Wolfram-co |
| 0077 | B9 | INCONCLUSIVE | INCONCLUSIVE | study-design MCQ 3-slot; conceptual; not Wolfram-verifi |
| 0104 | B9 | HIGH | 2387*pi/1800 | arc length r=7.7 theta=31deg; =4.1661 units; teacher(ex |
| 0105 | B9 | HIGH | 24, 9.114 | range=24 ssd=9.114 confirmed; teacher/best agree |
| 0113 | B9 | HIGH | (-2x^2-16x-7)/25 | cos(2theta) trig-sub; equiv to (25-2(x+4)^2)/25; teache |
| 0135 | B9 | HIGH | 3/5 | solve 8x+2=3x+5; x=3/5; best=36 is CATASTROPHICALLY WRO |
| 0136 | B9 | MED | A, C | percent-freq MCQ 2-slot; slot1=A(×100), slot2=C(n eleme |
| 0154 | B9 | HIGH | 18.75 | paint cost: 488sqft/100*$3.75=$18.75; teacher/best agre |
| 0171 | B9 | HIGH | 20 | area of rect {3<=x<=7, 2<=y<=7}=4*5=20; best=21 is wron |
| 0177 | B9 | HIGH | pi^2/6 | vol of rotation; solve func eq -> f(x)=x/sqrt(1+x^2); V |
| 0188 | B9 | HIGH | 60, 60, 60 | mean=median=mode=60; Wolfram confirmed; best=61 is wron |
| 0196 | B9 | HIGH | 14.7447, 10.3244, 35 | right-tri: a=18sin55=14.7447, b=18cos55=10.3244, B=35;  |
| 0201 | B9 | HIGH | (5t+8)^2 | factor 25t^2+80t+64=(5t+8)^2; teacher/best equivalent f |
| 0208 | B9 | HIGH | 16.2, 720/(49*pi) | r1=81/5=16.2, r2=720/(49pi); teacher/best agree (81/5=1 |
| 0214 | B10 | HIGH | 11, F, 10, T | primality check: floor(sqrt(121))=11 (F, not prime), fl |
| 0227 | B10 | HIGH | A, C | matched pairs df=9=option A; pooled variance=C; best sl |
| 0240 | B10 | HIGH | 12, 4.9, 3.3 | spring oscillation: period=12s, midline=4.9ft, amplitud |
| 0243 | B10 | HIGH | 0.8925, 0.2150 | p-val z=1.24: left-tail P=Phi(1.24)=0.8925; two-tail P= |
| 0255 | B10 | INCONCLUSIVE | INCONCLUSIVE | OEIS tiling 4x2n L-tetrominoes for n=15..24; Wolfram ca |
| 0263 | B10 | HIGH | -63/16 | tan(arcsin(3/5)+arccos(5/13))=-63/16=-3.9375; Wolfram c |
| 0269 | B10 | HIGH | 1.789, 0.3198, B | t_crit df=47 alpha=0.04 = 1.789 (teacher~1.79 correct;  |
| 0271 | B10 | HIGH | -4, 0, 4 | 4a^6=64a^4 -> 4a^4(a^2-16)=0 -> a=-4,0,4; best=4 is sev |
| 0287 | B10 | HIGH | 212, 136 | sample size: a) p=0.5 n=212; b) p=0.8 n=136; best=136 i |
| 0296 | B10 | HIGH | 45, 180, 270 | lawn width=45, factory=180x270; teacher/best agree (val |
| 0301 | B10 | HIGH | 0.878, 57.2 | logistic: pi(43)=0.878; dist at pi=0.6: x=57.2; best sl |
| 0313 | B10 | HIGH | -2*sqrt(14)/15 | unit circle Q4: y=-sqrt(1-(13/15)^2)=-2sqrt(14)/15; bes |
| 0319 | B10 | HIGH | False, True, True, False | T/F stats statements; teacher/best agree (different not |
| 0322 | B10 | HIGH | 40, 25, 1000 | sheep pens optimization: L=40ft, w=25ft, area=1000ft^2; |
| 0345 | B10 | HIGH | -5/6, 5/6 | /12x/=10 -> x=pm10/12=pm5/6; teacher/best agree (exact  |
| 0347 | B10 | INCONCLUSIVE | INCONCLUSIVE | 9x9 tiling with 1x3 tiles, N mod 1000; hard combinatori |
| 0369 | B10 | HIGH | 3/4, 5, 2 | vertex form: a=3/4, h=5, k=2; teacher/best agree (fract |
| 0372 | B10 | HIGH | 0.51 | ME=1.96*20.58/sqrt(6377)=0.5051~0.51; teacher correct;  |
| 0382 | B10 | HIGH | 187/18, 55/9 | room dims: l=187/18~10.39m, w=55/9~6.11m; teacher/best  |
| 0386 | B10 | INCONCLUSIVE | INCONCLUSIVE | combinatorics/geometry problem; teacher=3, best=5; not  |
| 0397 | B10 | HIGH | 256*pi, 2048*pi/3 | sphere r=8: SA=4pi*64=256pi~804.2; V=4/3*pi*512=2048pi/ |
| 0404 | B10 | HIGH | 52 | prime outcomes {2,3,5}: (6+10+10)/50*100=52%; teacher/b |
| 0411 | B10 | HIGH | 392*pi/45 | arc: r=8, 196deg -> s=8*196pi/180=392pi/45~27.37; teach |
| 0421 | B10 | HIGH | -9*sqrt(5)/20, -sqrt(5)/20 | sec=1/cos=-9/(4sqrt(5))=-9sqrt(5)/20; tan=-sqrt(5)/20;  |
| 0437 | B10 | HIGH | 76.37, 79.63 | 95% CI: ME=1.96*17/sqrt(420)=1.626; (78-1.63,78+1.63)=( |
| 0438 | B11 | HIGH | 5, 9, 1, 10, 2, 0, 10, x^3y^7, 1 | poly terms/coeff/degree 9-slot; slot9=leading coeff=1;  |
| 0443 | B11 | INCONCLUSIVE | INCONCLUSIVE | Q(8) mod 1000 competition problem; not Wolfram-computab |
| 0444 | B11 | HIGH | 113, 35, 112, 61, 148, 43 | division: 9075=113*80+35, 8685=112*77+61, 8331=148*56+4 |
| 0447 | B11 | HIGH | x <= 4 | x<=6 AND x<=4 -> x<=4; teacher/best agree (different no |
| 0450 | B11 | INCONCLUSIVE | INCONCLUSIVE | equiangular hexagon competition problem; teacher=I, bes |
| 0461 | B11 | HIGH | 2, 302 | range rule std=8/4=2; n=(z97*sigma/ME)^2=ceil((2.17*2/0 |
| 0488 | B11 | INCONCLUSIVE | INCONCLUSIVE | Linetown orientation competition: 2025-line acyclic ori |
| 0492 | B11 | HIGH | A, A | R^2=0.9^2=0.81=81% variation explained->A; slot2=A; bes |
| 0501 | B11 | INCONCLUSIVE | INCONCLUSIVE | GCD subset sum competition; teacher=F, best=INVALID; no |
| 0503 | B11 | HIGH | y=-43000x+833000, 446000, 2019 | slope=-43000, f(9)=446000, depleted year 2019; best="44 |
| 0505 | B11 | HIGH | 1, 3, 6, -5, -4, 2 | Horner at x=-7: 1,3,6,-5,-4,2 confirmed; best=2 is seve |
| 0508 | B11 | HIGH | n(n-1)/2 | n students n races score = n(n-1)/2; teacher/best agree |
| 0535 | B11 | HIGH | -4, -6 | x^2/240+x/24+1/10=0 -> x^2+10x+24=0 -> x=-4,-6; teacher |
| 0539 | B11 | HIGH | 4, 5 | p(4)=-100 (neg), p(5)=800 (pos) -> root between 4 and 5 |
| 0540 | B11 | INCONCLUSIVE | INCONCLUSIVE | AR(1) process MCQ 3-slot; teacher=A,B,C, best=A,C,C; sl |
| 0557 | B11 | HIGH | 5 | /5/=5 trivially; best=6 is WRONG (trivial error) |
| 0558 | B11 | HIGH | f(x)=(13/2)x-25 | linear fn f(250)=1600, f(650)=4200: slope=13/2, b=-25;  |
| 0583 | B11 | INCONCLUSIVE | INCONCLUSIVE | rectangle cut competition (2024x2025); teacher=119, bes |
| 0593 | B11 | HIGH | 19.4 | bearing navigation: d=15.5*sin(43.4)/sin(96.1)*cos(52.5 |
| 0595 | B11 | MED | A, D, E, G, probability | logistic likelihood MCQ: A(deviance>=0),D(logL<=0),E(L< |
| 0598 | B11 | INCONCLUSIVE | INCONCLUSIVE | quadratic form to standard form; hard linear algebra; t |
| 0599 | B11 | HIGH | 1.81 | SE=8.5/sqrt(22)=1.812; teacher=1.81, best=1.8123; all a |
| 0606 | B11 | HIGH | 181 | least odd prime of y_25 (same recurrence as 0017); y_25 |
| 0607 | B11 | HIGH | 0, 0, 4, 0, 0, 14, 6, 6, 20, -6, -6, 0, -4, -4, 10, -4, | sphere centers 18-slot; teacher/best agree (same values |
| 0608 | B11 | HIGH | B, A, A, 1981 | time-vs-year: B(not fn), A(fn), A(record meaning), 1981 |
| 0610 | B12 | INCONCLUSIVE | INCONCLUSIVE | complex plane perimeter; competition; teacher=4pi, best |
| 0620 | B12 | HIGH | 4/sqrt(7), 16/7, 2.167, B | chi-sq test: s=4/sqrt(7), chi2=16/7, crit=2.167(df7,alp |
| 0642 | B12 | HIGH | 6, pi/3, 13 | y=7+6cos(6x): amp=6, period=2pi/6=pi/3, max=7+6=13; tea |
| 0646 | B12 | INCONCLUSIVE | INCONCLUSIVE | Taylor error bound MCQ; teacher=A, best=J; not computed |
| 0647 | B12 | INCONCLUSIVE | INCONCLUSIVE | OEIS period-of-reciprocal MCQ; teacher=J, best=B |
| 0655 | B12 | HIGH | S = 0.85*L | 15% discount: S=0.85L; trivial; best=1 is completely wr |
| 0675 | B12 | INCONCLUSIVE | INCONCLUSIVE | OEIS Hurwitz-Radon MCQ; teacher=B, best=INVALID |
| 0676 | B12 | MED | D, A, A | study design MCQ 3-slot; teacher correct; best=A (1 of  |
| 0679 | B12 | HIGH | 11 | silo radius: 40pi*r^2+(2/3)pi*r^3=18000 -> r=11.002~11; |
| 0681 | B12 | HIGH | 28900, 170, 135, 205 | artist revenue: max=28900 at price=170; 135/205 are sym |
| 0682 | B12 | INCONCLUSIVE | INCONCLUSIVE | ordered triples GCD competition; teacher=G, best=INVALI |
| 0684 | B12 | HIGH | -1.55 | critical z left-tail alpha=0.06: InvNorm(0.06)=-1.555;  |
| 0690 | B12 | HIGH | 5.2340 | log_pi(400)=ln(400)/ln(pi)=5.2340; value confirmed; MCQ |
| 0695 | B12 | INCONCLUSIVE | INCONCLUSIVE | infinitesimals comparison; teacher=E, best=INVALID; not |
| 0696 | B12 | HIGH | x+8, -81 | complete square: x^2+16x-17=(x+8)^2-81; teacher="x+8,-8 |
| 0700 | B12 | INCONCLUSIVE | INCONCLUSIVE | reciprocity sum competition; teacher=F, best=A; not Wol |
| 0704 | B12 | HIGH | 3.652, 1.645, B | proportion z-test 3-slot; teacher/best agree (minor rou |
| 0712 | B12 | INCONCLUSIVE | INCONCLUSIVE | herbal tea study design MCQ 3-slot; conceptual; teacher |
| 0716 | B12 | HIGH | 19/33 | R^2=SSR/(SSR+SSE)=95/165=19/33; Wolfram confirmed; best |
| 0720 | B12 | INCONCLUSIVE | INCONCLUSIVE | ODE truncation error proof; teacher=D, best=INVALID; re |
| 0723 | B12 | HIGH | -sqrt(3)/2, -sqrt(2)/2 | sin(300)=-sqrt(3)/2, sin(225)=-sqrt(2)/2; teacher/best  |
| 0727 | B12 | INCONCLUSIVE | INCONCLUSIVE | sum optimization competition; teacher=A, best=INVALID |
| 0751 | B12 | INCONCLUSIVE | INCONCLUSIVE | n-gon polygon count; teacher=31, best=45; competition |
| 0762 | B12 | HIGH | 2x(55x+21) | 8x*7x+6x*8x+7*6x+x*6x=110x^2+42x=2x(55x+21); teacher/be |
| 0772 | B12 | INCONCLUSIVE | INCONCLUSIVE | OEIS bell-ringing MCQ; teacher=H, best=J |
| 0781 | B13 | HIGH | sqrt(15)/8 | sqrt(3/8)*sqrt(5/8)=sqrt(15)/8; teacher/best agree |
| 0785 | B13 | HIGH | False, True, False, False | T/F stats; teacher=words, best=0/1 numeric (0.000=False |
| 0790 | B13 | HIGH | -20x^2+45x-25=0 | -5(4x-5)(x-1)=-20x^2+45x-25; teacher correct; best=INVA |
| 0794 | B13 | HIGH | 4.47, 4 | mean=85/19=4.47, median=4; teacher correct; best=5 is w |
| 0801 | B13 | INCONCLUSIVE | INCONCLUSIVE | projective space linear maps competition; teacher=G, be |
| 0818 | B13 | HIGH | 5a+6b, ab | 6/a+5/b=(6b+5a)/(ab); teacher/best agree (numerator+den |
| 0830 | B13 | HIGH | 44*pi/15 | arc: 3960*8/60*pi/180=44pi/15=9.215; teacher(exact)=bes |
| 0834 | B13 | HIGH | pi/4, 3*pi/2, -19*pi/6 | 45=pi/4, 270=3pi/2, -570=-19pi/6; teacher correct; best |
| 0836 | B13 | HIGH | 2025 | min chords of length 2025: continuous fn theorem gives  |
| 0851 | B13 | HIGH | B, C | y=-5/8 x: (0,0)->B, (-24,15)->C satisfy; teacher/best a |
| 0872 | B13 | HIGH | infinity, 0 | lim(t->-inf)(t^2+5)=inf; lim(y->inf)4y^-2=0; teacher co |
| 0880 | B13 | HIGH | 35/37, 35/12 | cos=12/37: sin=35/37, tan=35/12; teacher(exact)=best(de |
| 0887 | B13 | INCONCLUSIVE | INCONCLUSIVE | fuzzy logic min/max equation; teacher=I, best=C; not Wo |
| 0896 | B13 | HIGH | False,True,False,False,True,True,False,True | expr-vs-eqn T/F 8-slot; teacher=words, best=0/1 binary; |
| 0904 | B13 | INCONCLUSIVE | INCONCLUSIVE | fuzzy relation matrix composition; teacher=A, best=D; n |
| 0916 | B13 | HIGH | 3*sqrt(2), 6*sqrt(2), 18 | AB=3sqrt2, AC=6sqrt2, area=18; teacher(exact)=best(deci |
| 0927 | B13 | HIGH | False,True,True,True,False,False | log properties T/F 6-slot; teacher=words, best=0/1 bina |
| 0936 | B13 | HIGH | 275/16 | P(-4)=0 -> k=275/16; teacher correct; best=27517 is dig |
| 0010 | B13 | MED | 2*pi*rho/(rho^2-a^2) form | contour integral /dz///z-a/^2; standard result=2pi*rho/ |
| 0022 | B13 | INCONCLUSIVE | INCONCLUSIVE | polyhedron 37 faces vertex count; teacher/best both=G ( |
| 0030 | B13 | HIGH | 2944, 664 | sample size: a) p=0.5 n=2944; b) given p->664; teacher/ |
| 0033 | B13 | INCONCLUSIVE | INCONCLUSIVE | triangle orthocenter/circumcenter geometry; teacher/bes |
| 0042 | B13 | HIGH | No, Yes, A | P=0.095: a)5% No, b)10% Yes, c)A; teacher/best agree |
| 0044 | B13 | HIGH | True, True, True, False | regression T/F 4-slot; teacher/best agree |
| 0045 | B13 | INCONCLUSIVE | INCONCLUSIVE | OEIS male-offspring recurrence MCQ; teacher/best both=A |
| 0054 | B14 | MED | 1 | chessboard polygon a1>=a3+something; teacher+best agree |
| 0069 | B14 | HIGH | pi(4-pi)/2 | int_0^pi x sin^2 x/(1+sin x) dx = pi(4-pi)/2 = 1.3484;  |
| 0075 | B14 | HIGH | x > 21250 | Plan A vs B: 1100+0.11x vs 1450+0.09x -> x>21250 wait s |
| 0088 | B14 | MED | C | OEIS polynomial decomposition; teacher+best agree=C; no |
| 0108 | B14 | HIGH | 72, 12x | cos^2-sin^2=cos(2t): A=72, B=12x; teacher+best agree |
| 0110 | B14 | MED | 3, 9 | fox population sinusoid params; teacher+best agree=3,9 |
| 0111 | B14 | HIGH | 8x^3 | 4thrt(64x^5)*4thrt(64x^7)=4thrt(4096 x^12)=8x^3; teache |
| 0152 | B14 | MED | J | 4-fold sum max divided by 1000; teacher+best agree=J; c |
| 0164 | B14 | MED | G | polynomial f(x) property; teacher+best agree=G; competi |
| 0176 | B14 | HIGH | (p-6k-m)/8 | solve 8w+6k+m=p -> w=(p-6k-m)/8; teacher+best agree |
| 0211 | B14 | HIGH | 181 | least odd prime of q_255: mod3,5,7 nonzero, mod181=0; t |
| 0238 | B14 | HIGH | -61, 61, 62 | partial fractions: -61/x+61/x^2+62/(x+1); f=-61,g=61,h= |
| 0248 | B14 | MED | 180 | gnome field-of-view competition; teacher+best agree=180 |
| 0253 | B14 | MED | E | quadratic form eigenvalues a,b integers; teacher+best a |
| 0274 | B14 | MED | G | OEIS permutations of order 3; teacher+best agree=G; not |
| 0285 | B14 | MED | 147 | ordered triples a^3+b^3+c^3 div 3^7; teacher+best agree |
| 0299 | B14 | HIGH | 18805.7, no | wedding cost mean=18805.7, CI conclusion=no; teacher+be |
| 0306 | B14 | HIGH | 1 | lim x->0 ((1+tanx)/(1+sinx))^(1/sinx)=1; teacher+best=H |
| 0308 | B14 | MED | 12 | tangent circles competition (IMO-style); teacher+best a |
| 0339 | B14 | MED | G | power series of rational function; teacher+best agree=G |
| 0362 | B14 | HIGH | (6x-5y)(6x+5y) | factor 36x^2-25y^2=(6x-5y)(6x+5y); teacher+best agree |
| 0367 | B14 | HIGH | 60.3, 46.3, 53.3 | arcsin(0.8686)=60.3, arctan(1.0464)=46.3, arcsec(1.6733 |
| 0383 | B14 | MED | 80 | divisoral table competition; teacher+best agree=80 |
| 0389 | B14 | HIGH | (x^2+5x+5)^2-1 | (x+1)(x+2)(x+3)(x+4)=(x^2+5x+5)^2-1; teacher+best=F; fo |
| 0427 | B14 | MED | E | a^2+b^2=c^2+ab Heron competition; teacher+best agree=E |
| 0021 | B15 | HIGH | 0.2915t+56.93, 67.43 | regression L(t)=0.2915t+56.93; est=67.43; best=67.43 un |
| 0027 | B15 | HIGH | 1/3, 2/3, 7/6, 11/6 | sin=sqrt3/2->1/3,2/3; sin=-1/2->7/6,11/6; best="7/6,11/ |
| 0043 | B15 | HIGH | 3/8, 14, 28 | sin^4(7x)=3/8-1/2cos(14x)+1/8cos(28x); best correct (Tr |
| 0082 | B15 | MED | 1.309, 1.677, ?, No | two-sample t 4-slot; best="1.309,1.677,No" undercount 3 |
| 0157 | B15 | HIGH | 50sin(0.1t)-7cos(0.1t), 46.31 | spring SHM: x=-7cos(0.1t)+50sin(0.1t); x(13)=46.31; bes |
| 0194 | B15 | MED | 600.0, July, 1908, 890.0, March, 1907 | population poly extrema 6-slot; best has all 6; max/min |
| 0210 | B15 | HIGH | -(49sqrt3+16sqrt33)/15, 2x/(x^2+1) | tan(arcsin(4/7)+arccos(1/2))=-11.786 confirmed; best co |
| 0225 | B15 | MED | 0.6254, 4, 2.776, A | regression slope t-test 4-slot; best has all 4 slots; p |
| 0239 | B15 | HIGH | 35, 3.450 | add 2 values=mean: mean stays 35, std=sqrt(11*3.75^2/13 |
| 0242 | B15 | MED | 241.2, 239.5, 233, 221.7, 14.89, 6.173 | stock prices stats 6-slot; best has all 6; plausible |
| 0262 | B15 | HIGH | 850-50t, 1480-140t, 7 | F=850-50t, A=1480-140t, equal at t=7; best=7 undercount |
| 0273 | B15 | HIGH | -cos^2(x), 1, 2cos^2(x) | trig simplify: sin^2-1=-cos^2; sin^2+cos^2=1; cos^2+cos |
| 0281 | B15 | HIGH | -0.4618, 0.8870, -0.5206, -2.1655 | odd/even: sin(-x)=-0.4618,cos(-x)=0.8870,tan(-x)=-0.520 |
| 0297 | B15 | MED | 0.2372, (-inf,-1.881)U(1.881,inf), 0.8126, C | t-test 4-slot ball bearings; best has all 4; plausible |
| 0318 | B15 | HIGH | 8, 0.562 | P on circle r=8 -> r=8; y=64/15, theta=arcsin(y/8)=0.56 |
| 0320 | B15 | HIGH | approaches normal (limit 1), 3.73 | f(t)->1 as t->inf; 75% at t=2+sqrt3=3.73; best=3.73 und |
| 0325 | B15 | HIGH | [0,280], [0,14] | gas g(m)=14-0.05m; domain[0,280] range[0,14]; best="280 |
| 0417 | B15 | MED | 1.006, 0.9676, 28, 29.10, 1.039 | ANOVA table 5-slot; best has all 5; MS/F/df plausible |
| 0418 | B15 | MED | 2.958, 1.751, 0.001530, B | t-test GPA 4-slot; best has all 4; t=2.958 plausible (n |
| 0446 | B15 | HIGH | 1.87, 0.972 | regression: SE=1.87, R^2=0.972 (confirmed); best=0.9720 |
| 0449 | B15 | MED | 3.5850, 0.0003460, B | wristwatch t-test 3-slot; best has all 3; plausible |
| 0456 | B15 | MED | -7.740, A, B | two-pond salinity t-test 3-slot; best has all 3; plausi |
| 0467 | B15 | MED | 0.02667w+0.03333, 100<=w<=220, 0<=C<=6, 4.967 | calories-weight linear 4-slot; best has all 4; slope/do |
| 0468 | B15 | MED | ?, 0.8816 | astronaut orientation stat 2-slot; best=0.8816 undercou |
| 0470 | B15 | HIGH | 1.96, 2.201, 2.326, 2.718, 2.576, 3.106 | z/t for 95/98/99% CI df=11; best="2.576,3.106" undercou |
| 0490 | B16 | MED | 23, ... | cooling 6440/280=23 BTU/sqft const; best="23.00,410.0"  |
| 0491 | B16 | MED | 1255.37, 1091.15, 1419.59, No, Central Limit Theorem | flight-miles CI 5-slot; best has all 5; plausible |
| 0497 | B16 | HIGH | 1.111, 88.81, 88.81, 0.9004 | tan(48d)=1.111, arctan(48)=88.81, tan^-1(48)=88.81, cot |
| 0542 | B16 | MED | 285, [7457 pop / 8388 sample], [86.35 pop / 91.59 sampl | range=285 confirmed; var/std convention-dependent: best |
| 0553 | B16 | HIGH | 24, 1.6 | IQ diff=124-100=24; z=24/15=1.6; best=1.600 undercount  |
| 0555 | B16 | MED | 1.109, 0.1336 | poll proportion 2-slot n=1300; best plausible |
| 0586 | B16 | MED | 1.899, -0.9423, 0.1109, -0.02966 | cubic regression coeffs 4-slot; best has all 4 |
| 0601 | B16 | HIGH | (3s-1)(2s+1) | factor 6s^2+s-1=(3s-1)(2s+1); best correct |
| 0602 | B16 | MED | -70.8, 0.719, 53.6 | supermodel ht/wt regression 3-slot; best plausible |
| 0619 | B16 | MED | -3.226, 0.001230, A | two-sample t-test 3-slot; best plausible |
| 0666 | B16 | HIGH | 76*1.532^t, 42.68 | exp model: S(t)=76*(419/76)^(t/4)=76*1.532^t; best=42.6 |
| 0680 | B16 | MED | 0.035, 0.0525, 0.0775, A | avg rates of change 4-slot; best has all 4; (21.64-21.5 |
| 0713 | B16 | HIGH | -3, not real | -5thrt(243)=-3; 4thrt(-81)=not real; best correct |
| 0718 | B16 | HIGH | 65761800, 72704000, median(better) | mean=65,761,800 median=72,704,000; outlier 1200 -> medi |
| 0725 | B16 | MED | 41.30, 13.28, A | chi-square gender/dept 3-slot; best plausible |
| 0753 | B16 | MED | ..., 16.56 | Steadia linear pop 4-slot; best=16.56 undercount 1of4 |
| 0842 | B16 | MED | 65.47, 1.552, 6.052, 1.833, B | chicken-weight t-test 5-slot; best has all 5 |
| 0857 | B16 | MED | A, 0.8974, 0.9146, A, 0.9015, 0.9221 | M&M weights 6-slot; best has all 6 |
| 0885 | B16 | HIGH | 18, 139.875, 18, B | mode=18, mean=1119/8=139.875, median=18, Mean(B) fails  |
| 0914 | B16 | HIGH | (0.190, 0.247) | 95% CI prop: 175/800 +/- 1.96*SE = (0.1901, 0.2474); be |
| 0923 | B16 | MED | 93, 48, ... | gas-leak linear 3-slot; best="93,48" undercount 2of3 |
| 0015 | B16 | HIGH | 8, NONE | x^8+4 degree 8; 8^x+4 not poly NONE; best correct |
| 0035 | B16 | HIGH | down, ln(p) | horiz stretch p of ln(x): ln(x/p)=ln(x)-ln(p) -> down b |
| 0046 | B16 | MED | 1.645, 1.719, 1.960, -1.960, 1.719, B, A | hypothesis test 7-slot; best has all 7; z-crit/stat pla |
| 0050 | B16 | HIGH | 140A+150B=5930, 3A+4B=142 | apple/banana system; best correct (calories + fiber equ |
| 0056 | B17 | MED | D, D, A | regression concept MCQ 3-slot; best all slots present |
| 0063 | B17 | HIGH | 15.84, 18.96 | 92.4% CI: mean=17.4, s=2.413, t(9)~2.045 -> (15.84,18.9 |
| 0097 | B17 | HIGH | 0, 4, 4 | r=8sinθ -> x^2+(y-4)^2=16; center(0,4) r=4; best correc |
| 0099 | B17 | HIGH | -6, 12, -6 | -/3-9/=-6; /-3-9/=12; -1/9-3/=-6; best correct |
| 0101 | B17 | MED | C, C, A, C | hypothesis test concept MCQ 4-slot; best all slots pres |
| 0119 | B17 | MED | A, C, B, D | quadrant matching 4-slot; best all slots present |
| 0129 | B17 | HIGH | 5/sin(t), sqrt(7), -3cos(t), 2sqrt(2)tan(t) | polar conversions: y=5->r=5/sint; x^2+y^2=7->r=sqrt7; b |
| 0133 | B17 | HIGH | -0.8660, 0.5000, -1.732, 2.000 | θ=5π/3: sin=-√3/2,cos=1/2,tan=-√3,sec=2; best correct |
| 0158 | B17 | MED | A, C | distribution terminology MCQ 2-slot; best all slots |
| 0163 | B17 | HIGH | 9, -5, 4 | (x-5)(x+4)^2-(x-5)^2(x+4)=9(x-5)(x+4); A=9,B=-5,C=4; be |
| 0179 | B17 | HIGH | 29,3,21,1,21,4,19,4,23,3 | 177/6=29r3,127/6=21r1,151/7=21r4...; best correct (veri |
| 0185 | B17 | MED | T, F, T, F, T | interval T/F 5-slot; best all slots present |
| 0187 | B17 | MED | 0.0281,0.0067,0.3825,0.4512,22,18,2,35,30 | logistic regression Pima 9-slot; best all slots; R-depe |
| 0265 | B17 | MED | A, D | central location nominal MCQ 2-slot; best all slots |
| 0289 | B17 | HIGH | 4, 9 | perimeter 40<12w-8<100 -> 4<w<9; best correct |
| 0315 | B17 | MED | B, B, A | sampling concept MCQ 3-slot; best all slots |
| 0323 | B17 | MED | [10,12), [-8,-6), [10,18), [-16,-6) | floor function preimages 4-slot; best all slots present |
| 0330 | B17 | MED | 26.76, 2614 | profit max P(x)=9x+0.3x^2-0.0015x^3-427; best=x*+maxP p |
| 0343 | B17 | MED | D, A, C, B, E | polynomial-description matching 5-slot; best all slots |
| 0370 | B17 | HIGH | -5, 10 | y=10cos(5x)-5: midline y=-5, amplitude=10; best correct |
| 0373 | B17 | MED | 51.13, 56.71 | 93% CI CD lengths; best plausible |
| 0378 | B17 | MED | 0.0001420,0.00002206,0.0001199,0.1554,15.54 | baseball wins-vs-avg regression 5-slot; best all slots |
| 0393 | B17 | HIGH | (1/10)arccos((x-6)/16), -10, 22 | inverse of 16cos(10x)+6: f^-1=(1/10)arccos((x-6)/16), d |
| 0401 | B17 | HIGH | 143.2, 240.0, 52.52, -135.0 | rad->deg: 5/2=143.2,4π/3=240,11/12=52.52,-3π/4=-135; be |
| 0408 | B17 | MED | 5816/9999, 3017/99990, 574/999, 653/9990, 428/999 | repeating decimals to fractions 5-slot; best all slots  |
| 0019 | B18 | HIGH | 181 | j_155 least odd prime: mod181=0 (recurrence family 0017 |
| 0055 | B18 | HIGH | 5x^4 | y=kx^4, 405=k*81->k=5; y=5x^4; MATCH (best correct) |
| 0112 | B18 | INCONCLUSIVE | INCONCLUSIVE | cube cross-section pentagon competition; best=600; not  |
| 0161 | B18 | INCONCLUSIVE | INCONCLUSIVE | median-of-subsets competition; best=C(2024,1012); not c |
| 0184 | B18 | INCONCLUSIVE | INCONCLUSIVE | OEIS GF(2) polynomial mult table; best=A; not computabl |
| 0195 | B18 | MED | -2.445, -0.7553 | two-sample CI female/male drinks; best plausible (CI bo |
| 0198 | B18 | INCONCLUSIVE | INCONCLUSIVE | reducible polynomial triplets competition; best=5; not  |
| 0229 | B18 | INCONCLUSIVE | INCONCLUSIVE | tree/complex-numbers competition; best=n-2; not computa |
| 0312 | B18 | INCONCLUSIVE | INCONCLUSIVE | Ana/Banana periodic function game; best=20; not computa |
| 0316 | B18 | INCONCLUSIVE | INCONCLUSIVE | triangle/tangent-circle competition; best=I; not comput |
| 0376 | B18 | INCONCLUSIVE | INCONCLUSIVE | gcd(a^2+b^2+c^2,abc) sum competition; best=1275; not co |
| 0391 | B18 | INCONCLUSIVE | INCONCLUSIVE | sequence-mod-prime competition; best=I; not computable |
| 0405 | B18 | INCONCLUSIVE | INCONCLUSIVE | OEIS partitions 3 kinds; best=B; not computable |
| 0445 | B18 | INCONCLUSIVE | INCONCLUSIVE | coin-flip 20H-before-19T m+n mod competition; best=G; n |
| 0498 | B18 | INCONCLUSIVE | INCONCLUSIVE | list mean8/median13/mode15/range27 competition; best=BR |
| 0502 | B18 | HIGH | 8/11 | period of 2tan(11pi/8 x-...)=pi/(11pi/8)=8/11; MATCH (b |
| 0522 | B18 | HIGH | -0.472, 0.472 | cos x=4x^2 -> x=+/-0.4719; MATCH (best correct) |
| 0611 | B18 | HIGH | 1.356 | SE=sqrt(SSE/(n-2))=sqrt(57/31)=1.356; DISCREPANCY (best |
| 0775 | B18 | HIGH | 6sin(x-7)-6 | right 7, down 6, vstretch 6: y=6sin(x-7)-6; DISCREPANCY |
| 0802 | B18 | HIGH | 26/7 | 12/6 * 13/7 = 26/7; MATCH (best correct) |
| 0812 | B18 | HIGH | 512/sin^6(2t) | (xy)^6=8 polar: r^12 sin^6(2t)/64=8 -> 512/sin^6(2t)=r^ |
| 0906 | B18 | HIGH | x=2, x=5 | VA of 3/((x-2)(x-5)): x=2,x=5; MATCH (best correct) |
| 0409 | B18 | MED | prediction-interval + mean-CI at x=3 | 96.2% PI and CI at x=3; best="(-0.02462, 4.239)" likely |
| 0415 | B18 | HIGH | sqrt(A/6), A, (A/6)^(3/2), A | s=f(A)=sqrt(A/6) confirmed; MATCH (best has all 4 slots |
| 0448 | B18 | MED | x^3-4x^2-6x+30, x^2-9x+20 | rational function reduced form 2-slot; best has both po |
| 0001 | B19 | MED | Unchanged (A) | weighted mean invariant when all weights scaled by same |
| 0007 | B19 | INCONCLUSIVE | INCONCLUSIVE | snakes-on-circle merging competition; best=56; not Wolf |
| 0013 | B19 | MED | (1/8)(2sec^6(4x)+3sec^4(4x)+6sec^2(4x)+12 ln/tan(4x)/)+ | integral antiderivative computed (Wolfram); MCQ best=C; |
| 0014 | B19 | HIGH | ln(35)/ln(3) | 7*3^t=245 -> 3^t=35 -> t=ln35/ln3; MATCH (best correct) |
| 0034 | B19 | MED | 20 is an outlier (Q3+1.5*IQR=19.5<20) | boxplot: IQR=6, upper fence 19.5, max 20 -> outlier; be |
| 0048 | B19 | HIGH | C (-2 ~ ln(0.135)) | e^-2=0.135 -> -2=ln(0.135)=option C; MATCH (best=C) |
| 0053 | B19 | INCONCLUSIVE | INCONCLUSIVE | bird-in-3x3x3-maze Markov competition; best=F; not Wolf |
| 0073 | B19 | INCONCLUSIVE | INCONCLUSIVE | joint pdf of U=X^2+Y^2,V=X/Y transformation; best=E; ha |
| 0074 | B19 | HIGH | 12.36, 25.04 | paired diff CI 94.6%: mean=18.7,s=9.056,t(9)=2.22 -> (1 |
| 0080 | B19 | HIGH | sqrt(3)/12 | 4/(6sqrt3+4sqrt3+6sqrt3)=4/(16sqrt3)=sqrt3/12; value ve |
| 0092 | B19 | INCONCLUSIVE | INCONCLUSIVE | parametric integral int_0^1 x^(m-1)/(1+x^n)dx; no numer |
| 0094 | B19 | HIGH | 4/3 | area x=1-y^2,x=0: int_-1^1(1-y^2)dy=4/3; value verified |
| 0095 | B19 | INCONCLUSIVE | INCONCLUSIVE | isosceles triangle circumcircle competition; best=12; n |
| 0098 | B19 | INCONCLUSIVE | INCONCLUSIVE | 52-card riffle permutation order competition; best=A; n |
| 0109 | B19 | HIGH | (a) 4,2 (b) 5,1,1 (c) 3,-1,1 | eigenvalues of 3 matrices computed; value verified; MCQ |
| 0114 | B19 | MED | sin(2^(n+1) a)/(2^(n+1) sin a) | product cos(a)...cos(2^n a)=sin(2^(n+1)a)/(2^(n+1)sin a |
| 0123 | B19 | HIGH | x^2 cos(y) + y^2 cos(x) | exact differential primitive: d(x^2cosy+y^2cosx) matche |
| 0128 | B19 | HIGH | (y-3)/(y+3) | (y^2-9)/(y+3)^2=(y-3)/(y+3); MATCH (best correct) |
| 0130 | B19 | HIGH | r^42 | r^16*r^13*r^13=r^42; MATCH (best correct) |
| 0131 | B19 | HIGH | 0.1084 | prop z=(0.55-0.53)/sqrt(0.53*0.47/950)=1.235, p=1-Phi=0 |
| 0146 | B19 | MED | antiderivative (messy radical integral) | int(4x^2+25x+7)/sqrt(x^2+8x)dx computable but messy; MC |
| 0147 | B19 | HIGH | 25*pi/3 | vol rev of sqrt(x)+sqrt(y)=sqrt5 about x-axis: pi*int_0 |
| 0148 | B19 | INCONCLUSIVE | INCONCLUSIVE | compound Poisson process distribution; best=A; conceptu |
| 0150 | B19 | MED | best L2 cubic approx of e^x on [-1,1] (Legendre) | least-squares cubic via Legendre coeffs; computable but |
| 0153 | B19 | MED | quadratic form standard form via completing square | f(x1,x2,x3) diagonalization computable; MCQ best=B |
| 0156 | B20 | HIGH | eigenvalues -7, 2, 2 | eigenvalues computed; value verified; MCQ best=H |
| 0162 | B20 | INCONCLUSIVE | INCONCLUSIVE | OEIS floor(i/j) triangle; best=B; not computable |
| 0166 | B20 | HIGH | 175*(1/4)^n | marsh decay A=175(1/4)^n; MATCH (best correct) |
| 0172 | B20 | HIGH | 1320/3721 | sin(2arccos(11/61))=2*(11/61)*(60/61)=1320/3721; MATCH  |
| 0175 | B20 | INCONCLUSIVE | INCONCLUSIVE | OEIS lcm(1..n); best=I; not computable |
| 0178 | B20 | HIGH | -4 | det B=det[a2-2a3,a1,a2]=-2det[a3,a1,a2]=-2/A/=-4; value |
| 0180 | B20 | HIGH | (1/2)m - 7/2 | 7/8(-4+4m/7)=-7/2+m/2; MATCH (best correct) |
| 0183 | B20 | MED | reduction formula for int csc^5(x)dx | int 1/sin^5 x dx computable (reduction); MCQ best=D |
| 0189 | B20 | HIGH | 850a + 1200r = 35000 | coffee yield equation setup; MATCH (best correct) |
| 0199 | B20 | INCONCLUSIVE | INCONCLUSIVE | convex pentagon min sum-of-distances (Fermat point) com |
| 0200 | B20 | INCONCLUSIVE | INCONCLUSIVE | Brocard-angle triangle competition; best=I; not Wolfram |
| 0206 | B20 | HIGH | 4 | (sqrt11+sqrt7)(sqrt11-sqrt7)=11-7=4; MATCH (best correc |
| 0212 | B20 | INCONCLUSIVE | INCONCLUSIVE | renewal process exponential interarrival; best=J; conce |
| 0216 | B20 | HIGH | 60 | T/6=10 -> T=60; MATCH (best correct) |
| 0220 | B20 | INCONCLUSIVE | INCONCLUSIVE | count a with d1*d2 perfect square competition; best=A;  |
| 0224 | B20 | HIGH | 2643 | y=193+25*98=2643; MATCH (best correct) |
| 0230 | B20 | HIGH | -2.424 | 16=50(1.6)^x -> x=log(0.32)/log(1.6)=-2.424; MATCH (bes |
| 0231 | B20 | HIGH | y=0.5161x+4.742 | least-squares fit: slope 0.5161, intercept 4.742; MATCH |
| 0234 | B20 | HIGH | 29x^7 + 6x^5 | (16x^7-9x^5)+(13x^7+15x^5)=29x^7+6x^5; MATCH (best corr |
| 0235 | B20 | INCONCLUSIVE | INCONCLUSIVE | 32-card subset competition; best=B; not computable |
| 0252 | B20 | MED | normal populations + equal variances + independence | one-way ANOVA conditions; MCQ best=C; standard answer ~ |
| 0264 | B20 | HIGH | 256*pi*t^2 | r=8t, SA=4pi r^2=4pi(8t)^2=256pi t^2; MATCH (best corre |
| 0267 | B20 | HIGH | k = -1/2 | int_0^2(ky+1)dy=2k+2=1 -> k=-1/2; value verified; MCQ b |
| 0272 | B20 | HIGH | x + sqrt(x^2-1) | tan=sqrt(x^2-1) -> sec=x; sec+tan=x+sqrt(x^2-1); value  |
| 0277 | B20 | HIGH | 38800 | 44232/1.14=38800; MATCH (best correct) |
| 0279 | B21 | MED | Taylor series of f'(x) (sigma form) | f=(x-ln(1+x))/x^2; f' series computable; MCQ best=J |
| 0282 | B21 | MED | e^2, -e^2 | solve-for-x; best="e^2,-e^2" plausible (log equation) |
| 0283 | B21 | MED | 114 (target HR) | heart-rate percent calc; best=114 plausible |
| 0284 | B21 | INCONCLUSIVE | INCONCLUSIVE | area of /x-/y//+/y-/x//+/y/=9 competition; best=E |
| 0286 | B21 | INCONCLUSIVE | INCONCLUSIVE | smallest x with 2nd-deriv condition on prod cos; best=H |
| 0290 | B21 | HIGH | 2 | int_1^{e^2} dx/(x sqrt(1-lnx)): u=lnx, real convergent  |
| 0292 | B21 | HIGH | -2 - sqrt(3) | tan(285)=tan(-75)=-tan(75)=-(2+sqrt3); MATCH (best corr |
| 0295 | B21 | HIGH | 8*pi/15 | vol rev sqrt(x)+sqrt(y)=sqrt2: pi*a^3/15 with a=2 = 8pi |
| 0304 | B21 | MED | residue-theorem contour integral (involved) | oint z^13/((z^2+5)^3(z^4+1)^2) /z/=3; all poles enclose |
| 0305 | B21 | INCONCLUSIVE | INCONCLUSIVE | OEIS prime-power algorithm; best=B; not computable |
| 0321 | B21 | HIGH | a = 1 | tangent to x^2 e^-x through origin: a e^-a=(2a-a^2)e^-a |
| 0324 | B21 | INCONCLUSIVE | INCONCLUSIVE | OEIS ordered-factorization count; best=H; not computabl |
| 0331 | B21 | INCONCLUSIVE | INCONCLUSIVE | abc+a+b=c constraint optimization competition; best=H |
| 0337 | B21 | MED | rank condition on a,b (computable per options) | rank of 3 column vectors with params a,b; MCQ best=H |
| 0340 | B21 | MED | R^2 definition (multiple true statements) | R^2 multiple-correlation MCQ; best="C,E,F"; conceptual |
| 0348 | B21 | MED | int arcsin(4x)/sqrt(4x+1) dx (messy) | computable by parts but messy closed form; MCQ best=D |
| 0351 | B21 | HIGH | 12.287 | dy/dt=4cos(t)+12cos(12t) at t=1 (rad)=12.287; MCQ best= |
| 0355 | B21 | HIGH | inflection point (-3, -26/9) | f=4(x+1)/x^2-2, f''=0 at x=-3, f(-3)=-26/9; MCQ best=H |
| 0356 | B21 | MED | Laurent series of 1/(z^2+1) at z=-1 and z=inf | series expansions computable; MCQ best=F |
| 0365 | B21 | MED | x in [-36,36], y in [0,6] | y=(1296-x^2)^(1/4): domain /x/<=36, range [0,6]; MCQ be |
| 0366 | B21 | MED | solution-space/rank statement (computable per options) | a2,a3,a4 indep, a1=...; MCQ best=G; conceptual |
| 0377 | B21 | INCONCLUSIVE | INCONCLUSIVE | largest prime factor of smallest n competition; best=B |
| 0381 | B21 | HIGH | 2040 | sum_{k=1}^{120} 17 = 120*17 = 2040; MATCH (best correct |
| 0384 | B21 | HIGH | (ln(11/32)-3)/5 | 64e^(5x+3)=22 -> x=(ln(11/32)-3)/5; MATCH (best correct |
| 0394 | B21 | MED | int x*arctan(2x)^2 dx (by parts, messy) | computable by parts; messy closed form; MCQ best=H |
| 0398 | B22 | MED | transition/coordinate matrix (computable per options) | basis transition matrix problem; MCQ best=A |
| 0400 | B22 | MED | determinant distribution of random Bernoulli matrix | det of 2x2 Bernoulli(0.4) matrix distribution; MCQ best |
| 0402 | B22 | INCONCLUSIVE | INCONCLUSIVE | OEIS fully-multiplicative a(p)=floor((p+1)/2); best=J |
| 0412 | B22 | MED | (4*sqrt(78)-35)/72 | cos(a)=-sqrt32/9 QII, sin(b)=-5/8 QIII; sum/diff identi |
| 0414 | B22 | MED | int 3/(4x^2 sqrt(5x^2-2x+1))dx (messy) | computable but messy radical integral; MCQ best=I |
| 0430 | B22 | HIGH | 1 | lim=ln(1+x^2+x^4)/x^2 ->1; verified; MCQ best=E |
| 0432 | B22 | MED | 1.202, 2.129, 4.344, 5.271 | trig equation roots in [0,2pi]; best has 4 roots; plaus |
| 0433 | B22 | HIGH | 4cos^3(t)-3cos(t) | cos(3θ)=4cos^3θ-3cosθ; value verified; MCQ best=C |
| 0434 | B22 | INCONCLUSIVE | INCONCLUSIVE | OEIS circle-partition into 2s and 3s; best=A |
| 0440 | B22 | MED | 5/2 | min area convex lattice pentagon = 5/2 (known result);  |
| 0451 | B22 | MED | 0.1290,0.1935,0.2097,14,0.1774,0.06452 | rel-freq table, total=62; best slots plausible (8/62=0. |
| 0452 | B22 | MED | 42 | chi-sq independence df=(8-1)(7-1)=42; best=42 plausible |
| 0459 | B22 | HIGH | sin^2(A), cos(A)/sin(A), sec^2(A), ... | fundamental identities: 1-cos^2=sin^2, cot=cos/sin, etc |
| 0464 | B22 | MED | parallel-system exponential reliability (computable) | L1,L2 parallel exponential lifetime distribution; MCQ b |
| 0465 | B22 | HIGH | 8/9 | vol under z=2r inside r=cosθ: (2/3)int cos^3=8/9; verif |
| 0466 | B22 | HIGH | 26.88 | scale 1/64: 0.42*64=26.88~26.9; MATCH (best=26.9) |
| 0471 | B22 | INCONCLUSIVE | INCONCLUSIVE | triangle circumcircle power-of-point competition; best= |
| 0473 | B22 | HIGH | [-7, -3] | u^2+10u+21<=0 -> (u+3)(u+7)<=0 -> [-7,-3]; MATCH (best  |
| 0477 | B22 | MED | A, C (leading + open-ended to avoid) | questionnaire design MCQ; best="A,C"; conceptual |
| 0481 | B22 | INCONCLUSIVE | INCONCLUSIVE | 7-digit increasing-order count mod competition; best=A |
| 0483 | B22 | INCONCLUSIVE | INCONCLUSIVE | max x+3y constraint competition; best=A |
| 0486 | B22 | INCONCLUSIVE | INCONCLUSIVE | increasing sequences AIME competition; best=B |
| 0493 | B22 | MED | 14.67, B, 0.06866, 0.1083 | color-blindness proportions/CI 4-slot; best has all 4;  |
| 0500 | B22 | MED | iterative method convergence/error bound | AX=b iterative error estimate; MCQ best=J; conceptual |
| 0504 | B22 | HIGH | -3/2, -3*sqrt(3)/2 | polar (3,4pi/3): x=3cos=-3/2, y=3sin=-3sqrt3/2; MATCH ( |
| 0507 | B23 | INCONCLUSIVE | INCONCLUSIVE | factorial-sum binomial competition; best=I |
| 0511 | B23 | MED | arc length = t + 2t^3/3 (integrand 1+2t^2) | ds=sqrt((1+2t^2)^2)=1+2t^2; needs interval for number;  |
| 0512 | B23 | HIGH | 64p^2 + 64p + 16 | (8p+4)^2=64p^2+64p+16; MATCH (best correct) |
| 0513 | B23 | HIGH | -1.405, 1.405, 1.751 | alpha=0.08: lower z=-1.405, right z=1.405, two-tail z=1 |
| 0514 | B23 | MED | definite integral setup for r=2 cap r=4cos(theta) | common-region polar area integral; MCQ best=I |
| 0517 | B23 | INCONCLUSIVE | INCONCLUSIVE | sum of 3-digit distinct-digit integers mod 1000 competi |
| 0524 | B23 | MED | Dini derivatives (a,b,a',b' bounds) | Dini upper/lower derivatives of piecewise oscillating f |
| 0526 | B23 | HIGH | 128x^4 + 16x^2 + 4 | y=8(4x^2)^2+4(4x^2)+4=128x^4+16x^2+4; MATCH (best corre |
| 0532 | B23 | MED | polar conic r=ed/(1-e cos) form | polar conic with focus at origin, given e and directrix |
| 0533 | B23 | MED | 0.0563 (p-value) | GMAT one-sample test p-value; best=0.0563 plausible |
| 0534 | B23 | MED | a,b,c from repeated-root general solution | y=(C1+C2x)e^... -> repeated root -> a,b; particular ->  |
| 0536 | B23 | MED | LU decomposition of given 3x3 | compact LU factorization; computable; MCQ best=E |
| 0544 | B23 | HIGH | yes: power function (8/7)x^3 | s(x)=8/(7x^-3)=(8/7)x^3 is a power function; MCQ best=A |
| 0545 | B23 | HIGH | 400000 | 8000*50=400000; MATCH (best correct) |
| 0547 | B23 | MED | inscribed rectangle+triangle optimization | area optimization in circle; MCQ best=H |
| 0549 | B23 | INCONCLUSIVE | INCONCLUSIVE | OEIS sum-of-two-squares count; best=J |
| 0551 | B23 | HIGH | sqrt(28) | cos=-6/8 -> r=8, x=-6, y=+sqrt(64-36)=sqrt28; MATCH (be |
| 0552 | B23 | MED | 33150, 36300 | Jeopardy winnings CI 2-slot; best plausible |
| 0554 | B23 | MED | max entropy rate of random walk (4 edges) | random-walk entropy rate; MCQ best=A; conceptual |
| 0556 | B23 | MED | chain rule dA/dt = f'(r) h'(t) | related-rates chain-rule statement; MCQ best="C,D" |
| 0560 | B23 | MED | mean 0, sd 1 (standardized variable) | standardized var properties MCQ; best="C,A,A" |
| 0561 | B23 | HIGH | 2^26*3^14*5^7*7^4*11^2*13^2*17*19*23*29 | 30! prime factorization verified; MCQ best=E |
| 0567 | B23 | MED | false-statement about frequency distributions | identify false stat statement; best="A,A"; conceptual |
| 0569 | B23 | HIGH | (p^2-1)(p^2-p) | /GL_2(F_p)/=(p^2-1)(p^2-p); value verified; MCQ best=B |
| 0574 | B23 | MED | rank/det property of given 3x3 | matrix A property (det=0, rank 2); MCQ best=E |
| 0577 | B24 | MED | condition 2a^3-9ab+27c=0 (roots in AP) | arithmetic-sequence roots condition; MCQ best=F |
| 0579 | B24 | HIGH | e^(8/3) | lim (tan4x/4x)^(1/2x^2)=e^(8/3); verified; MCQ best=C |
| 0580 | B24 | HIGH | 2/3 | lim(1/x^2-cot^2 x)=2/3; MCQ best=D |
| 0581 | B24 | MED | max of y from y'+2(lnx+1)y=0 | separable ODE y=e^(-2x lnx); max value computable; MCQ  |
| 0582 | B24 | HIGH | 1035 | sum 1..45 = 45*46/2 = 1035; MATCH (best correct) |
| 0594 | B24 | MED | expectation/variance of given discrete X | discrete distribution moment; MCQ best=F |
| 0597 | B24 | INCONCLUSIVE | INCONCLUSIVE | triangle extension competition; best=B |
| 0600 | B24 | MED | eigenvalues of block matrix [[0,A],[B,0]] | block antidiagonal eigenvalues = +/-sqrt(eig(AB)); MCQ  |
| 0603 | B24 | MED | median least affected by outlier etc | outlier-robustness MCQ; best="C,A,B"; conceptual |
| 0613 | B24 | MED | beta linear combo coefficients (solve system) | express beta in basis; MCQ best=I |
| 0614 | B24 | MED | x(x-a)(x-b)(x-c)+1 factorable condition | factorization condition; MCQ best=I |
| 0615 | B24 | MED | 14, 9 | cyclist two-speed word problem; best=14,9 plausible |
| 0616 | B24 | HIGH | y=C1 cos x+C2 sin x -(1/3)sin 2x | y''+y=sin2x: y_p=-1/3 sin2x; MCQ best=J |
| 0618 | B24 | MED | volume rotating arcsin region about x-axis | V=pi*int arcsin^2... computable; MCQ best=A |
| 0625 | B24 | HIGH | 5(x+2)(x+3) | 5x^2+25x+30=5(x+2)(x+3); MATCH (best correct) |
| 0626 | B24 | MED | complex path integral of /z/ | int/z/dz over line vs semicircle; MCQ best=G |
| 0627 | B24 | HIGH | 1090 | SA=163pi -> r=sqrt163/2, V=163sqrt163 pi/6=1089.6~1090; |
| 0631 | B24 | INCONCLUSIVE | INCONCLUSIVE | Putnam binomial-series integral competition; best=A |
| 0635 | B24 | HIGH | 37.60, 0.7460, -25.40 | Q=37.6(0.746)^t: a=37.6,b=0.746,r=-25.4%; MATCH (best c |
| 0639 | B24 | HIGH | 3.325 | ME=(21.16-14.51)/2=3.325; MATCH (best correct) |
| 0644 | B24 | INCONCLUSIVE | INCONCLUSIVE | count n<=2010 with phi(n)/n competition; best=A |
| 0648 | B24 | HIGH | 11.51 + 0.83x, 30.60 | wage W=11.51+0.83x; at x=23 -> 30.60; MATCH (best corre |
| 0653 | B24 | MED | (600-45t)/7, 85.71, 47.14 | nicotine linear decay 3-slot; best plausible |
| 0654 | B24 | HIGH | sqrt(19), 2, 2, 2 | piecewise f: f(12)=sqrt19, f(-7)=f(pi)=f(-7.1)=2; MATCH |
| 0656 | B24 | HIGH | 6x^2 - 23x + 15 | roots 5/6,3: (6x-5)(x-3)=6x^2-23x+15; MATCH (best corre |
