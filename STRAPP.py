import streamlit as st
import pandas as pd
import io
from datetime import datetime

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Genome Risk Analyzer",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== CUSTOM CSS ======================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3B82F6;
        margin-top: 1.5rem;
    }
    .high-risk { color: #EF4444; font-weight: bold; }
    .moderate-risk { color: #F59E0B; font-weight: bold; }
    .low-risk { color: #10B981; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ====================== TITLE ======================
st.markdown('<h1 class="main-header">🧬 Genome Risk Analyzer</h1>', unsafe_allow_html=True)
st.markdown("**Professional Risk Classification Dashboard** | Gene & Trait Level Analysis")

# ====================== SIDEBAR ======================
st.sidebar.header("📤 Data Upload")
uploaded_file = st.sidebar.file_uploader(
    "Upload your Genome Risk Excel file",
    type=["xlsx", "xls"],
    help="File must contain columns: 'Gene Name', 'genotype', 'Traits'"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Analysis Parameters")
high_gene_threshold = st.sidebar.slider("High Risk Gene Threshold (%)", 30, 70, 50, key="gene_th")
moderate_trait_threshold = st.sidebar.slider("Moderate Risk Trait Threshold (%)", 30, 70, 50, key="mod_th")
high_trait_threshold = st.sidebar.slider("High Risk Trait Threshold (%)", 60, 90, 75, key="high_th")

# ====================== MAIN APP ======================
if uploaded_file is None:
    st.info("👆 Please upload your Excel file in the sidebar to begin analysis.")
    st.stop()

# --------------------- LOAD DATA ---------------------
@st.cache_data
def load_data(file):
    try:
        # Try default engine first (usually works)
        df = pd.read_excel(file)
        st.success("✅ Excel file loaded successfully!")
        return df
    except Exception as e:
        try:
            # Fallback with openpyxl
            df = pd.read_excel(file, engine='openpyxl')
            st.success("✅ Excel file loaded using openpyxl!")
            return df
        except Exception as e2:
            st.error("❌ Failed to load Excel file")
            st.error(f"Error: {str(e)}")
            st.info("""
            **Tips:**
            - Make sure the file is a valid `.xlsx` file (not `.csv`)
            - Try saving the file again as Excel Workbook (*.xlsx)
            - Check if the file is corrupted
            """)
            st.stop()

df = load_data(uploaded_file)

# --------------------- CORE FUNCTIONS ---------------------
def classify_gene(genotypes, high_threshold=0.50):
    total = len(genotypes)
    high = (genotypes == 46023).sum()
    moderate = (genotypes == "0/1").sum()
    high_pct = high / total
    risk_pct = (high + moderate) / total
    
    if high_pct >= high_threshold:
        return "High Risk"
    elif risk_pct >= 0.50:
        return "Moderate Risk"
    else:
        return "Low Risk"

def classify_group(subdf, high_t=0.75, risk_t=0.50):
    total = len(subdf)
    high = (subdf["Status"] == "High Risk").sum()
    moderate = (subdf["Status"] == "Moderate Risk").sum()
    high_pct = high / total
    risk_pct = (high + moderate) / total
    
    if high_pct >= high_t:
        return "High Risk"
    elif risk_pct >= risk_t:
        return "Moderate Risk"
    else:
        return "Low Risk"

# --------------------- PROCESSING ---------------------
with st.spinner("🔬 Analyzing genome data..."):
    # Step 1: Gene Level
    gene_status = (
        df.groupby("Gene Name")["genotype"]
        .apply(lambda x: classify_gene(x, high_gene_threshold/100))
        .reset_index(name="Status")
    )
    
    df = df.merge(gene_status, on="Gene Name", how="left")
    
    # Step 2: Trait Level
    trait_status = (
        df.groupby("Traits")
        .apply(lambda x: classify_group(x, high_trait_threshold/100, moderate_trait_threshold/100))
        .reset_index(name="Overall_Status")
    )
    
    df = df.merge(trait_status, on="Traits", how="left")

# ====================== DASHBOARD ======================
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Genes", len(df["Gene Name"].unique()))
with col2:
    st.metric("Total Traits", len(df["Traits"].unique()))
with col3:
    st.metric("Total Variants", len(df))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Gene Risk Overview", "📋 Trait Risk Overview", "🔍 Raw Data"])

with tab1:
    st.subheader("Gene-Level Risk Classification")
    gene_summary = gene_status["Status"].value_counts().reset_index()
    gene_summary.columns = ["Risk Level", "Count"]
    gene_summary["Percentage"] = (gene_summary["Count"] / gene_summary["Count"].sum() * 100).round(1)
    st.dataframe(gene_summary, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Trait-Level Overall Risk")
    trait_display = trait_status.merge(
        df.groupby("Traits").size().reset_index(name="Variant Count"), 
        on="Traits"
    )
    st.dataframe(trait_display, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Processed Data Preview")
    st.dataframe(
        df[["Gene Name", "genotype", "Status", "Traits", "Overall_Status"]].head(100), 
        use_container_width=True
    )

# --------------------- DOWNLOADS ---------------------
st.markdown("### 📥 Download Results")
col_dl1, col_dl2 = st.columns(2)

full_output = io.BytesIO()
df.to_excel(full_output, index=False)
full_output.seek(0)

trait_output = io.BytesIO()
trait_status.to_excel(trait_output, index=False)
trait_output.seek(0)

with col_dl1:
    st.download_button(
        label="📊 Download Full Processed Data",
        data=full_output,
        file_name=f"risk_filled_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_dl2:
    st.download_button(
        label="📋 Download Trait Summary Only",
        data=trait_output,
        file_name=f"TRAIT_RISK_SUMMARY_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

st.caption("Genome Risk Analyzer • Built with Streamlit")
