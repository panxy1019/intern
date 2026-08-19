# P0 Lightweight Validation + Final Training Format Rendering

- Input records: 10000
- Passed records: 9990
- Rejected records: 10
- Messages records: 9990
- Prompt/text records: 9990
- Unique weaknesses: 40

## View distribution

- continuation: 1698
- counterfactual: 1691
- error_detection: 2092
- multiple_choice: 2073
- ordering: 1026
- pairwise_preference: 1410

## Role distribution

- primary: 7994
- secondary: 1996

## Rejection reasons

- duplicate_options_or_pairs: 6
- options_or_pairs_too_short: 3
- options_or_pairs_not_list: 1

### continuation samples

- example_id: `PRM_1CDED7D924F0:scenario-04:continuation:secondary`
- weakness_id: `WKN_46DB2D85`
- view_role: `secondary`

Canonical source:

```json
{
  "context": "A research assistant is asking a senior archivist how to find a specific historical map. The archivist says, 'That map is in the fragile collection. Do not go to the physical stacks. The handling risks damage. Use the digital catalog to retrieve the high-resolution scan. It is fully indexed and available online. Do not physically locate the item unless the scan is corrupted.' The assistant has access to both the computer and the key to the stacks.",
  "current_state": "The assistant needs the map for a presentation. The digital catalog is open. The key to the physical stacks is in the assistant's pocket.",
  "goal": "Obtain the map content without risking damage to the fragile physical document.",
  "view": {
    "view_type": "continuation",
    "instruction": "Select the next logical step for the assistant that adheres to the archivist's recommendation.",
    "input": "What should the assistant do next?",
    "target": "The action that utilizes the digital catalog.",
    "options_or_pairs": [
      "The assistant unlocks the physical stacks door.",
      "The assistant searches the digital catalog for the map scan.",
      "The assistant asks for a physical copy to be printed.",
      "The assistant waits for the archivist to bring the map."
    ],
    "shortcut_control": null
  }
}
```

Rendered prompt:

```text
A research assistant is asking a senior archivist how to find a specific historical map. The archivist says, 'That map is in the fragile collection. Do not go to the physical stacks. The handling risks damage. Use the digital catalog to retrieve the high-resolution scan. It is fully indexed and available online. Do not physically locate the item unless the scan is corrupted.' The assistant has access to both the computer and the key to the stacks.

Current state: The assistant needs the map for a presentation. The digital catalog is open. The key to the physical stacks is in the assistant's pocket.

Goal: Obtain the map content without risking damage to the fragile physical document.

Select the next logical step for the assistant that adheres to the archivist's recommendation.

What should the assistant do next?

Options:

- The assistant unlocks the physical stacks door.

- The assistant searches the digital catalog for the map scan.

- The assistant asks for a physical copy to be printed.

- The assistant waits for the archivist to bring the map.
```

Rendered target:

```text
The action that utilizes the digital catalog.
```

- example_id: `PRM_F68045740012:scenario-02:continuation:primary`
- weakness_id: `WKN_ED203B2F`
- view_role: `primary`

Canonical source:

```json
{
  "context": "Two hikers are stranded in a snowy forest after a sudden storm. One is a novice who is beginning to shiver uncontrollably. The other is an experienced guide.",
  "current_state": "The novice is losing body heat rapidly and is at risk of hypothermia, but does not yet realize the severity.",
  "goal": "Prevent the novice from developing hypothermia and maintain core body temperature.",
  "view": {
    "view_type": "continuation",
    "instruction": "Select the response that correctly prioritizes the physiological survival goal over social comfort.",
    "input": "Novice: 'I feel so cold, my fingers are going numb.' Guide: 'We need to act fast. What is the most important thing you need to do right now?'",
    "target": "The guide should advise putting on dry layers and consuming calories to maintain core temperature.",
    "options_or_pairs": [],
    "shortcut_control": null
  }
}
```

Rendered prompt:

```text
Two hikers are stranded in a snowy forest after a sudden storm. One is a novice who is beginning to shiver uncontrollably. The other is an experienced guide.

Current state: The novice is losing body heat rapidly and is at risk of hypothermia, but does not yet realize the severity.

Goal: Prevent the novice from developing hypothermia and maintain core body temperature.

Select the response that correctly prioritizes the physiological survival goal over social comfort.

Novice: 'I feel so cold, my fingers are going numb.' Guide: 'We need to act fast. What is the most important thing you need to do right now?'

Options:
```

Rendered target:

```text
The guide should advise putting on dry layers and consuming calories to maintain core temperature.
```

- example_id: `PRM_F568327060C2:scenario-01:continuation:primary`
- weakness_id: `WKN_9C9895C2`
- view_role: `primary`

Canonical source:

