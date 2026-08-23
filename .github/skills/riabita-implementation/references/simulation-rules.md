# Simulation Rules

Authoritative specification of RIABITA ROMA's mathematics. This file overrides the
sample code in `Technical-Documentation.md`. Implement exactly what is written here.

All values are floating point internally. Round only for display.

## Vector order

Every array, tuple, matrix row, matrix column, and impact vector uses this order:

```
index 0 = M  Mobility
index 1 = C  Culture
index 2 = T  Tourism
index 3 = S  Socio-demographic
```

Three allocation vectors participate in a progressive round:

- **Dimension vector** `d = (M, C, T, S)`, each value in `0..100`.
- **Turn allocation vector** `b = (B_M, B_C, B_T, B_S)`, integer credits whose
  positive sum does not exceed the remaining game budget.
- **Cumulative allocation vector** `B`, the component-wise sum of completed turn
  allocations. Its sum starts at `0` and reaches exactly `100` when the round is
  complete.

## Rules version

Expose `RULES_VERSION = "2.0.0"`. Store it with every leaderboard entry (REQ-081).
Increment the minor version when any constant below changes, and the major version
when the operation order changes.

## Operation order

Fixed and non-negotiable. Each step consumes the output of the previous one.

1. **Validate** the turn allocation against the remaining credits. Reject invalid
   input before any arithmetic.
2. **Apply the impact matrix** atomically to the dimensions produced by the previous
   turn, or to the district baseline in turn 1.
3. **Apply tourism pressure** to `S`, based on post-matrix `T`.
4. **Apply the event** impact vector.
5. **Clamp** dimensions to `0..100`.
6. **Compute modifiers** (equilibrium, gap, concentration, diversification) from the
   clamped dimensions and the allocations.
7. **Compute RIz** as the weighted sum plus the modifier total, then clamp to `0..100`.
8. **Compute metrics**: yield, risk, Sharpe, profile.

Computing a modifier before clamping, or evaluating tourism pressure before the
matrix is fully applied, produces different scores. Do not reorder.

## Step 1: Validation

Reject the round and report a stable error identifier when any rule fails.

| Rule | Error identifier |
|---|---|
| Exactly four allocations are supplied | `allocation_length` |
| Every allocation is an integer | `allocation_not_integer` |
| Every allocation is within `0..100` | `allocation_out_of_range` |
| A complete single-turn allocation used by `run_simulation` sums to exactly `100` | `allocation_sum` |
| A progressive turn allocates at least one credit | `allocation_empty` |
| A progressive turn total is no greater than the remaining credits | `allocation_exceeds_remaining` |
| Exactly four baseline dimensions are supplied, each within `0..100` | `dimension_out_of_range` |

Validation is a pure function returning the failed identifiers. The engine raises on
failure; the UI calls the same function to render a localized message (REQ-024).

`allocation_sum` carries the signed difference `sum - 100` for the complete
single-turn engine contract. `allocation_exceeds_remaining` carries
`sum - remaining` so the UI can tell the player how many credits to remove.

## Step 2: Impact matrix

Coefficients express change **per 10 credits** invested. Rows are the investment
area; columns are the affected dimension.

| Investment ↓ / Effect → | ΔM | ΔC | ΔT | ΔS |
|---|---|---|---|---|
| Mobility | +1.0 | +0.4 | +0.3 | +0.2 |
| Culture | +0.2 | +1.0 | +0.5 | +0.4 |
| Tourism | +0.2 | +0.3 | +1.0 | 0.0 |
| Socio-demographic | +0.2 | +0.3 | −0.1 | +1.0 |

Compute the whole delta vector before changing any dimension, then add it to the
dimensions at the start of the turn:

$$\Delta_j = \sum_{i=0}^{3} \frac{b_i}{10} \cdot \text{Matrix}[i][j] \qquad d^{(2)} = d^{(\text{turn start})} + \Delta$$

Equivalently, `delta = (b / 10) @ MATRIX` with `MATRIX` in the row/column layout above.

**Atomicity is mandatory.** Accumulating into `M` and then reading the updated `M`
while computing `C` yields wrong results. Build `delta` first, then apply it once.

Do not clamp here. Intermediate values may exceed `100`; clamping happens at step 5.

## Step 3: Tourism pressure

Overtourism suppresses residential quality while tourism investment is active.
Evaluate against `T` **after** step 2, and apply only the highest matching tier.

| Condition on post-matrix `T` | Effect on `S` |
|---|---|
| `T > 85` | `S -= (B_T / 10) * 0.5` |
| `T > 70` (and not `> 85`) | `S -= (B_T / 10) * 0.2` |
| otherwise | no change |

