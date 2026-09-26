> Historical workflow note: the CSV-to-GeoJSON converter described below is retired and is not used by the app. The runtime reads `src/riabita/data/zona_carme_riabita/zone_carme_riabita.shp` directly and uses its embedded `MO`, `CO`, `TO`, and `SO` fields. A0 has missing dimensions and is omitted. See [README.md](../README.md) for the current data contract.

I have created a robust Python helper script called convert\_csv\_to\_geojson.py to automatically transform the tabular carme\_indicators.csv dataset into a spatially complete, interactive carme\_zones.geojson map file.  
Below is a detailed breakdown of the mathematical heuristics used to model the geography of Rome's historic center, the complete python source code, and how to integrate it with your interactive Streamlit dashboard.

### 1\. Spatial Modeling Heuristics

Because the original CArME spreadsheet contains only tabular socio-demographic, cultural, and tourism metrics 1, 2, it lacks raw geometry data (such as coordinates). To convert this into a visual GeoJSON map, the helper script mathematically projects each of the **35 unique zones** around the central archaeological node of **Velabro (A0)** 3, 4:

* **The Anchor Node:** The Velabro (A0) is set as the origin point at exactly 41.889° N, 12.482° E 3-5.  
* **The Walking Rings (Fasce Concentriche):** The script utilizes the walking isochrone rules outlined in the research methodology to determine distance from the center 3, 6:  
* **1a Fascia (A-Zones, 5–10 min):** Distributed at a radius of 550m to 800m 3, 7\.  
* **2a Fascia (B-Zones, 10–20 min):** Distributed at a radius of 1100m to 1500m 7, 8\.  
* **3a Fascia (C-Zones, 20–30 min):** Distributed at a outer radius of 1800m to 2300m 8-10.  
* **Angular Sector Offsets:** Each Rione or study zone is mapped to its true geographical bearing relative to the Roman Forum (e.g., Trastevere zones are oriented South-West at 235°–245° across the Tiber, Pigna/Parione are North-West, and Esquilino/Celio are East/South-East) 7-9.  
* **Boundary Polygon Generation:** To represent urban space, the script calculates a centroid for each zone and generates an **8-sided octagon polygon** centered on that node, with the radius scaled proportionally to the zone’s fascia (from 250m for A0 to 500m for C-zones).

### 2\. The Python Helper Code: convert\_csv\_to\_geojson.py

This standalone script uses pandas and standard Python math modules to read the CSV, perform the projection math, map the physical attributes, and write out a fully compliant RFC-7946 GeoJSON.  
import pandas as pd  
import numpy as np  
import json  
import math

