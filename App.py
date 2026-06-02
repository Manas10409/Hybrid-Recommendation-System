import streamlit as st
import pandas as pd
import json
import os
import uuid
from matching_functions import get_top_matches
from weights import create_user, get_user, update_weights, load_store
import plotly.graph_objects as go
import plotly.express as px

LOCATIONS = [
    "Bangalore", "Mumbai", "Chennai", "Hyderabad", "Pune",
    "Delhi", "Kolkata", "Ahmedabad", "Kochi", "Jaipur",
    "Noida", "Gurugram", "Coimbatore", "Mysuru", "Chandigarh"
]

PROFESSIONS = [
    "Data Analyst", "Software Engineer", "Product Manager", "UX Designer",
    "Marketing Specialist", "Business Analyst", "Machine Learning Engineer",
    "Content Strategist", "DevOps Engineer", "HR Manager", "Financial Analyst",
    "Graphic Designer", "Full Stack Developer", "Operations Manager",
    "Cybersecurity Analyst", "Cloud Architect", "Data Scientist",
    "Digital Marketing Manager", "Backend Developer", "Scrum Master",
    "Research Scientist", "Project Manager", "UI Developer",
    "Sales Manager", "Quality Analyst"
]

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"
]

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'matches' not in st.session_state:
    st.session_state.matches = None
if 'feedback_given' not in st.session_state:
    st.session_state.feedback_given = set()

def load_matches():
    user_data = get_user(st.session_state.user_id)
    weights = user_data['weights']
    matches = get_top_matches(st.session_state.profile, weights)
    st.session_state.matches = matches
    st.session_state.feedback_given = set()

with st.sidebar:
    st.title("Profile Matcher")
    st.markdown("---")
    page = st.radio("Navigation", ["New User", "Returning User", "System Demo"])

    if st.session_state.user_id:
        st.markdown("---")
        st.success(f"**Your ID:**\n`{st.session_state.user_id}`")
        st.caption("Save this ID to return later!")

        user_data = get_user(st.session_state.user_id)
        w = user_data['weights']
        st.markdown("---")
        st.markdown("### Your Learning Weights")
        st.metric("NLP (Career)", f"{w['w1']:.2f}")
        st.metric("MBTI", f"{w['w2']:.2f}")
        st.metric("Location", f"{w['w3']:.2f}")
        st.caption(f"Interactions: {w['interactions']}")