Comparisons are strictly greater-than. Tiers never stack: `T = 90` applies only the
`0.5` coefficient.

When `B_T = 0` the reduction is zero, so a district that is already over the
threshold is not penalized here unless the player invested in tourism. The
threshold-independent consequence of high tourism is handled by the gap penalty in
step 6.

## Step 4: Event

Exactly one event applies per turn. Add its impact vector to the dimensions:

$$d^{(4)} = d^{(3)} + \text{impact}$$

Catalog impacts, in `(M, C, T, S)` order:

| Event ID | Impact |
|---|---|
| `transport_line` | `(+10, +2, 0, +2)` |
| `cultural_festival` | `(+2, +10, +8, 0)` |
| `tourist_boom` | `(0, 0, +10, −5)` |
| `housing_crisis` | `(0, 0, +2, −10)` |
| `heat_wave` | `(−2, −2, −2, −5)` |

Events are drawn with uniform probability from the catalog using the injected
generator (REQ-042). A round may also run with an explicitly chosen event, or with
no event at all, in which case the impact vector is treated as zero.

Event impacts are **not** re-run through the impact matrix and do **not** re-trigger
step 3.

## Step 5: Clamp

$$d^{(5)}_j = \min(100, \max(0, d^{(4)}_j))$$

All later steps use the clamped values.

## Step 6: Modifiers

Compute each modifier independently from the current dimensions and the
**cumulative allocation** `B`. Return it as an itemized record carrying its
identifier, its signed point value, and the data that triggered it (REQ-035, REQ-058).
Modifiers do not short-circuit one another; the total is their sum.

Let `σ` be the **population** standard deviation (divide by `n`, not `n − 1`) of the
four clamped dimension values.

**Equilibrium** — identifier `equilibrium`:

| Condition | Points |
|---|---|
| `σ < 10` | `+10` |
| `10 ≤ σ < 15` | `+5` |
| `15 ≤ σ ≤ 25` | `0` |
| `σ > 25` | `−5` |

**Overtourism gap** — identifier `overtourism_gap`, evaluated on clamped `T` and `S`,
highest tier only:

| Condition | Points |
|---|---|
| `T > S + 40` | `−10` |
| `T > S + 25` (and not `> S + 40`) | `−5` |
| otherwise | `0` |

**Concentration** — identifier `concentration`:

| Condition | Points |
|---|---|
| `max(b) > 60` | `−5` |
| otherwise | `0` |

Flat penalty. It applies once no matter how many allocations exceed 60.

**Diversification** — identifier `diversification`, where `k` is the count of
allocations strictly greater than zero:

| Condition | Points |
|---|---|
| `k = 4` | `+5` |
| `k = 3` | `+2` |
| `k ≤ 2` | `0` |

> **Assumption.** The brief specifies a "low" and "high" diversification bonus without
> numbers. `+2` and `+5` are chosen so the bonus rewards breadth without dominating
> the `±10` equilibrium band. Keep both values in the constants module so a
> research-backed figure can replace them (REQ-080).

## Step 7: RIz

Weights are equal and must sum to `1.0`:

$$w = (0.25,\ 0.25,\ 0.25,\ 0.25)$$

$$\text{RIz}_{\text{base}} = \sum_j w_j \cdot d^{(5)}_j$$

$$\text{RIz}_{\text{final}} = \min\left(100,\ \max\left(0,\ \text{RIz}_{\text{base}} + \sum \text{modifiers}\right)\right)$$

The **initial RIz** is always the weighted sum of the original district baseline
with **no** modifiers, clamped to `0..100`. The final RIz uses the dimensions after
the latest turn and modifiers derived from the cumulative allocation. This makes
yield cumulative across the round.

## Step 8: Metrics

| Metric | Definition |
|---|---|
| Urban yield `R` | `RIz_final − RIz_initial` |
| Urban risk | `σ` of the clamped final dimensions, population standard deviation |
| Urban Sharpe | `R / risk` when `risk > 1e-9`, otherwise `0.0` |
| Percentage change | `(R / RIz_initial) × 100`, or `0.0` when `RIz_initial` is zero |

Yield is signed. A negative yield is a valid, meaningful result and must display as
such rather than being floored at zero.

Guarding the Sharpe denominator with a tolerance rather than `!= 0` avoids an
overflow when all four dimensions are nearly identical.

## Urban profile

Evaluate in order and stop at the first match.