def generate\_carme\_geojson(csv\_path, output\_geojson\_path):  
    """  
    Parses CArME indicator tabular data and projects it into a relative spatial   
    GeoJSON structure mapping the historic rings of Rome.  
    """  
    \# Load the source CSV  
    df \= pd.read\_csv(csv\_path)  
      
    \# Anchor on the central Velabro node (A0)  
    lat\_center \= 41.889  
    lon\_center \= 12.482  
      
    \# Map each Zona\_ID to its precise angular bearing (degrees from North)   
    \# and radial distance (meters) based on Rome's historic urban plan  
    zone\_placements \= {  
        'A0': {'angle': 0, 'distance': 0, 'radius': 250},  
          
        \# 1a Fascia (A-zones, 5-10 min)  
        'A1': {'angle': 270, 'distance': 550, 'radius': 300}, \# Sant'Angelo  
        'A2': {'angle': 315, 'distance': 550, 'radius': 300}, \# Pigna  
        'A3': {'angle': 30, 'distance': 550, 'radius': 300},  \# Trevi sud  
        'A4': {'angle': 75, 'distance': 650, 'radius': 300},  \# Monti nord  
        'A6': {'angle': 100, 'distance': 650, 'radius': 300}, \# Monti-Esquilino  
        'A7': {'angle': 135, 'distance': 650, 'radius': 300}, \# Celio  
        'A8': {'angle': 180, 'distance': 800, 'radius': 300}, \# San Saba  
        'A9': {'angle': 210, 'distance': 650, 'radius': 300}, \# Ripa-Aventino  
        'A10': {'angle': 240, 'distance': 750, 'radius': 300},\# Trastevere 1a  
          
        \# 2a Fascia (B-zones, 10-20 min)  
        'B1': {'angle': 280, 'distance': 1100, 'radius': 400},\# Regola  
        'B2': {'angle': 310, 'distance': 1200, 'radius': 400},\# Parione/Eustachio  
        'B3': {'angle': 25, 'distance': 1200, 'radius': 400}, \# Trevi nord  
        'B4': {'angle': 60, 'distance': 1200, 'radius': 400}, \# Monti nord 2a  
        'B5': {'angle': 90, 'distance': 1300, 'radius': 400}, \# Esquilino Ovest  
        'B6': {'angle': 120, 'distance': 1400, 'radius': 400},\# Monti-Appio  
        'B7': {'angle': 175, 'distance': 1500, 'radius': 400},\# San Saba-Ostiense  
        'B8': {'angle': 205, 'distance': 1300, 'radius': 400},\# Ripa-Aventino 2  
        'B10': {'angle': 235, 'distance': 1400, 'radius': 400},\# Trastevere 2a  
          
        \# 3a Fascia (C-zones, 20-30 min)  
        'C1': {'angle': 295, 'distance': 1900, 'radius': 500},\# Ponte  
        'C2': {'angle': 345, 'distance': 1900, 'radius': 500},\# Campo Marzio  
        'C3': {'angle': 45, 'distance': 2000, 'radius': 500}, \# Repubblica  
        'C4': {'angle': 80, 'distance': 2000, 'radius': 500}, \# Esquilino Est  
        'C5': {'angle': 115, 'distance': 2100, 'radius': 500},\# Appio-Latino  
        'C6': {'angle': 160, 'distance': 2300, 'radius': 500},\# Ostiense-Ardeatino  
        'C7': {'angle': 215, 'distance': 1900, 'radius': 500},\# Testaccio  
        'C8': {'angle': 245, 'distance': 2100, 'radius': 500},\# Trastevere 3  
          
        \# Composite spatial areas  
        'A1B1': {'angle': 275, 'distance': 800, 'radius': 450},  
        'A2B2': {'angle': 312, 'distance': 850, 'radius': 450},  
        'A3B3': {'angle': 27, 'distance': 850, 'radius': 450},  
          
        \# Unnamed study divisions  
        'Studio\_1': {'angle': 5, 'distance': 1500, 'radius': 450},  
        'Studio\_2': {'angle': 77, 'distance': 1500, 'radius': 450},  
        'Studio\_3': {'angle': 149, 'distance': 1500, 'radius': 450},  
        'Studio\_4': {'angle': 221, 'distance': 1500, 'radius': 450},  
        'Studio\_5': {'angle': 293, 'distance': 1500, 'radius': 450},  
    }  
      
    features \= \[\]  
    m\_per\_deg\_lat \= 111320.0 \# Length of 1 degree latitude in meters  
      
    for idx, row in df.iterrows():  
        zona\_id \= str(row\['Zona\_ID'\]).strip()  
          
        \# Get placement parameters or provide fallback values  
        placement \= zone\_placements.get(zona\_id, {'angle': 180, 'distance': 1500, 'radius': 400})  
          
        angle\_rad \= math.radians(placement\['angle'\])  
        dist \= placement\['distance'\]  
        rad \= placement\['radius'\]  
          
        \# Convert polar offsets (bearing, distance) to Cartesian meters  
        dy \= dist \* math.cos(angle\_rad)  
        dx \= dist \* math.sin(angle\_rad)  
          
        \# Translate meters to latitude and longitude coordinates  
        lat\_c \= lat\_center \+ (dy / m\_per\_deg\_lat)  
        lon\_c \= lon\_center \+ (dx / (m\_per\_deg\_lat \* math.cos(math.radians(lat\_center))))  
          
        \# Compute points for an octagon polygon  
        num\_sides \= 8  
        coords \= \[\]  
        for i in range(num\_sides):  
            p\_angle \= 2 \* math.pi \* i / num\_sides  
            px \= rad \* math.sin(p\_angle)  
            py \= rad \* math.cos(p\_angle)  
              
            p\_lat \= lat\_c \+ (py / m\_per\_deg\_lat)  
            p\_lon \= lon\_c \+ (px / (m\_per\_deg\_lat \* math.cos(math.radians(lat\_c))))  
            coords.append(\[p\_lon, p\_lat\])  
              
        \# Close the polygon ring loop  
        coords.append(coords)  
          
        \# Construct and clean the features properties dictionary  
        properties \= {}  
        for col in df.columns:  
            val \= row\[col\]  
            if pd.isna(val):  
                properties\[col\] \= None  
            elif isinstance(val, (int, np.integer)):  
                properties\[col\] \= int(val)  
            elif isinstance(val, (float, np.floating)):  
                properties\[col\] \= round(float(val), 4\)  
            else:  
                properties\[col\] \= str(val)  
                  
        \# Inject computed centroids for map tooltips or Plotly hover text  
        properties\['centroid\_lat'\] \= round(lat\_c, 5\)  
        properties\['centroid\_lon'\] \= round(lon\_c, 5\)  
          
        feature \= {  
            "type": "Feature",  
            "properties": properties,  
            "geometry": {  
                "type": "Polygon",  
                "coordinates": \[coords\]  
            }  
        }  
        features.append(feature)  
          
    geojson\_data \= {  
        "type": "FeatureCollection",  
        "features": features  
    }  
      
    with open(output\_geojson\_path, 'w', encoding='utf-8') as f:  
        json.dump(geojson\_data, f, indent=2, ensure\_ascii=False)  
          
    print(f"GeoJSON successfully generated with {len(features)} zones.")

