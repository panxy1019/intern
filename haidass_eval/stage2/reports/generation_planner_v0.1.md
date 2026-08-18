# Stage 2 Generation Planner v0.1

## Scope and status

This stage implements deterministic planning only. It does not call a generator, deploy a model, create synthetic samples, verify generated data, or start training.

- Pilot weakness seeds: **40**
- Generation plans: **2000**
- Compiled generator prompts: **2000**
- Expected independent scenarios: **8000**
- Expected raw multi-view examples: **10000**
- Validation status: **valid**
- Axis-combination repeat rate: **0.00%**

## Architecture

```text
Stage 1 training-safe seeds + prototypes + frozen taxonomy
    -> deterministic qualification and stratified seed selection
    -> capability-aware diversity space
    -> balanced orthogonal axis sampler
    -> multi-view policy
    -> GenerationPlan JSONL
    -> deterministic Prompt Compiler
    -> compiled prompt manifest (no model call)
```

Generation Plan is defined as `Weakness Seed x Orthogonally Sampled Content/Reasoning/Negative Axes x Multi-view Supervision Policy`. Content variation and supervision representation are stored separately so a view change cannot silently change the latent weakness.

## Seed qualification

The selector excludes calibration, noise/ambiguity artifacts, empty or `other` sub-capabilities, labels outside the frozen taxonomy, support below three, confidence below 0.85, and invariants containing source identifiers, digits, benchmark terms, or likely named entities. It then fills fixed capability quotas with mechanism/operation/distractor diversity and reserves one trusted long-tail slot per eligible capability.

- Input Stage 1 seeds: 1227
- Qualified candidates: 174
- Qualifications: `{"A": 12, "B": 12, "LONG_TAIL": 16}`

### Rejection reasons

| Value | Count |
|---|---:|
| `insufficient_support` | 763 |
| `capability_not_supported_in_pilot` | 106 |
| `empty_or_other_sub_capability` | 84 |
| `unreliable_or_specific_invariant` | 47 |
| `excluded_failure_family_or_artifact` | 26 |
| `noncanonical_label` | 14 |
| `low_confidence` | 13 |

### Capability coverage

| Value | Count |
|---|---:|
| `procedural_reasoning` | 9 |
| `discourse_coherence` | 6 |
| `semantic_reasoning` | 6 |
| `narrative_reasoning` | 6 |
| `physical_reasoning` | 6 |
| `state_tracking` | 5 |
| `temporal_reasoning` | 2 |

### Failure-mechanism coverage

| Value | Count |
|---|---:|
| `surface_similarity_override` | 8 |
| `over_reliance_on_generic_script` | 4 |
| `surface_level_topic_matching_override` | 3 |
| `over_reliance_on_surface_lexical_cues` | 3 |
| `surface_form_over_semantic_state` | 3 |
| `surface_level_semantic_association_override` | 3 |
| `surface_level_topic_matching_over_semantic_absurdity` | 3 |
| `over_reliance_on_surface_plausibility_and_general_knowledge` | 3 |
| `temporal_constraint_neglect` | 3 |
| `over_reliance_on_surface_action_similarity` | 2 |
| `over_reliance_on_surface_lexical_overlap` | 1 |
| `over_reliance_on_surface_similarity` | 1 |
| `literal_semantic_bias_ignoring_safety` | 1 |
| `overweighting_salient_action_verbs` | 1 |
| `over_reliance_on_generic_fitness_language` | 1 |

## Planning behavior

Every seed receives exactly 50 plans, regardless of how many weakness-specific axes it supports. Axis values use deterministic coprime rotations with seed-specific offsets, producing balanced marginals without a Cartesian-product advantage for high-dimensional weaknesses.

### Plans per weakness

| Value | Count |
|---|---:|
| `WKN_BC219538` | 50 |
| `WKN_4214D576` | 50 |
| `WKN_B29B36B8` | 50 |
| `WKN_3397A7CC` | 50 |
| `WKN_1146728E` | 50 |
| `WKN_331BC3AC` | 50 |
| `WKN_4EBE7B65` | 50 |
| `WKN_00DD1694` | 50 |
| `WKN_3C017A32` | 50 |
| `WKN_A041B388` | 50 |
| `WKN_B82946BD` | 50 |
| `WKN_23D0F1C0` | 50 |
| `WKN_44540A08` | 50 |
| `WKN_03261741` | 50 |
| `WKN_88CE4792` | 50 |
| `WKN_149E33E0` | 50 |
| `WKN_158DD736` | 50 |
| `WKN_ED203B2F` | 50 |
| `WKN_97E12526` | 50 |
| `WKN_01E4708F` | 50 |
| `WKN_EBC7927C` | 50 |
| `WKN_DF69CAA9` | 50 |
| `WKN_B1057194` | 50 |
| `WKN_9C9895C2` | 50 |
| `WKN_9767168B` | 50 |
| `WKN_07AB8736` | 50 |
| `WKN_12331C38` | 50 |
| `WKN_B3B3832A` | 50 |
| `WKN_6059D2DE` | 50 |
| `WKN_1913AB79` | 50 |
| `WKN_AFC0089D` | 50 |
| `WKN_BB33C466` | 50 |
| `WKN_6470F5CA` | 50 |
| `WKN_FBE5C9A0` | 50 |
| `WKN_B8B99B3E` | 50 |
| `WKN_2558B785` | 50 |
| `WKN_26F6FB6D` | 50 |
| `WKN_27FE06BB` | 50 |
| `WKN_7720F352` | 50 |
| `WKN_B0E5ADE3` | 50 |