```json
{
  "context": "Technician's note: 'Step 1: Execute ALTER TABLE commands to add new columns. Step 2: [MISSING]. Step 3: Verify data consistency in the new columns.'",
  "current_state": "The ALTER TABLE commands have been successfully executed, and the schema is updated.",
  "goal": "Identify the immediate next procedural step in the migration workflow.",
  "view": {
    "view_type": "continuation",
    "instruction": "Select the action that logically follows the completion of Step 1 in the provided note.",
    "input": "The note indicates Step 1 (Schema Alteration) is complete. What is Step 2?",
    "target": "Run the data population script to fill the new columns.",
    "options_or_pairs": [
      "Run the data population script to fill the new columns.",
      "Initiate a full system backup to ensure safety before proceeding."
    ],
    "shortcut_control": null
  }
}
```

Rendered prompt:

```text
Technician's note: 'Step 1: Execute ALTER TABLE commands to add new columns. Step 2: [MISSING]. Step 3: Verify data consistency in the new columns.'

Current state: The ALTER TABLE commands have been successfully executed, and the schema is updated.

Goal: Identify the immediate next procedural step in the migration workflow.

Select the action that logically follows the completion of Step 1 in the provided note.

The note indicates Step 1 (Schema Alteration) is complete. What is Step 2?

Options:

- Run the data population script to fill the new columns.

- Initiate a full system backup to ensure safety before proceeding.
```

Rendered target:

```text
Run the data population script to fill the new columns.
```


### counterfactual samples

- example_id: `PRM_EFF718325970:scenario-03:counterfactual:primary`
- weakness_id: `WKN_1C0010E4`
- view_role: `primary`

Canonical source:

```json
{
  "context": "I am a student in a biology lab. I am cleaning the microscope stage. A thin, fragile glass slide is stuck under the stage clips due to a small amount of dried liquid. The slide is not broken yet, but it is very thin.",
  "current_state": "The slide is trapped under the metal clips. The liquid has dried, creating a mild adhesive bond. The glass is fragile.",
  "goal": "Remove the glass slide from the microscope stage without breaking it.",
  "view": {
    "view_type": "counterfactual",
    "instruction": "If the student used the metal spatula to pry the slide, what would be the physical result for the glass?",
    "input": "A metal spatula is inserted under the edge of the fragile glass slide and used to pry it up.",
    "target": "The lateral force applied by the prying action exceeds the shear strength of the thin glass, causing it to crack or shatter.",
    "options_or_pairs": [],
    "shortcut_control": {
      "field": "counterfactual_polarity",
      "value": "positive",
      "view": "counterfactual"
    }
  }
}
```

Rendered prompt:

```text
I am a student in a biology lab. I am cleaning the microscope stage. A thin, fragile glass slide is stuck under the stage clips due to a small amount of dried liquid. The slide is not broken yet, but it is very thin.

Current state: The slide is trapped under the metal clips. The liquid has dried, creating a mild adhesive bond. The glass is fragile.

Goal: Remove the glass slide from the microscope stage without breaking it.

If the student used the metal spatula to pry the slide, what would be the physical result for the glass?

A metal spatula is inserted under the edge of the fragile glass slide and used to pry it up.
```

Rendered target:

```text
The lateral force applied by the prying action exceeds the shear strength of the thin glass, causing it to crack or shatter.
```

- example_id: `PRM_28AF9BDEFB46:scenario-01:counterfactual:primary`
- weakness_id: `WKN_724E3F9E`
- view_role: `primary`

Canonical source:

```json
{
  "context": "A DIY enthusiast is re-sealing the joint between a bathroom sink and the countertop. They have just finished cleaning the area and have selected a tube of high-quality silicone sealant. They are holding the tube and a utility knife.",
  "current_state": "The sink joint is clean and dry. The silicone sealant tube is uncapped and ready. The user is holding the tube.",
  "goal": "Identify the immediate next procedural step to continue the re-sealing process.",
  "view": {
    "view_type": "counterfactual",
    "instruction": "Evaluate the counterfactual scenario where the user ignores the current task context. If the user proceeds with the invalid transition, what is the primary procedural failure?",
    "input": "User selects 'Apply the silicone sealant to the window frame to check its consistency before using it on the sink.'",
    "target": "The user breaks the instructional sequence by introducing an unrelated location (window) and delaying the necessary preparation (cutting the tip) for the current task.",
    "options_or_pairs": [],
    "shortcut_control": {
      "field": "counterfactual_polarity",
      "value": "negative",
      "view": "counterfactual"
    }
  }
}
```

Rendered prompt:

```text
A DIY enthusiast is re-sealing the joint between a bathroom sink and the countertop. They have just finished cleaning the area and have selected a tube of high-quality silicone sealant. They are holding the tube and a utility knife.

Current state: The sink joint is clean and dry. The silicone sealant tube is uncapped and ready. The user is holding the tube.

Goal: Identify the immediate next procedural step to continue the re-sealing process.

Evaluate the counterfactual scenario where the user ignores the current task context. If the user proceeds with the invalid transition, what is the primary procedural failure?

User selects 'Apply the silicone sealant to the window frame to check its consistency before using it on the sink.'
```

