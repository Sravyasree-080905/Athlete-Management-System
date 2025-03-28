import streamlit as st
import sqlite3
from datetime import datetime
import google.generativeai as genai
import os
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.stylable_container import stylable_container
import time

# Initialize environment
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
def configure_genai():
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        return True
    else:
        st.error("API Key not found. Please set GEMINI_API_KEY in your environment.")
        return False

# Function to get AI response using Gemini 2.0 Flash
def get_ai_response(prompt):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('athlete_profiles.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  sport TEXT,
                  age INTEGER,
                  height REAL,
                  weight REAL,
                  gender TEXT,
                  join_date TEXT,
                  last_updated TEXT)''')
    
    conn.commit()
    conn.close()

init_db()

# Professional athlete icons
def show_athlete_icon(gender=None):
    """Displays professional male/female athlete icons using SVG"""
    if gender == "Female":
        st.markdown("""
        <div style="text-align: center;">
            <svg width="120" height="120" viewBox="0 0 24 24" fill="#FF69B4">
                <path d="M12 12C14.76 12 17 9.76 17 7C17 4.24 14.76 2 12 2C9.24 2 7 4.24 7 7C7 9.76 9.24 12 12 12Z"/>
                <path d="M12 14C7.58 14 4 17.58 4 22H20C20 17.58 16.42 14 12 14Z"/>
            </svg>
            <p style="text-align: center; color: #64748b;">Female Athlete</p>
        </div>
        """, unsafe_allow_html=True)
    elif gender == "Male":
        st.markdown("""
        <div style="text-align: center;">
            <svg width="120" height="120" viewBox="0 0 24 24" fill="#4169E1">
                <path d="M12 12C14.76 12 17 9.76 17 7C17 4.24 14.76 2 12 2C9.24 2 7 4.24 7 7C7 9.76 9.24 12 12 12Z"/>
                <path d="M12 14C7.58 14 4 17.58 4 22H20C20 17.58 16.42 14 12 14Z"/>
                <path d="M16 7C16 8.66 14.66 10 13 10C11.34 10 10 8.66 10 7C10 5.34 11.34 4 13 4C14.66 4 16 5.34 16 7Z" fill="white"/>
            </svg>
            <p style="text-align: center; color: #64748b;">Male Athlete</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center;">
            <svg width="120" height="120" viewBox="0 0 24 24" fill="#808080">
                <path d="M12 12C14.76 12 17 9.76 17 7C17 4.24 14.76 2 12 2C9.24 2 7 4.24 7 7C7 9.76 9.24 12 12 12Z"/>
                <path d="M12 14C7.58 14 4 17.58 4 22H20C20 17.58 16.42 14 12 14Z"/>
            </svg>
            <p style="text-align: center; color: #64748b;">Athlete Profile</p>
        </div>
        """, unsafe_allow_html=True)

# Profile Management
def save_profile(name, sport, age, height, weight, gender):
    conn = sqlite3.connect('athlete_profiles.db')
    c = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        c.execute('''INSERT INTO profiles 
                    (name, sport, age, height, weight, gender, join_date, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (name, sport, age, height, weight, gender, current_time, current_time))
        
        conn.commit()
        return c.lastrowid
    except Exception as e:
        st.error(f"Error saving profile: {str(e)}")
        return None
    finally:
        conn.close()
