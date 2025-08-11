# streamlit_dashboard_improved.py
"""
RBAC Role Mining Dashboard - Improved UI
- Removed risk levels from display
- Highlights 3 naming criteria
- Cleaner, more focused interface
"""

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Page config
st.set_page_config(
    page_title="RBAC Role Mining",
    page_icon="🔐",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .naming-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .business-focused {
        background-color: #e8f4f8;
        border-left: 4px solid #1e88e5;
    }
    .technical-focused {
        background-color: #f3e5f5;
        border-left: 4px solid #8e24aa;
    }
    .hierarchical-focused {
        background-color: #e8f5e9;
        border-left: 4px solid #43a047;
    }
    .recommended {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_roles' not in st.session_state:
    st.session_state.generated_roles = {}
if 'batch_status' not in st.session_state:
    st.session_state.batch_status = None

# API Functions
def check_api():
    try:
        response = requests.get(f"{API_BASE_URL}/health/", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_clusters():
    try:
        response = requests.get(f"{API_BASE_URL}/clusters/", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def generate_multiple_roles(cluster_id):
    try:
        response = requests.post(
            f"{API_BASE_URL}/roles/generate-multiple",
            json={"cluster_id": cluster_id},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

# Sidebar
with st.sidebar:
    st.title("🔐 RBAC Role Mining")
    
    # API Status
    if check_api():
        st.success("✅ System Connected")
    else:
        st.error("❌ System Offline")
        st.info("Start the API server:")
        st.code("uvicorn app.main:app --reload")
    
    st.divider()
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "🎯 Generate Roles", "🚀 Batch Process", "📋 Review & Export", "ℹ️ About"]
    )
    
    st.divider()
    
    # Quick Stats
    st.metric("Total Roles Generated", len(st.session_state.generated_roles))
    approved = sum(1 for r in st.session_state.generated_roles.values() if r.get("approved"))
    st.metric("Approved Roles", approved)

# Main Pages
if page == "🏠 Dashboard":
    st.title("RBAC Role Mining Dashboard")
    st.markdown("### AI-Powered Role Generation with 3 Naming Approaches")
    
    clusters = get_clusters()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Clusters", len(clusters))
    with col2:
        st.metric("Roles Generated", len(st.session_state.generated_roles))
    with col3:
        pending = len(clusters) - len(st.session_state.generated_roles)
        st.metric("Pending Generation", max(0, pending))
    with col4:
        st.metric("Approved Roles", approved)
    
    # Information about naming approaches
    st.divider()
    st.subheader("📌 Our 3 Role Naming Approaches")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("""
        **🏢 Business-Focused**
        
        Emphasizes business function and responsibilities
        
        *Example: Financial Report Analyst*
        """)
    
    with col2:
        st.info("""
        **⚙️ Technical-Focused**
        
        Emphasizes systems and technical access
        
        *Example: ERP System Read User*
        """)
    
    with col3:
        st.info("""
        **📊 Hierarchical-Focused**
        
        Emphasizes seniority and organizational level
        
        *Example: Senior Finance Specialist*
        """)
    
    # Cluster Status Table
    st.divider()
    st.subheader("Cluster Overview")
    if clusters:
        data = []
        for c in clusters:
            cid = c.get("cluster_id")
            status = "✅ Generated" if cid in st.session_state.generated_roles else "⏳ Pending"
            selected_role = "-"
            if cid in st.session_state.generated_roles:
                role_data = st.session_state.generated_roles[cid]
                selected_opt = role_data.get("selected", role_data.get("recommended_option", 1))
                for opt in role_data.get("role_options", []):
                    if opt.get("option_number") == selected_opt:
                        selected_role = opt.get("role_name", "-")
                        break
            
            data.append({
                "Cluster ID": cid,
                "Users": c.get("user_count", 0),
                "Entitlements": c.get("entitlement_count", 0),
                "Departments": ", ".join(c.get("top_departments", [])[:2]),
                "Status": status,
                "Selected Role": selected_role
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("No clusters found. Please upload data files.")

elif page == "🎯 Generate Roles":
    st.title("Generate RBAC Roles")
    st.markdown("### Generate 3 role name options using different naming approaches")
    
    clusters = get_clusters()
    if not clusters:
        st.warning("No clusters available. Please upload data first.")
        st.stop()
    
    cluster_ids = [c.get("cluster_id") for c in clusters]
    selected = st.selectbox("Select a Cluster to Process", cluster_ids)
    
    # Show cluster details
    cluster_info = next((c for c in clusters if c.get("cluster_id") == selected), None)
    if cluster_info:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Users in Cluster", cluster_info.get("user_count", 0))
        with col2:
            st.metric("Entitlements", cluster_info.get("entitlement_count", 0))
        with col3:
            st.metric("Departments", len(cluster_info.get("top_departments", [])))
        
        with st.expander("Cluster Details"):
            st.write("**Top Job Titles:**", ", ".join(cluster_info.get("top_job_titles", [])))
            st.write("**Top Departments:**", ", ".join(cluster_info.get("top_departments", [])))
    
    # Generate button
    if st.button("🎯 Generate 3 Role Options", type="primary", use_container_width=True):
        with st.spinner("AI is generating 3 different role naming options..."):
            result = generate_multiple_roles(selected)
            if result:
                st.session_state.generated_roles[selected] = result
                st.success("✅ Successfully generated 3 role options!")
                st.balloons()
            else:
                st.error("Failed to generate roles. Please try again.")
    
    # Display generated roles
    if selected in st.session_state.generated_roles:
        st.divider()
        role = st.session_state.generated_roles[selected]
        
        st.subheader("Generated Role Options")
        
        # Show entitlements if available
        if "entitlements" in role and role["entitlements"]:
            with st.expander(f"📋 View {len(role['entitlements'])} Entitlements for this Role", expanded=False):
                for ent in role["entitlements"]:
                    if isinstance(ent, dict):
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.write(f"**{ent.get('id', 'N/A')}**")
                        with col2:
                            st.write(f"**{ent.get('name', 'N/A')}**")
                            st.caption(ent.get('description', 'No description'))
                    else:
                        st.write(f"• {ent}")
        
        # Show AI recommendation
        recommended = role.get("recommended_option", 1)
        if role.get("recommendation_reason"):
            st.info(f"💡 **AI Recommendation:** Option {recommended} - {role.get('recommendation_reason')}")
        
        # Display 3 options with clear labeling
        tabs = st.tabs(["🏢 Business-Focused", "⚙️ Technical-Focused", "📊 Hierarchical-Focused"])
        
        style_mapping = {
            "business_focused": 0,
            "technical_focused": 1,
            "hierarchical_focused": 2
        }
        
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
                
                if st.button(f"Select This Option", key=f"select_{selected}_{opt.get('option_number')}"):
                    role["selected"] = opt.get("option_number")
                    role["selected_name"] = opt.get("role_name")
                    st.success(f"✅ Selected: {opt.get('role_name')}")
                    st.rerun()
                
                if role.get("selected") == opt.get("option_number"):
                    st.success("✅ CURRENTLY SELECTED")

elif page == "🚀 Batch Process":
    st.title("Batch Role Generation")
    st.markdown("### Process all clusters at once with 3 naming options each")
    
    clusters = get_clusters()
    total = len(clusters)
    pending = [c.get("cluster_id") for c in clusters 
              if c.get("cluster_id") not in st.session_state.generated_roles]
    already_done = total - len(pending)
    
    # Status cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Clusters", total)
    with col2:
        st.metric("Already Processed", already_done)
    with col3:
        st.metric("Pending", len(pending))
    
    if pending:
        st.info(f"Ready to generate roles for {len(pending)} clusters. Each cluster will receive 3 naming options.")
        
        with st.expander("Clusters to be processed"):
            st.write(", ".join(pending))
        
        if st.button("🚀 Start Batch Generation", type="primary", use_container_width=True):
            progress = st.progress(0)
            status = st.empty()
            
            success = 0
            failed = []
            
            for i, cid in enumerate(pending):
                status.text(f"Processing {cid}... ({i+1}/{len(pending)})")
                progress.progress((i + 1) / len(pending))
                
                result = generate_multiple_roles(cid)
                if result:
                    st.session_state.generated_roles[cid] = result
                    success += 1
                else:
                    failed.append(cid)
                
                time.sleep(0.5)  # Avoid overwhelming the API
            
            progress.empty()
            status.empty()
            
            if success > 0:
                st.success(f"✅ Successfully generated roles for {success} clusters!")
                if failed:
                    st.warning(f"Failed to process: {', '.join(failed)}")
            
            st.session_state.batch_status = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processed": success,
                "failed": len(failed)
            }
            st.rerun()
    else:
        st.success("✅ All clusters have been processed!")
    
    # Show last batch status
    if st.session_state.batch_status:
        st.divider()
        st.subheader("Last Batch Run")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Run Time", st.session_state.batch_status['timestamp'])
        with col2:
            st.metric("Successful", st.session_state.batch_status['processed'])
        with col3:
            st.metric("Failed", st.session_state.batch_status.get('failed', 0))

elif page == "📋 Review & Export":
    st.title("Review & Export Roles")
    st.markdown("### Review generated roles and export for implementation")
    
    if not st.session_state.generated_roles:
        st.info("No roles generated yet. Please generate some roles first.")
        st.stop()
    
    # Export section
    st.subheader("Export Options")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        export_format = st.selectbox("Format", ["CSV", "JSON", "JSON (Detailed)"])
    with col2:
        approved_only = st.checkbox("Approved Only")
    with col3:
        selected_only = st.checkbox("Selected Options Only", value=True)
    with col4:
        if st.button("📥 Export", type="primary"):
            export_data = []
            
            for cid, role in st.session_state.generated_roles.items():
                if approved_only and not role.get("approved"):
                    continue
                
                if selected_only:
                    # Export only selected option
                    selected = role.get("selected", role.get("recommended_option", 1))
                    for opt in role.get("role_options", []):
                        if opt.get("option_number") == selected:
                            export_data.append({
                                "cluster_id": cid,
                                "role_name": opt.get("role_name"),
                                "naming_style": opt.get("style", "").replace("_", " ").title(),
                                "description": opt.get("description"),
                                "rationale": opt.get("rationale"),
                                "approved": role.get("approved", False),
                                "user_count": role.get("user_count", 0),
                                "entitlement_count": role.get("entitlement_count", 0)
                            })
                            break
                else:
                    # Export all options
                    for opt in role.get("role_options", []):
                        export_data.append({
                            "cluster_id": cid,
                            "option_number": opt.get("option_number"),
                            "role_name": opt.get("role_name"),
                            "naming_style": opt.get("style", "").replace("_", " ").title(),
                            "description": opt.get("description"),
                            "rationale": opt.get("rationale"),
                            "is_selected": opt.get("option_number") == role.get("selected", role.get("recommended_option")),
                            "is_recommended": opt.get("option_number") == role.get("recommended_option"),
                            "approved": role.get("approved", False)
                        })
            
            if export_data:
                if export_format == "CSV":
                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        f"Download CSV ({len(export_data)} items)",
                        csv,
                        f"rbac_roles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                else:
                    json_str = json.dumps(export_data, indent=2)
                    st.download_button(
                        f"Download JSON ({len(export_data)} items)",
                        json_str,
                        f"rbac_roles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json"
                    )
                st.success(f"✅ Prepared {len(export_data)} items for export")
            else:
                st.warning("No data matches export criteria")
    
    st.divider()
    
    # Review section
    st.subheader("Review Generated Roles")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.selectbox("Filter by Status", ["All", "Approved", "Pending"])
    with col2:
        filter_style = st.selectbox("Filter by Selected Style", 
                                   ["All", "Business-Focused", "Technical-Focused", "Hierarchical-Focused"])
    
    # Display roles
    displayed = 0
    for cid, role in st.session_state.generated_roles.items():
        # Apply filters
        if filter_status == "Approved" and not role.get("approved"):
            continue
        if filter_status == "Pending" and role.get("approved"):
            continue
        
        # Get selected option details
        selected_opt_num = role.get("selected", role.get("recommended_option", 1))
        selected_opt = None
        for opt in role.get("role_options", []):
            if opt.get("option_number") == selected_opt_num:
                selected_opt = opt
                break
        
        if filter_style != "All" and selected_opt:
            style_map = {
                "Business-Focused": "business_focused",
                "Technical-Focused": "technical_focused",
                "Hierarchical-Focused": "hierarchical_focused"
            }
            if selected_opt.get("style") != style_map.get(filter_style):
                continue
        
        displayed += 1
        
        # Display role
        status_emoji = "✅" if role.get("approved") else "⏳"
        with st.expander(f"{status_emoji} {cid} - {selected_opt.get('role_name') if selected_opt else 'No selection'}"):
            
            # Selection and approval controls
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                options = []
                for opt in role.get("role_options", []):
                    style_label = opt.get("style", "").replace("_", " ").title()
                    options.append(f"Option {opt.get('option_number')}: {style_label}")
                
                current_selection = selected_opt_num - 1 if selected_opt_num else 0
                new_selection = st.selectbox(
                    "Select Option",
                    options,
                    index=current_selection,
                    key=f"sel_{cid}"
                )
                new_opt_num = int(new_selection.split(":")[0].split()[-1])
                if new_opt_num != selected_opt_num:
                    role["selected"] = new_opt_num
                    st.rerun()
            
            with col2:
                if st.button("Approve", key=f"app_{cid}", disabled=bool(role.get("approved", False))):
                    role["approved"] = True
                    st.success("Approved!")
                    st.rerun()
            
            with col3:
                if role.get("approved"):
                    st.success("✅ APPROVED")
                else:
                    st.info("⏳ PENDING")
            
            # Show details of selected option
            if selected_opt:
                st.divider()
                st.write(f"**Selected Role Name:** {selected_opt.get('role_name')}")
                st.write(f"**Naming Style:** {selected_opt.get('style', '').replace('_', ' ').title()}")
                st.write(f"**Description:** {selected_opt.get('description')}")
                st.write(f"**Business Rationale:** {selected_opt.get('rationale')}")
                
                if selected_opt.get("option_number") == role.get("recommended_option"):
                    st.info("💡 This was the AI recommended option")
    
    if displayed == 0:
        st.warning("No roles match the selected filters")

elif page == "ℹ️ About":
    st.title("About RBAC Role Mining System")
    
    st.markdown("""
    ### 🎯 Purpose
    This system uses AI to automatically generate role names from clustered user entitlement data, 
    providing organizations with a streamlined approach to Role-Based Access Control (RBAC) implementation.
    
    ### 🔑 Key Features
    
    #### **Three Naming Approaches**
    Our AI generates three different role name options for each cluster, catering to different organizational preferences:
    
    1. **🏢 Business-Focused Naming**
       - Emphasizes what the person does in the organization
       - Uses business terminology that's familiar to management
       - Example: "Healthcare Claims Processor", "Financial Report Analyst"
    
    2. **⚙️ Technical-Focused Naming**
       - Emphasizes the systems and technical access
       - Clear for IT teams and system administrators
       - Example: "ERP System Read User", "Database Query Analyst"
    
    3. **📊 Hierarchical-Focused Naming**
       - Emphasizes organizational level and seniority
       - Useful for organizations with clear hierarchical structures
       - Example: "Senior Finance Specialist", "Lead Data Administrator"
    
    ### 💡 Why Three Options?
    
    - **Flexibility**: Different stakeholders prefer different naming conventions
    - **Context**: Each style emphasizes different aspects of the role
    - **Adoption**: Increases acceptance by providing choices
    - **Best Practices**: AI recommends the most suitable option based on the data
    
    ### 📊 How It Works
    
    1. **Data Input**: Upload cluster data with user-entitlement mappings
    2. **AI Analysis**: Azure OpenAI analyzes patterns and user profiles
    3. **Role Generation**: Creates 3 professionally named options
    4. **Review & Select**: Choose the most appropriate option
    5. **Export**: Download approved roles for IAM implementation
    
    ### 🚀 Benefits
    
    - **Time Savings**: Reduces role definition time by 80%
    - **Consistency**: Ensures uniform naming conventions
    - **Compliance**: Follows least privilege principles
    - **Scalability**: Process hundreds of clusters in minutes
    
    ### 🔧 Powered By
    - **Azure OpenAI GPT-4**: Advanced language model for intelligent role generation
    - **Python FastAPI**: High-performance backend
    - **Streamlit**: Interactive user interface
    
    ---
    
    **Version:** 1.0.0  
    **Support:** Contact your IT administrator
    """)

# Footer
st.divider()
st.caption("RBAC Role Mining System v1.0 | Powered by Azure OpenAI GPT-4o | Three Naming Approaches for Maximum Flexibility")