
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Genetic Risk Classifier", layout="wide")

st.title("🧬 Genetic Risk Classification System")
st.markdown("Upload an Excel genotype file to classify gene-level and trait-level risk.")

# --------------------------------------------------
# Risk Classification Functions
# --------------------------------------------------

def normalize_genotype(gt):
    """Fix Excel genotype corruption issues"""

    if pd.isna(gt):
        return gt

    # Convert Excel serial dates back to genotype
    if gt == 46023 or gt == 46023.0:
        return "1/1"

    gt = str(gt).strip()

    return gt


# --------------------------------------------------
# Gene-level classification
# --------------------------------------------------

def classify_gene(genotypes):

    total = len(genotypes)

    high = (genotypes == "1/1").sum()
    moderate = (genotypes == "0/1").sum()
    low = (genotypes == "0/0").sum()

    high_pct = high / total
    risk_pct = (high + moderate) / total

    # High Risk
    if high_pct >= 0.50:
        return "High Risk"

    # Moderate Risk
    elif risk_pct >= 0.50:
        return "Moderate Risk"

    # Low Risk
    else:
        return "Low Risk"


# --------------------------------------------------
# Trait-level classification
# --------------------------------------------------

def classify_group(subdf):

    total = len(subdf)

    high = (subdf["Status"] == "High Risk").sum()
    moderate = (subdf["Status"] == "Moderate Risk").sum()
    low = (subdf["Status"] == "Low Risk").sum()

    high_pct = high / total
    risk_pct = (high + moderate) / total

    # High Risk
    if high_pct >= 0.75:
        return "High Risk"

    # Moderate Risk
    elif risk_pct >= 0.50:
        return "Moderate Risk"

    # Low Risk
    else:
        return "Low Risk"


# --------------------------------------------------
# File Upload
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

if uploaded_file is not None:

    try:
        # Read Excel
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        st.success("✅ File loaded successfully")

        st.subheader("Preview of Uploaded Data")
        st.dataframe(df.head())

        # --------------------------------------------------
        # Normalize genotype column
        # --------------------------------------------------

        df["genotype"] = df["genotype"].apply(normalize_genotype)

        st.subheader("Unique Genotypes Detected")
        st.write(df["genotype"].unique())

        # --------------------------------------------------
        # Gene-level classification
        # --------------------------------------------------

        gene_status = (
            df.groupby("Gene Name")["genotype"]
            .apply(classify_gene)
            .reset_index(name="Status")
        )

        # Merge back
        df = df.merge(gene_status, on="Gene Name", how="left")

        st.subheader("Gene-Level Risk Classification")
        st.dataframe(gene_status.head(20))

        # --------------------------------------------------
        # Trait-level classification
        # --------------------------------------------------

        trait_status = (
            df.groupby("Traits")
            .apply(classify_group)
            .reset_index(name="Overall_Status")
        )

        # Merge back
        df = df.merge(trait_status, on="Traits", how="left")

        st.subheader("Trait-Level Risk Classification")
        st.dataframe(trait_status.head(20))

        # --------------------------------------------------
        # Summary Metrics
        # --------------------------------------------------

        st.subheader("📊 Summary Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Variants", len(df))

        with col2:
            st.metric("Total Genes", df["Gene Name"].nunique())

        with col3:
            st.metric("Total Traits", df["Traits"].nunique())

        # --------------------------------------------------
        # Download Outputs (2 Excel Files)
        # --------------------------------------------------

        output_excel = "risk_filled_output.xlsx"
        trait_excel = "trait_summary_output.xlsx"

        df.to_excel(output_excel, index=False)
        trait_status.to_excel(trait_excel, index=False)

        with open(output_excel, "rb") as f:
            st.download_button(
                label="⬇ Download Full Risk Report",
                data=f,
                file_name=output_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with open(trait_excel, "rb") as f:
            st.download_button(
                label="⬇ Download Trait Summary",
                data=f,
                file_name=trait_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.success("✅ Risk classification completed successfully")

    except Exception as e:
        st.error(f"❌ Error: {e}")

