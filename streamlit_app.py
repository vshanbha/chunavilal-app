import streamlit as st
import pandas as pd
import json
import zipfile

import plotly.express as px
from langchain_openai import ChatOpenAI
from langchain.agents import AgentType
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from streamlit_extras.dataframe_explorer import dataframe_explorer

st.set_page_config(
    page_title='Chunavilal',
    page_icon=':ballot_box_with_ballot:',
    layout="wide"
)

def start_chat(df, ct):
    ct.markdown("Ask Chunavilal about the election results?")
    history = ct.container(height=400)
    if "messages" not in st.session_state or ct.button("Clear conversation history"):
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    for msg in st.session_state.messages:
        history.chat_message(msg["role"]).write(msg["content"])

    if prompt := ct.chat_input(placeholder="What is this data about?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        history.chat_message("user").write(prompt)

        if not openai_api_key:
            st.sidebar.info("Please add your OpenAI API key to continue.")
            st.stop()


        pandas_df_agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=True,
            prefix="""Respond strictly using the dataframe provided as input. 
                The dataframe contains the following columns:
                name : Name of the candidate,
                constituency_name : Name of the constituency,
                state_name : State or Union Territory which the constituency is a part of,
                party : Name of the party to which the candidate belongs,
                status : Whether the candidate won or lost,
                votes : Number of votes received by the candidate,
                margin : Victory or defeat margin for the candidate.
                
                Translate the question to a query for the dataframe, execute the query and then respond to the question.
                If you can't find data in the input dataframe, then indicate that you do not have the data
                """,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True
        )

        with history.chat_message("assistant"):
#            st_cb = StreamlitCallbackHandler(history.container(), expand_new_thoughts=False)
#            response = pandas_df_agent.run(st.session_state.messages, callbacks=[st_cb])
            response = pandas_df_agent.run(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": response})
            history.write(response)

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
        df = pd.DataFrame(candidate_list)
        df["votes"] = pd.to_numeric(df["votes"])
        return df
    else:
        return None
    
def show_wins(won_df, ct):
    # Group by party and calculate the number of wins
    wins_df = won_df.groupby("party").size().reset_index(name="wins")
    if (wins_df["wins"].count()>10):
        wins_df.loc[wins_df["wins"] < 1, "party"] = "Others"
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

st.title(":ballot_box_with_ballot: Chunavilal - Election Result Analyst")
if "API_KEY" in st.secrets:
    openai_api_key = st.secrets["API_KEY"]
else:
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

llm = ChatOpenAI(
            temperature=0, openai_api_key=openai_api_key, streaming=True
        )

states = df["state_name"].unique()
states = ["All India", *states ]


charts, raw_data, chat = st.tabs(["Charts", "Raw Data", "Chat with Chunavilal"])

down_df = df[["name","constituency_name","state_name","party","status","votes","margin"]]

start_chat(down_df, chat)


with raw_data:
    # Raw Data
    with raw_data:
        raw_data.markdown("Candidate wise vote information:")
        filtered_df = dataframe_explorer(down_df, case=False)
        raw_data.dataframe(filtered_df, column_config={
                "name": "Candidate name",
                "party": "Party",
                "constituency_name": "Constituency",
                "state_name": "State / Union Territory",
                "status": "Status",
                "votes": st.column_config.NumberColumn(
                    "Votes",
                    format="%d",
                ),
                "margin": st.column_config.NumberColumn("Margin",format="%+i")
            },
            column_order=("name","party","constituency_name","state_name","status","votes","margin"),
                use_container_width=True,
                hide_index=True
        )

# Offer option to select state / Union Territory
sel_state = charts.selectbox("Select State or Union Territory", states)

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

charts.info("""Aggregate stats for {}.\n
        Total votes {} split across {} parties and {} constituencies"""
        .format(sel_state,total_votes, len(parties), len(constituencies)))

col1, col2 = charts.columns(2)

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
charts.plotly_chart(fig,use_container_width=True)