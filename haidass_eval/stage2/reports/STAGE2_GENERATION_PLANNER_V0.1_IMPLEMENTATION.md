# Stage 2 Generation Planner v0.1 Implementation Guide

## 1. Purpose and boundary

Stage 2 v0.1 converts the abstract, training-safe Stage 1 weakness bank into a
deterministic generation manifest. It produces plans and prompts only:

```text
Stage 1 safe seeds + prototypes + frozen taxonomy
    -> qualified pilot seeds
    -> capability-aware diversity axes
    -> balanced orthogonal sampling
    -> multi-view policy
    -> generation plans
    -> compiled prompt manifest
```

This implementation does **not** call a local or remote model, generate a
synthetic scenario, run a verifier, start training, or deploy serving
infrastructure. The compiled prompts are inert JSONL records awaiting human
review.

## 2. Final output

The validated run contains:

| Artifact | Count | Purpose |
|---|---:|---|
| Qualified weakness seeds | 40 | Balanced semantic weakness pilot |
| Generation plans | 2,000 | 50 plans for every seed |
| Compiled prompts | 2,000 | One deterministic prompt per plan |
| Future independent scenarios | 8,000 | Four requested by every prompt |
| Future multi-view examples | 10,000 | Four primary plus one secondary per prompt |
| Human-review pairs | 30 | Deterministic manual-review sample |

No axis combination is repeated across the 2,000 plans.

## 3. Inputs and trust boundaries

The planner reads three Stage 1 products:

```text
data/training_safe/weakness_seeds_stage1.jsonl
prototypes/weakness_prototypes_v1.jsonl
taxonomy/failure_taxonomy_v1.yaml
taxonomy/distractor_taxonomy_v1.yaml
```

The training-safe seed supplies the abstract weakness. Prototype statistics are
used only for support and confidence qualification. Frozen taxonomy files are
used as allowlists for capability, sub-capability, reasoning operation, failure
mechanism, and distractor type.

The Stage 2 pilot export deliberately omits Stage 1 `required_reasoning` because
some historical values contain source-specific descriptions. Generator prompts
receive only the vetted semantic invariant and canonical weakness labels.

## 4. Seed qualification

A candidate is rejected when any of the following applies:

- capability is calibration, noise robustness, or outside the pilot quotas;
- sub-capability is empty, unknown, or `other`;
- any controlled label is absent from the frozen taxonomy;
- prototype support is below three;
- mean attribution confidence is below 0.85;
- semantic invariant is empty, excessively short/long, or contains a number;
- semantic invariant contains source identifiers, benchmark terms, likely named
  entities, or a known concrete source-scenario marker.

Candidates are selected against fixed capability quotas. Within each quota, the
selector rewards failure-mechanism, reasoning-operation, and distractor-type
coverage instead of simply choosing the most frequent weaknesses. One trusted
long-tail slot is reserved where the capability has an eligible candidate.

The exact qualification audit, including every rejection count, is stored in:

```text
stage2/reports/generation_planner_v0.1.run.json
```

## 5. Diversity space

Global axes change scenario content and reasoning conditions:

```text
domain
scenario_family
persona
narrative_style
difficulty
context_length
state_explicitness
answer_length_profile
noise_profile
```

Weakness-specific axes are selected by capability family:

| Family | Additional axes |
|---|---|
| Procedural | dependency depth, completed steps, action distance |
| Temporal | event count, temporal distance, cue explicitness |
| Physical | affordance type, material constraint, tool constraint |
| Causal/state | dependency depth, hidden state, counterfactual condition |
| Discourse/narrative | discourse span, continuity constraint, distractor distance |
| Semantic/goal | constraint count, conflict type, evidence explicitness |

The complete vocabulary is versioned in
`stage2/planning/diversity_axes_v0.1.yaml`.

## 6. Orthogonal sampling

Every weakness receives exactly 50 plans. For each axis, the planner computes a
stable seed-specific offset and a step coprime to the axis cardinality. Plan
index `i` selects:

```text
value[(offset + i * coprime_step) mod axis_size]
```

This yields balanced marginals, deterministic output, and broad combinations
without materializing a Cartesian product. A weakness with more applicable axes
does not receive more plans. Plan IDs are stable hashes of planner version,
weakness ID, and per-seed plan index.