Rendered target:

```text
The user breaks the instructional sequence by introducing an unrelated location (window) and delaying the necessary preparation (cutting the tip) for the current task.
```

- example_id: `PRM_C7C35A7E8B36:scenario-01:counterfactual:primary`
- weakness_id: `WKN_46DB2D85`
- view_role: `primary`

Canonical source:

```json
{
  "context": "I am a new logistics coordinator. My supervisor just sent a memo stating that due to the incoming storm, all outbound shipments from the North Hub must be held for 24 hours to ensure driver safety. I am looking at the dashboard, and I see 40 pending orders that are marked 'urgent' by the customers. The system is flashing red because these orders are approaching their SLA deadline. I feel a strong pressure to act before the deadline hits.",
  "current_state": "Supervisor has issued a 24-hour hold order for the North Hub due to weather. 40 urgent orders are pending and nearing SLA breach.",
  "goal": "Execute the correct logistical action in accordance with the supervisor's explicit safety directive.",
  "view": {
    "view_type": "counterfactual",
    "instruction": "Determine the counterfactual outcome if the operator ignored the supervisor's hold order and dispatched the vehicles instead.",
    "input": "The operator dispatches the 40 vehicles into the storm zone despite the hold order.",
    "target": "The vehicles encounter hazardous road conditions, leading to potential accidents or significant delays that far exceed the original SLA breach, violating the safety protocol.",
    "options_or_pairs": [],
    "shortcut_control": {
      "field": "counterfactual_polarity",
      "value": "negative",
      "view": "counterfactual"
    }
  }
}
```

Rendered prompt:

```text
I am a new logistics coordinator. My supervisor just sent a memo stating that due to the incoming storm, all outbound shipments from the North Hub must be held for 24 hours to ensure driver safety. I am looking at the dashboard, and I see 40 pending orders that are marked 'urgent' by the customers. The system is flashing red because these orders are approaching their SLA deadline. I feel a strong pressure to act before the deadline hits.

Current state: Supervisor has issued a 24-hour hold order for the North Hub due to weather. 40 urgent orders are pending and nearing SLA breach.

Goal: Execute the correct logistical action in accordance with the supervisor's explicit safety directive.

Determine the counterfactual outcome if the operator ignored the supervisor's hold order and dispatched the vehicles instead.

The operator dispatches the 40 vehicles into the storm zone despite the hold order.
```

Rendered target:

```text
The vehicles encounter hazardous road conditions, leading to potential accidents or significant delays that far exceed the original SLA breach, violating the safety protocol.
```


### error_detection samples

- example_id: `PRM_02A5E32A432A:scenario-04:error_detection:primary`
- weakness_id: `WKN_B3E4ABCB`
- view_role: `primary`

Canonical source:

```json
{
  "context": "Incident Report: Community Art Project. An artist was creating custom labels using a heated metal stamp (250°C) on a sheet of polycarbonate plastic. They pressed the stamp into the plastic to create a logo. Instead of a sharp, clean impression, the edges of the logo were blurry, and the plastic around the mark was raised and glossy. The artist's log entry read: 'Poked the logo into the plastic with the hot stamp.'",
  "current_state": "The metal stamp is at 250°C. The polycarbonate sheet is at room temperature. The stamp is pressed into the plastic surface.",
  "goal": "Correctly interpret the physical outcome of the stamp-plastic interaction to ensure the process is understood for future iterations.",
  "view": {
    "view_type": "error_detection",
    "instruction": "Review the artist's log and the physical result. Which of the following statements is physically inaccurate?",
    "input": "1. The heat caused the polycarbonate to soften, allowing it to deform under pressure. 2. The glossy appearance indicates the surface reached a temperature where it could flow. 3. The stamp acted as a cold die, mechanically imprinting the shape without changing the plastic's phase.",
    "target": "Statement 3 is the error. The heat is essential to the deformation process (melting/softening), not just a side effect.",
    "options_or_pairs": [],
    "shortcut_control": {
      "field": "error_detection_error_position",
      "value": "third",
      "view": "error_detection"
    }
  }
}
```

Rendered prompt:

```text
Incident Report: Community Art Project. An artist was creating custom labels using a heated metal stamp (250°C) on a sheet of polycarbonate plastic. They pressed the stamp into the plastic to create a logo. Instead of a sharp, clean impression, the edges of the logo were blurry, and the plastic around the mark was raised and glossy. The artist's log entry read: 'Poked the logo into the plastic with the hot stamp.'

Current state: The metal stamp is at 250°C. The polycarbonate sheet is at room temperature. The stamp is pressed into the plastic surface.

Goal: Correctly interpret the physical outcome of the stamp-plastic interaction to ensure the process is understood for future iterations.

Review the artist's log and the physical result. Which of the following statements is physically inaccurate?

1. The heat caused the polycarbonate to soften, allowing it to deform under pressure. 2. The glossy appearance indicates the surface reached a temperature where it could flow. 3. The stamp acted as a cold die, mechanically imprinting the shape without changing the plastic's phase.
```