def show_dashboard():
    """Professional Athlete Dashboard with premium profile header"""
    
    # Premium Profile Header - Always at the very top
    if 'current_profile' in st.session_state and st.session_state.current_profile:
        profile_info = st.session_state.athlete_data['personal_info']
        
        # Premium CSS Styling
        st.markdown("""
        <style>
            .athlete-profile {
                background: white;
                border-radius: 12px;
                padding: 2rem;
                margin-bottom: 2.5rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                border: 1px solid rgba(0,0,0,0.05);
                font-family: 'Inter', sans-serif;
            }
            .profile-header {
                display: flex;
                align-items: center;
                gap: 2.5rem;
            }
            .profile-avatar {
                width: 120px;
                height: 120px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 3rem;
                font-weight: 600;
                flex-shrink: 0;
            }
            .profile-details {
                flex-grow: 1;
            }
            .profile-name {
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
                color: #1a1a1a;
            }
            .profile-title {
                font-size: 1rem;
                color: #6b7280;
                margin-bottom: 1.25rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .profile-stats {
                display: flex;
                gap: 2rem;
            }
            .stat-item {
                display: flex;
                flex-direction: column;
            }
            .stat-label {
                font-size: 0.75rem;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.25rem;
            }
            .stat-value {
                font-size: 1.25rem;
                font-weight: 600;
                color: #111827;
            }
            .profile-actions {
                display: flex;
                gap: 1rem;
                margin-top: 1.5rem;
            }
            .action-btn {
                padding: 0.5rem 1.25rem;
                border-radius: 8px;
                font-weight: 500;
                font-size: 0.875rem;
                cursor: pointer;
                transition: all 0.2s;
                border: none;
            }
            .primary-btn {
                background: #4f46e5;
                color: white;
            }
            .secondary-btn {
                background: white;
                color: #4f46e5;
                border: 1px solid #d1d5db;
            }
            .badge {
                display: inline-flex;
                align-items: center;
                padding: 0.35rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 500;
                background: #e0e7ff;
                color: #4f46e5;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Get initials for avatar
        initials = ''.join([name[0].upper() for name in profile_info.get('name', 'A').split()[:2]])
        
        with st.container():
            st.markdown(f"""
            <div class="athlete-profile">
                <div class="profile-header">
                    <div class="profile-avatar">{initials}</div>
                    <div class="profile-details">
                        <h1 class="profile-name">{profile_info.get('name', 'Athlete Name')}</h1>
                        <div class="profile-title">
                            <span>{profile_info.get('sport', 'Professional Athlete')}</span>
                            <span class="badge">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 4px;">
                                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="#4f46e5"/>
                                    <path d="M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z" fill="white"/>
                                </svg>
                                Verified Athlete
                            </span>
                        </div>
                        <div class="profile-stats">
                            <div class="stat-item">
                                <span class="stat-label">Age</span>
                                <span class="stat-value">{profile_info.get('age', '--')}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Height</span>
                                <span class="stat-value">{profile_info.get('height', '--')} cm</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Weight</span>
                                <span class="stat-value">{profile_info.get('weight', '--')} kg</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">BMI</span>
                                <span class="stat-value">
                                    {calculate_bmi(profile_info.get('height', 0), profile_info.get('weight', 0)) if profile_info.get('height') and profile_info.get('weight') else '--'}
                                </span>
                            </div>
                        </div>
                        <div class="profile-actions">
                            <button class="action-btn primary-btn">Edit Profile</button>
                            <button class="action-btn secondary-btn">Performance Report</button>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Always show module status
    st.header("Performance Dashboard")
    show_module_status()
    
    # Only show detailed analytics if all modules are completed
    if all_modules_completed():
        # Data Overview Section
        with st.container():
            st.markdown("### Performance Metrics Summary")
            perf_data = st.session_state.athlete_data['performance']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Speed (km/h)", f"{perf_data.get('speed', 0)}", 
                         delta=f"{(perf_data.get('speed', 0)-22.5):.1f} vs avg")
            with col2:
                st.metric("Strength (kg)", f"{perf_data.get('strength', 0)}", 
                         delta=f"{(perf_data.get('strength', 0)-120):.1f} vs avg")
            with col3:
                st.metric("Reaction Time (s)", f"{perf_data.get('reaction_time', 0):.2f}", 
                         delta=f"{(0.5 - perf_data.get('reaction_time', 0)):.2f} improvement")
            with col4:
                st.metric("Stamina (min)", f"{perf_data.get('stamina', 0)}", 
                         delta=f"{(perf_data.get('stamina', 0)-75):.1f} vs avg")

        # Health Risk Analysis
        st.markdown("---")
        with st.container():
            st.markdown("### Health & Injury Risk Assessment")
            injury_data = st.session_state.athlete_data['injury']
            
            risk_score = (
                injury_data.get('training_intensity', 0) * 0.4 + 
                injury_data.get('past_injuries', 0) * 0.3 - 
                injury_data.get('sleep_hours', 0) * 0.2 - 
                injury_data.get('nutrition_score', 0) * 0.1
            )
            
            recovery_score = (
                injury_data.get('sleep_hours', 0)/8 * 40 + 
                injury_data.get('nutrition_score', 0)/10 * 60
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("*Injury Risk Factors*")
                st.progress(min(100, int(risk_score*10)))
                st.caption(f"Risk Score: {risk_score:.1f}/10 - {'High' if risk_score > 6 else 'Medium' if risk_score > 3 else 'Low'} Risk")
                
                st.markdown("*Key Indicators:*")
                st.write(f"- Training Intensity: {injury_data.get('training_intensity', 0)}/10")
                st.write(f"- Sleep Duration: {injury_data.get('sleep_hours', 0)} hours")
                st.write(f"- Nutrition Quality: {injury_data.get('nutrition_score', 0)}/10")
            
            with col2:
                st.markdown("*Recovery Status*")
                st.progress(min(100, int(recovery_score)))
                st.caption(f"Recovery Score: {recovery_score:.0f}/100")
                
                st.markdown("*Recommendations:*")
                if risk_score > 6:
                    st.write("- Reduce training intensity by 20%")
                    st.write("- Increase sleep to 8+ hours nightly")
                elif risk_score > 3:
                    st.write("- Maintain current training load")
                    st.write("- Focus on recovery nutrition")
                else:
                    st.write("- Optimal recovery status")
                    st.write("- Maintain current regimen")

        # Performance Trends
        st.markdown("---")
        with st.container():
            st.markdown("### Performance Trend Analysis")
            perf_data = st.session_state.athlete_data['performance']
            
            metrics = ['Speed', 'Strength', 'Stamina', 'Reaction Time']
            current = [
                perf_data.get('speed', 0),
                perf_data.get('strength', 0),
                perf_data.get('stamina', 0),
                10 - perf_data.get('reaction_time', 0)*10
            ]
            previous = [x*0.9 for x in current]
            
            df = pd.DataFrame({
                'Metric': metrics,
                'Current': current,
                'Previous': previous
            })
            
            fig = px.bar(df, x='Metric', y=['Previous', 'Current'],
                        barmode='group', title="Performance Comparison",
                        color_discrete_sequence=['#a3a3a3', '#3b82f6'])
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # Financial Health Dashboard
        st.markdown("---")
        with st.container():
            st.markdown("### Financial Health Overview")
            finance_data = st.session_state.athlete_data['finance']
            
            total_income = (finance_data.get('salary', 0) + 
                          finance_data.get('endorsements', 0) + 
                          finance_data.get('appearances', 0) + 
                          finance_data.get('other_income', 0))
            
            total_expenses = sum([finance_data.get(k, 0) for k in [
                'coaching', 'equipment', 'physio', 'travel', 
                'nutrition', 'housing', 'insurance', 'transport', 
                'other_expenses'
            ]])
            
            savings_rate = ((total_income - total_expenses) / total_income * 100 
                          if total_income > 0 else 0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Income", f"₹{total_income:,.0f}")
            with col2:
                st.metric("Total Expenses", f"₹{total_expenses:,.0f}")
            with col3:
                st.metric("Savings Rate", f"{savings_rate:.1f}%")
            
            st.markdown("*Expense Allocation*")
            expense_categories = ['Coaching', 'Equipment', 'Physio', 'Travel', 
                                'Nutrition', 'Housing', 'Insurance', 'Transport']
            expense_values = [finance_data.get(k.lower(), 0) for k in expense_categories]
            
            fig = px.pie(names=expense_categories, values=expense_values,
                        hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig, use_container_width=True)

        # AI-Powered Insights
        st.markdown("---")
        with st.container():
            st.markdown("### Performance Insights")
            analysis_prompt = f"""
            Analyze this athlete's complete profile:
            
            Performance Data: {st.session_state.athlete_data.get('performance', {})}
            Injury Risk Factors: {st.session_state.athlete_data.get('injury', {})}
            Career Status: {st.session_state.athlete_data.get('career', {})}
            Nutrition Profile: {st.session_state.athlete_data.get('nutrition', {})}
            Financial Health: {st.session_state.athlete_data.get('finance', {})}
            
            Provide:
            1. Three key strengths
            2. Three areas for improvement
            3. Recommended training adjustments
            4. Nutrition and recovery suggestions
            5. Financial optimization strategies
            """
            
            analysis = get_ai_response(analysis_prompt)
            st.markdown("#### Comprehensive Performance Analysis")
            st.write(analysis)
    else:
        st.info(" Complete all modules to unlock detailed performance analytics and insights")
        # Show progress tracker
        cols = st.columns(3)
        completion_status = {
            'Performance': bool(st.session_state.athlete_data.get('performance')),
            'Injury': bool(st.session_state.athlete_data.get('injury')),
            'Career': bool(st.session_state.athlete_data.get('career')),
            'Nutrition': bool(st.session_state.athlete_data.get('nutrition')),
            'Finance': bool(st.session_state.athlete_data.get('finance'))
        }
        
        with cols[1]:
            st.metric("Modules Completed", 
                     f"{sum(completion_status.values())}/5",
                     delta=f"{5 - sum(completion_status.values())} remaining")
def calculate_bmi(height_cm, weight_kg):
    """Helper function to calculate BMI"""
    if height_cm <= 0 or weight_kg <= 0:
        return "--"
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)
    return bmi
def all_modules_completed():
    """Check if all modules have data"""
    required_modules = ['performance', 'injury', 'career', 'nutrition', 'finance']
    return all(st.session_state.athlete_data.get(module) for module in required_modules)

def show_module_status():
    """Professional module cards with fully clickable area"""
    
    # Load Inter font
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            .dashboard-card-container {
                position: relative;
            }
            .dashboard-card {
                border: 1px solid rgba(226, 232, 240, 0.8);
                border-radius: 14px;
                padding: 28px;
                margin: 12px 0;
                background: linear-gradient(145deg, #ffffff, #f9fafb);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
                height: 160px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                font-family: 'Inter', sans-serif;
            }
            .dashboard-card:hover {
                box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.08), 0 4px 6px -4px rgba(59, 130, 246, 0.08);
                transform: translateY(-2px);
                border-color: rgba(165, 180, 252, 0.6);
                cursor: pointer;
            }
        </style>
    """, unsafe_allow_html=True)

    modules = {
        "Performance Analytics": "performance",
        "Injury Prevention": "injury", 
        "Career Development": "career",
        "Nutrition Planning": "nutrition",
        "Financial Planning": "finance"
    }

    # Create columns with medium gap
    cols = st.columns(3, gap="medium")
    
    for i, (module_name, module_key) in enumerate(modules.items()):
        with cols[i % 3]:
            is_complete = bool(st.session_state.athlete_data.get(module_key))
            
            # Create container for the card
            with st.container():
                # Create the clickable card
                clickable_card = f"""
                <div class="dashboard-card">
                    <div class="card-title">{module_name}</div>
                    <div class="card-status {'complete' if is_complete else ''}">
                        {'Review Module' if is_complete else 'Begin Now'}
                    </div>
                </div>
                """
                st.markdown(clickable_card, unsafe_allow_html=True)
                
                # Add invisible button that covers the entire card
                if st.button(" ", key=f"card_btn_{module_key}", 
                           help=f"Go to {module_name}"):
                    st.session_state.current_module = module_key
                    st.rerun()
                
                # Style the button to cover the card
                st.markdown(f"""
                <style>
                    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stButton"] > button[key="card_btn_{module_key}"] {{
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        opacity: 0;
                        z-index: 1;
                        padding: 0;
                        margin: 0;
                    }}
                    div[data-testid="stHorizontalBlock"] > div:nth-child({i%3+1}) {{
                        position: relative;
                    }}
                </style>
                """, unsafe_allow_html=True)

def add_back_button():
    if st.button("← Back to Dashboard", key="back_button"):
        if 'current_module' in st.session_state:
            del st.session_state.current_module
        st.rerun()

def analyze_performance():
    st.markdown("<h2>Performance Tracking</h2>", unsafe_allow_html=True)
    
    add_back_button()
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            with stylable_container(
                key="perf_metric_speed",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #3b82f6;
                }
                """
            ):
                st.metric(label="Avg Speed", value="22.5 km/h", delta="+1.2 km/h")
        
        with col2:
            with stylable_container(
                key="perf_metric_reaction",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #10b981;
                }
                """
            ):
                st.metric(label="Reaction Time", value="0.42s", delta="-0.08s")
        
        with col3:
            with stylable_container(
                key="perf_metric_strength",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #f59e0b;
                }
                """
            ):
                st.metric(label="Strength Index", value="87/100", delta="+5 points")

    with st.expander("Detailed Performance Analysis", expanded=True):
        with st.form("performance_form"):
            athlete_name = st.text_input("Athlete Name", key="perf_name_input", placeholder="Enter athlete's full name")
            
            tab1, tab2, tab3 = st.tabs(["Physical Metrics", "Technical Skills", "Mental Attributes"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    speed = st.slider("Speed (km/hr)", 5, 40, 22, key="perf_speed_slider")
                    stamina = st.slider("Stamina (mins)", 10, 180, 75, key="perf_stamina_slider")
                    strength = st.slider("Strength (kg)", 0, 200, 120, key="perf_strength_slider")
                with col2:
                    reaction_time = st.slider("Reaction Time (secs)", 0.1, 2.0, 0.5, 0.1, key="perf_reaction_slider")
                    flexibility = st.slider("Flexibility (1-10)", 1, 10, 7, key="perf_flex_slider")
                    recovery_rate = st.slider("Recovery Rate (1-10)", 1, 10, 6, key="perf_recovery_slider")
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    technique = st.slider("Technique (1-10)", 1, 10, 7, key="perf_technique_slider")
                    coordination = st.slider("Coordination (1-10)", 1, 10, 8, key="perf_coordination_slider")
                    accuracy = st.slider("Accuracy (1-10)", 1, 10, 7, key="perf_accuracy_slider")
                with col2:
                    tactical_awareness = st.slider("Tactical Awareness (1-10)", 1, 10, 6, key="perf_tactical_slider")
                    equipment_handling = st.slider("Equipment Handling (1-10)", 1, 10, 8, key="perf_equipment_slider")
            
            with tab3:
                col1, col2 = st.columns(2)
                with col1:
                    focus = st.slider("Focus (1-10)", 1, 10, 7, key="perf_focus_slider")
                    confidence = st.slider("Confidence (1-10)", 1, 10, 8, key="perf_confidence_slider")
                    resilience = st.slider("Resilience (1-10)", 1, 10, 7, key="perf_resilience_slider")
                with col2:
                    motivation = st.slider("Motivation (1-10)", 1, 10, 6, key="perf_motivation_slider")
                    composure = st.slider("Composure (1-10)", 1, 10, 8, key="perf_composure_slider")
            
            submit_button = st.form_submit_button("Analyze Performance", use_container_width=True)
            
            if submit_button:
                with st.spinner("Crunching numbers..."):
                    time.sleep(1)
                    performance_data = {
                        "speed": speed,
                        "stamina": stamina,
                        "strength": strength,
                        "reaction_time": reaction_time,
                        "flexibility": flexibility,
                        "recovery_rate": recovery_rate,
                        "technique": technique,
                        "coordination": coordination,
                        "accuracy": accuracy,
                        "tactical_awareness": tactical_awareness,
                        "equipment_handling": equipment_handling,
                        "focus": focus,
                        "confidence": confidence,
                        "resilience": resilience,
                        "motivation": motivation,
                        "composure": composure
                    }
                    
                    # Store in session state
                    st.session_state.athlete_data['performance'] = performance_data
                    st.session_state.athlete_data['personal_info']['name'] = athlete_name
                    
                    # Create a combined dataframe for visualization
                    combined_data = []
                    for metric, value in performance_data.items():
                        combined_data.append({"Metric": metric, "Value": value})
                    
                    df = pd.DataFrame(combined_data)
                    
                    fig = px.bar(
                        df,
                        x="Metric",
                        y="Value",
                        title=f"Performance Metrics for {athlete_name}",
                        color="Metric"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    prompt = f"Analyze this athlete's performance: {performance_data}"
                    st.success(get_ai_response(prompt))

def injury_prediction():
    st.markdown("<h2>Injury Prediction</h2>", unsafe_allow_html=True)
    add_back_button()
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            with stylable_container(
                key="injury_metric_risk",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #ef4444;
                }
                """
            ):
                st.metric(label="High Risk Athletes", value="3", delta="+1 this week")
        
        with col2:
            with stylable_container(
                key="injury_metric_recovery",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #f59e0b;
                }
                """
            ):
                st.metric(label="Recovery Progress", value="68%", delta="+12%")
        
        with col3:
            with stylable_container(
                key="injury_metric_days",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #10b981;
                }
                """
            ):
                st.metric(label="Injury-Free Days", value="27", delta="+5 streak")

    with st.expander("Injury Risk Assessment", expanded=True):
        with st.form("injury_form"):
            athlete_name = st.text_input("Athlete Name", key="injury_name_input", placeholder="Enter athlete's full name")
            
            col1, col2 = st.columns(2)
            with col1:
                training_intensity = st.slider("Training Intensity (1-10)", 1, 10, 7, key="injury_intensity_slider")
                past_injuries = st.number_input("Number of Past Injuries", 0, 20, 2, key="injury_past_input")
                fatigue_level = st.slider("Fatigue Level (1-10)", 1, 10, 5, key="injury_fatigue_slider")
            with col2:
                sleep_hours = st.slider("Average Sleep Hours", 0, 12, 7, key="injury_sleep_slider")
                nutrition_score = st.slider("Nutrition Score (1-10)", 1, 10, 8, key="injury_nutrition_slider")
                stress_level = st.slider("Stress Level (1-10)", 1, 10, 4, key="injury_stress_slider")
            
            submit_button = st.form_submit_button("Predict Injury Risk", use_container_width=True)
            
            if submit_button:
                with st.spinner("Analyzing..."):
                    time.sleep(1)
                    risk_score = (training_intensity * 0.4) + (past_injuries * 0.3) - (sleep_hours * 0.2) - (nutrition_score * 0.1)
                    st.write(f"Injury Risk Score: {risk_score:.2f}")
                    
                    # Store in session state
                    st.session_state.athlete_data['injury'] = {
                        "training_intensity": training_intensity,
                        "past_injuries": past_injuries,
                        "fatigue_level": fatigue_level,
                        "sleep_hours": sleep_hours,
                        "nutrition_score": nutrition_score,
                        "stress_level": stress_level,
                        "risk_score": risk_score
                    }
                    st.session_state.athlete_data['personal_info']['name'] = athlete_name
                    
                    prompt = f"Injury risk analysis for {athlete_name}: Intensity={training_intensity}, Injuries={past_injuries}, Sleep={sleep_hours}, Nutrition={nutrition_score}, Stress={stress_level}"
                    st.success(get_ai_response(prompt))

def career_planning():
    st.markdown("<h2>Career Planning</h2>", unsafe_allow_html=True)
    add_back_button()
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            with stylable_container(
                key="career_metric_potential",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #3b82f6;
                }
                """
            ):
                st.metric(label="Career Potential", value="High", delta="Improving")
        
        with col2:
            with stylable_container(
                key="career_metric_years",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #f59e0b;
                }
                """
            ):
                st.metric(label="Peak Years Left", value="5-7", delta="Optimal")
        
        with col3:
            with stylable_container(
                key="career_metric_transition",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #10b981;
                }
                """
            ):
                st.metric(label="Transition Readiness", value="68%", delta="+8%")

    with st.expander("Career Pathway Analysis", expanded=True):
        with st.form("career_form"):
            athlete_name = st.text_input("Athlete Name", key="career_name_input", placeholder="Enter athlete's full name")
            age = st.slider("Age", 15, 45, 24, key="career_age_slider")
            sport = st.selectbox("Primary Sport", 
                               ["Cricket", "Football", "Basketball", "Tennis", "Swimming", "Athletics", "Gymnastics", "Other"], 
                               key="career_sport_select")
            experience = st.slider("Years of Experience", 0, 30, 5, key="career_exp_slider")
            
            strengths = st.text_area("Strengths", key="career_strengths_area", placeholder="List the athlete's key strengths")
            
            submit_button = st.form_submit_button("Generate Career Plan", use_container_width=True)
            
            if submit_button:
                with st.spinner("Developing pathway..."):
                    time.sleep(1)
                    # Store in session state
                    st.session_state.athlete_data['career'] = {
                        "age": age,
                        "sport": sport,
                        "experience": experience,
                        "strengths": strengths
                    }
                    st.session_state.athlete_data['personal_info'] = {
                        "name": athlete_name,
                        "sport": sport,
                        "age": age
                    }
                    
                    prompt = f"Career plan for {athlete_name}, {age}y/o {sport} athlete with {experience} years experience. Strengths: {strengths}"
                    st.success(get_ai_response(prompt))

