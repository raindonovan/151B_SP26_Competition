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