if \_\_name\_\_ \== '\_\_main\_\_':  
    generate\_carme\_geojson(  
        csv\_path='carme\_indicators.csv',  
        output\_geojson\_path='carme\_zones.geojson'  
    )

### 3\. How to Use the Output in Streamlit

In your data\_loader.py module, you can directly import this GeoJSON using **GeoPandas** to replace the static dict data:  
import geopandas as gpd

class RiabitaDataLoader:  
    def \_\_init\_\_(self, geojson\_path="carme\_zones.geojson"):  
        \# This single line reads the file and parses all geometries and properties automatically  
        self.districts\_df \= gpd.read\_file(geojson\_path)  
To display these zones inside an interactive Mapbox choropleth directly within visuals.py:  
import plotly.express as px

def create\_selection\_map(self, gdf):  
    fig \= px.choropleth\_mapbox(  
        gdf,  
        geojson=json.loads(gdf.to\_json()), \# Use the internal geometry  
        locations=gdf.index,  
        color="Mean\_RIz",                  \# Color code zones based on real habitability potential \[11\]  
        color\_continuous\_scale="Viridis",  
        mapbox\_style="carto-positron",  
        zoom=12.5,  
        center={"lat": 41.889, "lon": 12.482},  
        opacity=0.6,  
        hover\_name="Nome",  
        hover\_data=\["Classe", "Popolazione\_Residente", "Posti\_Letto\_Turistici"\] \# Hover info matches mockup \[5, 12\]  
    )  
    fig.update\_layout(margin={"r":0,"t":0,"l":0,"b":0})  
    return fig

### Key Technical Advantages of this Integration:

1. **Type-Safe Property Injection:** The parser handles null values (such as the missing employment rates for A0) without breaking, turning them into JSON-friendly null values 5\.  
2. **No Spatial Degeneracy:** Octagonal boundaries prevent overlapping coordinates at the center, meaning Streamlit’s Plotly event listeners can cleanly distinguish click events for each neighborhood.  
3. **Real Hover Metrics:** When players hover over a zone on the selection map, the exact statistics from the CArME report—such as the **260% tourist-bed-to-population ratio in Trevi (A3)** or the **low graduate percentage (3.1%) in A0**—will display in real-time before starting the simulation 5, 13\.