def nutrition_planner():
    st.markdown("<h2>Nutrition Planner</h2>", unsafe_allow_html=True)
    add_back_button()
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            with stylable_container(
                key="nutrition_metric_calories",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #3b82f6;
                }
                """
            ):
                st.metric(label="Daily Calories", value="2,800", delta="+200")
        
        with col2:
            with stylable_container(
                key="nutrition_metric_protein",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #10b981;
                }
                """
            ):
                st.metric(label="Protein (g)", value="180g", delta="+15g")
        
        with col3:
            with stylable_container(
                key="nutrition_metric_hydration",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #f59e0b;
                }
                """
            ):
                st.metric(label="Hydration (L)", value="3.2L", delta="+0.5L")

    with st.expander("Personalized Meal Plan", expanded=True):
        with st.form("nutrition_form"):
            athlete_name = st.text_input("Athlete Name", key="nutrition_name_input", placeholder="Enter athlete's full name")
            
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input("Weight (kg)", min_value=40, max_value=150, value=75, key="nutrition_weight_input")
                height = st.number_input("Height (cm)", min_value=140, max_value=220, value=180, key="nutrition_height_input")
                age = st.number_input("Age", min_value=15, max_value=50, value=25, key="nutrition_age_input")
            with col2:
                activity_level = st.selectbox("Activity Level", 
                                           ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"], 
                                           key="nutrition_activity_select")
                dietary_pref = st.selectbox("Dietary Preference", 
                                         ["No Restrictions", "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free"], 
                                         key="nutrition_diet_select")
                allergies = st.text_input("Allergies", key="nutrition_allergies_input", placeholder="List any food allergies")
            
            submit_button = st.form_submit_button("Generate Meal Plan", use_container_width=True)
            
            if submit_button:
                with st.spinner("Creating personalized nutrition plan..."):
                    time.sleep(1)
                    bmi = weight / ((height/100) ** 2)
                    st.write(f"Calculated BMI: {bmi:.1f}")
                    
                    # Store in session state
                    st.session_state.athlete_data['nutrition'] = {
                        "weight": weight,
                        "height": height,
                        "age": age,
                        "activity_level": activity_level,
                        "dietary_pref": dietary_pref,
                        "allergies": allergies,
                        "bmi": bmi
                    }
                    st.session_state.athlete_data['personal_info'] = {
                        "name": athlete_name,
                        "age": age,
                        "weight": weight,
                        "height": height
                    }
                    
                    prompt = f"""
                    Create a personalized meal plan for {athlete_name}:
                    - Weight: {weight}kg
                    - Height: {height}cm
                    - Age: {age}
                    - Activity Level: {activity_level}
                    - Dietary Preference: {dietary_pref}
                    - Allergies: {allergies}
                    
                    Include:
                    1. Daily macronutrient breakdown
                    2. Sample meal plan for 3 days
                    3. Hydration recommendations
                    4. Pre/post-workout nutrition
                    """
                    st.success(get_ai_response(prompt))

def financial_planner():
    st.markdown("<h2>Financial Planner</h2>", unsafe_allow_html=True)
    add_back_button()
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            with stylable_container(
                key="finance_metric_income",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #3b82f6;
                }
                """
            ):
                st.metric(label="Monthly Income", value="₹7,00,000", delta="+₹40,000")
        
        with col2:
            with stylable_container(
                key="finance_metric_expenses",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #ef4444;
                }
                """
            ):
                st.metric(label="Monthly Expenses", value="₹3,50,000", delta="+₹15,000")
        
        with col3:
            with stylable_container(
                key="finance_metric_savings",
                css_styles="""
                {
                    background: white;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #10b981;
                }
                """
            ):
                st.metric(label="Savings Rate", value="32%", delta="+2%")

    with st.expander("Financial Health Analysis", expanded=True):
        with st.form("finance_form"):
            athlete_name = st.text_input("Athlete Name", key="finance_name_input", placeholder="Enter athlete's full name")
            
            st.markdown("### Income Sources")
            col1, col2 = st.columns(2)
            with col1:
                salary = st.number_input("Competition Earnings", min_value=0, value=500000, step=50000, key="finance_salary_input")
                endorsements = st.number_input("Sponsorships", min_value=0, value=150000, step=50000, key="finance_endorsements_input")
            with col2:
                appearances = st.number_input("Appearance Fees", min_value=0, value=50000, step=10000, key="finance_appearances_input")
                other_income = st.number_input("Other Income", min_value=0, value=50000, step=10000, key="finance_other_input")
            
            st.markdown("### Athlete-Specific Expenses")
            tab1, tab2 = st.tabs(["Training Expenses", "Lifestyle Expenses"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    coaching = st.number_input("Coaching Fees", min_value=0, value=80000, step=10000, key="finance_coaching_input")
                    equipment = st.number_input("Equipment", min_value=0, value=40000, step=5000, key="finance_equipment_input")
                    physio = st.number_input("Physiotherapy", min_value=0, value=30000, step=5000, key="finance_physio_input")
                with col2:
                    travel = st.number_input("Competition Travel", min_value=0, value=50000, step=5000, key="finance_travel_input")
                    nutrition = st.number_input("Sports Nutrition", min_value=0, value=25000, step=5000, key="finance_nutrition_input")
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    housing = st.number_input("Housing", min_value=0, value=120000, step=10000, key="finance_housing_input")
                    insurance = st.number_input("Insurance", min_value=0, value=25000, step=5000, key="finance_insurance_input")
                with col2:
                    transport = st.number_input("Transport", min_value=0, value=25000, step=5000, key="finance_transport_input")
                    other_expenses = st.number_input("Other Expenses", min_value=0, value=25000, step=5000, key="finance_other_exp_input")
            
            submit_button = st.form_submit_button("Generate Financial Plan", use_container_width=True)
            
            if submit_button:
                with st.spinner("Analyzing financial health..."):
                    time.sleep(1)
                    total_income = salary + endorsements + appearances + other_income
                    total_expenses = (coaching + equipment + physio + travel + 
                                    nutrition + housing + insurance + transport + 
                                    other_expenses)
                    savings = total_income - total_expenses
                    savings_rate = (savings / total_income) * 100 if total_income > 0 else 0
                    
                    st.write(f"*Monthly Savings:* ₹{savings:,.2f} ({savings_rate:.1f}% of income)")
                    
                    # Financial health indicator
                    if savings_rate > 30:
                        financial_health = "Excellent"
                        health_color = "green"
                    elif savings_rate > 15:
                        financial_health = "Good"
                        health_color = "blue"
                    else:
                        financial_health = "Needs Improvement"
                        health_color = "red"
                    
                    st.markdown(f"*Financial Health:* <span style='color:{health_color}'>{financial_health}</span>", unsafe_allow_html=True)
                    
                    # Store in session state
                    st.session_state.athlete_data['finance'] = {
                        "salary": salary,
                        "endorsements": endorsements,
                        "appearances": appearances,
                        "other_income": other_income,
                        "coaching": coaching,
                        "equipment": equipment,
                        "physio": physio,
                        "travel": travel,
                        "nutrition": nutrition,
                        "housing": housing,
                        "insurance": insurance,
                        "transport": transport,
                        "other_expenses": other_expenses,
                        "total_income": total_income,
                        "total_expenses": total_expenses,
                        "savings": savings,
                        "savings_rate": savings_rate
                    }
                    st.session_state.athlete_data['personal_info']['name'] = athlete_name
                    
                    # Generate recommendations
                    prompt = f"""
                    Create a financial management plan for professional athlete {athlete_name}:
                    - Total Monthly Income: ₹{total_income:,.2f}
                    - Total Monthly Expenses: ₹{total_expenses:,.2f}
                    - Monthly Savings: ₹{savings:,.2f} ({savings_rate:.1f}%)
                    
                    Focus specifically on:
                    1. Optimizing athlete-specific expenses (training, equipment, coaching)
                    2. Sponsorship and endorsement management strategies
                    3. Savings and investment strategies for athletes
                    4. Budgeting for competition seasons vs off-seasons
                    5. Retirement planning for athletes
                    
                    Provide concrete, actionable recommendations.
                    """
                    st.success(get_ai_response(prompt))

def show_profile_creation():
    st.header("Create Athlete Profile")
    
    with st.form("profile_form"):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Profile Details")
            gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
            show_athlete_icon(gender)
        
        with col2:
            name = st.text_input("Full Name*", placeholder="John Doe")
            sport = st.selectbox("Primary Sport*", 
                               ["Football", "Basketball", "Tennis", 
                                "Swimming", "Athletics", "Other"])
            
            col3, col4 = st.columns(2)
            with col3:
                age = st.number_input("Age*", min_value=12, max_value=60, value=25)
                weight = st.number_input("Weight (kg)*", min_value=40, max_value=150, value=75)
            with col4:
                height = st.number_input("Height (cm)*", min_value=140, max_value=220, value=180)
        
        if st.form_submit_button("Create Profile", use_container_width=True):
            if name:
                profile_id = save_profile(name, sport, age, height, weight, gender)
                if profile_id:
                    st.session_state.current_profile = profile_id
                    st.session_state.athlete_data['personal_info'] = {
                        'name': name,
                        'sport': sport,
                        'age': age,
                        'height': height,
                        'weight': weight,
                        'gender': gender
                    }
                    st.success("Profile created successfully!")
                    st.rerun()
            else:
                st.error("Please enter at least a name")
def main():
    st.set_page_config(
        page_title="Athlete Management System",
        page_icon="🏅", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Configure Gemini AI
    if not configure_genai():
        return
    
    # Initialize session state
    if 'athlete_data' not in st.session_state:
        st.session_state.athlete_data = {
            'performance': {},
            'injury': {},
            'career': {},
            'nutrition': {},
            'finance': {},
            'personal_info': {}
        }
    
    if 'current_profile' not in st.session_state:
        st.session_state.current_profile = None
    
    # Profile creation/selection logic
    if not st.session_state.current_profile:
        show_profile_creation()
        st.stop()
    
    # Handle card clicks first
    if 'current_module' in st.session_state:
        module = st.session_state.current_module
        if module == "performance":
            analyze_performance()
        elif module == "injury":
            injury_prediction()
        elif module == "career":
            career_planning()
        elif module == "nutrition":
            nutrition_planner()
        elif module == "finance":
            financial_planner()
        else:
            show_dashboard()
        return
    
    # Main application with sidebar
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",
            options=["Dashboard", "Performance", "Injury", "Career", "Nutrition", "Finance"],
            icons=["speedometer", "speedometer2", "bandaid", "graph-up", "nut", "cash-stack"],
            menu_icon="app-indicator",
            default_index=0
        )
    
    # Handle sidebar navigation
    if selected == "Dashboard":
        show_dashboard()
    elif selected == "Performance":
        analyze_performance()
    elif selected == "Injury":
        injury_prediction()
    elif selected == "Career":
        career_planning()
    elif selected == "Nutrition":
        nutrition_planner()
    elif selected == "Finance":
        financial_planner()
if __name__ == "__main__":
    main()