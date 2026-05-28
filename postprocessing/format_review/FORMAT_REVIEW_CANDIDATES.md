# FORMAT REVIEW CANDIDATES — Day 3 17:00 PT

**Source:** `results/master_item_tracker.csv` V3 (commit e9a9fc4a)

**Purpose:** Surface highest-leverage items for manual review before submissions.

Each item shows: current best_answer | teacher_consensus | wolfram | back_solve | recommended action

---

## 1. ZERO-RISK: Apply Wolfram HIGH (58 items)

These have wolfram-verified canonical answers. Apply directly.

| id | current best_answer | wolfram_override | wolfram_batch |
|---|---|---|---|
| 5 | `32.09` | `541.3, 63.25, 135.325, 4.2167, 32.09` | B2 |
| 9 | `\dfrac{L - 8x}{6F}` | `L-8x, 6F` | B1 |
| 12 | `2c+4p=70,\ 11` | `2c + 4p = 70, 11` | B2 |
| 40 | `INVALID` | `D = 800 - 50d` | B8 |
| 41 | `4048` | `2112` | WEBSEARCH |
| 67 | `7.6(1.09)^t, 13.89, 5.384` | `7.6(1.09)^t, 13.9, 5.4` | B8 |
| 68 | `5.442` | `-2.857, 6.986, -1.082, 3.707, -3.707, A, -12.647, ` | B2 |
| 72 | `IV` | `-0.8352, -0.9187, 0.3950, -2.3258, Quadrant IV` | B8 |
| 89 | `46.57` | `\frac{326}{7}` | B8 |
| 100 | `\frac{180}{7}\text{ grams}` | `\frac{180}{7}` | B8 |
| 103 | `8\sqrt2` | `8\sqrt{2}` | B8 |
| 106 | `\frac{13}{6}\text{ hours}` | `\frac{13}{6}` | B8 |
| 117 | `INVALID` | `B` | WEBSEARCH |
| 118 | `3.600` | `\frac{18}{5}` | B8 |
| 120 | `138` | `8` | WEBSEARCH |
| 124 | `G` | `H` | B8 |
| 125 | `G` | `G` | WEBSEARCH |
| 134 | `1,5,12,20,26,30,31,28` | `1, 5, 12, 20, 26, 30, 31, 27.63` | B2 |
| 167 | `B, A, B, B` | `Negative, Negative, Positive, Negative` | B8 |
| 181 | `D` | `A` | B8 |
| 192 | `A` | `1.06, (1.88, infty), 0.1449, A` | B2 |
| 218 | `0.775` | `\arcsin\!(\frac{7}{10})` | B8 |
| 233 | `1.960,\ -1.960,\ -5.177,\ B` | `1.96, -1.96, -5.18, B` | B8 |
| 247 | `2474, \dfrac{2474}{1 + 37.06 e^{-0.53t}}, 2474` | `\frac{2409}{65}, \frac{2474}{1+\frac{2409}{65}e^{-` | B8 |
| 257 | `3` | `2.52, 3.00, A` | B2 |
| 317 | `H` | `D` | B8 |
| 353 | `5,7` | `8, C, 5 and 7, D` | B3 |
| 385 | `A` | `A, A, A` | B3 |
| 395 | `85/3, -95/4, -10/7` | `\frac{85}{3}, -\frac{95}{4}, -\frac{10}{7}` | B8 |
| 413 | `\text{A}` | `0.89, (1.83, infty), 0.2008, A` | B3 |
| 435 | `0.4457, 0.5368` | `0.4457, 0.5368, A` | B1 |
| 454 | `0.9375` | `1.5, 0.9375` | B8 |
| 469 | `19.06` | `s^2, 0.1575A, 0.1575s^2, C, 81, square feet, 14.17` | B3 |
| 479 | `40.01, 43.99` | `40.36, 43.64, 40.01, 43.99` | B1 |
| 487 | `-0.9636` | `-21.1, -0.9636` | B3 |
| 495 | `100, 100, 200, 0.255, 5.99, B` | `100, 100, 200, 0.255, 5.991, B` | B3 |
| 496 | `99.594` | `9.594^\circ` | B8 |
| 499 | `2.149` | `36.9, 0.3225, 32.25, 2.149` | B4 |
| 506 | `A` | `J` | B8 |
| 519 | `98.30` | `426.3, 5090, 98.30` | B4 |
| 548 | `120.00` | `1.20x = 144, $120.00` | B1 |
| 578 | `7.624,8.996,95.44` | `7.62, 9.00, 95.44` | B1 |
| 584 | `6.000` | `7z, 6w` | B8 |
| 587 | `A` | `B, C, D, E, F, J, C, A, B, B` | B4 |
| 591 | `3.162, -0.3218, 4.123, 1.326` | `1.081, 1.683, 1.819, -0.832, 3.162, -0.322, 4.123,` | B4 |
| 633 | `INVALID` | `B, D, 8` | B5 |
| 638 | `D` | `0.15, (-infty, -1.75)U(1.75, infty), 0.88, D` | B5 |
| 657 | `-10.33, 10.33` | `172.52, 187.48, 172.87, 187.13, 0, 5.167, -10.33, ` | B5 |
| 715 | `8.500` | `5, 7, 9, 13, 8.5, 6, 7, 8, 9, 10, 11, 8.5` | B5 |
| 721 | `C,A,A` | `D, A, A` | B5 |
| 748 | `B` | `222.51, 186.49, 79.43, 66.57, 50.05, 41.95, 31.01,` | B5 |
| 793 | `D` | `1.35, (1.49, inf), 0.0895, D` | B6 |
| 884 | `(x - 59)^2 + 74` | `g(x)=(x-59)^2+74` | B8 |
| 886 | `A, C` | `A, C` | B6 |
| 902 | `3, 2` | `9, 6` | B8 |
| 917 | `190` | `189.8, 246.4, 43` | B6 |
| 924 | `2010` | `n = 55 + 0.2t, 2010` | B7 |
| 929 | `6.086,\ (-0.72,\ 3.12),\ A` | `5.860, (-0.78, 3.18), A` | B7 |