Rendered target:

```text
Statement 3 is the error. The heat is essential to the deformation process (melting/softening), not just a side effect.
```

- example_id: `PRM_E7174CD21ADF:scenario-01:error_detection:primary`
- weakness_id: `WKN_BEB5BD94`
- view_role: `primary`

Canonical source:

```json
{
  "context": "A customer is troubleshooting a slow-draining kitchen sink. They have just finished the step of removing the stopper and checking for visible debris, finding the area clear but the water still draining slowly.",
  "current_state": "The stopper is removed and the immediate area is clear, but the clog persists deeper in the pipe.",
  "goal": "Provide the next specific troubleshooting step to address the persistent clog.",
  "view": {
    "view_type": "error_detection",
    "instruction": "Review the sequence of troubleshooting steps provided to the customer. Identify which step is the error that breaks topical coherence by shifting away from the immediate troubleshooting goal.",
    "input": "1. Remove the sink stopper and inspect the P-trap for visible debris. 2. If no debris is found, check the water level in the sink after running the tap. 3. If the water still drains slowly, use a plunger to create pressure against the drain opening. 4. To keep the drain flowing well, pour a cup of baking soda followed by vinegar down the drain monthly.",
    "target": "Step 4",
    "options_or_pairs": [],
    "shortcut_control": {
      "field": "error_detection_error_position",
      "value": "fourth"
    }
  }
}
```

Rendered prompt:

```text
A customer is troubleshooting a slow-draining kitchen sink. They have just finished the step of removing the stopper and checking for visible debris, finding the area clear but the water still draining slowly.

Current state: The stopper is removed and the immediate area is clear, but the clog persists deeper in the pipe.

Goal: Provide the next specific troubleshooting step to address the persistent clog.

Review the sequence of troubleshooting steps provided to the customer. Identify which step is the error that breaks topical coherence by shifting away from the immediate troubleshooting goal.

1. Remove the sink stopper and inspect the P-trap for visible debris. 2. If no debris is found, check the water level in the sink after running the tap. 3. If the water still drains slowly, use a plunger to create pressure against the drain opening. 4. To keep the drain flowing well, pour a cup of baking soda followed by vinegar down the drain monthly.
```

Rendered target:

```text
Step 4
```

- example_id: `PRM_58194738A781:scenario-04:error_detection:primary`
- weakness_id: `WKN_1913AB79`
- view_role: `primary`

Canonical source:

```json
{
  "context": "A home baker is preparing a honey glaze for a cake. The jar of honey contains a few large, crystallized sugar lumps at the bottom. The recipe calls for blending the honey with lemon juice. The honey is heat-sensitive and should not be boiled. A blender is available.",
  "current_state": "The honey jar is open with visible sugar lumps. The lemon juice is measured. The blender is empty.",
  "goal": "Create a smooth, homogeneous honey glaze without gritty particles.",
  "view": {
    "view_type": "error_detection",
    "instruction": "Identify the first erroneous step in the following recipe instruction.",
    "input": "Instruction: 1. Add the entire contents of the honey jar, including the sugar lumps, to the blender. 2. Add lemon juice. 3. Blend on high for 30 seconds. 4. Pour over cake.",
    "target": "Step 1",
    "options_or_pairs": [
      "Step 1",
      "Step 2",
      "Step 3",
      "Step 4"
    ],
    "shortcut_control": {
      "field": "error_detection_error_position",
      "value": "first",
      "view": "error_detection"
    }
  }
}
```

Rendered prompt:

```text
A home baker is preparing a honey glaze for a cake. The jar of honey contains a few large, crystallized sugar lumps at the bottom. The recipe calls for blending the honey with lemon juice. The honey is heat-sensitive and should not be boiled. A blender is available.

Current state: The honey jar is open with visible sugar lumps. The lemon juice is measured. The blender is empty.

Goal: Create a smooth, homogeneous honey glaze without gritty particles.

Identify the first erroneous step in the following recipe instruction.

Instruction: 1. Add the entire contents of the honey jar, including the sugar lumps, to the blender. 2. Add lemon juice. 3. Blend on high for 30 seconds. 4. Pour over cake.
```

Rendered target:

```text
Step 1
```


### multiple_choice samples

- example_id: `PRM_C3DA600A4E03:scenario-01:multiple_choice:primary`
- weakness_id: `WKN_724E3F9E`
- view_role: `primary`

Canonical source:

