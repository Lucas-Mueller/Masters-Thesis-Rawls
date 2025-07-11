
### Arhcitecture.
You must use the agents_sdk which you will find in the /knowledge_base/agents_sdk or under https://openai.github.io/openai-agents-python/ 

Write clean and easy to understand code. Make it short and easy to understand. Ask questions back if you are uncertain

### **Experiment Objective**

To determine which principle of distributive justice a group of autonomous agents will unanimously select when they are made impartial by a "veil of ignorance."

---

### **Experimental Design**

#### **1. The Participants**
The experiment is conducted with groups of 3-50 agents, the precise number can be defined by the user/programmer. 

#### **2. The Conditions of Choice**
* **Impartiality:** Agents choose a principle without any knowledge of the specific economic position they will occupy. They are only told that their position (from best-off to worst-off) will be randomly assigned to them *after* their group makes its decision.
* **The Principles:** Agents must choose from one of four possible principles to govern their society's economic distribution:
    1.  **Maximize the Minimum Income:** The principle that ensures the worst-off member of society is as well-off as possible.
    2.  **Maximize the Average Income:** The principle that ensures the greatest possible total income for the group, without regard for its distribution.
    3.  **Maximize the Average Income with a Floor Constraint:** A hybrid principle that establishes a minimum guaranteed income (a "safety net") for everyone, and then maximizes the average income.
    4.  **Maximize the Average Income with a Range Constraint:** A hybrid principle that limits the gap between the richest and poorest members, and then maximizes the average income.

---

### **Experimental Procedure**
### **Phase 1: Choosing the Principles

#### **Step 1: Familiarization**
Each agent is individually presented with a clear and neutral description of the four principles of justice, including simple numerical examples to illustrate how each one functions.
Then the agent evaluates the each principle and stores this in a memory that is private to each agent.
Then the agent chooses the principle he/she favors. 
If all agents agree the Phase is ended and Phase 2 is entered

#### **Step 2: Deliberation and Unanimous Choice**
* The group of agents is placed in a shared communication channel.
* They are instructed to discuss the merits of the four principles until they reach a **unanimous agreement** on one.
* They are informed that failure to reach unanimity will result in a less desirable outcome (e.g., a random and potentially low-paying distribution), creating a strong incentive to agree.
* All communication between the agents is recorded. Each agent's formal preference after discussion is also recorded.

### Phase 2: Applying the norm
We will do this later

---

### **Data to be Recorded**

1.  **Deliberation Content:** The complete transcript of the discussion among the agents.
2.  **Choice Outcome:** The principle of justice unanimously selected by each group.
3.  **Post-Experiment Feedback:** After receiving their final payoff, each agent is to be individually asked to report:
    * Their level of satisfaction with the group's choice.
    * Their assessment of the fairness of the chosen principle.
    * Whether they would make the same choice again.

---

### **Key Experimental Variations for Further Testing**

To ensure the results are robust, the experiment should be repeatable with the following modifications:

* **Decision Rule:** Change the requirement from unanimity to a **majority rule**.
* **Imposed Principle:** Instead of the agents choosing, **impose a principle** upon the group and compare their subsequent task performance and satisfaction to groups that chose their own principle.