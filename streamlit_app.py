# streamlit_app.py
"""
RBAC Role Mining Dashboard - Full Streamlit App (with Upload UI)
- Upload the 3 backend input files directly from the UI
- Shows entitlements in Generate and Review pages
- Two-column layout for Review with a scrollable entitlements pane
- Batch processing, export (CSV/JSON), selection & approval
- Uses API endpoints for clusters & role generation (FastAPI backend)
- Replaces deprecated st.experimental_rerun -> st.rerun
"""

import os
import json
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


# -----------------------
# Configuration
# -----------------------
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")  # update if needed

st.set_page_config(
    page_title="RBAC Role Mining",
    page_icon="🔐",
    layout="wide",
)

# -----------------------
# Custom CSS
# -----------------------
st.markdown(
    """
<style>
    .naming-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .business-focused { background-color: #e8f4f8; border-left: 4px solid #1e88e5; }
    .technical-focused { background-color: #f3e5f5; border-left: 4px solid #8e24aa; }
    .hierarchical-focused { background-color: #e8f5e9; border-left: 4px solid #43a047; }
    .recommended { background-color: #fff3cd; border: 2px solid #ffc107; }

    /* Scrollable entitlement box */
    .ent-box {
        max-height: 320px;
        overflow: auto;
        padding-right: 0.5rem;
    }

    /* Small responsive tweaks */
    @media (max-width: 800px) {
        .ent-box { max-height: 240px; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------
# Session state init
# -----------------------
if "generated_roles" not in st.session_state:
    # stored as { cluster_id: role_response_dict }
    st.session_state["generated_roles"] = {}

if "batch_status" not in st.session_state:
    st.session_state["batch_status"] = None


# -----------------------
# API helpers
# -----------------------
def check_api() -> bool:
    try:
        resp = requests.get(f"{API_BASE_URL}/health/", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def get_clusters():
    try:
        resp = requests.get(f"{API_BASE_URL}/clusters/", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def generate_multiple_roles(cluster_id: str, force: bool = False):
    """
    POST to roles/generate-multiple. If force==True, backend can overwrite cached results.
    """
    try:
        payload = {"cluster_id": cluster_id}
        if force:
            payload["force"] = True
        resp = requests.post(f"{API_BASE_URL}/roles/generate-multiple", json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def upload_data_file(file, file_type: str):
    """
    Upload a single file to FastAPI.
    Endpoint (per your backend): POST /api/v1/clusters/upload?file_type=...
    file_type ∈ { cluster_summary, user_metadata, entitlement_metadata }
    """
    try:
        # Guess MIME
        name_lower = (file.name or "").lower()
        if name_lower.endswith(".csv"):
            mime = "text/csv"
        elif name_lower.endswith(".json"):
            mime = "application/json"
        else:
            # default
            mime = "application/octet-stream"

        # Streamlit UploadedFile supports .getvalue() and .read()
        content = file.getvalue()  # bytes
        files = {"file": (file.name, content, mime)}
        resp = requests.post(f"{API_BASE_URL}/clusters/upload", params={"file_type": file_type}, files=files, timeout=60)

        if resp.status_code == 200:
            return True, resp.json()
        else:
            # Try to parse detail if present
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            return False, detail
    except Exception as e:
        return False, {"error": str(e)}


# -----------------------
# Sidebar
# -----------------------
with st.sidebar:
    st.title("🔐 RBAC Role Mining")

    # API status
    api_up = check_api()
    if api_up:
        st.success("✅ System Connected")
    else:
        st.error("❌ System Offline")
        st.info("Start the API server:")
        st.code("uvicorn app.main:app --reload --port 8000")

    st.divider()

    # Navigation (added 📤 Upload Data page)
    page = st.radio(
        "Navigation",
        ["📤 Upload Data", "🏠 Dashboard", "🎯 Generate Roles", "🚀 Batch Process", "📋 Review & Export", "ℹ️ About"],
    )

    st.divider()

    # Quick stats
    total_roles = len(st.session_state["generated_roles"])
    approved_count = sum(1 for r in st.session_state["generated_roles"].values() if r.get("approved"))
    st.metric("Total Roles Generated", total_roles)
    st.metric("Approved Roles", approved_count)


# -----------------------
# Page: Upload Data
# -----------------------
if page == "📤 Upload Data":
    st.title("📤 Upload Input Data Files")
    st.markdown(
        """
Upload the three files used by the backend loader.  
**Accepted types**: CSV for `cluster_summary` and `user_metadata`, JSON or CSV for `entitlement_metadata`.

**Endpoint used:** `POST /api/v1/clusters/upload?file_type=...`
"""
    )

    up_col1, up_col2 = st.columns([2, 1])
    with up_col1:
        f_user = st.file_uploader("👤 user_metadata.csv", type=["csv"], key="up_user")
        f_ent = st.file_uploader("🧩 entitlement_metadata (json or csv)", type=["json", "csv"], key="up_ent")
        f_cluster = st.file_uploader("🧮 cluster_summary.csv", type=["csv"], key="up_cluster")

    with up_col2:
        st.info(
            "Tips:\n"
            "- First upload Entitlements (JSON preferred), then Users, then Clusters\n"
            "- After uploads succeed, go to *Generate Roles*"
        )

    st.divider()

    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    with c1:
        if st.button("Upload user_metadata"):
            if not f_user:
                st.error("Please select **user_metadata.csv**.")
            else:
                with st.spinner("Uploading user_metadata..."):
                    ok, res = upload_data_file(f_user, "user_metadata")
                if ok:
                    st.success("✅ user_metadata uploaded")
                else:
                    st.error(f"❌ Upload failed: {res}")
    with c2:
        if st.button("Upload entitlement_metadata"):
            if not f_ent:
                st.error("Please select **entitlement_metadata.(json/csv)**.")
            else:
                with st.spinner("Uploading entitlement_metadata..."):
                    ok, res = upload_data_file(f_ent, "entitlement_metadata")
                if ok:
                    st.success("✅ entitlement_metadata uploaded")
                else:
                    st.error(f"❌ Upload failed: {res}")
    with c3:
        if st.button("Upload cluster_summary"):
            if not f_cluster:
                st.error("Please select **cluster_summary.csv**.")
            else:
                with st.spinner("Uploading cluster_summary..."):
                    ok, res = upload_data_file(f_cluster, "cluster_summary")
                if ok:
                    st.success("✅ cluster_summary uploaded")
                else:
                    st.error(f"❌ Upload failed: {res}")
    with c4:
        if st.button("🔄 Reload Cluster List"):
            # simply trigger a refresh
            st.success("Reloading...")
            st.rerun()

    st.divider()
    st.subheader("Current Clusters (from backend)")
    clusters_preview = get_clusters()
    if clusters_preview:
        df_prev = pd.DataFrame(
            [
                {
                    "Cluster ID": c.get("cluster_id"),
                    "Users": c.get("user_count", 0),
                    "Entitlements": c.get("entitlement_count", 0),
                    "Top Departments": ", ".join(c.get("top_departments", [])[:2]),
                }
                for c in clusters_preview
            ]
        )
        st.dataframe(df_prev, use_container_width=True, hide_index=True)
    else:
        st.info("No clusters found yet. Upload files and reload.")


# -----------------------
# Page: Dashboard
# -----------------------
elif page == "🏠 Dashboard":
    st.title("RBAC Role Mining Dashboard")
    st.markdown("### AI-Powered Role Generation with 3 Naming Approaches")

    clusters = get_clusters()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Clusters", len(clusters))
    with col2:
        st.metric("Roles Generated", len(st.session_state["generated_roles"]))
    with col3:
        pending_count = max(0, len(clusters) - len(st.session_state["generated_roles"]))
        st.metric("Pending Generation", pending_count)
    with col4:
        st.metric("Approved Roles", approved_count)

    st.divider()
    st.subheader("📌 Our 3 Role Naming Approaches")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(
            """
            **🏢 Business-Focused**

            Emphasizes business function and responsibilities

            *Example: Financial Report Analyst*
            """
        )
    with c2:
        st.info(
            """
            **⚙️ Technical-Focused**

            Emphasizes systems and technical access

            *Example: ERP System Read User*
            """
        )
    with c3:
        st.info(
            """
            **📊 Hierarchical-Focused**

            Emphasizes seniority and organizational level

            *Example: Senior Finance Specialist*
            """
        )

    st.divider()
    st.subheader("Cluster Overview")
    if clusters:
        table_data = []
        for c in clusters:
            cid = c.get("cluster_id")
            status = "✅ Generated" if cid in st.session_state["generated_roles"] else "⏳ Pending"
            selected_role = "-"
            if cid in st.session_state["generated_roles"]:
                role_data = st.session_state["generated_roles"][cid]
                selected_opt = role_data.get("selected", role_data.get("recommended_option", 1))
                for opt in role_data.get("role_options", []):
                    if opt.get("option_number") == selected_opt:
                        selected_role = opt.get("role_name", "-")
                        break
            table_data.append(
                {
                    "Cluster ID": cid,
                    "Users": c.get("user_count", 0),
                    "Entitlements": c.get("entitlement_count", 0),
                    "Departments": ", ".join(c.get("top_departments", [])[:2]),
                    "Status": status,
                    "Selected Role": selected_role,
                }
            )
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("No clusters found. Upload data on the **📤 Upload Data** page or check API.")


# -----------------------
# Page: Generate Roles
# -----------------------
elif page == "🎯 Generate Roles":
    st.title("Generate RBAC Roles")
    st.markdown("### Generate 3 role name options using different naming approaches")

    clusters = get_clusters()
    if not clusters:
        st.warning("No clusters available. Upload data first on **📤 Upload Data**.")
        st.stop()

    cluster_ids = [c.get("cluster_id") for c in clusters]
    selected = st.selectbox("Select a Cluster to Process", cluster_ids)

    cluster_info = next((c for c in clusters if c.get("cluster_id") == selected), None)
    if cluster_info:
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Users in Cluster", cluster_info.get("user_count", 0))
        with m2:
            st.metric("Entitlements", cluster_info.get("entitlement_count", 0))
        with m3:
            st.metric("Departments", len(cluster_info.get("top_departments", [])))

        with st.expander("Cluster Details"):
            st.write("**Top Job Titles:**", ", ".join(cluster_info.get("top_job_titles", [])[:10]))
            st.write("**Top Departments:**", ", ".join(cluster_info.get("top_departments", [])[:10]))

    # Generation controls
    col_left, col_right = st.columns([2, 1])
    with col_left:
        if st.button("🎯 Generate 3 Role Options", type="primary", use_container_width=True):
            with st.spinner("AI is generating 3 different role naming options..."):
                result = generate_multiple_roles(selected)
                if result:
                    st.session_state["generated_roles"][selected] = result
                    st.success("✅ Successfully generated 3 role options!")
                    st.balloons()
                else:
                    st.error("Failed to generate roles. Please try again or check API.")
    with col_right:
        if st.button("🔁 Force Regenerate (overwrite)", use_container_width=True):
            with st.spinner("Forcing regeneration..."):
                result = generate_multiple_roles(selected, force=True)
                if result:
                    st.session_state["generated_roles"][selected] = result
                    st.success("✅ Force regenerated roles for cluster.")
                    st.balloons()
                else:
                    st.error("Force regeneration failed.")

    # Display generated roles / entitlements
    if selected in st.session_state["generated_roles"]:
        st.divider()
        role = st.session_state["generated_roles"][selected]
        st.subheader("Generated Role Options")

        # Entitlements expander
        if "entitlements" in role and role["entitlements"]:
            with st.expander(f"📋 View {len(role['entitlements'])} Entitlements for this Role", expanded=False):
                for idx, ent in enumerate(role["entitlements"], 1):
                    if isinstance(ent, dict):
                        col_a, col_b = st.columns([1, 3])
                        with col_a:
                            st.write(f"**{ent.get('id', 'N/A')}**")
                        with col_b:
                            st.write(f"**{ent.get('name', 'N/A')}**")
                            st.caption(ent.get("description", "No description"))
                    else:
                        st.write(f"• {ent}")

        # Recommendation
        recommended = role.get("recommended_option", 1)
        if role.get("recommendation_reason"):
            st.info(f"💡 **AI Recommendation:** Option {recommended} - {role.get('recommendation_reason')}")

        # Tabs for the 3 options
        tabs = st.tabs(["🏢 Business-Focused", "⚙️ Technical-Focused", "📊 Hierarchical-Focused"])
        style_mapping = {"business_focused": 0, "technical_focused": 1, "hierarchical_focused": 2}

        for opt in role.get("role_options", []):
            style = opt.get("style", "business_focused")
            tab_index = style_mapping.get(style, 0)
            with tabs[tab_index]:
                is_recommended = opt.get("option_number") == recommended
                if is_recommended:
                    st.markdown("**⭐ AI RECOMMENDED**")

                st.markdown(f"### {opt.get('role_name', 'N/A')}")
                st.write(f"**Naming Style:** {style.replace('_', ' ').title()}")
                st.write(f"**Description:** {opt.get('description', 'N/A')}")
                st.write(f"**Business Rationale:** {opt.get('rationale', 'N/A')}")

                if st.button("Select This Option", key=f"select_{selected}_{opt.get('option_number')}"):
                    role["selected"] = opt.get("option_number")
                    role["selected_name"] = opt.get("role_name")
                    st.success(f"✅ Selected: {opt.get('role_name')}")
                    st.rerun()

                if role.get("selected") == opt.get("option_number"):
                    st.success("✅ CURRENTLY SELECTED")


# -----------------------
# Page: Batch Process
# -----------------------
elif page == "🚀 Batch Process":
    st.title("Batch Role Generation")
    st.markdown("### Process all clusters at once with 3 naming options each")

    clusters = get_clusters()
    total = len(clusters)
    pending = [c.get("cluster_id") for c in clusters if c.get("cluster_id") not in st.session_state["generated_roles"]]
    already_done = total - len(pending)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Clusters", total)
    with c2:
        st.metric("Already Processed", already_done)
    with c3:
        st.metric("Pending", len(pending))

    if pending:
        st.info(f"Ready to generate roles for {len(pending)} clusters. Each cluster will receive 3 naming options.")
        with st.expander("Clusters to be processed"):
            st.write(", ".join(pending[:200]))  # show up to first 200 for safety

        if st.button("🚀 Start Batch Generation", type="primary", use_container_width=True):
            progress = st.progress(0)
            status = st.empty()

            success = 0
            failed = []

            for i, cid in enumerate(pending):
                status.text(f"Processing {cid}... ({i+1}/{len(pending)})")
                pct = int(((i + 1) / len(pending)) * 100)
                progress.progress(pct)

                result = generate_multiple_roles(cid)
                if result:
                    st.session_state["generated_roles"][cid] = result
                    success += 1
                else:
                    failed.append(cid)

                time.sleep(0.2)

            progress.empty()
            status.empty()

            st.session_state["batch_status"] = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processed": success,
                "failed": len(failed),
                "failed_list": failed[:50],
            }

            if success > 0:
                st.success(f"✅ Successfully generated roles for {success} clusters")
            if failed:
                st.warning(f"⚠️ Failed to process {len(failed)} clusters (showing up to 50): {', '.join(failed[:50])}")

            st.rerun()
    else:
        st.success("✅ All clusters have been processed!")

    if st.session_state["batch_status"]:
        st.divider()
        st.subheader("Last Batch Run")
        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            st.metric("Run Time", st.session_state["batch_status"]["timestamp"])
        with bcol2:
            st.metric("Successful", st.session_state["batch_status"]["processed"])
        with bcol3:
            st.metric("Failed", st.session_state["batch_status"]["failed"])


# -----------------------
# Page: Review & Export
# -----------------------
elif page == "📋 Review & Export":
    st.title("Review & Export Roles")
    st.markdown("### Review generated roles and export for implementation")

    if not st.session_state["generated_roles"]:
        st.info("No roles generated yet. Please generate some roles first.")
        st.stop()

    # Export controls
    st.subheader("Export Options")
    ecol1, ecol2, ecol3, ecol4 = st.columns(4)
    with ecol1:
        export_format = st.selectbox("Format", ["CSV", "JSON", "JSON (Detailed)"])
    with ecol2:
        approved_only = st.checkbox("Approved Only")
    with ecol3:
        selected_only = st.checkbox("Selected Options Only", value=True)
    with ecol4:
        if st.button("📥 Export", type="primary"):
            export_data = []

            for cid, role in st.session_state["generated_roles"].items():
                if approved_only and not role.get("approved"):
                    continue

                # choose what to export for this role
                if selected_only:
                    selected_num = role.get("selected", role.get("recommended_option", 1))
                    for opt in role.get("role_options", []):
                        if opt.get("option_number") == selected_num:
                            export_item = {
                                "cluster_id": cid,
                                "role_name": opt.get("role_name"),
                                "naming_style": opt.get("style", "").replace("_", " ").title(),
                                "description": opt.get("description"),
                                "rationale": opt.get("rationale"),
                                "approved": role.get("approved", False),
                                "user_count": role.get("user_count", 0),
                                "entitlement_count": role.get("entitlement_count", 0),
                                # include entitlements list for context
                                "entitlements": role.get("entitlements", []),
                            }
                            export_data.append(export_item)
                            break
                else:
                    for opt in role.get("role_options", []):
                        export_data.append(
                            {
                                "cluster_id": cid,
                                "option_number": opt.get("option_number"),
                                "role_name": opt.get("role_name"),
                                "naming_style": opt.get("style", "").replace("_", " ").title(),
                                "description": opt.get("description"),
                                "rationale": opt.get("rationale"),
                                "is_selected": opt.get("option_number")
                                == role.get("selected", role.get("recommended_option")),
                                "is_recommended": opt.get("option_number") == role.get("recommended_option"),
                                "approved": role.get("approved", False),
                                "entitlements": role.get("entitlements", []),
                            }
                        )

            if not export_data:
                st.warning("No data matches export criteria")
            else:
                if export_format == "CSV":
                    # For CSV, convert entitlements (list/dict) into JSON string in a column
                    df = pd.json_normalize(export_data)
                    if "entitlements" in df.columns:
                        df["entitlements"] = df["entitlements"].apply(lambda x: json.dumps(x, ensure_ascii=False))
                    csv = df.to_csv(index=False)
                    st.download_button(
                        f"Download CSV ({len(export_data)} items)",
                        csv,
                        f"rbac_roles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv",
                    )
                else:
                    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                    st.download_button(
                        f"Download JSON ({len(export_data)} items)",
                        json_str,
                        f"rbac_roles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json",
                    )
                st.success(f"✅ Prepared {len(export_data)} items for export")

    st.divider()

    # Review filters
    st.subheader("Review Generated Roles")
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        filter_status = st.selectbox("Filter by Status", ["All", "Approved", "Pending"])
    with fcol2:
        filter_style = st.selectbox(
            "Filter by Selected Style", ["All", "Business-Focused", "Technical-Focused", "Hierarchical-Focused"]
        )

    displayed = 0
    for cid, role in st.session_state["generated_roles"].items():
        # apply status filter
        if filter_status == "Approved" and not role.get("approved"):
            continue
        if filter_status == "Pending" and role.get("approved"):
            continue

        # selected option
        selected_opt_num = role.get("selected", role.get("recommended_option", 1))
        selected_opt = None
        for opt in role.get("role_options", []):
            if opt.get("option_number") == selected_opt_num:
                selected_opt = opt
                break

        # apply style filter
        if filter_style != "All" and selected_opt:
            style_map = {
                "Business-Focused": "business_focused",
                "Technical-Focused": "technical_focused",
                "Hierarchical-Focused": "hierarchical_focused",
            }
            if selected_opt.get("style") != style_map.get(filter_style):
                continue

        displayed += 1
        status_emoji = "✅" if role.get("approved") else "⏳"
        exp_label = f"{status_emoji} {cid} - {selected_opt.get('role_name') if selected_opt else 'No selection'}"

        with st.expander(exp_label, expanded=False):
            # Left: selection & details. Right: entitlements
            left, right = st.columns([2, 1])

            with left:
                # selection options
                options_display = []
                for op in role.get("role_options", []):
                    style_label = op.get("style", "").replace("_", " ").title()
                    options_display.append(f"Option {op.get('option_number')}: {style_label} - {op.get('role_name')}")

                # find index for selectbox
                try:
                    current_index = next(
                        i for i, o in enumerate(role.get("role_options", [])) if o.get("option_number") == selected_opt_num
                    )
                except StopIteration:
                    current_index = 0

                new_selection = st.selectbox("Select Option", options_display, index=current_index, key=f"sel_{cid}")
                new_opt_num = int(new_selection.split(":")[0].split()[-1])
                if new_opt_num != selected_opt_num:
                    role["selected"] = new_opt_num
                    st.rerun()

            with left:
                # approve button and status
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if st.button("Approve", key=f"app_{cid}", disabled=bool(role.get("approved", False))):
                        role["approved"] = True
                        st.success("Approved!")
                        st.rerun()
                with col_b:
                    if role.get("approved"):
                        st.success("✅ APPROVED")
                    else:
                        st.info("⏳ PENDING")

            # show selected details
            if selected_opt:
                left.write("---")
                left.write(f"**Selected Role Name:** {selected_opt.get('role_name')}")
                left.write(f"**Naming Style:** {selected_opt.get('style', '').replace('_', ' ').title()}")
                left.write(f"**Description:** {selected_opt.get('description')}")
                left.write(f"**Business Rationale:** {selected_opt.get('rationale')}")

                if selected_opt.get("option_number") == role.get("recommended_option"):
                    left.info("💡 This was the AI recommended option")

            # right column: entitlements (scrollable)
            with right:
                if "entitlements" in role and role["entitlements"]:
                    st.markdown("<div class='ent-box'>", unsafe_allow_html=True)
                    st.subheader("🔑 Entitlements")
                    st.caption(f"This role includes {len(role['entitlements'])} entitlements")

                    for idx, ent in enumerate(role["entitlements"], 1):
                        if isinstance(ent, dict):
                            st.markdown(f"**{ent.get('id', f'ENT-{idx:02d}')}**: {ent.get('name', 'N/A')}")
                            st.caption(ent.get("description", "No description available"))
                        else:
                            st.markdown(f"• {ent}")
                        if idx < len(role["entitlements"]):
                            st.markdown("---")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No entitlements available for this role.")

    if displayed == 0:
        st.warning("No roles match the selected filters")


# -----------------------
# Page: About
# -----------------------
elif page == "ℹ️ About":
    st.title("About RBAC Role Mining System")
    st.markdown(
        """
### 🎯 Purpose
This system uses AI to automatically generate role names from clustered user entitlement data,
providing organizations with a streamlined approach to Role-Based Access Control (RBAC) implementation.

### 🔑 Key Features
- **Three Naming Approaches**: Business-focused, Technical-focused, Hierarchical-focused
- **Review & Export**: See entitlements, select, approve, and export roles
- **Batch Processing**: Generate roles for many clusters at once
- **Upload UI**: Send source files to the backend without leaving the app

### 📊 How It Works
1. Upload cluster data with user-entitlement mappings on **📤 Upload Data**
2. AI analyzes patterns and generates role naming options
3. Choose and approve a role
4. Export selected/approved roles for implementation

### 🔧 Powered By
- Azure OpenAI (or compatible LLM) for role generation (backend)
- Python FastAPI backend
- Streamlit frontend (this app)

**Version:** 1.1.0
"""
    )

# -----------------------
# Footer
# -----------------------
st.divider()
st.caption("RBAC Role Mining System v1.1 | Upload • Generate • Review • Export")