```json
{
  "context": "You are a senior food service technician performing a quarterly maintenance check on a commercial combi-oven. You have just retrieved the digital pressure gauge and the appropriate adapter kit from the tool cabinet. The oven is powered down and cool. The maintenance log indicates that the pressure relief valve requires calibration before the unit can be returned to service.",
  "current_state": "The technician has selected the digital pressure gauge and adapter kit. The oven is in a safe, powered-down state. The specific task is to calibrate the pressure relief valve.",
  "goal": "Identify the correct next procedural step to continue the calibration of the pressure relief valve using the selected equipment.",
  "view": {
    "view_type": "multiple_choice",
    "instruction": "Select the next step in the maintenance procedure.",
    "input": "Current state: Digital pressure gauge and adapter kit selected. Target component: Pressure relief valve. Action: Calibration.",
    "target": "B",
    "options_or_pairs": [
      "A: Check the oven's electrical breakers to ensure they are not tripped before proceeding.",
      "B: Attach the adapter kit to the pressure relief valve port and ensure a secure seal.",
      "C: Verify that the kitchen's main ventilation fan is operating at full capacity.",
      "D: Record the current date and time in the maintenance log before touching the equipment."
    ],
    "shortcut_control": {
      "field": "mcq_gold_position",
      "value": "B",
      "view": "multiple_choice"
    }
  }
}
```

Rendered prompt:

```text
You are a senior food service technician performing a quarterly maintenance check on a commercial combi-oven. You have just retrieved the digital pressure gauge and the appropriate adapter kit from the tool cabinet. The oven is powered down and cool. The maintenance log indicates that the pressure relief valve requires calibration before the unit can be returned to service.

Current state: The technician has selected the digital pressure gauge and adapter kit. The oven is in a safe, powered-down state. The specific task is to calibrate the pressure relief valve.

Goal: Identify the correct next procedural step to continue the calibration of the pressure relief valve using the selected equipment.

Select the next step in the maintenance procedure.

Current state: Digital pressure gauge and adapter kit selected. Target component: Pressure relief valve. Action: Calibration.

Choices:

A: Check the oven's electrical breakers to ensure they are not tripped before proceeding.

B: Attach the adapter kit to the pressure relief valve port and ensure a secure seal.

C: Verify that the kitchen's main ventilation fan is operating at full capacity.

D: Record the current date and time in the maintenance log before touching the equipment.
```

Rendered target:

```text
B
```

- example_id: `PRM_4B5C10813DA9:scenario-01:multiple_choice:primary`
- weakness_id: `WKN_D8F1ADE0`
- view_role: `primary`

Canonical source:

```json
{
  "context": "You are a volunteer at a community kitchen. You have just finished prepping vegetables on the stainless steel prep table. The table is now covered in vegetable residue and water. The next phase of the workflow involves plating the cooked mains for the lunch service which starts in 10 minutes.",
  "current_state": "The prep table is dirty with vegetable residue. The cooked mains are ready in the warming tray. The lunch service start time is in 10 minutes.",
  "goal": "Determine the correct immediate next action to maintain food safety and procedural integrity.",
  "view": {
    "view_type": "multiple_choice",
    "instruction": "Select the correct next step in the procedure.",
    "input": "Current State: Prep table is dirty. Mains are ready. Service in 10 mins.",
    "target": "A",
    "options_or_pairs": [
      "A. Wipe down and sanitize the prep table with the approved sanitizer solution.",
      "B. Plate the cooked mains directly onto the dirty prep table to save time.",
      "C. Discard the cooked mains and start prepping new vegetables from scratch.",
      "D. Call the health inspector to report the dirty table before proceeding."
    ],
    "shortcut_control": {
      "field": "mcq_gold_position",
      "value": "A",
      "view": "multiple_choice"
    }
  }
}
```

Rendered prompt:

```text
You are a volunteer at a community kitchen. You have just finished prepping vegetables on the stainless steel prep table. The table is now covered in vegetable residue and water. The next phase of the workflow involves plating the cooked mains for the lunch service which starts in 10 minutes.

Current state: The prep table is dirty with vegetable residue. The cooked mains are ready in the warming tray. The lunch service start time is in 10 minutes.

Goal: Determine the correct immediate next action to maintain food safety and procedural integrity.

Select the correct next step in the procedure.

Current State: Prep table is dirty. Mains are ready. Service in 10 mins.

Choices:

A. Wipe down and sanitize the prep table with the approved sanitizer solution.

B. Plate the cooked mains directly onto the dirty prep table to save time.

C. Discard the cooked mains and start prepping new vegetables from scratch.

D. Call the health inspector to report the dirty table before proceeding.
```

Rendered target:

```text
A
```

- example_id: `PRM_F56D95615AA3:scenario-01:multiple_choice:primary`
- weakness_id: `WKN_23D0F1C0`
- view_role: `primary`

Canonical source:

