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

    file_path = "downloads/uncontested.json"
    with open(file_path) as json_file:
        uncontested = json.load(json_file)
        if not (not uncontested or len(uncontested) == 0):
            for val in uncontested:
                val["votes"] = None
                val["margin"] = None
                candidate_list.append(val)
    if (candidate_list):
        return pd.DataFrame(candidate_list)
    else:
        return None
    
def show_wins(won_df, ct):
    # Group by party and calculate the number of wins
    wins_df = won_df.groupby("party").size().reset_index(name="wins")
    if (wins_df["wins"].count()>10):
        wins_df.loc[wins_df["wins"] < 2, "party"] = "Others"
    fig1 = px.pie(wins_df, values="wins", names="party", title="Wins by Party:")
    fig1.update_traces(textinfo="value", hoverinfo="label+percent+value")
    ct.plotly_chart(fig1,use_container_width=True)

def show_percentage(grouped_df, ct):
    fig1 = px.pie(grouped_df, values="percentage_vote", names="party_name", title="Vote Percentage by Party:",
                  hover_data=["votes"])
    ct.plotly_chart(fig1,use_container_width=True)


def get_vote_percentage(df):
    # Replace name of Party with "Others" if percentage of total votes is less than 3
    gf = df.groupby("party")["votes"].sum().to_frame()
    gf["percentage_vote"] = gf["votes"] * 100/ total_votes

    gf["party_name"] = gf.index
    gf["party_name"] = gf["party_name"].mask(
        (gf['percentage_vote'] < 1.0) & 
        ((gf["party_name"] != "Independent") & (gf["party_name"] != "None of the Above")), "Others")
    
    return gf

df = load_data()

df["votes"] = pd.to_numeric(df["votes"])

states = df["state_name"].unique()
states = ["All India", *states ]

# Offer option to select state / Union Territory
sel_state = st.selectbox("Select State or Union Territory", states)

of = df
if "All India" != sel_state:
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
col1, col2 = st.columns(2)

show_wins(won_df, col1);

grouped_df = get_vote_percentage(of)
show_percentage(grouped_df, col2)

# Show constituency wise distribution
show_parties = grouped_df["party_name"].unique()
of["party_name"] = of["party"].copy()
mask = ~of["party"].isin(show_parties)
of.loc[mask, "party_name"] = "Others"

fig = px.bar(of, y="constituency_name", x="votes", color="party_name",orientation="h",
             hover_data=["party","name","status","votes","margin"], height=800,
             title="Vote Percentage by Constituency:")
st.plotly_chart(fig,use_container_width=True)

# Raw Data
st.markdown("Candidate wise vote information:")
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
    hide_index=True
    )
