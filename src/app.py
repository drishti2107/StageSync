
import streamlit as st
import pandas as pd
import psycopg2

from crud import (
    create_production,
    read_productions,
    update_production,
    delete_production,
    read_director_ids,
    read_producer_ids
)

from db import run


# ==================================================
# 1. CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="StageSync",
    page_icon="🎬",
    layout="wide"
)

TYPES = ["Play", "Musical", "Opera", "Dance", "Concert"]

COLS = [
    "production_id",
    "title",
    "type",
    "start_date",
    "end_date",
    "director_id",
    "producer_id"
]

WORKSPACE_TABLES = {
    "Productions": [
        "production"
    ],

    "People": [
        "director",
        "producer",
        "cast_member",
        "crew_member",
        "stage_manager",
        "vendor"
    ],

    "Scheduling": [
        "schedule",
        "rehearsal",
        "performance",
        "perf_reh_venue_book",
        "rehearsal_req_cast",
        "rehearsal_req_crew",
        "attendance",
        "call_sheet"
    ],

    "Budget & Expenses": [
        "budget",
        "expense",
        "vendor"
    ],

    "Resources": [
        "resource",
        "prop",
        "costume",
        "equipment",
        "rehearsal_resource_checkout"
    ],

    "Venues": [
        "venue"
    ]
}


# ==================================================
# 2. SESSION STATE
# ==================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "workspace" not in st.session_state:
    st.session_state.workspace = "Productions"


# ==================================================
# 3. CUSTOM CSS
# ==================================================

st.markdown("""
<style>

.stApp {
    background-color: #0e1424;
    color: #f1f5f9;
}

[data-testid="stSidebar"] {
    background-color: #151e32;
}

[data-testid="stSidebar"] .stButton {
    width: 100%;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    display: flex;
    justify-content: flex-start;
    align-items: center;
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
}

[data-testid="stSidebar"] .stButton > button p {
    text-align: left;
    width: 100%;
}

[data-testid="stSidebar"] button[kind="secondary"] {
    background-color: transparent;
    color: #e2e8f0;
    border: 1px solid transparent;
}

[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background-color: #293653;
    color: white;
    border: 1px solid #475569;
}

[data-testid="stSidebar"] button[kind="primary"] {
    background-color: #293653;
    color: #c4b5fd;
    border: 1px solid #475569;
}

h1, h2, h3 {
    color: #f8fafc;
}

.main-title {
    font-size: 34px;
    font-weight: 750;
    color: #c4b5fd;
    margin-bottom: 0;
}

.subtitle {
    color: #94a3b8;
    font-size: 14px;
    margin-bottom: 25px;
}

div[data-testid="stMetric"] {
    background-color: #19243a;
    border: 1px solid #303e59;
    padding: 18px;
    border-radius: 12px;
}

.stButton > button[kind="primary"] {
    background-color: #7c3aed;
    color: white;
    border: none;
    border-radius: 8px;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #303e59;
    border-radius: 10px;
}

hr {
    border-color: #303e59;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 4. DATABASE FUNCTIONS
# ==================================================

def show_db_error(e):

    msg = str(e).lower()

    if "foreign key" in msg:
        st.error(
            "This record is referenced by another table, "
            "or a referenced record does not exist."
        )

    elif "check constraint" in msg:
        st.error(
            "Invalid data. One or more database rules "
            "have been violated."
        )

    elif "unique constraint" in msg:
        st.error(
            "A record with this unique value already exists."
        )

    else:
        st.error(f"Database error: {e}")


def get_productions():

    return read_productions()


def get_all_tables():

    rows, _ = run(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """,
        fetch=True
    )

    return [row[0] for row in rows]


def get_table_data(table_name):

    tables = get_all_tables()

    if table_name not in tables:
        raise ValueError("Invalid table name")

    safe_name = '"' + table_name.replace('"', '""') + '"'

    rows, _ = run(
        f"SELECT * FROM {safe_name}",
        fetch=True
    )

    columns, _ = run(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table_name,),
        fetch=True
    )

    column_names = [col[0] for col in columns]

    return pd.DataFrame(rows, columns=column_names)


def display_table(table_name):

    df = get_table_data(table_name)

    st.markdown(
        f"### {table_name.replace('_', ' ').title()}"
    )

    col1, col2 = st.columns(2)

    col1.metric("Total Records", len(df))
    col2.metric("Total Columns", len(df.columns))

    st.divider()

    search = st.text_input(
        "🔍 Search records",
        placeholder="Search in this table...",
        key=f"search_{table_name}"
    )

    filtered = df.copy()

    if search and not filtered.empty:

        filtered = filtered[
            filtered.astype(str).apply(
                lambda column: column.str.contains(
                    search,
                    case=False,
                    na=False
                )
            ).any(axis=1)
        ]

    st.caption(
        f"Showing {len(filtered)} of {len(df)} records"
    )

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download CSV",
        data=filtered.to_csv(index=False),
        file_name=f"{table_name}.csv",
        mime="text/csv",
        key=f"download_{table_name}"
    )


