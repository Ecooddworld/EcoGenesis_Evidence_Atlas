# Synthetic Ambiguous Benchmark

Цель benchmark: проверить не красивую презентацию, а защиту от главной ошибки `top hit = species`.

## Result

- Status: `regression_pass`
- Records processed: 120
- Naive top-hit species claims: 120
- Unsafe naive species claims under EcoGenesis rules: 90
- EcoGenesis species rule-pass fixture records: 30
- EcoGenesis safe-rank records: 84
- Hard-gate failures: 0
- Overclaim prevention rate: 0.75

## Conclusion

Naive top-hit would emit 120 species claims; 90 are blocked or downgraded by EcoGenesis hard gates.

Это повторяемый synthetic regression, а не оценка биологической точности. Публичная fixture-attestation нужна только для покрытия pass-path кода и не является внешним reference audit. Если ambiguity/LCA, barcode gap, diagnostic k-mers или metadata gates не проходят, species-level output блокируется, понижается по рангу или отправляется в repair/review queue.
