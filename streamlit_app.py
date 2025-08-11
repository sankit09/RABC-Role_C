# streamlit_dashboard.py
"""
RBAC Role Mining Dashboard - Final Clean Version
- Fixed nested expander issue
- Proper batch generation display
- Clean export functionality
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
    st.title("🔐 RBAC System")
    
    if check_api():
        st.success("✅ API Connected")
    else:
        st.error("❌ API Offline")
    
    st.divider()
    page = st.radio("Menu", ["📊 Dashboard", "🎯 Generate", "🚀 Batch", "📋 Review"])
    
    st.divider()
    st.metric("Total Roles", len(st.session_state.generated_roles))

# Main Pages
if page == "📊 Dashboard":
    st.title("RBAC Role Mining Dashboard")
    
    clusters = get_clusters()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Clusters", len(clusters))
    with col2:
        st.metric("Generated", len(st.session_state.generated_roles))
    with col3:
        pending = len(clusters) - len(st.session_state.generated_roles)
        st.metric("Pending", max(0, pending))
    with col4:
        approved = sum(1 for r in st.session_state.generated_roles.values() if r.get("approved"))
        st.metric("Approved", approved)
    
    # Cluster Status
    st.subheader("Cluster Status")
    if clusters:
        data = []
        for c in clusters:
            cid = c.get("cluster_id")
            status = "✅ Generated" if cid in st.session_state.generated_roles else "⏳ Pending"
            risk = st.session_state.generated_roles.get(cid, {}).get("risk_level", "-")
            data.append({
                "Cluster": cid,
                "Users": c.get("user_count", 0),
                "Entitlements": c.get("entitlement_count", 0),
                "Status": status,
                "Risk": risk
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "🎯 Generate":
    st.title("Generate Single Role")
    
    clusters = get_clusters()
    if not clusters:
        st.warning("No clusters available")
        st.stop()
    
    cluster_ids = [c.get("cluster_id") for c in clusters]
    selected = st.selectbox("Select Cluster", cluster_ids)
    
    if st.button("Generate 3 Options", type="primary"):
        with st.spinner("Generating..."):
            result = generate_multiple_roles(selected)
            if result:
                st.session_state.generated_roles[selected] = result
                st.success("✅ Generated successfully!")
                st.balloons()
    
    # Display if exists
    if selected in st.session_state.generated_roles:
        role = st.session_state.generated_roles[selected]
        
        st.divider()
        st.write(f"**Risk:** {role.get('risk_level')}")
        st.write(f"**Recommended:** Option {role.get('recommended_option')}")
        
        # Show options
        for opt in role.get("role_options", []):
            num = opt.get("option_number")
            name = opt.get("role_name")
            style = opt.get("style", "").replace("_", " ").title()
            
            if num == role.get("recommended_option"):
                st.success(f"⭐ Option {num}: **{name}** ({style})")
            else:
                st.info(f"Option {num}: **{name}** ({style})")

elif page == "🚀 Batch":
    st.title("Batch Generate All Roles")
    
    clusters = get_clusters()
    total = len(clusters)
    pending = [c.get("cluster_id") for c in clusters 
              if c.get("cluster_id") not in st.session_state.generated_roles]
    
    st.info(f"**Total:** {total} clusters | **Pending:** {len(pending)} clusters")
    
    if st.button("🚀 Generate All", type="primary", disabled=len(pending)==0):
        progress = st.progress(0)
        status = st.empty()
        
        success = 0
        for i, cid in enumerate(pending):
            status.text(f"Processing {cid}...")
            progress.progress((i + 1) / len(pending))
            
            result = generate_multiple_roles(cid)
            if result:
                st.session_state.generated_roles[cid] = result
                success += 1
            time.sleep(0.5)  # Small delay to avoid overwhelming API
        
        progress.empty()
        status.empty()
        
        st.success(f"✅ Generated {success}/{len(pending)} roles!")
        st.session_state.batch_status = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "processed": success
        }
        st.rerun()
    
    # Show last batch status
    if st.session_state.batch_status:
        st.divider()
        st.write(f"Last batch: {st.session_state.batch_status['timestamp']} - "
                f"Processed {st.session_state.batch_status['processed']} clusters")

elif page == "📋 Review":
    st.title("Review & Export")
    
    if not st.session_state.generated_roles:
        st.info("No roles generated yet")
        st.stop()
    
    # Export section first
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        export_type = st.selectbox("Export Format", ["CSV", "JSON"])
    with col2:
        approved_only = st.checkbox("Approved Only")
    with col3:
        if st.button("📥 Export", type="primary"):
            export_data = []
            
            for cid, role in st.session_state.generated_roles.items():
                if approved_only and not role.get("approved"):
                    continue
                
                # Get selected or recommended option
                selected = role.get("selected", role.get("recommended_option", 1))
                for opt in role.get("role_options", []):
                    if opt.get("option_number") == selected:
                        export_data.append({
                            "cluster_id": cid,
                            "role_name": opt.get("role_name"),
                            "description": opt.get("description"),
                            "risk_level": role.get("risk_level"),
                            "approved": role.get("approved", False)
                        })
                        break
            
            if export_data:
                if export_type == "CSV":
                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"roles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                else:
                    json_str = json.dumps(export_data, indent=2)
                    st.download_button(
                        "Download JSON",
                        json_str,
                        f"roles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json"
                    )
    
    st.divider()
    
    # Display roles
    for cid, role in st.session_state.generated_roles.items():
        with st.expander(f"{cid} - {role.get('risk_level')} Risk"):
            # Options
            options = [f"Option {i+1}" for i in range(len(role.get("role_options", [])))]
            selected_idx = (role.get("selected", role.get("recommended_option", 1)) - 1)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                new_selection = st.selectbox(
                    "Select Option",
                    options,
                    index=selected_idx,
                    key=f"sel_{cid}"
                )
                role["selected"] = int(new_selection.split()[-1])
            
            with col2:
                if st.button("Approve", key=f"app_{cid}"):
                    role["approved"] = True
                    st.success("Approved!")
                    st.rerun()
            
            # Show selected option details
            for opt in role.get("role_options", []):
                if opt.get("option_number") == role["selected"]:
                    st.write(f"**Name:** {opt.get('role_name')}")
                    st.write(f"**Description:** {opt.get('description')}")
                    st.write(f"**Rationale:** {opt.get('rationale')}")
                    break
            
            if role.get("approved"):
                st.success("✅ APPROVED")

st.divider()
st.caption("RBAC Role Mining v1.0 | Azure OpenAI GPT-4o")