| Order | Condition | Profile ID | Italian | English |
|---|---|---|---|---|
| 1 | `yield ≤ 0` | `stagnant` | Città in Stallo | Stagnant City |
| 2 | `risk > 25` | `vulnerable` | Città Vulnerabile | Vulnerable City |
| 3 | `risk < 15` | `resilient` | Città Resiliente | Resilient City |
| 4 | otherwise | `transitional` | Città in Transizione | Transitional City |

> **Assumption.** The brief names only the first three profiles, which leaves
> `15 ≤ risk ≤ 25` with a positive yield unclassified. `transitional` closes that gap.
> Order matters: a high-scoring but wildly unbalanced city must read as vulnerable,
> and a city that gained nothing must read as stagnant regardless of its balance.

## Determinism

The engine never calls `random` or `numpy.random` at import time or at module level.
It accepts a generator (for example `numpy.random.Generator` or `random.Random`)
constructed by the caller.

- A seeded turn reproduces the same event, the same random benchmark allocation, and
  the same scores (REQ-037).
- Tests pass an explicit seed where the draw itself is under test.
- The Streamlit layer completes and stores a turn atomically, so a re-render does
  not silently redraw its event.

## Benchmark strategy fairness

Both benchmarks receive the same turn budget as the player, obey every rule in
step 1, and allocate before the event is drawn (REQ-054, REQ-055).

### AI strategy

Deterministic heuristic, computed from the baseline dimensions only:

1. Split the turn budget as evenly as integers allow, assigning remainder credits
   to the lowest indices first. A 100-credit turn starts at `[25, 25, 25, 25]`.
2. **Overtourism guard.** If `T0 > S0 + 10`, move up to `10` available credits
   from tourism to socio-demographic.
3. **Weakest-dimension lift.** Let `lo` be the index of the lowest current value and
   `hi` the index of the highest. Break ties by lowest index. If `lo != hi`, move `5`
   credits from `hi` to `lo`, but skip the move if it would push the source below `0`
   or the target above `60`.
4. The result must still sum to `100` with every allocation in `0..60`.

Worked example for San Lorenzo `(55, 40, 80, 35)`: even split → overtourism guard
gives `[25, 25, 15, 35]` → lift moves 5 from `T` (highest, 80) to `S` (lowest, 35) →
**`[25, 25, 10, 40]`**.

### Random strategy

Draw four weights from a Dirichlet distribution with concentration `1.0` using the
injected generator, scale by the current turn budget, then convert to integers with the
**largest-remainder method**:

1. Take the floor of each scaled weight.
2. Compute `remainder = turn_budget − sum(floors)`.
3. Give one extra credit to each of the `remainder` indices with the largest
   fractional parts, breaking ties by lowest index.

Naive rounding does not reliably sum to the supplied turn budget and would fail
validation.

## Precision and display

- Keep full float precision through every step. Never round intermediate values.
- Display dimension values, deltas, RIz, yield, and risk to **one decimal**.
- Display the Sharpe ratio to **two decimals**.
- Render deltas with an explicit sign, including `+0.0` for a rounded-to-zero gain.
- Compare floats in tests with a tolerance, not equality.

## Golden example

Use this as a regression test. It exercises the matrix, tourism pressure, the gap
penalty, diversification, and a negative yield.

**Input** — a single-turn round for district San Lorenzo
`d⁰ = (55, 40, 80, 35)`, allocation `b = (25, 25, 25, 25)`, no event.

| Step | Result |
|---|---|
| Matrix delta | `(+4.0, +5.0, +4.25, +4.0)` |
| After matrix | `(59.0, 45.0, 84.25, 39.0)` |
| Tourism pressure | `T = 84.25 > 70`, so `S -= 2.5 × 0.2 = 0.5` → `S = 38.5` |
| After event | unchanged, no event |
| After clamp | `(59.0, 45.0, 84.25, 38.5)` |
| `σ` (population) | `≈ 17.5529` |
| Equilibrium | `15 ≤ σ ≤ 25` → `0` |
| Overtourism gap | `84.25 > 38.5 + 40 = 78.5` → `−10` |
| Concentration | `max(b) = 25` → `0` |
| Diversification | `k = 4` → `+5` |
| Modifier total | `−5` |
| `RIz_base` | `56.6875` |
| `RIz_final` | `51.6875` |
| `RIz_initial` | `52.5` |
| Yield | `−0.8125` |
| Risk | `≈ 17.5529` |
| Sharpe | `≈ −0.0463` |
| Profile | `stagnant` (yield ≤ 0) |

The even split loses points here: San Lorenzo already has a severe tourism-to-resident
gap, and spreading credits evenly cannot close it. This is intended game design, and
it is why the AI heuristic shifts credits away from tourism.