# ==================================================
# 5. SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:

    st.markdown("## 🎬 StageSync")

    st.caption("PRODUCTION MANAGEMENT")

    st.divider()

    # DASHBOARD

    st.markdown("##### MAIN MENU")

    if st.button(
        "🏠  Dashboard",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state.page == "Dashboard"
            else "secondary"
        )
    ):

        st.session_state.page = "Dashboard"
        st.rerun()

    st.divider()

    # WORKSPACE

    st.markdown("##### WORKSPACE")

    workspace_items = {
        "Productions": "🎭",
        "People": "👥",
        "Scheduling": "📅",
        "Budget & Expenses": "💰",
        "Resources": "📦",
        "Venues": "📍"
    }

    for item, emoji in workspace_items.items():

        active = (
            st.session_state.page == "Workspace"
            and st.session_state.workspace == item
        )

        if st.button(
            f"{emoji}  {item}",
            use_container_width=True,
            type="primary" if active else "secondary",
            key=f"nav_{item}"
        ):

            st.session_state.page = "Workspace"
            st.session_state.workspace = item
            st.rerun()

    st.divider()

    # SYSTEM

    st.markdown("##### SYSTEM - Navigate Other System Features")

    if st.button(
        "🗄️  Database Explorer",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state.page == "Database Explorer"
            else "secondary"
        )
    ):

        st.session_state.page = "Database Explorer"
        st.rerun()

    st.divider()

    st.caption("CONNECTED DATABASE")

    st.markdown("🟢 PostgreSQL")

    st.caption("Production Management System")

    st.divider()

    st.caption("StageSync | 2026")


# ==================================================
# 6. MAIN HEADER
# ==================================================

page = st.session_state.page

st.markdown(
    '<div class="main-title">🎬 StageSync</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Your production management workspace'
    '</div>',
    unsafe_allow_html=True
)


# ==================================================
# 7. DASHBOARD
# ==================================================

if page == "Dashboard":

    st.subheader("Dashboard")

    st.caption(
        "Overview of your production database"
    )

    try:

        rows = get_productions()

        df = pd.DataFrame(rows, columns=COLS)

        total = len(df)

        if total > 0:

            dates = pd.to_datetime(
                df["start_date"],
                errors="coerce"
            )

            upcoming = int(
                (
                    dates >
                    pd.Timestamp.today().normalize()
                ).sum()
            )

            production_types = df["type"].nunique()

        else:

            upcoming = 0
            production_types = 0

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Productions",
            total
        )

        col2.metric(
            "Upcoming Productions",
            upcoming
        )

        col3.metric(
            "Production Types",
            production_types
        )

        st.divider()

        st.subheader("Recent Productions")

        if total > 0:

            recent = df.tail(5).copy()

            recent.columns = [
                "Production ID",
                "Title",
                "Type",
                "Start Date",
                "End Date",
                "Director ID",
                "Producer ID"
            ]

            st.dataframe(
                recent,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No productions have been added yet."
            )

    except psycopg2.Error as e:

        show_db_error(e)


# ==================================================
# 8. WORKSPACE
# ==================================================

