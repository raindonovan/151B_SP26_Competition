# Grader normalization report

- Mode: `dfrac_only`
- Input:  `submissions/slot1_adapter_v5_plus_run14b_20260525_1623.csv`
- Output: `submissions/slotA_slot1_dfrac_only.csv`

## Summary
- Total rows: **943**
- Rows with at least one `\boxed{}`: **925**
- Rows modified: **38** (4.03%)

## Per-rule trigger counts (rows where rule fired)
- `dfrac_or_tfrac`: 38

## Sample modified rows (up to 10)
- **id=9**
  - before: `\dfrac{L - 8x}{6F}`
  - after:  `\frac{L - 8x}{6F}`
- **id=65**
  - before: `-\dfrac{6}{7}, \dfrac{2}{7}`
  - after:  `-\frac{6}{7}, \frac{2}{7}`
- **id=70**
  - before: `\dfrac{5}{56}`
  - after:  `\frac{5}{56}`
- **id=79**
  - before: `\dfrac{25}{7}`
  - after:  `\frac{25}{7}`
- **id=113**
  - before: `\dfrac{-2x^2 - 16x - 7}{25}`
  - after:  `\frac{-2x^2 - 16x - 7}{25}`
- **id=128**
  - before: `\dfrac{y - 3}{y + 3}`
  - after:  `\frac{y - 3}{y + 3}`
- **id=129**
  - before: `\dfrac{5}{\sin t}, \sqrt{7}, -3 \cos t, 2\sqrt{2} \tan t`
  - after:  `\frac{5}{\sin t}, \sqrt{7}, -3 \cos t, 2\sqrt{2} \tan t`
- **id=139**
  - before: `201, \dfrac{1}{n(n+1)}`
  - after:  `201, \frac{1}{n(n+1)}`
- **id=172**
  - before: `\dfrac{1320}{3721}`
  - after:  `\frac{1320}{3721}`
- **id=190**
  - before: `-\dfrac{21}{8}`
  - after:  `-\frac{21}{8}`

## Sample unmodified rows (5 random)
- **id=691** last-box: `(19.67, 26.99)`
- **id=121** last-box: `35`
- **id=26** last-box: `I`
- **id=806** last-box: `-0.6551, -0.7556, 0.8670, 1.153, -1.324, -1.527`
- **id=298** last-box: `C`

