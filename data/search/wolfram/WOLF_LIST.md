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
