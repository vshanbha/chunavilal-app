import streamlit as st
import pandas as pd
import json
import zipfile

import plotly.express as px
# from langchain_openai import ChatOpenAI
# from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate

st.set_page_config(
    page_title='Chunavilal',
    page_icon=':ballot_box_with_ballot:',
    layout="wide"

)

st.title("Chunavilal")
# if "API_KEY" in st.secrets:
#     openai_api_key = st.secrets["API_KEY"]
# else:
#     openai_api_key = st.text_input("OpenAI API Key", type="password")

@st.cache_data(ttl="2h")
def load_data():
    zipPath = "database.zip"
    with zipfile.ZipFile(zipPath, mode="r") as archive:
        for file in archive.namelist():
            if file.endswith(".json"):
                archive.extract(file, "downloads/")

    file_path = "downloads/candidate_data.json"
    with open(file_path) as json_file:
        candidate_list = json.load(json_file)
    if (candidate_list):
        return pd.DataFrame(candidate_list)
    else:
        return None

df = load_data()

df["votes"] = pd.to_numeric(df["votes"])

# Offer option to select state / Union Territory
sel_state = st.selectbox("Select State or Union Territory", df["state_name"].unique())

of = df.query("state_name == @sel_state")

# Total votes
total_votes = of["votes"].sum()

# Unique parties
parties = of["party"].unique()

# Filter only the 'won' status rows
won_df = of[of["status"] == "won"]

# Unique constituencies
constituencies = won_df["constituency_code"].unique()

st.info("""Aggregate stats for {}.\n
        Total votes {} split across {} parties and {} constituencies"""
        .format(sel_state,total_votes, len(parties), len(constituencies)))

# Group by party and calculate the number of wins
wins_df = won_df.groupby("party").size().reset_index(name="wins")
wins_df

# Replace name of Party with "Others" if percentage of total votes is less than 3
gf = of.groupby("party")["votes"].sum().to_frame()
gf["percentage_vote"] = gf["votes"] * 100/ total_votes

gf["party_name"] = gf.index
gf["party_name"] = gf["party_name"].mask(
    (gf['percentage_vote'] < 3.0) & 
    ((gf["party_name"] != "Independent") & (gf["party_name"] != "None of the Above")), "Others")

show_parties = gf["party_name"].unique()
of["party_name"] = of["party"].copy()
mask = ~of["party"].isin(show_parties)
of.loc[mask, "party_name"] = "Others"

fig = px.bar(of, x="constituency_name", y="votes", color="party_name",
#              color_discrete_map = color_map,
             hover_data=['party','status','votes','margin'],height=600)
st.plotly_chart(fig,use_container_width=True)

# Raw Data

st.dataframe(of, column_config={
        "url" : st.column_config.ImageColumn(
             "Photo",help="Photo of the candidate"
        ),
        "name": "Candidate name",
        "status": "Status",
        "votes": st.column_config.NumberColumn(
            "Votes",
            format="%d",
        ),
        "margin": st.column_config.NumberColumn("Margin",format="%+i"),
        "party": "Party",
        "constituency_name": "Constituency",
    },
    column_order=("name","status","votes","margin","party","constituency_name"),
    use_container_width=True,
    hide_index=True)