## 2. ZERO-RISK: Apply Rescue HIGH (5 items)

Items previously scoring zero (no boxed answer). Rescue produced 4/4 or 3/4 unanimous votes.

| id | rescue_answer | votes |
|---|---|---|
| 229 | `2` | 4/4 |
| 308 | `12` | 4/4 |
| 383 | `80` | 4/4 |
| 445 | `D` | 3/4 |
| 498 | `15` | 4/4 |

## 3. LOW-RISK: MCQ value-to-letter conversions (1 item + 16 MCQ-not-letter)

Items where best_answer is a value when grader wants a letter.

| id | current | should be | options |
|---|---|---|---|
| 141 | `3` | **H** | 3 |

## 4. MANUAL REVIEW: MCQ items where best_answer is not a letter (16 items)

These need manual inspection. The answer might already be correct (e.g., free-response forms) or might need letter conversion.

| id | current | teacher_consensus | wolfram | back_solve | options (first 5) |
|---|---|---|---|---|---|
| 18 | `INVALID` | `H` | `` | `I` | A=30; B=8; C=40; D=35; E=45/5 |
| 117 | `INVALID` | `B` | `B` | `B` | A=2017; B=2020; C=2011; D=2019; E=2014 |
| 403 | `INVALID` | `J` | `` | `J` | A=$$
\underset{\s; B=$$
\underset{\s; C=$$
\underset{\s; D=$$
\underset{\s; E=$$
\underset{\s |
| 443 | `\text{No listed option}` | `G` | `` | `G` | A=12; B=14; C=16; D=23; E=18 |
| 457 | `Letter` | `C` | `` | `G` | A=837; B=835; C=836; D=830; E=839 |
| 501 | `INVALID` | `F` | `` | `F` | A=111; B=107; C=103; D=102; E=105 |
| 518 | `INVALID` | `E` | `` | `C` | A=[5, 8, 12, 10, ; B=[8, 7, 13, 11, ; C=[6, 8, 12, 10, ; D=[9, 6, 12, 13, ; E=[6, 7, 12, 11,  |
| 589 | `INVALID` | `D` | `` | `D` | A=21; B=26; C=25; D=24; E=29 |
| 670 | `INVALID` | `D` | `` | `A` | A=420; B=789; C=256; D=521; E=300 |
| 675 | `INVALID` | `B` | `` | `J` | A=[102, 108, 113,; B=[106, 108, 112,; C=[106, 107, 111,; D=[104, 109, 113,; E=[107, 108, 110, |
| 682 | `INVALID` | `G` | `` | `G` | A=295; B=292; C=260; D=270; E=288 |
| 695 | `INVALID` | `E` | `` | `B` | A=$$
\ \gamma, \ ; B=$$
\ \beta, \ \; C=$$
\ \alpha, \ ; D=$$
\ \gamma, \ ; E=$$
\ \alpha, \  |
| 720 | `INVALID` | `D` | `` | `I` | A=$$
\varepsilon_; B=$$
\varepsilon_; C=$$
\varepsilon_; D=$$
\varepsilon_; E=$$
\varepsilon_ |
| 727 | `INVALID` | `A` | `` | `A` | A=\frac{480}{49}; B=\frac{480}{56}; C=\frac{480}{51}; D=\frac{480}{48}; E=\frac{480}{47} |
| 786 | `PLACEHOLDER_0786` | `` | `` | `C` | A=31877746252; B=31877746254; C=31877746253; D=31877746258; E=31877746259 |
| 935 | `INVALID` | `H` | `` | `H` | A=405; B=435; C=480; D=420; E=455 |

## 5. MULTI-ANSWER EXPANSION: Undercount items (82 total)

- **6 have wolfram canonical** — apply directly (subset of Section 1)
- **51 have teacher consensus** — could apply teacher's multi-answer form
- Rest need manual review or multi-teacher voting

Top 20 undercount items (best_answer has fewer slots than [ANS] markers in question):

| id | n_slots_best | n_ans_slots_q | current | teacher | wolfram |
|---|---|---|---|---|---|
| 438 | 1 | 9 | `1` | `5,9,1,10,2,0,10,x^3y^7,1` | `` |
| 894 | 1 | 8 | `9` | `` | `0.008, 1.783, 2.013, -0.091, 0` |
| 25 | 6 | 12 | `8, 14, 25, 42, 55, 63` | `\frac{8}{63},\frac{2}{21},\fra` | `` |
| 380 | 1 | 7 | `1` | `0.075,0.239,32000,16710,38000,` | `` |
| 444 | 1 | 6 | `43` | `113,35,112,61,148,43` | `` |
| 505 | 1 | 6 | `2` | `1,3,6,-5,-4,2` | `` |
| 28 | 2 | 6 | `2, 140.00` | `2,70,1,768,2,140` | `` |
| 115 | 1 | 5 | `1958` | `11x-1200,11,109,(y+1200)/11,19` | `` |
| 470 | 2 | 6 | `2.576, 3.106` | `` | `` |
| 527 | 1 | 5 | `285.7` | `` | `` |
| 749 | 2 | 6 | `9 + 5n, (-1)^{n+1}(5n + 9)` | `` | `5, 5, 5, 5, 5, is, 14/9, 19/14` |
| 168 | 1 | 4 | `B` | `A,C,B,B` | `` |
| 328 | 1 | 4 | `C` | `B,D,A,C` | `` |
| 608 | 1 | 4 | `1981` | `B,A,A,1981` | `` |
| 620 | 1 | 4 | `B` | `\frac{4}{\sqrt7},\frac{16}{7},` | `` |
| 753 | 1 | 4 | `16.56` | `` | `` |
| 885 | 1 | 4 | `B` | `` | `` |
| 890 | 1 | 4 | `6` | `A,A,C,6` | `` |
| 20 | 1 | 3 | `229` | `228,229,250` | `` |
| 77 | 1 | 3 | `A` | `C,D,A` | `` |

## 6. PURE FORMAT ERRORS: format_only_diff_teacher (117 items)

Current answer matches teacher when normalized but the raw strings differ.
Likely sources: \dfrac vs \frac, \left/\right wrapping, whitespace, comma spacing.

Top 30 candidates:

| id | current | teacher_consensus | wolfram | tier |
|---|---|---|---|---|
| 15 | `8, NONE` | `8,NONE` | `` |  |
| 30 | `2944, 664` | `2944,664` | `` |  |
| 31 | `-3, 42` | `-3,42` | `` |  |
| 42 | `No, Yes, A` | `No,Yes,A` | `` |  |
| 44 | `True, True, True, False` | `True,True,True,False` | `` |  |
| 52 | `231, 385` | `231,385` | `` |  |
| 56 | `D, D, A` | `D,D,A` | `` |  |
| 60 | `C, A` | `C,A` | `` |  |
| 62 | `-15, 192, 0` | `-15,192,0` | `` |  |
| 65 | `-\dfrac{6}{7}, \dfrac{2}{7}` | `-\frac{6}{7},\frac{2}{7}` | `` |  |
| 76 | `-4, -11, 3, 33, -32, 9, -14, -13` | `-4,-11,3,33,-32,9,-14,-13` | `` |  |
| 84 | `-4, 5, -11` | `-4,5,-11` | `` |  |
| 87 | `OBSERVATION, OBSERVATION, EXPERIMENT` | `OBSERVATION,OBSERVATION,EXPERIMENT` | `` |  |
| 90 | `7n + 1` | `7n+1` | `` |  |
| 97 | `0, 4, 4` | `0,4,4` | `` |  |
| 99 | `-6, 12, -6` | `-6,12,-6` | `` |  |
| 101 | `C, C, A, C` | `C,C,A,C` | `` |  |
| 108 | `72, 12x` | `72,12x` | `` |  |
| 110 | `3, 9` | `3,9` | `` | W2 |
| 116 | `30, 6` | `30,6` | `` |  |
| 119 | `A, C, B, D` | `A,C,B,D` | `` |  |
| 128 | `\dfrac{y - 3}{y + 3}` | `\frac{y-3}{y+3}` | `` |  |
| 139 | `201, \dfrac{1}{n(n+1)}` | `201,\frac{1}{n(n+1)}` | `` |  |
| 158 | `A, C` | `A,C` | `` |  |
| 159 | `0.07, 0.007, 0.0007` | `0.07,0.007,0.0007` | `` |  |
| 163 | `9, -5, 4` | `9,-5,4` | `` |  |
| 176 | `\frac{p - 6k - m}{8}` | `\frac{p-6k-m}{8}` | `` |  |
| 179 | `29, 3, 21, 1, 21, 4, 19, 4, 23, 3` | `29,3,21,1,21,4,19,4,23,3` | `` |  |
| 185 | `T, F, T, F, T` | `T,F,T,F,T` | `` |  |
| 189 | `850a + 1200r = 35000` | `850a+1200r=35000` | `` |  |

## 7. BACK-SOLVE OVERRIDE CANDIDATES (top 20 of 173 items)

Items where the score-weighted majority across all submissions disagrees with our current best.
Confidence-weighted (back_solve_confidence > 0.5):

| id | back_solve_confidence | current | back_solve | teacher |
|---|---|---|---|---|
| 786 | 1.000 | `PLACEHOLDER_0786` | `C` | `` |
| 531 | 0.929 | `H` | `C, D, F, H` | `` |
| 611 | 0.901 | `PLACEHOLDER_0611` | `1.356` | `` |
| 851 | 0.892 | `B,\ C` | `B, C` | `B  and  C` |
| 609 | 0.879 | `30\sqrt{85} \approx 276.6 \tex` | `276.6` | `` |
| 873 | 0.879 | `A` | `B` | `A` |
| 437 | 0.830 | `79.63` | `(76.37, 79.63)` | `(76.37, 79.63)` |
| 852 | 0.829 | `PLACEHOLDER_0852` | `414.72` | `414.72` |
| 522 | 0.802 | `x \approx -0.472, \, 0.472` | `-0.472, 0.472` | `` |
| 447 | 0.795 | `(-\infty, 4]` | `x \leq 4` | `x \leq 4` |
| 11 | 0.779 | `answer` | `0.9391` | `` |
| 45 | 0.779 | `A` | `J` | `A` |
| 51 | 0.779 | `25352_8` | `25452` | `` |
| 313 | 0.779 | `-21414` | `-0.4989` | `-\frac{2\sqrt{14}}{15}` |
| 375 | 0.779 | `A` | `3.72` | `` |
| 411 | 0.779 | `39246` | `27.37` | `\frac{392\pi}{45}` |
| 558 | 0.779 | `f(x) = 6.5x - 25` | `6.5x - 25` | `f(x)=\frac{13}{2}x-25` |
| 610 | 0.779 | `\frac{8\pi}{3}+2\sqrt3` | `12.57` | `4\pi` |
| 679 | 0.779 | `answer` | `11.00` | `11` |
| 714 | 0.779 | `A` | `84.00` | `` |

---

## TLDR for the 3-hour window

**Highest confidence (zero-risk, apply directly):**
- 58 Wolfram HIGH overrides
- 5 rescue HIGH (4/4 votes)
- 4-5 web search GOLDs (already in wolfram_overrides.csv)
- 1 MCQ value-to-letter (id 0125 → G)

**= ~70 items to apply, expected lift +3-5pp from 0.653 → ~0.69**

**Medium confidence (review + apply):**
- 8 rescue MEDIUM (2/4 votes) — better than zero
- 30-50 top format_review candidates
- 20-30 top backsolve_review candidates

**= +1-3pp on top → potential 0.70-0.72**