```json
{
  "context": "I have been reviewing the Q3 delivery performance for our regional branch. The data shows a consistent 15% drop in on-time arrival rates specifically for packages routed through the central hub. I need to revise the standard operating procedure for the next quarter to address this specific choke point.",
  "current_state": "The analysis is complete, and the root cause is identified as a bottleneck in the sorting conveyor system at the central hub.",
  "goal": "Determine the most appropriate immediate revision to the logistics plan to resolve the identified bottleneck.",
  "view": {
    "view_type": "multiple_choice",
    "instruction": "Based on the reflective analysis of the delivery bottleneck, select the next step in the plan revision that logically follows the identified root cause.",
    "input": "Root cause: Sorting conveyor bottleneck at central hub. Goal: Reduce on-time arrival delay.",
    "target": "A",
    "options_or_pairs": [
      "A: Coordinate with facility management to schedule emergency maintenance on the central hub conveyors and activate the overflow routing protocol.",
      "B: Revise the marketing brochure to highlight the new real-time tracking features for customers experiencing delays.",
      "C: Implement a new employee incentive program for warehouse staff to improve general morale and speed.",
      "D: Change the packaging material from cardboard to biodegradable plastic to reduce weight and shipping costs."
    ],
    "shortcut_control": {
      "field": "mcq_gold_position",
      "value": "A",
      "view": "multiple_choice"
    }
  }
}
```

Rendered prompt:

```text
I have been reviewing the Q3 delivery performance for our regional branch. The data shows a consistent 15% drop in on-time arrival rates specifically for packages routed through the central hub. I need to revise the standard operating procedure for the next quarter to address this specific choke point.

Current state: The analysis is complete, and the root cause is identified as a bottleneck in the sorting conveyor system at the central hub.

Goal: Determine the most appropriate immediate revision to the logistics plan to resolve the identified bottleneck.

Based on the reflective analysis of the delivery bottleneck, select the next step in the plan revision that logically follows the identified root cause.

Root cause: Sorting conveyor bottleneck at central hub. Goal: Reduce on-time arrival delay.

Choices:

A: Coordinate with facility management to schedule emergency maintenance on the central hub conveyors and activate the overflow routing protocol.

B: Revise the marketing brochure to highlight the new real-time tracking features for customers experiencing delays.

C: Implement a new employee incentive program for warehouse staff to improve general morale and speed.

D: Change the packaging material from cardboard to biodegradable plastic to reduce weight and shipping costs.
```

Rendered target:

```text
A
```


### ordering samples

- example_id: `PRM_56BD31FA93AA:scenario-04:ordering:secondary`
- weakness_id: `WKN_724E3F9E`
- view_role: `secondary`

Canonical source:

```json
{
  "context": "Incident Report: Data Center Security Audit\nDate: 2024-02-20\nSafety Officer: L. Patel\n\nWe are conducting a safety audit for the new server room in Building C. The room contains high-density computing equipment. We have selected the Clean Agent Fire Suppression System (FM-200) for this room due to the need for non-conductive and residue-free extinguishing. The system has been physically installed and the piping is complete. The audit checklist indicates that the next phase is system validation. The audit team is present in the room. The adjacent HVAC system is currently under separate maintenance by a different crew.",
  "current_state": "FM-200 Fire Suppression System selected and installed. Audit team present. Next validation step required.",
  "goal": "Determine the correct next step in the safety protocol to validate the selected fire suppression system.",
  "view": {
    "view_type": "ordering",
    "instruction": "Arrange the following three steps in the correct chronological order based on the procedural logic of deploying the FM-200 fire suppression system. The steps are: 1. Conduct pressure integrity test, 2. Select FM-200 system, 3. Physically install piping.",
    "input": "Steps: [A] Conduct pressure integrity test, [B] Select FM-200 system, [C] Physically install piping.",
    "target": "B, C, A",
    "options_or_pairs": [
      "B, C, A",
      "C, B, A",
      "A, B, C"
    ],
    "shortcut_control": {
      "field": "ordering_permutation_pattern",
      "value": "correct",
      "view": "ordering"
    }
  }
}
```

Rendered prompt:

```text
Incident Report: Data Center Security Audit
Date: 2024-02-20
Safety Officer: L. Patel

We are conducting a safety audit for the new server room in Building C. The room contains high-density computing equipment. We have selected the Clean Agent Fire Suppression System (FM-200) for this room due to the need for non-conductive and residue-free extinguishing. The system has been physically installed and the piping is complete. The audit checklist indicates that the next phase is system validation. The audit team is present in the room. The adjacent HVAC system is currently under separate maintenance by a different crew.

Current state: FM-200 Fire Suppression System selected and installed. Audit team present. Next validation step required.

Goal: Determine the correct next step in the safety protocol to validate the selected fire suppression system.

Arrange the following three steps in the correct chronological order based on the procedural logic of deploying the FM-200 fire suppression system. The steps are: 1. Conduct pressure integrity test, 2. Select FM-200 system, 3. Physically install piping.

Steps: [A] Conduct pressure integrity test, [B] Select FM-200 system, [C] Physically install piping.
```

Rendered target:

```text
B, C, A
```

