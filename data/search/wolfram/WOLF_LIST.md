# WOLF_LIST.md — All Wolfram-Verified Items
**Total verified**: 66 items (B1-B8 + WEBSEARCH)

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