### Domain distribution

| Value | Count |
|---|---:|
| `education_and_training` | 171 |
| `food_service` | 171 |
| `logistics_and_delivery` | 169 |
| `community_events` | 169 |
| `crafts_and_fabrication` | 168 |
| `retail_and_inventory` | 167 |
| `public_services` | 166 |
| `travel_and_navigation` | 166 |
| `household_maintenance` | 165 |
| `outdoor_activities` | 164 |
| `digital_workflows` | 163 |
| `workplace_operations` | 161 |

### Narrative-style distribution

| Value | Count |
|---|---:|
| `stepwise_account` | 335 |
| `instructional_note` | 334 |
| `concise_observation` | 333 |
| `dialogue_fragment` | 333 |
| `incident_report` | 333 |
| `reflective_narration` | 332 |

### Difficulty distribution

| Value | Count |
|---|---:|
| `4` | 400 |
| `5` | 400 |
| `1` | 400 |
| `2` | 400 |
| `3` | 400 |

### Primary-view distribution

| Value | Count |
|---|---:|
| `error_detection` | 419 |
| `multiple_choice` | 413 |
| `continuation` | 340 |
| `counterfactual` | 338 |
| `pairwise_preference` | 284 |
| `ordering` | 206 |

### Secondary-view distribution

| Value | Count |
|---|---:|
| `multiple_choice` | 424 |
| `error_detection` | 416 |
| `continuation` | 339 |
| `counterfactual` | 339 |
| `pairwise_preference` | 279 |
| `ordering` | 203 |

### Primary distractor strategies

| Value | Count |
|---|---:|
| `topic_shift_with_shared_vocabulary` | 284 |
| `plausible_irrelevant_continuation` | 283 |
| `related_but_goal_inconsistent` | 283 |
| `correct_action_at_wrong_time` | 117 |
| `completed_state_repetition` | 117 |
| `temporally_misordered_valid_event` | 116 |
| `material_property_violation` | 89 |
| `affordance_mismatch` | 88 |
| `plausible_but_unsafe_action` | 87 |
| `constraint_violating_action` | 86 |
| `salient_action_match` | 76 |
| `topical_overlap_decoy` | 76 |
| `lexical_overlap_decoy` | 74 |
| `paraphrase_without_constraint_satisfaction` | 74 |
| `hidden_precondition_violation` | 51 |
| `stale_state_action` | 50 |
| `locally_plausible_but_globally_invalid_transition` | 49 |

### Answer-length profiles

| Value | Count |
|---|---:|
| `valid_longer` | 501 |
| `matched_structure` | 501 |
| `balanced` | 499 |
| `valid_shorter` | 499 |

## Multi-view contract

Each prompt requests four semantically independent scenarios. Every scenario receives one primary view; exactly one of the four receives the configured secondary view. Thus each prompt is expected to yield four scenarios and five raw supervision examples without rendering every scenario into all six views. View allowlists are capability-aware; for example, physical-affordance seeds never use `ordering` as a primary view.

## Prompt compiler

The compiler is a local `string.Template` transformation. It inserts only training-safe weakness fields and sampled axes. The prompt requires structured scenario output with `scenario_id`, `latent_structure`, `context`, `current_state`, `goal`, `valid_transition`, `invalid_transition`, and `views`. It prohibits source benchmark reuse, memorized benchmark style, copied entities, and entity/number-only rewrites.

## Validation

- Unique plan IDs: 2000 / 2000
- Unique prompt IDs: 2000 / 2000
- Duplicate axis combinations: 0
- Errors: `[]`

## Human-review sample

A deterministic random sample of 30 plan/prompt pairs is stored in `stage2/reports/review_samples_v0.1.jsonl`. Reviewers should confirm invariant preservation across domains, non-template scenario constraints, view/latent separation, hard-negative alignment, and contamination isolation.

