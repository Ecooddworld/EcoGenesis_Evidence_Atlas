# Synthetic Ambiguous Benchmark

Цель benchmark: проверить не красивую презентацию, а защиту от главной ошибки `top hit = species`.

## Result

- Status: `pass`
- Records processed: 120
- Naive top-hit species claims: 120
- Unsafe naive species claims under EcoGenesis rules: 90
- EcoGenesis species-safe claims: 30
- EcoGenesis safe-rank records: 84
- Hard-gate failures: 0
- Overclaim prevention rate: 0.75

## Conclusion

Naive top-hit would emit 120 species claims; 90 are blocked or downgraded by EcoGenesis hard gates.

EcoGenesis не пытается угадать вид по лучшему hit. Если ambiguity/LCA, barcode gap, diagnostic k-mers или metadata gates не проходят, species-level publication claim блокируется, понижается до safe rank или отправляется в repair/review queue.