elif page == "Workspace":

    workspace = st.session_state.workspace

    st.subheader(workspace)

    st.caption(
        f"Manage and explore your {workspace.lower()} data."
    )

    try:

        # PRODUCTIONS: FULL CRUD

        if workspace == "Productions":

            rows = get_productions()

            df = pd.DataFrame(rows, columns=COLS)

            action = st.radio(
                "Choose an operation",
                ["View", "Add", "Update", "Delete"],
                horizontal=True
            )

            st.divider()

            # VIEW

            if action == "View":

                st.markdown("### All Productions")

                col1, col2 = st.columns([3, 1])

                with col1:

                    search = st.text_input(
                        "🔍 Search productions",
                        placeholder="Search by title, type or ID..."
                    )

                with col2:

                    type_filter = st.selectbox(
                        "Filter by type",
                        ["All"] + TYPES
                    )

                filtered = df.copy()

                if search:

                    filtered = filtered[
                        filtered.astype(str).apply(
                            lambda column: column.str.contains(
                                search,
                                case=False,
                                na=False
                            )
                        ).any(axis=1)
                    ]

                if type_filter != "All":

                    filtered = filtered[
                        filtered["type"] == type_filter
                    ]

                display_df = filtered.copy()

                display_df.columns = [
                    "Production ID",
                    "Title",
                    "Type",
                    "Start Date",
                    "End Date",
                    "Director ID",
                    "Producer ID"
                ]

                st.caption(
                    f"Showing {len(filtered)} records"
                )

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

            # ADD

            elif action == "Add":

                st.markdown("### Add New Production")

                directors = read_director_ids()
                producers = read_producer_ids()

                if not directors or not producers:

                    st.warning(
                        "Add at least one director and producer first."
                    )

                else:

                    with st.form("add_production_form"):

                        st.markdown("#### Production Details")

                        col1, col2 = st.columns(2)

                        with col1:

                            title = st.text_input(
                                "Production Title"
                            )

                            ptype = st.selectbox(
                                "Production Type",
                                TYPES
                            )

                            start = st.date_input(
                                "Start Date"
                            )

                        with col2:

                            end = st.date_input(
                                "End Date"
                            )

                            did = st.selectbox(
                                "Director ID",
                                directors
                            )

                            pid = st.selectbox(
                                "Producer ID",
                                producers
                            )

                        submitted = st.form_submit_button(
                            "Add Production",
                            use_container_width=True
                        )

                        if submitted:

                            if not title.strip():

                                st.error("Title is required.")

                            elif end < start:

                                st.error(
                                    "End date cannot be before start date."
                                )

                            else:

                                try:

                                    n = create_production(
                                        title.strip(),
                                        ptype,
                                        start,
                                        end,
                                        did,
                                        pid
                                    )

                                    st.success(
                                        f"Successfully added {n} production."
                                    )

                                    st.rerun()

                                except psycopg2.Error as e:

                                    show_db_error(e)

            # UPDATE

            elif action == "Update":

                st.markdown("### Update Production")

                if not rows:

                    st.info("No productions available to update.")

                else:

                    directors = read_director_ids()
                    producers = read_producer_ids()

                    chosen = st.selectbox(
                        "Select Production",
                        rows,
                        format_func=lambda r: f"{r[0]} - {r[1]}"
                    )

                    pk = chosen[0]

                    if not directors or not producers:

                        st.warning(
                            "Director and producer records are required."
                        )

                    else:

                        with st.form("update_production_form"):

                            st.markdown("#### Edit Production Details")

                            col1, col2 = st.columns(2)

                            with col1:

                                new_title = st.text_input(
                                    "Production Title",
                                    value=chosen[1]
                                )

                                new_type = st.selectbox(
                                    "Production Type",
                                    TYPES,
                                    index=(
                                        TYPES.index(chosen[2])
                                        if chosen[2] in TYPES else 0
                                    )
                                )

                                new_start = st.date_input(
                                    "Start Date",
                                    value=chosen[3]
                                )

                            with col2:

                                new_end = st.date_input(
                                    "End Date",
                                    value=chosen[4]
                                )

                                new_did = st.selectbox(
                                    "Director ID",
                                    directors,
                                    index=(
                                        directors.index(chosen[5])
                                        if chosen[5] in directors else 0
                                    )
                                )

                                new_pid = st.selectbox(
                                    "Producer ID",
                                    producers,
                                    index=(
                                        producers.index(chosen[6])
                                        if chosen[6] in producers else 0
                                    )
                                )

                            submitted = st.form_submit_button(
                                "Save Changes",
                                use_container_width=True
                            )

                            if submitted:

                                if not new_title.strip():

                                    st.error("Title is required.")

                                elif new_end < new_start:

                                    st.error(
                                        "End date cannot be before start date."
                                    )

                                else:

                                    try:

                                        n = update_production(
                                            pk,
                                            new_title.strip(),
                                            new_type,
                                            new_start,
                                            new_end,
                                            new_did,
                                            new_pid
                                        )

                                        st.success(
                                            f"Successfully updated {n} record."
                                        )

                                        st.rerun()

                                    except psycopg2.Error as e:

                                        show_db_error(e)

            # DELETE

            elif action == "Delete":

                st.markdown("### Delete Production")

                if not rows:

                    st.info("No productions available to delete.")

                else:

                    chosen = st.selectbox(
                        "Select Production",
                        rows,
                        format_func=lambda r: f"{r[0]} - {r[1]}"
                    )

                    st.warning(
                        f"You are about to delete: {chosen[1]}"
                    )

                    sure = st.checkbox(
                        "I understand that this action cannot be undone."
                    )

                    if st.button(
                        "Delete Production",
                        type="primary"
                    ):

                        if not sure:

                            st.warning(
                                "Please confirm deletion first."
                            )

                        else:

                            try:

                                n = delete_production(chosen[0])

                                st.success(
                                    f"Successfully deleted {n} record."
                                )

                                st.rerun()

                            except psycopg2.Error as e:

                                show_db_error(e)

        # OTHER WORKSPACE SECTIONS

        else:

            tables = get_all_tables()

            available_tables = [
                table
                for table in WORKSPACE_TABLES[workspace]
                if table in tables
            ]

            if not available_tables:

                st.info(
                    "No tables found for this workspace."
                )

            else:

                selected_table = st.selectbox(
                    "Select a table",
                    available_tables,
                    format_func=lambda x: x.replace(
                        "_", " "
                    ).title()
                )

                st.divider()

                display_table(selected_table)

    except psycopg2.Error as e:

        show_db_error(e)


# ==================================================
# 9. DATABASE EXPLORER
# ==================================================

elif page == "Database Explorer":

    st.subheader("Database Explorer")

    st.caption(
        "Browse all tables in your PostgreSQL database."
    )

    try:

        tables = get_all_tables()

        if not tables:

            st.info("No database tables found.")

        else:

            selected_table = st.selectbox(
                "Select a database table",
                tables,
                format_func=lambda x: x.replace(
                    "_", " "
                ).title()
            )

            st.divider()

            display_table(selected_table)

    except psycopg2.Error as e:

        show_db_error(e)