- example_id: `PRM_C9AF16EFF575:scenario-04:ordering:primary`
- weakness_id: `WKN_3228D584`
- view_role: `primary`

Canonical source:

```json
{
  "context": "A blind taste test between two student-developed sauces is concluding. The last taker has submitted their rating sheet. The facilitator collects the last sheet, stacks them, and looks at the group. The trial is done.",
  "current_state": "All data collection for the taste test is complete.",
  "goal": "Select the valid continuation that respects the completion of the event.",
  "view": {
    "view_type": "ordering",
    "instruction": "Order the final steps of the taste test trial.",
    "input": "1. The last sheet is collected. 2. The trial is declared over. 3. The results are summarized. 4. The takers submit ratings.",
    "target": "4, 1, 2, 3",
    "options_or_pairs": [],
    "shortcut_control": {
      "field": "ordering_permutation_pattern",
      "value": "correct"
    }
  }
}
```

Rendered prompt:

```text
A blind taste test between two student-developed sauces is concluding. The last taker has submitted their rating sheet. The facilitator collects the last sheet, stacks them, and looks at the group. The trial is done.

Current state: All data collection for the taste test is complete.

Goal: Select the valid continuation that respects the completion of the event.

Order the final steps of the taste test trial.

1. The last sheet is collected. 2. The trial is declared over. 3. The results are summarized. 4. The takers submit ratings.
```

Rendered target:

```text
4, 1, 2, 3
```

- example_id: `PRM_64670BF4BA3E:scenario-02:ordering:primary`
- weakness_id: `WKN_B1057194`
- view_role: `primary`

Canonical source:

```json
{
  "context": "A local courier is delivering a package to a remote workshop. The courier has reached the workshop door, knocked, and the recipient has opened the door. The package is in the courier's hands, and the recipient is standing ready to receive it.",
  "current_state": "Recipient is at the door, package is in courier's hands, no signature or digital confirmation has occurred yet.",
  "goal": "Complete the physical transfer of the package to the recipient.",
  "view": {
    "view_type": "ordering",
    "instruction": "Select the action that immediately follows the recipient opening the door and standing ready.",
    "input": "Current state: Recipient at door, package in hands. Goal: Complete transfer.",
    "target": "Hand the package to the recipient and step back.",
    "options_or_pairs": [
      "Tap the 'delivered' button on the handheld device to log the completion.",
      "Hand the package to the recipient and step back.",
      "Call the dispatch center to report the successful delivery.",
      "Move to the next stop on the delivery route."
    ],
    "shortcut_control": {
      "field": "ordering_permutation_pattern",
      "value": "reverse",
      "view": "ordering"
    }
  }
}
```

Rendered prompt:

```text
A local courier is delivering a package to a remote workshop. The courier has reached the workshop door, knocked, and the recipient has opened the door. The package is in the courier's hands, and the recipient is standing ready to receive it.

Current state: Recipient is at the door, package is in courier's hands, no signature or digital confirmation has occurred yet.

Goal: Complete the physical transfer of the package to the recipient.

Select the action that immediately follows the recipient opening the door and standing ready.

Current state: Recipient at door, package in hands. Goal: Complete transfer.
```

Rendered target:

```text
Hand the package to the recipient and step back.
```


### pairwise_preference samples

- example_id: `PRM_7CB41D51C674:scenario-01:pairwise_preference:primary`
- weakness_id: `WKN_D8F1ADE0`
- view_role: `primary`

Canonical source:

```json
{
  "context": "You are leading a retail inventory team during a quarterly audit. The process requires physically counting items on Shelf A, then Shelf B, then Shelf C, before compiling a discrepancy report. You have just finished counting Shelf A and found 12 missing units. The team is waiting for your next instruction. The audit protocol strictly forbids compiling reports until all shelves are counted to ensure data consistency.",
  "current_state": "Shelf A count is complete with discrepancies noted. Shelf B and C are uncounted. The discrepancy report template is open but empty.",
  "goal": "Determine the correct next step in the audit sequence to maintain data integrity.",
  "view": {
    "view_type": "pairwise_preference",
    "instruction": "Choose the instruction that correctly follows the audit protocol given the current state.",
    "input": "Option A: 'Start counting Shelf B now.' Option B: 'Compile the report for Shelf A and email it to the manager.'",
    "target": "Option A is the correct next step.",
    "options_or_pairs": [
      "Option A: 'Start counting Shelf B now.'",
      "Option B: 'Compile the report for Shelf A and email it to the manager.'"
    ],
    "shortcut_control": {
      "field": "pairwise_chosen_side",
      "value": "right",
      "view": "pairwise_preference"
    }
  }
}
```

Rendered prompt:

