import json
from io import StringIO

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st


STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"

JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": [
          "2014",
          "2015",
          "2016",
          "2017",
          "2018",
          "2019",
          "2020",
          "2021",
          "2022",
          "2023"
        ]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "39",
          "44",
          "49",
          "51",
          "57",
          "59",
          "65",
          "67",
          "70",
          "74",
          "78",
          "82",
          "84",
          "86",
          "37"
        ]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": [
          "2",
          "3"
        ]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}
"""


@st.cache_data
def import_data():
    headers = {
        "Content-Type": "application/json"
    }

    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    response = requests.post(
        STATISTIKAAMETI_API_URL,
        json=parsed_payload,
        headers=headers
    )
    response.raise_for_status()

    text = response.content.decode("utf-8-sig")
    df = pd.read_csv(StringIO(text))

    df["Aasta"] = df["Aasta"].astype(int)
    df["Loomulik iive"] = (
        df["Mehed Loomulik iive"] + df["Naised Loomulik iive"]
    )

    return df


@st.cache_data
def import_geojson():
    gdf = gpd.read_file(GEOJSON_FILE)
    return gdf


def merge_data(df, gdf):
    merged_data = gdf.merge(
        df,
        left_on="MNIMI",
        right_on="Maakond",
        how="inner"
    )
    return merged_data


def get_data_for_year(df, year):
    year_data = df[df["Aasta"] == year]
    return year_data


def plot_map(df, year):
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    df.plot(
        column="Loomulik iive",
        ax=ax,
        legend=True,
        cmap="viridis",
        legend_kwds={"label": "Loomulik iive"}
    )

    ax.set_title(f"Loomulik iive maakonniti aastal {year}")
    ax.axis("off")
    plt.tight_layout()

    return fig


st.title("Loomulik iive Eesti maakondades")
st.write(
    "Töölaud kuvab Statistikaameti andmete põhjal loomulikku iivet "
    "Eesti maakondades valitud aastal."
)

df = import_data()
gdf = import_geojson()
merged_data = merge_data(df, gdf)

available_years = sorted(merged_data["Aasta"].unique())

selected_year = st.sidebar.selectbox(
    "Vali aasta",
    available_years,
    index=len(available_years) - 1
)

year_data = get_data_for_year(merged_data, selected_year)

st.subheader(f"Loomulik iive aastal {selected_year}")

fig = plot_map(year_data, selected_year)
st.pyplot(fig)

st.dataframe(
    year_data[["Maakond", "Mehed Loomulik iive", "Naised Loomulik iive", "Loomulik iive"]]
    .sort_values("Loomulik iive", ascending=False)
    .reset_index(drop=True)
)
