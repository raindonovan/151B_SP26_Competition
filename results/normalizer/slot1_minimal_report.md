# Grader normalization report

- Mode: `minimal`
- Input:  `submissions/slot1_adapter_v5_plus_run14b_20260525_1623.csv`
- Output: `submissions/slot1_minimal_norm.csv`

## Summary
- Total rows: **943**
- Rows with at least one `\boxed{}`: **925**
- Rows modified: **9** (0.95%)

## Per-rule trigger counts (rows where rule fired)
- `left_right`: 8
- `thin_space`: 1

## Sample modified rows (up to 10)
- **id=64**
  - before: `850 - 350 \cos\left(\frac{\pi}{6} t\right)`
  - after:  `850 - 350 \cos(\frac{\pi}{6} t)`
- **id=166**
  - before: `175 \cdot \left( \frac{1}{4} \right)^n`
  - after:  `175 \cdot ( \frac{1}{4} )^n`
- **id=238**
  - before: `-61,\,61,\,62`
  - after:  `-61,61,62`
- **id=384**
  - before: `\frac{\ln\left(\frac{11}{32}\right) - 3}{5}`
  - after:  `\frac{\ln(\frac{11}{32}) - 3}{5}`
- **id=393**
  - before: `\frac{1}{10} \arccos\left(\frac{x - 6}{16}\right), [-10, 22]`
  - after:  `\frac{1}{10} \arccos(\frac{x - 6}{16}), [-10, 22]`
- **id=415**
  - before: `\sqrt{\frac{A}{6}}, A, \left( \frac{A}{6} \right)^{3/2}, A`
  - after:  `\sqrt{\frac{A}{6}}, A, ( \frac{A}{6} )^{3/2}, A`
- **id=792**
  - before: `\dfrac{\ln\left(\dfrac{V}{T}\right)}{\ln\left(\dfrac{h}{g}\right)}`
  - after:  `\dfrac{\ln(\dfrac{V}{T})}{\ln(\dfrac{h}{g})}`
- **id=841**
  - before: `\sin\left(40 + 8\sqrt{x}\right), 5 + \sqrt{\sin(8x)}`
  - after:  `\sin(40 + 8\sqrt{x}), 5 + \sqrt{\sin(8x)}`
- **id=895**
  - before: `70 \left( \dfrac{2}{7} \right)^{\frac{x - 10}{20}}`
  - after:  `70 ( \dfrac{2}{7} )^{\frac{x - 10}{20}}`

## Sample unmodified rows (5 random)
- **id=673** last-box: `3497040`
- **id=117** last-box: `B`
- **id=25** last-box: `8, 14, 25, 42, 55, 63`
- **id=779** last-box: `F`
- **id=289** last-box: `4,9`

