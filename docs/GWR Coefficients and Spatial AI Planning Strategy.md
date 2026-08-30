The **Geographically Weighted Regression (GWR) coefficients** from the CArME academic study are integrated into the game's **AI Planner** engine in `src/riabita/strategies.py`.

### 1\. Spatial Planning Theory: Why GWR Coefficients Matter

In a traditional simulation, an AI opponent would simply attempt to maximize the standard gameplay score using uniform weights (0.25 for each of the four dimensions) 2\. However, the CArME study proves that **urban habitability is highly dependent on distance and direction** (anisotropic mosaic behavior) 3, 4:

* **The Inner Core (5–10 minutes walking distance):** Habitability is heavily driven by functional attraction, physical accessibility, and local cultural infrastructure 5, 6\. Mobility and Culture have strong positive coefficients 5\.  
* **The Peripheral Belt (25–30 minutes walking distance):** Tourism pressure has a negative localized impact, accessibility loses dominance, and the **Socio-demographic dimension becomes the primary driver of residential stability** 5, 6\.

By feeding these empirical coefficients directly into the AI, the **AI Planner** ceases to be a generic optimizer and instead acts as a **localized urban planning expert** 7\. It dynamically alters its strategy based on the selected neighborhood's temporal band.

### 2\. Empirical GWR Coefficient Matrix

The AI references the following regression parameters calculated via Gaussian kernels and cross-validated bandwidths 1, 5:  
Distance Ring,Representative Zones,\\\\(\\beta\_{mob}\\\\) (Mobility),\\\\(\\beta\_{cult}\\\\) (Culture),\\\\(\\beta\_{tour}\\\\) (Tourism),\\\\(\\beta\_{socio}\\\\) (Socio-demo)  
5 min,"A0 (Velabro), A1 (Sant'Angelo)",+0.41,+0.32,+0.27,-0.05  
10 min,"A6 (Monti sud), A10 (Trastevere 1)",+0.36,+0.28,+0.12,-0.02  
15 min,"B1 (Regola), B5 (Esquilino Ovest)",+0.09,+0.24,+0.19,+0.05  
20 min,"B6 (Appio-Latino), B10 (Trastevere 2)",-0.03,+0.18,+0.04,+0.21  
25 min,"C1 (Ponte), C3 (Repubblica)",-0.05,+0.08,-0.02,+0.32  
30 min,"C6 (Ostiense), C7 (Testaccio)",-0.07,+0.02,-0.05,+0.38

### 3\. AI Multi-Objective Optimization Logic

The updated AI algorithm in `riabita.strategies` uses a **two-tiered grid-search optimizer**:

1. **Primary Objective:** Maximize the standard game score (including standard deviation bonuses and overtourism penalties) 8, 9 to remain highly competitive on the user leaderboard 10\.  
2. **Secondary Objective (GWR Suitability Projection):** If multiple budget distributions yield the same optimal game score, the AI calculates the dot product of the final values and the GWR coefficient vector (\\\\(\\vec{V}*{final} \\cdot \\vec{\\beta}*{GWR}\\\\)) 5\. It selects the distribution that **best matches the physical priorities of that neighborhood's distance band**.

#### Example Emergent Behaviors:

* **Central Rione (e.g., A10 \- Trastevere, 10 min):** The GWR weights value Mobility (0.36) and Culture (0.28) highly 5\. The AI is highly aggressive in allocating funds to **Culture** and **Mobility** to capture massive combined scores 11, 12\.  
* **Peripheral Rione (e.g., C6 \- Ostiense, 30 min):** The GWR weight for Socio-demographics is a dominant **\+0.38**, while Mobility is **\-0.07** 5\. The AI pivots and concentrates its investments on **Socio-demographics** (quality of life, residential services) 13 to align with local requirements.

### 4\. Integration Blueprint

The production planner is provided by `riabita.strategies.ai_allocation()` and is called by the progressive Streamlit state layer. It uses the selected district's band, the current AI dimensions, and cumulative allocation; it does not receive the pending event.

\# Example production import
from riabita import strategies
from riabita.domain.models import Dimensions

\# Query the AI for a GWR-driven strategy  
\# Parameters: zone ID and initial values \[M0, C0, T0, S0\]  
ai\_plan \= strategies.ai_allocation(
	Dimensions(55.0, 40.0, 80.0, 35.0),
	budget_total=100,
	district_id='A10',
)

print(f"Recommended AI Budget: {ai\_plan}")
