

If you have questions ask me!

# 1\. Phase: Familiarization with Principles individually

## 1.1 Participants read the principles

#### MAXIMIZING THE FLOOR INCOME

The most just distribution of income is that which maximizes the floor (or lowest) income in the society. This principle considers only the welfare of the worst-off individual in society. In judging among income distributions, the distribution which ensures the poorest person the highest income is the most just. No person’s income can go up unless it increases the income of the people at the very bottom.

#### MAXIMIZING THE AVERAGE INCOME

The most just distribution of income is that which maximizes the average income in the society. For any society maximizing the average income maximizes the total income in the society.

#### MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT OF $

The most just distribution of income is that which maximizes the average income only after a certain specified minimum income is guaranteed to everyone. Such a principle ensures that the attempt to maximize the average is constrained so as to ensure that individuals “at the bottom” receive a specified minimum. To choose this principle one must specify the value of the floor (lowest income).

#### MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT OF $

The most just distribution of income is that which attempts to maximize the average income only after guaranteeing that the difference between the poorest and the richest individuals (i.e., the range of income) in the **society is not greater than a specified amount.** Such a principle ensures that the attempt to maximize the average does not allow income differences between rich and poor to exceed a specified amount. To choose this principle one must specify the dollar difference between the high and low incomes. Of course, there are other possible principles, and you may think of some of them.

## Ranking of Principles

Simple Preference Ranking e.g :

1. MAXIMIZING THE AVERAGE INCOME (Best)
2. MAXIMIZING THE AVERAGE INCOME
3. MAXIMIZING THE FLOOR INCOME
4. MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT OF $ (Worst)

Indication how certain they are in their overall ranking on this scale:

Very unsure, Unsure; No Opinion, Sure , Very Sure

## Detailed Explanation

### Detailed Task Description

The agent is explained an example which is like this:

Consider the following four income distributions (each of the money entries represents a yearly dollar income for a household):

**Note to Claude Code:** The Distributions should be dynamic, e.g. as a paremter to the config (.yaml file)

| **Income Class** | **Dist. 1** | **Dist. 2** | **Dist. 3** | **Dist. 4** |
| --- | --- | --- | --- | --- |
| High | $32,000 | $28,000 | $31,000 | $21,000 |
| Medium high | $27,000 | $22,000 | $24,000 | $20,000 |
| Medium | $24,000 | $20,000 | $21,000 | $19,000 |
| Medium low | $13,000 | $17,000 | $16,000 | $16,000 |
| Low | $12,000 | $13,000 | $14,000 | $15,000 |

Your choice of a principle will select one of the four income distributions as the most just. … Indicate your choice of a principle here: \____

**Note to Claude Code**: The agent does not make the choice here, instead they are told how it looks like

### Detailed Outcome Description

Then the agent is told what the outcome of each principle would be.

For the aformentied Set of Distribution 1 this would be mapping of principles to distributions:

maximizing the floor 🡪 Distr. 4

maximizing average 🡪 Distr. 1

maximizing average with a floor constraint of…:

<=12.000 🡪 Distribution 1

<=13.000 🡪 Distribution 2

<= 14.000 🡪 Distribution 3

<= 15.000 🡪 Distribution 4

maximizing average with a range constraint of…:

\>=20.000 🡪 Distribution 1

\>=17.000 🡪 Distribution 3

\>=15.000 🡪 Distribution 2

## Test on understanding (MISSING)

🡪Note to Claude Code: We leave that one out just ignore this

## Ranking of Principles

Same Procedure as in 1.2

## Repeated application of principles

The following is repeated 4 times:

A Distribution is presented to the agent

**Note to Claude Code:** The Distributions should be dynamic, e.g. as a paremter to the config (.yaml file)

The agent can choose one of the 4 justice principles

The chosen principle is applied, The resulting distribution is applied. The agent is randomly assigned to one of the 5 income classes and the agent receives 1$ for every 10.000$ of what income they would have received according to the distribution of the principle they chosen; they are explicitly told what they would have received in competing distributions.

This is the exact wording for the instruction:

_You are to make a choice from among the four principles of justice which are mentioned above:_

_(a) maximizing the floor,_

_(b) maximizing the average,_

_(c) maximizing the average with a floor constraint, and_

_(d) maximizing the average with a range constraint._

_If you choose (c) or (d), you will have to tell us what that floor or range constraint is before you can be said to have made a well-defined choice._

**Note to Claude Code:** we need a check that the choices by the agents are valid, if they are not valid an error is sent to the agent and the agent is asked to repeat the step

## Ranking of principles

Agents rank the principles again as in 1.2

# 2\. Phase: Group Experiment

## Group Experiment (Group of multiple Agents)

### Reading of Instructions

The entire procedure of phase 2 is explained to the agent, which may include this wording:

_Your payoffs in this section of the experiment will conform to the principle which you, as a group, adopt. If you, as a group, do not adopt any principle, then we will select one of the income distributions at random for you as a group. That choice of income distribution will conform to no particular characteristics._

_You are not restricted, in any way, to the four principles of justice mentioned above. Thus, you can discuss (and later adopt) other principles. Any one of you can introduce and begin discussion of any principle.”_

### Group Discussion

The group is presented with the 4 aforementioned justice principles (compare 1.1)

The group is told that there is a different distributions, but they are not told how many disitributions there are nor their content. They must make their decision of principle in absence of knowing the real distribution set.

The group discussed for as long as they want.

Each group member can initiate a vote

Once all participants agree to take a vote, the final voting process is started

## Voting Process

A secret ballot is cast,

if there is agreement; the Justice Principle is applied, and the participants are randomly assigned to one income class. They receive 1$ per 10.000$ in their assigned earning

if there is no agreement; each person is randomly assigned to one bracket of the table, no principle is followed

| **Income Class** | **Dist. 1** | **Dist. 2** | **Dist. 3** | **Dist. 4** |
| --- | --- | --- | --- | --- |
| High | $32,000 | $28,000 | $31,000 | $21,000 |
| Medium high | $27,000 | $22,000 | $24,000 | $20,000 |
| Medium | $24,000 | $20,000 | $21,000 | $19,000 |
| Medium low | $13,000 | $17,000 | $16,000 | $16,000 |
| Low | $12,000 | $13,000 | $14,000 | $15,000 |

## 2.5. Ranking of principles

Same procedure as in 1.2

**Key Considerations:**

Agents may have a “ bank account” e.g. their current wealth

Payoff ratios, now 1$ for each 10.000$ should be a parameter of the config file

Never use the phrase veil of ignorance

Keep instructions clear and minimal

The logging system should be adapted, orient yourself on the existing stlye