if page == "New User":
    st.title("Create Your Profile")
    st.markdown("Fill in your details to find your top professional matches.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Full Name")
        age = st.slider("Age", 20, 45, 28)
        profession = st.selectbox("Profession", PROFESSIONS)
        location = st.selectbox("Location", LOCATIONS)
        mbti = st.selectbox("MBTI Type", MBTI_TYPES)
        experience = st.slider("Years of Experience", 1, 20, 3)

    with col2:
        professional_summary = st.text_area(
            "Professional Summary",
            placeholder="e.g. Data analyst with 3 years of experience in healthcare analytics, skilled in SQL and Python...",
            height=120
        )
        about_me = st.text_area(
            "About Me",
            placeholder="e.g. I enjoy solving real-world problems and mentoring juniors. Outside work I love reading and hiking...",
            height=120
        )
        interests = st.text_input(
            "Interests (comma separated)",
            placeholder="e.g. Machine Learning, Chess, Hiking"
        )

    st.markdown("---")

    if st.button("Find My Matches", type="primary"):
        if not name or not professional_summary or not about_me or not interests:
            st.error("Please fill in all fields before continuing.")
        else:
            profile = {
                "name": name,
                "age": age,
                "profession": profession,
                "location": location,
                "mbti": mbti,
                "experience_years": experience,
                "professional_summary": professional_summary,
                "about_me": about_me,
                "interests": interests
            }

            with st.spinner("Creating your profile and finding matches..."):
                user_id = create_user(profile)
                st.session_state.user_id = user_id
                st.session_state.profile = profile
                load_matches()

            st.success(f"Profile created! Your ID is: **{user_id}** — save this!")
            st.rerun()
    if st.session_state.user_id and st.session_state.matches is not None:
        st.markdown("---")
        st.title("Your Top 5 Matches")

        user_data = get_user(st.session_state.user_id)
        w = user_data['weights']
        interactions = w['interactions']

        if interactions > 0:
            st.info(f"Matches personalized after {interactions} interactions. "
                    f"Weights — NLP: {w['w1']:.2f} | MBTI: {w['w2']:.2f} | Location: {w['w3']:.2f}")
        else:
            st.info("These are your initial matches based on default weights. "
                    "Accept or reject to personalize your recommendations!")

        matches = st.session_state.matches

        for _, row in matches.iterrows():
            with st.expander(
                f"**{row['name']}** — {row['profession']} | {row['location']} | {row['mbti']} | Score: {row['total_score']:.2f}"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Professional Summary:**\n{row['professional_summary']}")

                with col2:
                    st.markdown("**Compatibility Scores:**")
                    st.progress(float(row['nlp_score']), text=f"Career Match: {row['nlp_score']:.2f}")
                    st.progress(float(row['mbti_score']), text=f"MBTI Match: {row['mbti_score']:.2f}")
                    st.progress(float(row['location_score']), text=f"Location Match: {row['location_score']:.2f}")

                match_id = row['user_id']

                if match_id in st.session_state.feedback_given:
                    st.success("Feedback recorded for this match!")
                else:
                    c1, c2 = st.columns(2)
                    if c1.button("Accept", key=f"acc_{match_id}"):
                        update_weights(
                            st.session_state.user_id, 1,
                            row['nlp_score'], row['mbti_score'], row['location_score']
                        )
                        st.session_state.feedback_given.add(match_id)
                        st.rerun()

                    if c2.button("Reject", key=f"rej_{match_id}"):
                        update_weights(
                            st.session_state.user_id, 0,
                            row['nlp_score'], row['mbti_score'], row['location_score']
                        )
                        st.session_state.feedback_given.add(match_id)
                        st.rerun()

        st.markdown("---")
        if st.button("Refresh Matches with Updated Weights"):
            load_matches()
            st.rerun()

        # Weight evolution chart
        if interactions > 0:
            st.markdown("---")
            st.subheader("How Your Preferences Have Evolved")
            st.markdown(
                f"After **{interactions}** interactions, your weights have shifted from "
                f"the default (NLP: 0.50, MBTI: 0.30, Location: 0.20) to "
                f"(NLP: **{w['w1']:.2f}**, MBTI: **{w['w2']:.2f}**, Location: **{w['w3']:.2f}**)."
            )

            weight_df = pd.DataFrame({
                'Component': ['NLP (Career)', 'MBTI', 'Location'],
                'Default': [0.50, 0.30, 0.20],
                'Current': [w['w1'], w['w2'], w['w3']]
            }).set_index('Component')

            fig = px.bar(weight_df, barmode='group', title="Weight Evolution", labels={'value': 'Weight Value', 'Component': 'Component'}).update_layout(yaxis=dict(range=[0, 1]))
            st.plotly_chart(fig, use_container_width=True)

elif page == "Returning User":
    st.title("Welcome Back!")
    st.markdown("Enter your saved ID to continue where you left off.")
    st.markdown("---")

    entered_id = st.text_input("Enter Your User ID", placeholder="e.g. a3f9b2c1")

    if st.button("Load My Profile", type="primary"):
        user_data = get_user(entered_id)
        if user_data is None:
            st.error("ID not found. Please check your ID or create a new profile.")
        else:
            st.session_state.user_id = entered_id
            st.session_state.profile = user_data['profile']
            load_matches()
            st.success(f"Welcome back, {user_data['profile']['name']}!")
            st.rerun()

    if st.session_state.user_id and st.session_state.matches is not None:
        st.markdown("---")
        st.title("Your Top 5 Matches")

        user_data = get_user(st.session_state.user_id)
        w = user_data['weights']
        interactions = w['interactions']

        if interactions > 0:
            st.info(f"Matches personalized after {interactions} interactions. "
                    f"Weights — NLP: {w['w1']:.2f} | MBTI: {w['w2']:.2f} | Location: {w['w3']:.2f}")
        else:
            st.info("These are your initial matches based on default weights. "
                    "Accept or reject to personalize your recommendations!")

        matches = st.session_state.matches

        for _, row in matches.iterrows():
            with st.expander(
                f"**{row['name']}** — {row['profession']} | {row['location']} | {row['mbti']} | Score: {row['total_score']:.2f}"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Professional Summary:**\n{row['professional_summary']}")

                with col2:
                    st.markdown("**Compatibility Scores:**")
                    st.progress(float(row['nlp_score']), text=f"Career Match: {row['nlp_score']:.2f}")
                    st.progress(float(row['mbti_score']), text=f"MBTI Match: {row['mbti_score']:.2f}")
                    st.progress(float(row['location_score']), text=f"Location Match: {row['location_score']:.2f}")

                match_id = row['user_id']

                if match_id in st.session_state.feedback_given:
                    st.success("Feedback recorded for this match!")
                else:
                    c1, c2 = st.columns(2)
                    if c1.button("Accept", key=f"acc_{match_id}"):
                        update_weights(
                            st.session_state.user_id, 1,
                            row['nlp_score'], row['mbti_score'], row['location_score']
                        )
                        st.session_state.feedback_given.add(match_id)
                        st.rerun()

                    if c2.button("Reject", key=f"rej_{match_id}"):
                        update_weights(
                            st.session_state.user_id, 0,
                            row['nlp_score'], row['mbti_score'], row['location_score']
                        )
                        st.session_state.feedback_given.add(match_id)
                        st.rerun()

        st.markdown("---")
        if st.button("Refresh Matches with Updated Weights"):
            load_matches()
            st.rerun()

        # Weight evolution chart
        if interactions > 0:
            st.markdown("---")
            st.subheader("How Your Preferences Have Evolved")
            st.markdown(
                f"After **{interactions}** interactions, your weights have shifted from "
                f"the default (NLP: 0.50, MBTI: 0.30, Location: 0.20) to "
                f"(NLP: **{w['w1']:.2f}**, MBTI: **{w['w2']:.2f}**, Location: **{w['w3']:.2f}**)."
            )

            weight_df = pd.DataFrame({
                'Component': ['NLP (Career)', 'MBTI', 'Location'],
                'Default': [0.50, 0.30, 0.20],
                'Current': [w['w1'], w['w2'], w['w3']]
            }).set_index('Component')

            fig = px.bar(weight_df, barmode='group', title="Weight Evolution", labels={'value': 'Weight Value', 'Component': 'Component'}).update_layout(yaxis=dict(range=[0, 1]))
            st.plotly_chart(fig, use_container_width=True)
            
elif page == "System Demo":
    st.title("How the System Learns")
    st.markdown("This page shows how different users develop unique preferences over time starting from the same default weights.")
    
    
    store = load_store()
    
    if len(store) == 0:
        st.warning("No users yet. Create some profiles and interact with matches first.")
    else:
        names = []
        nlp_vals = []
        mbti_vals = []
        loc_vals = []
        interactions = []
        
        for uid, data in store.items():
            w = data['weights']
            names.append(data['profile']['name'])
            nlp_vals.append(w['w1'])
            mbti_vals.append(w['w2'])
            loc_vals.append(w['w3'])
            interactions.append(w['interactions'])
        
        fig = go.Figure(data=[
            go.Bar(name='NLP (Career)', x=names, y=nlp_vals, marker_color="#5684C9"),
            go.Bar(name='MBTI', x=names, y=mbti_vals, marker_color="#43C060"),
            go.Bar(name='Location', x=names, y=loc_vals, marker_color="#C93A3A")
        ])
        
        fig.update_layout(
            barmode='group',
            title='Learned Weights Per User', 
            yaxis=dict(range=[0, 1], title='Weight Value'),
            xaxis_title='User',
            legend_title='Component',
            height=450
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### User Summary")
        summary_df = pd.DataFrame({
            'Name': names,
            'NLP (Career)': nlp_vals,
            'MBTI': mbti_vals,
            'Location': loc_vals,
            'Interactions': interactions
        })
        st.write(summary_df)
        
        st.markdown("---")
        st.markdown("""
        **What this shows:**
        - All users start with the same default weights (NLP: 0.50, MBTI: 0.30, Location: 0.20)
        - Each user's weights converge differently based on their personal accept/reject behavior
        - This demonstrates genuine per-user personalization through gradient descent
        """)