## 7. Multi-view policy

Supported views are:

```text
continuation
multiple_choice
pairwise_preference
error_detection
ordering
counterfactual
```

Each future scenario has one primary view. Exactly one of the four scenarios in
a compiled prompt additionally has one secondary view, implementing the 25%
secondary-view target exactly rather than probabilistically at execution time.
The latent state, goal, valid transition, invalid transition, and weakness must
remain unchanged when rendered into a second view.

View allowlists are capability-aware. In particular, physical reasoning plans
do not force `ordering` as a primary view.

## 8. Generation Plan contract

Each line of `generation_plans_v0.1.jsonl` is an independent JSON object with:

```text
schema_version
plan_id, weakness_id
seed_evidence
weakness
content_axes
reasoning_axes
negative_axes
view_policy
generation
```

`content_axes` describes the scenario surface. `reasoning_axes` describes the
latent difficulty and capability-specific constraints. `negative_axes`
describes hard-negative construction. `view_policy` changes only supervision
representation. Keeping these sections separate prevents a view change from
silently changing the weakness being trained.

## 9. Prompt compiler

The compiler is a local `string.Template` transform implemented in
`src/stage2_planner.py`. It does not call an LLM. The versioned source template
is `stage2/templates/generator_prompt_v0.1.txt`.

Every compiled prompt requires exactly four semantically independent scenarios
and the following structured fields:

```text
scenario_id
latent_structure
context
current_state
goal
valid_transition
invalid_transition
views[]
```

The prompt rejects entity-only, number-only, paraphrase-only, and shared-template
variants. It also prohibits copying or reconstructing source evaluation items,
contexts, choices, answers, identifiers, named entities, distinctive numbers,
or source-specific wording.

## 10. Validation and reproducibility

The planner fails before publishing an invalid manifest. Validation checks:

- exact seed, plan, and prompt counts;
- one-to-one plan/prompt mapping;
- globally unique plan and prompt IDs;
- exactly 50 plans per weakness;
- distinct primary and secondary views;
- capability-specific view restrictions;
- forbidden source markers in compiled prompts;
- duplicate complete axis combinations;
- expected scenario and example totals.

The test suite additionally verifies deterministic planning, physical-view
restrictions, prompt output fields, and omission of source-specific reasoning
from the pilot contract. Two consecutive runs with unchanged inputs produce
byte-identical seeds, axes, plans, prompts, samples, and report files.

## 11. Run and inspect

Run the complete planner and tests:

```bash
cd /home/admin/Desktop/sql/haidass_eval/phase3/lighteval-mindspeed/badcase_synthesis
bash scripts/run_stage2_planner.sh
```

Run the planner alone:

```bash
.venv/bin/python src/stage2_planner.py --root .
```

Inspect the manual-review set:

```bash
less stage2/reports/review_samples_v0.1.jsonl
```

Inspect aggregate distributions and the 30 selected plan IDs:

```bash
less stage2/reports/generation_planner_v0.1.md
```

## 12. Output inventory

```text
stage2/
├── planning/
│   ├── diversity_axes_v0.1.yaml
│   └── generation_plans_v0.1.jsonl
├── prompts/
│   └── compiled_prompts_v0.1.jsonl
├── reports/
│   ├── generation_planner_v0.1.md
│   ├── generation_planner_v0.1.run.json
│   ├── review_samples_v0.1.jsonl
│   └── STAGE2_GENERATION_PLANNER_V0.1_IMPLEMENTATION.md
├── seeds/
│   └── pilot_weakness_seeds_v0.1.jsonl
└── templates/
    └── generator_prompt_v0.1.txt
```

## 13. Human-review gate before P0 generation

Reviewers should inspect all 30 sampled plan/prompt pairs and confirm:

1. the same invariant survives changes in domain and narrative style;
2. plans express materially different constraints, not simple word swaps;
3. the secondary view changes representation only;
4. hard negatives align with the failure and distractor mechanisms;
5. no source item, entity, number, or recoverable phrasing is present;
6. four future scenarios can be independently realized from each prompt.

Only after this review should a separate P0 generation stage consume the prompt
manifest. Generator execution, synthetic-data verification, deduplication,
training export, and model training remain outside v0.1.
