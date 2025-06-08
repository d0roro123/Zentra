import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
import time
import requests
import json

# Set Streamlit page configuration
st.set_page_config(
    page_title="Interactive Media Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling (mimicking some Tailwind aspects)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #333; /* Default text color for the entire app */
    }
    .stApp {
        background-color: #f3f4f6; /* Light gray background for the main app */
    }
    /* Ensure the main content block and sidebar background are white and text is dark */
    .main .block-container, .st-emotion-cache-1d391kg, .st-emotion-cache-1dp5dkx {
        background-color: #ffffff !important;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        padding: 24px;
        margin-bottom: 24px;
        color: #333 !important; /* Ensure text inside these blocks is dark */
    }
    /* Specific overrides for common Streamlit text elements */
    .stMarkdown, .stText, .stAlert p, .stAlert div, .stInfo, .stSuccess, .stWarning, .stError, .stSpinner span {
        color: #333 !important;
    }
    /* Specific overrides for alert backgrounds and text colors */
    .stAlert.st-emotion-cache-1f81d1e.e1p86y231 { /* General alert styling */
        border-radius: 10px;
    }
    .stAlert.st-emotion-cache-1f81d1e.e1p86y231[kind="info"] {
        background-color: #e0f2f7 !important; /* light blue for info */
        color: #0c4a6e !important; /* dark blue for info text */
    }
    .stAlert.st-emotion-cache-1f81d1e.e1p86y231[kind="success"] {
        background-color: #d1fae5 !important; /* light green for success */
        color: #065f46 !important; /* dark green for success text */
    }
    .stAlert.st-emotion-cache-1f81d1e.e1p86y231[kind="warning"] {
        background-color: #fef3c7 !important; /* light yellow for warning */
        color: #92400e !important; /* dark yellow for warning text */
    }
    .stAlert.st-emotion-cache-1f81d1e.e1p86y231[kind="error"] {
        background-color: #fee2e2 !important; /* light red for error */
        color: #991b1b !important; /* dark red for error text */
    }

    h1 {
        font-size: 2.25rem; /* text-4xl */
        font-weight: 700; /* font-bold */
        text-align: center;
        color: #1a202c; /* gray-800 */
        margin-bottom: 2rem; /* mb-8 */
    }
    h2 {
        font-size: 1.5rem; /* text-2xl */
        font-weight: 600; /* font-semibold */
        color: #2d3748; /* gray-700 */
        margin-bottom: 1rem; /* mb-4 */
    }
    h3 {
        font-size: 1.25rem; /* text-xl */
        font-weight: 500; /* font-medium */
        color: #2d3748; /* gray-700 */
        margin-bottom: 0.75rem; /* mb-3 */
    }
    .stButton > button {
        background-image: linear-gradient(to right, #6EE7B7 0%, #34D399 51%, #10B981 100%);
        margin: 10px;
        padding: 12px 24px;
        text-align: center;
        text-transform: uppercase;
        transition: 0.5s;
        background-size: 200% auto;
        color: white;
        box-shadow: 0 0 20px #eee;
        border-radius: 10px;
        border: none;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-position: right center;
        color: #fff;
        text-decoration: none;
    }
    /* Style for the secondary button (Reset Filters and Download PDF) */
    .stButton[data-testid="stSidebar"] > button[kind="secondary"],
    .stButton > button[kind="secondary"] {
        background-image: none !important; /* Remove gradient */
        background-color: #6b7280 !important; /* Tailwind gray-500 */
        color: white !important; /* White text for secondary button */
        box-shadow: 0 0 20px #ccc !important;
    }
    .stButton[data-testid="stSidebar"] > button[kind="secondary"]:hover,
    .stButton > button[kind="secondary"]:hover {
        background-color: #4b5563 !important; /* Tailwind gray-600 on hover */
        color: white !important;
    }
    .stPlotlyChart {
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'all_data' not in st.session_state:
    st.session_state.all_data = pd.DataFrame()
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = pd.DataFrame()
if 'data_cleaned_success' not in st.session_state:
    st.session_state.data_cleaned_success = False
if 'analysis_output' not in st.session_state:
    st.session_state.analysis_output = '<p class="text-gray-500">Click a button above to generate the analysis.</p>'


st.title("Interactive Media Intelligence Dashboard")

# --- 1. Upload CSV File ---
st.header("1. Upload CSV File")
st.markdown("Please upload a CSV file with the following columns: `Date`, `Platform`, `Sentiment`, `Location`, `Engagements`, `Media Type`, `Influencer Brand`, `Post Type`.")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

@st.cache_data(show_spinner=False)
def clean_data(df):
    """
    Cleans the raw data from CSV parsing.
    - Converts 'Date' to datetime objects.
    - Fills missing 'Engagements' with 0.
    - Normalizes column names (handles minor variations).
    """
    if df.empty:
        return pd.DataFrame()

    # Normalize column names
    col_map = {
        'date': 'Date', 'platform': 'Platform', 'sentiment': 'Sentiment',
        'location': 'Location', 'engagements': 'Engagements',
        'mediatype': 'Media Type', 'influencerbrand': 'Influencer Brand',
        'posttype': 'Post Type'
    }
    df.columns = [col_map.get(c.lower().replace(' ', ''), c) for c in df.columns]

    # Ensure required columns exist, fill with 'Unknown' if missing
    required_cols = ['Date', 'Platform', 'Sentiment', 'Location', 'Engagements', 'Media Type', 'Influencer Brand', 'Post Type']
    for col in required_cols:
        if col not in df.columns:
            df[col] = 'Unknown'

    # Convert 'Date' to datetime, coercing errors to NaT
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Drop rows where 'Date' could not be parsed
    df.dropna(subset=['Date'], inplace=True)

    # Convert 'Engagements' to numeric, filling NaNs with 0
    df['Engagements'] = pd.to_numeric(df['Engagements'], errors='coerce').fillna(0)

    return df

if uploaded_file is not None:
    with st.spinner("Processing data..."):
        try:
            raw_data = pd.read_csv(uploaded_file)
            st.session_state.all_data = clean_data(raw_data.copy())
            st.session_state.filtered_data = st.session_state.all_data.copy()
            st.session_state.data_cleaned_success = True

            if st.session_state.all_data.empty:
                st.error("No valid data found in the CSV after cleaning. Please check the file format and content.")
                st.session_state.data_cleaned_success = False
            else:
                st.success("Data Cleaned Successfully!")
                st.session_state.data_cleaned_success = True

        except Exception as e:
            st.error(f"Error reading or cleaning file: {e}")
            st.session_state.data_cleaned_success = False
            st.session_state.all_data = pd.DataFrame() # Reset dataframes on error
            st.session_state.filtered_data = pd.DataFrame()

# Only show dashboard content if data is available
if not st.session_state.all_data.empty:
    st.markdown("---") # Separator

    # --- 2. Cleaned Data Preview ---
    st.header("2. Cleaned Data Preview")
    st.markdown("A preview of the first few rows of the cleaned data:")
    st.dataframe(st.session_state.filtered_data.head())

    st.markdown("---") # Separator

    # --- 3. Filter Data (Sidebar) ---
    st.header("Filter Data")
    st.sidebar.header("Filter Data")

    # Get unique values for filters from all_data, not filtered_data
    platforms = ['All Platforms'] + sorted(st.session_state.all_data['Platform'].unique().tolist())
    sentiments = ['All Sentiments'] + sorted(st.session_state.all_data['Sentiment'].unique().tolist())
    media_types = ['All Media Types'] + sorted(st.session_state.all_data['Media Type'].unique().tolist())
    locations = ['All Locations'] + sorted(st.session_state.all_data['Location'].unique().tolist())

    col1, col2 = st.columns(2)
    with col1:
        selected_platform = st.sidebar.selectbox("Platform:", platforms)
        selected_sentiment = st.sidebar.selectbox("Sentiment:", sentiments)
        selected_media_type = st.sidebar.selectbox("Media Type:", media_types)
    with col2:
        selected_location = st.sidebar.selectbox("Location:", locations)

    # Date filters
    min_date_data = st.session_state.all_data['Date'].min()
    max_date_data = st.session_state.all_data['Date'].max()

    default_start_date = min_date_data.date() if pd.notna(min_date_data) else datetime.today().date()
    default_end_date = max_date_data.date() if pd.notna(max_date_data) else datetime.today().date()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Date Range")
    filter_start_date = st.sidebar.date_input("Start Date:", value=default_start_date)
    filter_end_date = st.sidebar.date_input("End Date:", value=default_end_date)


    # Engagement filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("Engagements Range")
    max_engagements_data = int(st.session_state.all_data['Engagements'].max()) if not st.session_state.all_data.empty else 10000
    filter_min_engagements = st.sidebar.number_input("Min Engagements:", min_value=0, value=0)
    filter_max_engagements = st.sidebar.number_input("Max Engagements:", min_value=0, value=max_engagements_data)

    # Apply Filters button
    if st.sidebar.button("Apply Filters"):
        st.session_state.filtered_data = st.session_state.all_data.copy()

        active_filters_display = []

        if selected_platform != 'All Platforms':
            st.session_state.filtered_data = st.session_state.filtered_data[st.session_state.filtered_data['Platform'] == selected_platform]
            active_filters_display.append(f"Platform: **{selected_platform}**")
        if selected_sentiment != 'All Sentiments':
            st.session_state.filtered_data = st.session_state.filtered_data[st.session_state.filtered_data['Sentiment'] == selected_sentiment]
            active_filters_display.append(f"Sentiment: **{selected_sentiment}**")
        if selected_media_type != 'All Media Types':
            st.session_state.filtered_data = st.session_state.filtered_data[st.session_state.filtered_data['Media Type'] == selected_media_type]
            active_filters_display.append(f"Media Type: **{selected_media_type}**")
        if selected_location != 'All Locations':
            st.session_state.filtered_data = st.session_state.filtered_data[st.session_state.filtered_data['Location'] == selected_location]
            active_filters_display.append(f"Location: **{selected_location}**")

        # Apply date filters
        st.session_state.filtered_data = st.session_state.filtered_data[st.session_state.filtered_data['Date'].dt.date >= filter_start_date]
        st.session_state.filtered_data = st.session_state.filtered_data[st.session_state.filtered_data['Date'].dt.date <= filter_end_date]
        active_filters_display.append(f"Date Range: **{filter_start_date}** to **{filter_end_date}**")

        # Apply engagement filters
        st.session_state.filtered_data = st.session_state.filtered_data[st.session_state.filtered_data['Engagements'] >= filter_min_engagements]
        st.session_state.filtered_data = st.session_state.filtered_data[st.session_state.filtered_data['Engagements'] <= filter_max_engagements]
        active_filters_display.append(f"Engagements: **{filter_min_engagements:,}** to **{filter_max_engagements:,}**")

        if not st.session_state.filtered_data.empty:
            st.info("Filters applied successfully!")
            st.markdown(f"**Active Filters:** {', '.join(active_filters_display)}")
        else:
            st.warning("No data found matching the current filters. Try resetting filters or adjusting criteria.")
            st.session_state.filtered_data = pd.DataFrame() # Ensure filtered_data is empty if no match

    # Reset Filters button
    if st.sidebar.button("Reset Filters", type="secondary"):
        st.session_state.filtered_data = st.session_state.all_data.copy()
        st.sidebar.success("Filters reset!")
        st.info("No filters applied.")
        # Reset sidebar widgets visually (Streamlit handles this implicitly on re-run)
        st.rerun() # Rerun to clear filter selections

    st.markdown("---") # Separator

    # --- 4. Interactive Charts ---
    st.header("3. Interactive Charts")

    if st.session_state.filtered_data.empty:
        st.warning("No data to display charts. Please upload data or adjust filters.")
    else:
        # --- Sentiment Breakdown (Pie Chart) ---
        st.subheader("Sentiment Breakdown")
        sentiment_counts = st.session_state.filtered_data['Sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Count']
        fig_sentiment = px.pie(sentiment_counts, values='Count', names='Sentiment',
                               title='Sentiment Breakdown',
                               color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_sentiment, use_container_width=True)

        st.markdown("#### Top 3 Insights:")
        sentiment_map = sentiment_counts.set_index('Sentiment').to_dict()['Count']
        total_sentiment = sum(sentiment_map.values())
        sorted_sentiments = sorted(sentiment_map.items(), key=lambda item: item[1], reverse=True)
        sentiment_insights = []
        if sorted_sentiments:
            top_s = sorted_sentiments[0]
            sentiment_insights.append(f"1. The dominant sentiment is **{top_s[0]}**, accounting for **{(top_s[1]/total_sentiment*100):.1f}%** of all entries.")
        if len(sorted_sentiments) > 1:
            next_s = sorted_sentiments[1]
            sentiment_insights.append(f"2. **{sorted_sentiments[0][0]}** is significantly higher than other sentiments, with {top_s[1]:,} mentions compared to {next_s[1]:,} for **{next_s[0]}**.")
        if len(sorted_sentiments) > 2:
            least_s = sorted_sentiments[-1]
            sentiment_insights.append(f"3. The least common sentiment is **{least_s[0]}** with only **{(least_s[1]/total_sentiment*100):.1f}%** of mentions.")
        for insight in sentiment_insights:
            st.markdown(f"- {insight}")


        # --- Engagement Trend over Time (Line Chart) ---
        st.subheader("Engagement Trend Over Time")
        engagement_trend = st.session_state.filtered_data.groupby('Date')['Engagements'].sum().reset_index()
        fig_engagement = px.line(engagement_trend, x='Date', y='Engagements',
                                 title='Engagement Trend Over Time',
                                 line_shape='spline', markers=True,
                                 color_discrete_sequence=['#3B82F6'])
        st.plotly_chart(fig_engagement, use_container_width=True)

        st.markdown("#### Top 3 Insights:")
        engagement_insights = []
        if not engagement_trend.empty:
            peak_date = engagement_trend.loc[engagement_trend['Engagements'].idxmax()]
            engagement_insights.append(f"1. The peak engagement occurred on **{peak_date['Date'].strftime('%Y-%m-%d')}** with **{peak_date['Engagements']:,}** engagements.")
            min_date = engagement_trend.loc[engagement_trend['Engagements'].idxmin()]
            engagement_insights.append(f"2. The lowest engagement period was around **{min_date['Date'].strftime('%Y-%m-%d')}** with **{min_date['Engagements']:,}** engagements.")
            if len(engagement_trend) > 1:
                first_eng = engagement_trend['Engagements'].iloc[0]
                last_eng = engagement_trend['Engagements'].iloc[-1]
                if last_eng > first_eng * 1.1:
                    engagement_insights.append("3. Overall, there appears to be an **upward trend in engagements** over the analyzed period.")
                elif last_eng < first_eng * 0.9:
                    engagement_insights.append("3. Overall, there appears to be a **downward trend in engagements** over the analyzed period.")
                else:
                    engagement_insights.append("3. Engagements have remained relatively stable over the analyzed period.")
        for insight in engagement_insights:
            st.markdown(f"- {insight}")


        # --- Platform Engagements (Bar Chart) ---
        st.subheader("Platform Engagements")
        platform_engagements = st.session_state.filtered_data.groupby('Platform')['Engagements'].sum().reset_index()
        platform_engagements = platform_engagements.sort_values('Engagements', ascending=False)
        fig_platform = px.bar(platform_engagements, x='Platform', y='Engagements',
                              title='Platform Engagements',
                              color_discrete_sequence=['#6366F1'])
        st.plotly_chart(fig_platform, use_container_width=True)

        st.markdown("#### Top 3 Insights:")
        platform_insights = []
        if not platform_engagements.empty:
            top_p = platform_engagements.iloc[0]
            total_engagements = platform_engagements['Engagements'].sum()
            platform_insights.append(f"1. **{top_p['Platform']}** is the leading platform for engagements, contributing **{(top_p['Engagements']/total_engagements*100):.1f}%** of the total.")
            if len(platform_engagements) > 1:
                second_p = platform_engagements.iloc[1]
                diff = top_p['Engagements'] - second_p['Engagements']
                platform_insights.append(f"2. There is a significant difference between the top platform and the next highest, with **{top_p['Platform']}** having **{diff:,}** more engagements than **{second_p['Platform']}**.")
            if len(platform_engagements) > 2:
                least_p = platform_engagements.iloc[-1]
                platform_insights.append(f"3. **{least_p['Platform']}** has the lowest engagement among all platforms with **{least_p['Engagements']:,}** engagements.")
        for insight in platform_insights:
            st.markdown(f"- {insight}")

        # --- Media Type Mix (Pie Chart) ---
        st.subheader("Media Type Mix")
        media_type_counts = st.session_state.filtered_data['Media Type'].value_counts().reset_index()
        media_type_counts.columns = ['Media Type', 'Count']
        fig_media_type = px.pie(media_type_counts, values='Count', names='Media Type',
                                title='Media Type Mix',
                                color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_media_type, use_container_width=True)

        st.markdown("#### Top 3 Insights:")
        media_type_map = media_type_counts.set_index('Media Type').to_dict()['Count']
        total_media_types = sum(media_type_map.values())
        sorted_media_types = sorted(media_type_map.items(), key=lambda item: item[1], reverse=True)
        media_type_insights = []
        if sorted_media_types:
            top_m = sorted_media_types[0]
            media_type_insights.append(f"1. The most prevalent media type is **{top_m[0]}**, making up **{(top_m[1]/total_media_types*100):.1f}%** of all posts.")
        if len(sorted_media_types) > 1:
            second_m = sorted_media_types[1]
            media_type_insights.append(f"2. **{sorted_media_types[0][0]}** and **{second_m[0]}** are the primary media types used, indicating their importance in content strategy.")
        if len(sorted_media_types) > 2:
            least_m = sorted_media_types[-1]
            media_type_insights.append(f"3. The least used media type is **{least_m[0]}**, representing only **{(least_m[1]/total_media_types*100):.1f}%** of the content mix.")
        for insight in media_type_insights:
            st.markdown(f"- {insight}")

        # --- Top 5 Locations (Bar Chart) ---
        st.subheader("Top 5 Locations by Engagement")
        location_engagements = st.session_state.filtered_data.groupby('Location')['Engagements'].sum().reset_index()
        location_engagements = location_engagements.sort_values('Engagements', ascending=False).head(5)
        fig_location = px.bar(location_engagements, x='Location', y='Engagements',
                              title='Top 5 Locations by Engagement',
                              color_discrete_sequence=['#DC2626'])
        st.plotly_chart(fig_location, use_container_width=True)

        st.markdown("#### Top 3 Insights:")
        location_insights = []
        if not location_engagements.empty:
            top_l = location_engagements.iloc[0]
            location_insights.append(f"1. **{top_l['Location']}** is the top-performing location with **{top_l['Engagements']:,}** engagements.")
            if len(location_engagements) > 1:
                second_l = location_engagements.iloc[1]
                total_top5 = location_engagements['Engagements'].sum()
                top_two_share = ((top_l['Engagements'] + second_l['Engagements']) / total_top5 * 100) if total_top5 > 0 else 0
                location_insights.append(f"2. The top two locations, **{top_l['Location']}** and **{second_l['Location']}**, together account for **{top_two_share:.1f}%** of engagements among the top 5.")
            if len(location_engagements) > 2:
                location_insights.append("3. There's a noticeable drop in engagements after the top 2-3 locations, indicating focused engagement in specific geographical areas.")
        for insight in location_insights:
            st.markdown(f"- {insight}")

    st.markdown("---") # Separator

    # --- 5. Executive Summary & Recommendations ---
    st.header("4. Executive Summary & Recommendations")

    analysis_col1, analysis_col2 = st.columns([0.3, 0.7])
    with analysis_col1:
        generate_our_analysis_btn = st.button("Generate Analysis (Our AI)")
    with analysis_col2:
        generate_openrouter_analysis_btn = st.button("Generate Analysis (OpenRouter AI)")
        openrouter_api_key = st.text_input("OpenRouter API Key (Optional):", type="password", help="Enter your OpenRouter API key (e.g., sk-...)")
        openrouter_model = st.selectbox("AI Model:",
                                        options=["openai/gpt-3.5-turbo", "mistralai/mixtral-8x7b-instruct", "google/gemini-pro", "anthropic/claude-3-opus"],
                                        help="Select the AI model for OpenRouter analysis.")

    # Function to generate insights for the AI prompt
    def aggregate_insights_for_ai(data_df):
        if data_df.empty:
            return "No data available for analysis."

        summary_parts = []

        # Sentiment
        sentiment_counts = data_df['Sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Count']
        total_sentiment = sentiment_counts['Count'].sum()
        sorted_sentiments = sorted(sentiment_counts.values.tolist(), key=lambda x: x[1], reverse=True)
        if sorted_sentiments:
            summary_parts.append("### Sentiment Breakdown:")
            for s, c in sorted_sentiments:
                percent = (c / total_sentiment * 100) if total_sentiment > 0 else 0
                summary_parts.append(f"- {s}: {c:,} mentions ({percent:.1f}%)")

        # Engagement Trend
        engagement_trend = data_df.groupby('Date')['Engagements'].sum().reset_index()
        if not engagement_trend.empty:
            summary_parts.append("\n### Engagement Trend Over Time:")
            peak_date = engagement_trend.loc[engagement_trend['Engagements'].idxmax()]
            summary_parts.append(f"- Peak engagement on {peak_date['Date'].strftime('%Y-%m-%d')} with {peak_date['Engagements']:,} engagements.")
            min_date = engagement_trend.loc[engagement_trend['Engagements'].idxmin()]
            summary_parts.append(f"- Lowest engagement on {min_date['Date'].strftime('%Y-%m-%d')} with {min_date['Engagements']:,} engagements.")
            if len(engagement_trend) > 1:
                first_eng = engagement_trend['Engagements'].iloc[0]
                last_eng = engagement_trend['Engagements'].iloc[-1]
                if last_eng > first_eng * 1.1:
                    summary_parts.append("- Overall upward trend in engagements.")
                elif last_eng < first_eng * 0.9:
                    summary_parts.append("- Overall downward trend in engagements.")
                else:
                    summary_parts.append("- Engagements remained relatively stable.")

        # Platform Engagements
        platform_engagements = data_df.groupby('Platform')['Engagements'].sum().reset_index()
        platform_engagements = platform_engagements.sort_values('Engagements', ascending=False)
        if not platform_engagements.empty:
            summary_parts.append("\n### Platform Engagements:")
            total_platform_eng = platform_engagements['Engagements'].sum()
            for i, row in platform_engagements.head(3).iterrows(): # Top 3 platforms
                percent = (row['Engagements'] / total_platform_eng * 100) if total_platform_eng > 0 else 0
                summary_parts.append(f"- **{row['Platform']}**: {row['Engagements']:,} engagements ({percent:.1f}%)")
            if len(platform_engagements) > 3:
                summary_parts.append(f"- Other platforms account for remaining engagements.")


        # Media Type Mix
        media_type_counts = data_df['Media Type'].value_counts().reset_index()
        media_type_counts.columns = ['Media Type', 'Count']
        total_media_type = media_type_counts['Count'].sum()
        sorted_media_types = sorted(media_type_counts.values.tolist(), key=lambda x: x[1], reverse=True)
        if sorted_media_types:
            summary_parts.append("\n### Media Type Mix:")
            for m, c in sorted_media_types:
                percent = (c / total_media_type * 100) if total_media_type > 0 else 0
                summary_parts.append(f"- {m}: {c:,} posts ({percent:.1f}%)")

        # Top Locations
        location_engagements = data_df.groupby('Location')['Engagements'].sum().reset_index()
        location_engagements = location_engagements.sort_values('Engagements', ascending=False).head(5)
        if not location_engagements.empty:
            summary_parts.append("\n### Top Locations by Engagement:")
            for i, row in location_engagements.iterrows():
                summary_parts.append(f"- **{row['Location']}**: {row['Engagements']:,} engagements")

        return "\n".join(summary_parts)

    def generate_our_analysis():
        if st.session_state.filtered_data.empty:
            st.error("Please upload and analyze data first to generate an analysis.")
            return

        with st.spinner("Generating analysis (Our AI)..."):
            time.sleep(1) # Simulate AI processing time

            analysis_markdown = """
            ### Executive Summary

            This analysis provides key insights from your media intelligence data. It covers sentiment, engagement trends, platform performance, media type distribution, and top locations.

            #### Key Findings:
            """
            analysis_markdown += aggregate_insights_for_ai(st.session_state.filtered_data)

            analysis_markdown += """

            #### Campaign Recommendations:
            -   **Focus on High-Engagement Platforms:** Allocate more resources to platforms that show higher engagement rates to maximize reach and impact.
            -   **Leverage Dominant Media Types:** Prioritize content creation around media types that consistently perform well and resonate with your audience.
            -   **Address Sentiment Gaps:** If negative or neutral sentiment is significant, develop strategies to improve perception, such as addressing customer feedback or refining messaging.
            -   **Optimize for Peak Engagement Times:** Schedule content publication to align with identified peak engagement periods to ensure maximum visibility.
            -   **Target Key Geographic Areas:** Tailor campaigns to focus on locations demonstrating high engagement, or develop localized strategies for emerging markets.
            -   **Diversify Content if Needed:** If insights show a lack of diversity in platforms or media types, consider experimenting with new channels or formats to expand audience reach.
            """
            st.session_state.analysis_output = analysis_markdown

    def generate_openrouter_analysis():
        if st.session_state.filtered_data.empty:
            st.error("Please upload and analyze data first to generate an analysis.")
            return

        if not openrouter_api_key:
            st.warning("Please enter your OpenRouter API Key to use this feature.")
            return

        with st.spinner(f"Generating analysis with {openrouter_model} (OpenRouter AI)..."):
            data_summary_for_ai = aggregate_insights_for_ai(st.session_state.filtered_data)
            prompt = f"""
            Based on the following media intelligence data insights, provide a concise executive summary and actionable campaign recommendations to optimize future strategies. Structure the response with clear headings for 'Executive Summary' and 'Campaign Recommendations'. Use **markdown bold** for emphasis.

            {data_summary_for_ai}

            Provide the output in markdown format.
            """

            headers = {
                "Authorization": f"Bearer {openrouter_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": openrouter_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                response.raise_for_status() # Raise an exception for HTTP errors
                result = response.json()

                if result.get("choices") and result["choices"][0].get("message"):
                    st.session_state.analysis_output = result["choices"][0]["message"]["content"]
                else:
                    st.error("AI response format unexpected from OpenRouter.")
                    st.session_state.analysis_output = "AI response format unexpected."
                    st.json(result) # Display full response for debugging

            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred while calling OpenRouter AI: {e}")
                st.session_state.analysis_output = f"Failed to get response from AI. Error: {e}"
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.session_state.analysis_output = f"An unexpected error occurred: {e}"

    if generate_our_analysis_btn:
        generate_our_analysis()
    if generate_openrouter_analysis_btn:
        generate_openrouter_analysis()

    if 'analysis_output' in st.session_state:
        st.markdown("### Analysis Output")
        st.markdown(st.session_state.analysis_output)
    else:
        st.markdown('<p class="text-gray-500">Click a button above to generate the analysis.</p>', unsafe_allow_html=True)


    st.markdown("---") # Separator

    # --- 6. Download Report (Unfunctional) ---
    st.header("5. Download Report")
    st.button("Download PDF Report", on_click=lambda: st.info("PDF download is not currently functional in this Streamlit application."), type="secondary")

# Branding Footer
st.markdown(
    """
    <div style="width:100%; text-align:center; padding-top:20px; color:#6b7280; font-size:0.875rem;">
        <p>Powered by Gemini AI</p>
        <p>&copy; Media Intelligence - Hafizhan Izzuddin Iman (2025)</p>
    </div>
    """,
    unsafe_allow_html=True
)