```text
You are leading a retail inventory team during a quarterly audit. The process requires physically counting items on Shelf A, then Shelf B, then Shelf C, before compiling a discrepancy report. You have just finished counting Shelf A and found 12 missing units. The team is waiting for your next instruction. The audit protocol strictly forbids compiling reports until all shelves are counted to ensure data consistency.

Current state: Shelf A count is complete with discrepancies noted. Shelf B and C are uncounted. The discrepancy report template is open but empty.

Goal: Determine the correct next step in the audit sequence to maintain data integrity.

Choose the instruction that correctly follows the audit protocol given the current state.

Option A: 'Start counting Shelf B now.' Option B: 'Compile the report for Shelf A and email it to the manager.'
```

Rendered target:

```text
Option A is the correct next step.
```

- example_id: `PRM_8D9558C17A4D:scenario-04:pairwise_preference:primary`
- weakness_id: `WKN_BC219538`
- view_role: `primary`

Canonical source:

```json
{
  "context": "A woodworker is assembling a small box. The process involves cutting parts, applying adhesive, clamping, and finishing.",
  "current_state": "The woodworker has just applied a thin layer of wood glue to the mating edge of the side panel and pressed it against the front panel. The panels are aligned but not yet secured.",
  "goal": "To ensure the joint cures properly without shifting.",
  "view": {
    "view_type": "pairwise_preference",
    "instruction": "Select the correct next step after applying glue to the joint and aligning the panels.",
    "input": "Previous Step: Applied glue and pressed panels together. Current State: Joint is aligned but unsecured; glue is wet.",
    "target": "right",
    "options_or_pairs": [
      {
        "label": "left",
        "content": "Sand the bottom edge of the base to smooth rough cuts."
      },
      {
        "label": "right",
        "content": "Apply a bar clamp to hold the joint securely."
      }
    ],
    "shortcut_control": {
      "field": "pairwise_chosen_side",
      "value": "right",
      "view": "pairwise_preference"
    }
  }
}
```

Rendered prompt:

```text
A woodworker is assembling a small box. The process involves cutting parts, applying adhesive, clamping, and finishing.

Current state: The woodworker has just applied a thin layer of wood glue to the mating edge of the side panel and pressed it against the front panel. The panels are aligned but not yet secured.

Goal: To ensure the joint cures properly without shifting.

Select the correct next step after applying glue to the joint and aligning the panels.

Previous Step: Applied glue and pressed panels together. Current State: Joint is aligned but unsecured; glue is wet.

{'label': 'left', 'content': 'Sand the bottom edge of the base to smooth rough cuts.'}

{'label': 'right', 'content': 'Apply a bar clamp to hold the joint securely.'}
```

Rendered target:

```text
right
```

- example_id: `PRM_D8D5EEF14D58:scenario-02:pairwise_preference:primary`
- weakness_id: `WKN_AFC0089D`
- view_role: `primary`

Canonical source:

```json
{
  "context": "A vocational student is completing a tiling module. They need to cut a 30cm x 30cm ceramic floor tile to fit around a drain. The tile is rigid and has a glazed surface. The workshop contains a standard crosscut wood saw, a diamond-tipped angle grinder, and a manual tile nippers. The student must cut a straight 15cm line from the edge of the tile.",
  "current_state": "The tile is placed on a sacrificial board. The student has the wood saw in their left hand and the angle grinder in their right hand. The line is marked with a chalk line.",
  "goal": "Select the tool that is functionally appropriate for cutting rigid ceramic material with a straight, clean edge.",
  "view": {
    "view_type": "pairwise_preference",
    "instruction": "Compare the two tool selections. Which one is functionally suitable for the specific material properties of ceramic tile?",
    "input": "Option 1: Use the diamond-tipped angle grinder.\nOption 2: Use the standard crosscut wood saw.",
    "target": "Option 1 is the correct choice.",
    "options_or_pairs": [
      {
        "left": "Option 1: Use the diamond-tipped angle grinder.",
        "right": "Option 2: Use the standard crosscut wood saw."
      }
    ],
    "shortcut_control": {
      "field": "pairwise_chosen_side",
      "value": "left",
      "view": "pairwise_preference"
    }
  }
}
```

Rendered prompt:

```text
A vocational student is completing a tiling module. They need to cut a 30cm x 30cm ceramic floor tile to fit around a drain. The tile is rigid and has a glazed surface. The workshop contains a standard crosscut wood saw, a diamond-tipped angle grinder, and a manual tile nippers. The student must cut a straight 15cm line from the edge of the tile.

Current state: The tile is placed on a sacrificial board. The student has the wood saw in their left hand and the angle grinder in their right hand. The line is marked with a chalk line.

Goal: Select the tool that is functionally appropriate for cutting rigid ceramic material with a straight, clean edge.

Compare the two tool selections. Which one is functionally suitable for the specific material properties of ceramic tile?

Option 1: Use the diamond-tipped angle grinder.
Option 2: Use the standard crosscut wood saw.

{'left': 'Option 1: Use the diamond-tipped angle grinder.', 'right': 'Option 2: Use the standard crosscut wood saw.'}
```

Rendered target:

```text
Option 1 is the correct choice.
```
