I have generated the CArME system indicators dataset as a structured CSV file as carme\_indicators.csv.  
This file organizes the complete set of indicators extracted from your university research on Rome's historic center, providing a scientific baseline for the **RIABITA ROMA** simulation engine.

### What the Dataset Contains

* **The Complete 26 CArME Zones:** Incorporates every study area (A1 to C8), populated with its official empirical **Mean \\\\(\\text{RI}\_z\\\\)** score and its corresponding **Habitability Potential** classification (*Alta/High*, *Media/Medium*, *Bassa/Low*) 1-3.  
* **Detailed Territorial Micro-Statistics:** Provides full structural data for zones with explicit statistics in the research report, including **A0 (Velabro)**, **A1B1 (Sant'Angelo/Regola)**, **A2B2 (Pigna/Parione/Sant'Eustachio/Colonna)**, **A3B3 (Trevi)**, **A10 (Trastevere)**, and the anonymous study areas 4-13.  
* **A Standardized 23-Column Schema:** Includes detailed columns for socio-demographic indicators (population, age indexes, graduate shares, employment, and family structures), built environment statistics (residential vs. public buildings), cultural vitalities (daily live and total performances), and tourism pressures (accommodation capacity and residential-to-tourist ratios) 14-20.

This clean tabular dataset allows your game's data\_loader.py to move beyond simulated data, initializing the game with authentic starting stats (\\\\(M\_0, C\_0, T\_0, S\_0\\\\)) directly mapped to Rome's physical geography 21, 22\.  
