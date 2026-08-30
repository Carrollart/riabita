In the urban simulation game **RIABITA ROMA**, success is not measured by a single metric. Instead, the simulation challenges players to balance two distinct, complementary evaluation systems: the **Re-habitability Index (RIz)** and the **Urban Sharpe Ratio** 1, 2\.  
Understanding the differences, relationships, and strategic tensions between these two metrics is essential to mastering the simulation and understanding its real-world urban planning foundations.

### 1\. Mathematical Formulation & Definitions

#### Re-habitability Index (RIz)

The **RIz** is a global composite index that evaluates the absolute potential of a historical urban fabric to support daily residential life 1, 3\.

* **Base Calculation:** It is calculated as the weighted arithmetic mean of the four standardized thematic domains: **Mobility (M)**, **Culture (C)**, **Tourism (T)**, and **Socio-demographics (S)**, where each pillar is assigned an equal weight of **0.25** 4-6:\\\\\\text{RIz}\_{\\text{base}} \= 0.25M \+ 0.25C \+ 0.25T \+ 0.25S\\\\  
* **Game Score Modifiers:** In the game, the final **RIz** includes dynamic bonuses and penalties applied directly to this base value, rewarding balanced configurations and punishing extreme functional specializations 6:  
* **Equilibrium Bonus:** **\+10 points** if the standard deviation (\\\\(\\sigma\\\\)) of the four pillars is \\\\(\< 10\\\\); **\+5 points** if \\\\(10 \\le \\sigma \< 15\\\\); **\-5 points** if \\\\(\\sigma \> 25\\\\) 7\.  
* **Overtourism Penalty:** **\-5 points** if \\\\(T \> S \+ 25\\\\); **\-10 points** if \\\\(T \> S \+ 40\\\\) 7\.  
* **Concentration Penalty:** **\-5 points** if more than 60% of the budget is allocated to a single dimension 2 (or a penalty applied if a single allocation exceeds 50% 8).

#### Urban Sharpe Ratio

Inspired by modern portfolio theory in finance, the **Urban Sharpe Ratio** evaluates the *efficiency and safety* of the player's investment strategy 9, 10\. It determines if the habitability gains were achieved sustainably or through high-risk imbalances 9, 11\.

* **Calculation:**\\\\\\text{Urban Sharpe} \= \\frac{R}{\\text{Risk}}\\\\  
* **Urban Yield (\\\\(R\\\\)):** The net improvement in habitability, defined as:\\\\R \= \\text{RIz}*{\\text{final}} \- \\text{RIz}*{\\text{initial}}\\\\ 2  
* **Urban Risk:** The standard deviation (\\\\(\\sigma\\\\)) of the four final dimensions, measuring inequality and structural dispersion across the neighborhood’s pillars 2, 7:\\\\\\text{Risk} \= \\sigma(M, C, T, S)\\\\

### 2\. Conceptual Comparison: Absolute State vs. Efficiency

The core conceptual divide between these two metrics can be summarized as follows:  
Feature,Re-habitability Index (RIz),Urban Sharpe Ratio  
Perspective,Absolute State (Static snapshot) 3,Investment Efficiency (Dynamic process) 9  
What it measures,The general livability potential of the neighborhood 3.,"How ""balanced"" the transition was relative to the structural risk created 9, 11."  
Primary Goal,Maximize the overall average performance of the pillars 12.,"Maximize the return per unit of urban imbalance (dispersion) 2, 9."  
Underlying Risk Model,"Penalizes risk via discrete thresholds (e.g., standard deviation and overtourism caps) 7.",Risk is a continuous denominator; any increase in dimensional dispersion directly erodes the score 2\.  
Sensitivity to Starting Point,Highly sensitive to initial district conditions (easy vs. hard districts) 13.,Normalized to the initial district because it uses Yield (\\\\(R\\\\)) 2\.

### 3\. The Role of "Urban Risk"

In **RIABITA ROMA**, **Urban Risk** is represented by the standard deviation (\\\\(\\sigma\\\\)) among the pillars 2\. This represents the real-world danger of **urban specialization and monofunctional monocultures** 13, 14\.

* **In the RIz Metric:** Risk acts as an external modifier. If you push a district into extreme imbalance (such as making Rione Trevi a hyper-tourism zone with collapsing community infrastructure 15), you are hit with discrete, block-based penalties (e.g., \-10 points for overtourism 7).  
* **In the Urban Sharpe Metric:** Risk is the foundational denominator 2\. Even if a player manages to increase their absolute **RIz** score by heavily developing one or two dimensions, an escalating standard deviation (\\\\(\\sigma\\\\)) will cause the **Urban Sharpe Ratio** to plummet. A strategy that generates a high yield (\\\\(R\\\\)) but leaves a massive gap between the highest and lowest pillars is mathematically penalized for its lack of resilience 2, 11\.

### 4\. Strategic Gameplay Implications

These mathematical differences force players to adopt different strategies depending on which metric they are trying to optimize:

* **The "RIz Maximizer" Strategy:**  
* This strategy prioritizes absolute growth 12\. A player might focus heavily on dimensions that have strong positive spillover effects (like Mobility, which yields \\\\(+1.0 \\ M, \+0.4 \\ C, \+0.3 \\ T, \+0.2 \\ S\\\\) per 10 credits 16).  
* While this can lift the overall average and secure a high **RIz**, the player risks over-concentrating resources, missing out on the **Resilience/Diversification Bonus** (granted for investing in 3 or 4 dimensions 11), and driving up standard deviation 7\.  
* **The "Urban Sharpe" Strategy:**  
* This strategy focuses on harmony and systemic equilibrium 9, 17\. To maximize the **Urban Sharpe**, players must lift the weakest starting pillars (for example, investing in Socio-demographics in Trastevere to offset high Tourism pressure 18, 19).  
* By keeping the final standard deviation low, they minimize the **Risk** denominator 2\. This approach naturally triggers the game’s **Equilibrium Bonus (+10 points)** and **Diversification Bonus**, which in turn boosts the numerator (Yield) while keeping the denominator small 7, 11\.

### 5\. Real-World Urban Planning Meaning

This comparison translates directly into the scientific findings of the CArME study on Rome's historical center:

* An area can have a high **RIz** due to exceptional public transit capacity, abundant cultural events, and intense tourist activity (as seen in central tourist-heavy hubs) 20, 21\.  
* However, if these features exist alongside a depopulated, aging, and economically vulnerable residential community, the system is highly fragile 13, 22\. The **Urban Sharpe Ratio** is the game’s way of demonstrating that true sustainable regeneration cannot be built on monofunctional specialization 9, 13\. It rewards a "diversified city portfolio" where tourism, culture, and mobility exist in a healthy, balanced symbiosis with resident life 9, 10, 23\.
