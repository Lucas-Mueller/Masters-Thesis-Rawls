
# Phase 2: Group Experiment - Detailed Operationalization Plan

This document provides a granular, call-by-call operationalization of Phase 2, mirroring the detail level from the `System Design Frohlich Replica.csv` and aligning with the procedures in `new_logic.md`.

**Actors:**
*   **System:** The core orchestrator, executing code and managing state.
*   **Participant Agent (PA):** The main agent participating in the experiment.
*   **Util Agent (UA):** A specialized service agent for parsing, validation, and explanation generation.

--- 

### **2.1 Reading of Instructions**

| Call ID | Trigger | Actor | Action / Prompt | Expected Output | Logged Information |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2.1.1 | Start of Phase 2 | System -> All PAs | **Input Prompt:** Broadcasts the full instructions for the group experiment, including rules on discussion, voting, and the consequences of non-unanimity. | Acknowledgment text from each PA. | Each PA's acknowledgment response. |

--- 

### **2.2 Group Discussion Loop**

*This loop continues until all agents have `wants_to_vote: true` or `max_rounds` is reached.* 

| Call ID | Trigger | Actor | Action / Prompt | Expected Output | Logged Information |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2.2.1 | Each turn in a round | System | **Internal Logic:** Determines which PA speaks next based on the speaking order for the current round. | The ID of the next PA to speak. | Current round number, speaking order. |
| 2.2.2 | Each turn in a round | System -> Current PA | **System Prompt:** Personality (from config) + Memory (formatted by the active Memory Mode).<br>**Input Prompt:** Provides the conversational history and asks for the agent's contribution. | Natural language text (argument, statement, etc.). | The PA's full text response, added to the discussion transcript. |
| 2.2.3 | After every PA turn | System -> UA | **Input Prompt:** The raw text from the PA in 2.2.2.<br>**Demand:** "Analyze this text. Does the agent explicitly state a desire to move to a vote? Respond with JSON: `{"wants_to_vote": boolean}`." | A JSON object: `{"wants_to_vote": true}` or `{"wants_to_vote": false}`. | The parsed vote intention boolean. |
| 2.2.4 | After call 2.2.3 | System | **Internal Logic:** Updates the internal state for the speaking PA (e.g., `agent_states['agent_N']['wants_to_vote'] = true`). Then, checks if all agents now have `wants_to_vote == true`. If so, the discussion loop terminates. | None (internal state change). | The updated agent state map. |

--- 

### **2.3 Voting Process**

*This entire block is executed privately for each Participant Agent.* 

| Call ID | Trigger | Actor | Action / Prompt | Expected Output | Logged Information |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2.3.1 | Discussion loop ends | System -> Each PA | **Input Prompt:** "The group has agreed to vote. Please cast your final, secret vote. If you choose principle 3 or 4, you must specify the constraint amount to make a well-defined choice." | Natural language text representing the vote. | The PA's raw vote text. |
| 2.3.2 | After each PA submits a vote (2.3.1) | System -> UA | **Input Prompt:** The raw vote text from the PA.<br>**Demand:** "Parse this text to extract the chosen principle and any constraint value. Validate the choice. Respond with JSON: `{"is_valid": boolean, "choice": {"principle_id": int, "constraint_value": int/null}, "error_reason": string/null}`." | A structured JSON object with the parsed vote and its validity status. | The full JSON response from the UA, including validity and parsed data. |
| 2.3.3 | **If vote in 2.3.2 is invalid** | System -> UA | **Input Prompt:** The invalid raw vote text from the PA.<br>**Demand:** "The following response was invalid. Generate a concise explanation for the Participant Agent detailing *why* it was invalid (e.g., 'You chose Principle 3 but did not specify a floor constraint value.')." | A natural language explanation string. | The generated explanation text. |
| 2.3.4 | After 2.3.3 | System -> PA | **System Prompt:** Personality + Memory.<br>**Input Prompt:** The explanation from 2.3.3 + "Your previous vote was invalid. Please submit a new, valid vote." | A new natural language vote from the PA. | The PA's new raw vote text. |
| 2.3.5 | After 2.3.4 | System | **Internal Logic:** The system loops back to call **2.3.2** with the new vote text. This retry loop (2.3.2 -> 2.3.3 -> 2.3.4) runs a maximum of 2 more times (3 total attempts). | A final, validated `PrincipleChoice` object for the agent. | The final validated `PrincipleChoice` object. |
| 2.3.6 | **If vote is still invalid after 3 attempts** | System | **Internal Logic:** The experiment run for this group is terminated. A fatal error is logged. | None (experiment halt). | A fatal error message: "Agent [N] failed to provide a valid vote after 3 attempts. Run terminated." |

--- 

### **2.4 Group Outcome Determination**

| Call ID | Trigger | Actor | Action / Prompt | Expected Output | Logged Information |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2.4.1 | All votes are validly collected | System | **Internal Logic:** Compares the final, validated `PrincipleChoice` JSON objects from all PAs. Unanimity requires all objects to be identical (including constraint values). | A boolean `is_unanimous` and the `agreed_principle` if unanimous. | The final group decision (e.g., `"principle_id": 3, "constraint_value": 15000` or `"decision": "random"`). |
| 2.4.2 | After 2.4.1 | System | **Internal Logic:** Based on the outcome, applies the chosen principle (or a random distribution) to the hidden income distribution table. Randomly assigns each PA to an income class and calculates their payout based on the `payout_ratio` from the config. | A mapping of each PA to their assigned income class and final payout amount. | For each PA: assigned income class, final income amount, and final payout. |
| 2.4.3 | After 2.4.2 | System -> All PAs | **Input Prompt:** Informs each agent of the final group outcome (the chosen principle or random selection), their personally assigned income class, and their final payout for the phase. | Acknowledgment text from each PA. | Each PA's acknowledgment response. |

--- 

### **2.5 Final Ranking**

| Call ID | Trigger | Actor | Action / Prompt | Expected Output | Logged Information |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2.5.1 | After group outcome is revealed | System -> Each PA | **Input Prompt:** "Based on the entire experiment, including the group discussion and final outcome, please provide your final ranking of the four principles and your certainty level." | Natural language text with the final ranking and certainty. | The PA's raw text response. |
| 2.5.2 | After each PA submits a final ranking | System -> UA | **Input Prompt:** The raw text from the PA in 2.5.1.<br>**Demand:** "Parse this text to extract the final principle ranking and certainty level. Respond with JSON." | A structured JSON object of the final ranking and certainty. | The final parsed ranking and certainty level for each PA (JSON). |