| Plan | Weakness | Domain | Style | Primary | Secondary |
|---|---|---|---|---|---|
| `GPL_0CA63F30A734` | `WKN_BC219538` | `logistics_and_delivery` | `instructional_note` | `continuation` | `multiple_choice` |
| `GPL_6E21FBCE7B8D` | `WKN_1146728E` | `education_and_training` | `dialogue_fragment` | `ordering` | `error_detection` |
| `GPL_DFC7DFB4AD89` | `WKN_1146728E` | `logistics_and_delivery` | `concise_observation` | `multiple_choice` | `error_detection` |
| `GPL_6AE4FB61B00D` | `WKN_3C017A32` | `community_events` | `dialogue_fragment` | `pairwise_preference` | `multiple_choice` |
| `GPL_89B6D0E080D8` | `WKN_A041B388` | `food_service` | `dialogue_fragment` | `error_detection` | `multiple_choice` |
| `GPL_FD0AF0A12ACD` | `WKN_A041B388` | `logistics_and_delivery` | `stepwise_account` | `continuation` | `multiple_choice` |
| `GPL_D9C426E9A12B` | `WKN_B82946BD` | `travel_and_navigation` | `instructional_note` | `continuation` | `error_detection` |
| `GPL_E96F6F079875` | `WKN_23D0F1C0` | `crafts_and_fabrication` | `reflective_narration` | `error_detection` | `pairwise_preference` |
| `GPL_8DD7D3579FF4` | `WKN_44540A08` | `travel_and_navigation` | `concise_observation` | `error_detection` | `multiple_choice` |
| `GPL_27E6F8D394F4` | `WKN_03261741` | `workplace_operations` | `reflective_narration` | `error_detection` | `continuation` |
| `GPL_DF03DB57A035` | `WKN_88CE4792` | `community_events` | `concise_observation` | `error_detection` | `continuation` |
| `GPL_CCFA28345587` | `WKN_97E12526` | `retail_and_inventory` | `concise_observation` | `error_detection` | `counterfactual` |
| `GPL_F2F0A280F0FC` | `WKN_EBC7927C` | `community_events` | `concise_observation` | `multiple_choice` | `pairwise_preference` |
| `GPL_4B1A9D1501FB` | `WKN_EBC7927C` | `crafts_and_fabrication` | `stepwise_account` | `pairwise_preference` | `counterfactual` |
| `GPL_49F57754163E` | `WKN_B1057194` | `digital_workflows` | `instructional_note` | `counterfactual` | `continuation` |
| `GPL_969A47CD4A41` | `WKN_9767168B` | `digital_workflows` | `instructional_note` | `continuation` | `error_detection` |
| `GPL_AF76B75FBEE5` | `WKN_07AB8736` | `public_services` | `concise_observation` | `multiple_choice` | `error_detection` |
| `GPL_301E9918E98C` | `WKN_07AB8736` | `crafts_and_fabrication` | `reflective_narration` | `multiple_choice` | `counterfactual` |
| `GPL_487EA1315A1E` | `WKN_07AB8736` | `outdoor_activities` | `stepwise_account` | `ordering` | `multiple_choice` |
| `GPL_9486A9A3B8D6` | `WKN_07AB8736` | `retail_and_inventory` | `incident_report` | `error_detection` | `counterfactual` |
| `GPL_039E9528A8CF` | `WKN_B3B3832A` | `outdoor_activities` | `instructional_note` | `pairwise_preference` | `counterfactual` |
| `GPL_09CF5226E66C` | `WKN_B3B3832A` | `crafts_and_fabrication` | `dialogue_fragment` | `counterfactual` | `multiple_choice` |
| `GPL_9BBD419982A4` | `WKN_6059D2DE` | `education_and_training` | `stepwise_account` | `error_detection` | `counterfactual` |
| `GPL_F1468C3DCD3E` | `WKN_1913AB79` | `public_services` | `dialogue_fragment` | `multiple_choice` | `pairwise_preference` |
| `GPL_C371901C4878` | `WKN_BB33C466` | `retail_and_inventory` | `dialogue_fragment` | `counterfactual` | `multiple_choice` |
| `GPL_5D44D798FCF5` | `WKN_BB33C466` | `digital_workflows` | `reflective_narration` | `error_detection` | `multiple_choice` |
| `GPL_C3636145EF4E` | `WKN_6470F5CA` | `education_and_training` | `concise_observation` | `error_detection` | `pairwise_preference` |
| `GPL_A8EF741CFE89` | `WKN_B8B99B3E` | `public_services` | `stepwise_account` | `multiple_choice` | `ordering` |
| `GPL_03251B9F11D9` | `WKN_26F6FB6D` | `public_services` | `dialogue_fragment` | `error_detection` | `ordering` |
| `GPL_E23CB5FB31AC` | `WKN_27FE06BB` | `outdoor_activities` | `incident_report` | `continuation` | `multiple_choice` |

## Reproduction

```bash
cd /home/admin/Desktop/sql/haidass_eval/phase3/lighteval-mindspeed/badcase_synthesis
.venv/bin/python src/stage2_planner.py --root .
.venv/bin/python -m unittest discover -s tests -v
```

The run is deterministic: unchanged inputs, taxonomy, template, and seed produce byte-stable plan and prompt manifests.

## Limitations and P0 generation gate

This pilot inherits unresolved Stage 1 taxonomy synonym splitting, so it restricts seeds through canonical membership and evidence filters but does not rewrite Stage 1 labels. Human review of the 30-pair sample is required before P0 generation. Generator execution, verification, training, and any model deployment remain explicitly out of scope.
