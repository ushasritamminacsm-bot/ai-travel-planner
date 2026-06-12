import streamlit as st
import google.generativeai as genai

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="TripMate AI — Student Travel Planner",
    page_icon="✈️",
    layout="centered",
)

# API key: default from secrets, or user can provide their own
default_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("🔑 API Key")
    user_key = st.text_input(
        "Use your own Gemini API key (optional)",
        type="password",
        placeholder="AIza...",
        help="Get a free key at aistudio.google.com/app/apikey. Leave blank to use the app's default key."
    )
    st.caption("Your key is only used for this session and never stored.")

GEMINI_API_KEY = user_key.strip() if user_key.strip() else default_key

if not GEMINI_API_KEY:
    st.error("⚠️ No Gemini API key available. Enter your own key in the sidebar, or the app owner must add GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# ---------------------------------------------------------
# STYLES
# ---------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0a0a12; color: #f0f0f8; }
    h1 { font-family: 'Trebuchet MS', sans-serif; }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #7c6ff7 0%, #5b53e8 100%);
        color: white; border: none; border-radius: 10px;
        padding: 0.7em; font-weight: 600; font-size: 16px;
    }
    .stDownloadButton>button {
        width: 100%; border-radius: 10px; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("✈️ TripMate AI")
st.caption("Smart, budget-friendly travel plans for students — powered by Gemini")

st.markdown("---")

# ---------------------------------------------------------
# INPUT FORM
# ---------------------------------------------------------
with st.form("trip_form"):
    st.subheader("About you")

    col1, col2 = st.columns(2)
    with col1:
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    with col2:
        age = st.number_input("Age", min_value=10, max_value=80, value=21, step=1)

    st.subheader("Trip details")

    travel_with = st.selectbox(
        "Travelling with",
        ["Solo", "Friends", "Family", "Couple", "Classmates", "College Group"]
    )

    col3, col4 = st.columns(2)
    with col3:
        duration = st.selectbox(
            "Duration",
            ["1 Day Trip", "2-3 Days (Weekend)", "4-5 Days", "1 Week", "2 Weeks", "1 Month"]
        )
    with col4:
        from_city = st.text_input("From (Starting city)", placeholder="e.g. Hyderabad")

    budget = st.number_input(
        "Total Budget (₹)", min_value=500, max_value=500000, value=15000, step=500
    )

    destination = st.text_input(
        "Preferred destination(s) — optional",
        placeholder="e.g. Goa, Manali, Hampi... or leave blank for AI suggestions"
    )

    interests = st.text_area(
        "Special interests / requirements",
        placeholder="e.g. love adventure sports, vegetarian food, first solo trip, need wheelchair access..."
    )

    submitted = st.form_submit_button("🚀 Generate My Travel Plan")

# ---------------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------------
def build_prompt():
    safety_section = (
        "5 specific safety tips for female travellers at this destination."
        if gender == "Female"
        else "4 general safety tips for this destination."
    )

    return f"""You are TripMate AI — an expert budget travel planner for Indian students.

Create a DETAILED, PRACTICAL travel plan for:
- Gender: {gender}
- Age: {age} years old
- Travelling with: {travel_with}
- Duration: {duration}
- Starting from: {from_city or 'India (unspecified city)'}
- Destination: {destination or 'suggest the best budget destination from their starting city'}
- Total Budget: ₹{budget:,}
- Special interests / requirements: {interests or 'none'}

Structure your response EXACTLY as follows (use these exact headings):

## TRIP SUMMARY
State the destination, total duration, and group type. Mention why this destination is perfect for this traveller profile.

## TRAVEL ROUTE & TRANSPORT
How to get there from {from_city or 'starting city'}: bus/train/flight options with approximate real costs. Include booking tips.

## BUDGET BREAKDOWN
List all cost categories with ₹ amounts:
- Transport (to & from): ₹___
- Local transport: ₹___
- Accommodation (per night × nights): ₹___
- Food (per day × days): ₹___
- Activities & entry fees: ₹___
- Miscellaneous / emergency: ₹___
- TOTAL: ₹___

## DAY-BY-DAY ITINERARY
For each day list: Morning / Afternoon / Evening activities with real place names, approximate costs, and tips.

## WHERE TO STAY
3 specific accommodation recommendations with price range per night and why it suits a student budget.

## WHAT TO EAT
5 must-try local dishes and where to find them cheaply. Include typical prices.

## MONEY-SAVING TIPS
7 specific, actionable tips to stretch the budget further at this specific destination.

## SAFETY TIPS
{safety_section}

## BEST TIME TO VISIT
When to go, when to avoid, and current season conditions.

## PACKING LIST
15 essential items specific to this trip's duration, destination, and activities.

Keep all price estimates realistic for 2024-2025. Use ₹ symbol. Be specific with real place names, real transport options, and real accommodation names where possible.
"""

# ---------------------------------------------------------
# GENERATE PLAN
# ---------------------------------------------------------
if submitted:
    if age < 10:
        st.error("Please enter a valid age.")
    elif budget < 500:
        st.error("Please enter a valid budget.")
    else:
        progress_bar = st.progress(0, text="🧳 Preparing your request...")

        stages = [
            (15, "📍 Analyzing your travel preferences..."),
            (35, "🚆 Checking transport & route options..."),
            (55, "🏨 Finding budget-friendly stays..."),
            (75, "📅 Building your day-by-day itinerary..."),
            (90, "💡 Adding money-saving tips & final touches..."),
        ]

        import threading
        result = {}

        def call_gemini():
            try:
                prompt = build_prompt()
                response = model.generate_content(prompt)
                result["text"] = response.text
            except Exception as e:
                result["error"] = e

        thread = threading.Thread(target=call_gemini)
        thread.start()

        i = 0
        while thread.is_alive():
            if i < len(stages):
                pct, msg = stages[i]
                progress_bar.progress(pct, text=msg)
                i += 1
            else:
                # keep last stage but inch forward slowly without hitting 100
                current = stages[-1][0]
                progress_bar.progress(min(current + (i - len(stages)) * 2, 97), text=stages[-1][1])
            thread.join(timeout=1.5)

        if "error" in result:
            err_str = str(result["error"])
            progress_bar.empty()
            if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                st.error("❌ Invalid API key. Please check your key in the sidebar and try again.")
            else:
                st.error(f"Something went wrong: {result['error']}")
        else:
            progress_bar.progress(100, text="✅ Done! Here's your plan...")
            plan_text = result["text"]
            progress_bar.empty()

            st.markdown("---")
            st.subheader("📋 Your Personalised Plan")

            # Stats row
            c1, c2, c3 = st.columns(3)
            c1.metric("Destination", destination or "AI Suggested")
            c2.metric("Duration", duration)
            c3.metric("Budget", f"₹{budget:,}")

            st.markdown(plan_text)

            # Download button
            download_content = f"""TRIPMATE AI — STUDENT TRAVEL PLAN
{'='*50}

TRAVELLER PROFILE
Gender: {gender} | Age: {age} | Group: {travel_with}
Duration: {duration} | Budget: ₹{budget:,}
From: {from_city or 'India'} | To: {destination or 'AI Suggested'}

{'='*50}

{plan_text}

{'='*50}
Generated by TripMate AI
"""
            st.download_button(
                label="⬇️ Download Plan as Text File",
                data=download_content,
                file_name="TripMate_Travel_Plan.txt",
                mime="text/plain",
            )

st.markdown("---")
st.caption("Made with ❤️ for students | Powered by Google Gemini")
