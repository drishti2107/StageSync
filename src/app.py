import streamlit as st
import pandas as pd
import psycopg2
from crud import (create_production, read_productions, update_production,
                  delete_production, read_director_ids, read_producer_ids)

TYPES = ["Play", "Musical", "Opera", "Dance", "Concert"]
COLS = ["production_id", "title", "type", "start_date", "end_date",
        "director_id", "producer_id"]

st.title("StageSync - Production Manager")
tab_view, tab_add, tab_upd, tab_del = st.tabs(["View", "Add", "Update", "Delete"])

directors = read_director_ids()
producers = read_producer_ids()

def show_db_error(e):
    msg = str(e).lower()
    if "foreign key" in msg:
        st.error("Can't do that: this production is referenced by other records "
                 "(cast, crew or resources), or the director/producer doesn't exist.")
    elif "check constraint" in msg:
        st.error("A rule was broken: type must be valid and end date must not be before start date.")
    else:
        st.error(f"Database error: {e}")

with tab_view:
    st.dataframe(pd.DataFrame(read_productions(), columns=COLS), use_container_width=True)

with tab_add:
    if not directors or not producers:
        st.warning("Add at least one director and one producer first.")
    else:
        title = st.text_input("Title", key="add_title")
        ptype = st.selectbox("Type", TYPES, key="add_type")
        start = st.date_input("Start date", key="add_start")
        end = st.date_input("End date", key="add_end")
        did = st.selectbox("Director ID", directors, key="add_dir")
        pid = st.selectbox("Producer ID", producers, key="add_prod")
        if st.button("Add production"):
            if not title.strip():
                st.error("Title is required.")
            elif end < start:
                st.error("End date cannot be before start date.")
            else:
                try:
                    n = create_production(title.strip(), ptype, start, end, did, pid)
                    st.success(f"Record inserted successfully ({n} row).")
                except psycopg2.Error as e:
                    show_db_error(e)

with tab_upd:
    rows = read_productions()
    if rows:
        chosen = st.selectbox("Select production", rows,
                              format_func=lambda r: f"{r[0]} - {r[1]}", key="upd_sel")
        pk = chosen[0]
        new_title = st.text_input("Title", chosen[1], key=f"ut{pk}")
        new_type = st.selectbox("Type", TYPES, index=TYPES.index(chosen[2]), key=f"uy{pk}")
        new_start = st.date_input("Start date", chosen[3], key=f"us{pk}")
        new_end = st.date_input("End date", chosen[4], key=f"ue{pk}")
        new_did = st.selectbox("Director ID", directors,
                               index=directors.index(chosen[5]), key=f"ud{pk}")
        new_pid = st.selectbox("Producer ID", producers,
                               index=producers.index(chosen[6]), key=f"up{pk}")
        if st.button("Update"):
            if not new_title.strip():
                st.error("Title is required.")
            elif new_end < new_start:
                st.error("End date cannot be before start date.")
            else:
                try:
                    n = update_production(pk, new_title.strip(), new_type,
                                          new_start, new_end, new_did, new_pid)
                    st.success(f"Updated {n} row.")
                except psycopg2.Error as e:
                    show_db_error(e)

with tab_del:
    rows = read_productions()
    if rows:
        chosen = st.selectbox("Production to delete", rows,
                              format_func=lambda r: f"{r[0]} - {r[1]}", key="del_sel")
        sure = st.checkbox("I'm sure")
        if st.button("Delete"):
            if not sure:
                st.warning("Tick the checkbox first.")
            else:
                try:
                    n = delete_production(chosen[0])
                    st.success(f"Deleted {n} row.")
                except psycopg2.Error as e:
                    show_db_error(e)