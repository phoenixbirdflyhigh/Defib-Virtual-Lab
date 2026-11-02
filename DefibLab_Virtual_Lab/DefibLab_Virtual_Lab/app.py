
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="DefibLab | Virtual Defibrillator Experiment", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1150px;}
.hero {padding: 1.25rem; border-radius: 18px; background: linear-gradient(120deg,#211744,#3d2c70); color: white; margin-bottom: 1rem;}
.small-muted {color:#777; font-size:.9rem}
.step-card {padding: 1rem; border: 1px solid rgba(120,120,140,.3); border-radius: 14px; margin-bottom:.6rem;}
div.stButton > button {border-radius: 10px; min-height: 2.7rem; width:100%;}
</style>
""", unsafe_allow_html=True)

STAGES = ["Emergency Room", "Treatment Room", "Electrode Placement", "Defibrillator", "Post-treatment", "Viva & Report"]

def init_state():
    defaults = {
        "stage": 0, "patient": {}, "scenario": "Ventricular fibrillation (VF)",
        "vitals": {}, "device_on": False, "pads_connected": False,
        "pad_positions": {"Right upper chest": False, "Left lateral chest": False},
        "energy": 200, "mode": "Manual / unsynchronized", "charged": False,
        "safety_clear": False, "shock_delivered": False, "post_rhythm": None,
        "events": [], "viva_answers": {}, "report_generated": False
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def log_event(event):
    st.session_state.events.append({"Time": datetime.now().strftime("%H:%M:%S"), "Event": event})

def ecg_figure(rhythm, after=False):
    fs = 500
    t = np.linspace(0, 6, fs*6)
    rng = np.random.default_rng(12 if not after else 24)
    if rhythm == "Normal sinus rhythm":
        y = 0.025*np.sin(2*np.pi*0.25*t)
        for beat in np.arange(0.5, 6, 0.85):
            y += 0.10*np.exp(-((t-(beat-0.18))/0.045)**2)  # P
            y += -0.13*np.exp(-((t-(beat-0.035))/0.012)**2)
            y += 1.00*np.exp(-((t-beat)/0.014)**2)
            y += -0.25*np.exp(-((t-(beat+0.035))/0.018)**2)
            y += 0.28*np.exp(-((t-(beat+0.24))/0.09)**2)
    elif rhythm == "Atrial fibrillation (AF)":
        y = 0.035*np.sin(2*np.pi*5.2*t) + 0.02*np.sin(2*np.pi*7.1*t)
        beats = [0.45, 1.08, 1.53, 2.48, 3.10, 3.55, 4.38, 5.42]
        for beat in beats:
            y += -0.12*np.exp(-((t-(beat-0.025))/0.014)**2) + 0.85*np.exp(-((t-beat)/0.014)**2)
            y += -0.20*np.exp(-((t-(beat+0.03))/0.018)**2) + 0.20*np.exp(-((t-(beat+0.20))/0.08)**2)
    else:  # VF
        y = 0.32*np.sin(2*np.pi*5.1*t) + 0.20*np.sin(2*np.pi*7.8*t+0.4) + 0.10*np.sin(2*np.pi*12.5*t)
        y *= (0.8 + 0.2*np.sin(2*np.pi*0.18*t))
        y += rng.normal(0, 0.035, len(t))
    y += rng.normal(0, 0.008, len(t))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=y, mode="lines", line=dict(color="#48d6b5", width=1.5), name="ECG"))
    fig.update_layout(height=250, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="#101820", font_color="#e7edf4", showlegend=False,
                      xaxis_title="Time (s)", yaxis_title="Relative amplitude",
                      xaxis=dict(showgrid=True, gridcolor="#293743"), yaxis=dict(showgrid=True, gridcolor="#293743"))
    return fig

def current_rhythm():
    if st.session_state.shock_delivered:
        return st.session_state.post_rhythm or "Normal sinus rhythm"
    return st.session_state.scenario

def go_stage(n):
    st.session_state.stage = n

st.markdown("""
<div class="hero">
  <h1 style="margin:0">⚡ DefibLab</h1>
  <p style="margin:.35rem 0 0 0">Interactive virtual laboratory · Experiment 01: Study the Working of a Defibrillator</p>
  <p style="margin:.45rem 0 0 0;font-size:.88rem;opacity:.9">Educational simulation only — not connected to medical equipment and not for real patient care.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("Experiment navigation")
    for i, stage in enumerate(STAGES):
        label = ("✓ " if i < st.session_state.stage else ("➤ " if i == st.session_state.stage else "")) + f"{i+1}. {stage}"
        if st.button(label, key=f"nav_{i}"):
            # Allow navigation but don't bypass required actions silently.
            st.session_state.stage = i
            st.rerun()
    st.divider()
    st.caption("Progress")
    st.progress((st.session_state.stage+1)/len(STAGES))
    if st.button("↻ Reset experiment"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

stage = st.session_state.stage

if stage == 0:
    st.header("01 · Emergency room")
    st.write("Register the simulated patient, gather a brief history and choose the teaching scenario. Required fields are marked with *.")
    with st.form("patient_form"):
        c1,c2 = st.columns(2)
        with c1:
            name = st.text_input("Patient name / case ID *", value=st.session_state.patient.get("name",""))
            age = st.number_input("Age (years) *", min_value=0, max_value=120, value=int(st.session_state.patient.get("age",45)))
            sex = st.selectbox("Sex", ["Not specified","Female","Male","Intersex / another description"], index=0)
            symptoms = st.text_area("Presenting symptoms *", value=st.session_state.patient.get("symptoms",""), placeholder="e.g., collapse, unresponsive, palpitations")
        with c2:
            history = st.text_area("Relevant medical history / allergies", value=st.session_state.patient.get("history",""), placeholder="Enter known history or 'unknown'")
            bp = st.text_input("Blood pressure (simulated)", value=st.session_state.vitals.get("bp","90/60 mmHg"))
            spo2 = st.number_input("SpO₂ (%) (simulated)", min_value=0, max_value=100, value=int(st.session_state.vitals.get("spo2",92)))
            hr = st.number_input("Initial heart rate (bpm, simulated)", min_value=0, max_value=250, value=int(st.session_state.vitals.get("hr",180)))
        scenario = st.selectbox("ECG scenario for this experiment", ["Ventricular fibrillation (VF)", "Atrial fibrillation (AF)", "Normal sinus rhythm"], index=["Ventricular fibrillation (VF)","Atrial fibrillation (AF)","Normal sinus rhythm"].index(st.session_state.scenario))
        st.info("In real care, assess responsiveness, activate emergency response, and follow current BLS/ACLS protocols. This simulated form is for learning only.")
        submitted = st.form_submit_button("Save patient & transfer to treatment room", type="primary")
    if submitted:
        if not name.strip() or not symptoms.strip():
            st.error("Please enter a patient name/case ID and presenting symptoms.")
        else:
            st.session_state.patient = {"name":name.strip(),"age":age,"sex":sex,"symptoms":symptoms.strip(),"history":history.strip() or "Not provided"}
            st.session_state.vitals = {"bp":bp,"spo2":spo2,"hr":hr}
            st.session_state.scenario = scenario
            st.session_state.shock_delivered = False
            st.session_state.charged = False
            st.session_state.safety_clear = False
            log_event("Patient registered; scenario selected: "+scenario)
            st.session_state.stage = 1
            st.rerun()

elif stage == 1:
    st.header("02 · Treatment room")
    if not st.session_state.patient:
        st.warning("Register a patient in the Emergency Room first.")
        if st.button("Go to Emergency Room"): go_stage(0); st.rerun()
    else:
        p = st.session_state.patient
        st.success(f"Patient transferred: **{p['name']}** · Case scenario: **{st.session_state.scenario}**")
        c1,c2,c3 = st.columns(3)
        c1.metric("Heart rate", f"{st.session_state.vitals['hr']} bpm")
        c2.metric("Blood pressure", st.session_state.vitals["bp"])
        c3.metric("SpO₂", f"{st.session_state.vitals['spo2']}%")
        st.subheader("Equipment checklist")
        st.write("The original teaching experiment uses a DC defibrillator, ECG simulator, DSO/oscilloscope and two discharge paddles. This app simulates these components in software.")
        st.session_state.device_on = st.toggle("Switch ON virtual defibrillator", value=st.session_state.device_on)
        st.session_state.pads_connected = st.toggle("Connect virtual paddles / patient cable", value=st.session_state.pads_connected)
        if st.session_state.device_on and st.session_state.pads_connected:
            st.success("Device powered on and virtual paddles connected.")
            if st.button("Continue to electrode placement", type="primary"):
                log_event("Virtual defibrillator switched on; paddles connected")
                go_stage(2); st.rerun()
        else:
            st.warning("Switch on the device and connect the paddles to continue.")
        st.plotly_chart(ecg_figure(st.session_state.scenario), use_container_width=True)
        st.caption("Synthetic teaching waveform — not a diagnostic ECG.")

elif stage == 2:
    st.header("03 · Electrode placement")
    st.write("Select each landmark on the virtual chest. The app checks the selected landmarks before allowing you to continue.")
    st.warning("Training illustration only. Follow the actual device manufacturer's instructions and your institution's current protocol in clinical practice.")
    # A simplified clickable schematic
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0.8,y0=0.2,x1=4.2,y1=5.7,line=dict(color="#9aa7b5",width=2),fillcolor="#d7b9a1")
    fig.add_shape(type="circle",x0=1.8,y0=5.0,x1=3.2,y1=6.2,line=dict(color="#9aa7b5"),fillcolor="#d7b9a1")
    fig.add_shape(type="circle",x0=1.55,y0=3.3,x1=2.1,y1=3.85,line=dict(color="#b55c65",width=2),fillcolor="#ef8b92")
    fig.add_shape(type="circle",x0=3.0,y0=1.8,x1=3.55,y1=2.35,line=dict(color="#b55c65",width=2),fillcolor="#ef8b92")
    fig.add_annotation(x=1.83,y=3.55,text="A",showarrow=True,arrowhead=2,ax=-65,ay=-15,font=dict(color="#222"))
    fig.add_annotation(x=3.27,y=2.08,text="B",showarrow=True,arrowhead=2,ax=65,ay=10,font=dict(color="#222"))
    fig.update_layout(height=380, margin=dict(l=0,r=0,t=10,b=0), showlegend=False,
                      xaxis=dict(visible=False,range=[0,5]),yaxis=dict(visible=False,range=[0,6.5]),
                      paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    c1,c2 = st.columns([1,1])
    with c1:
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Schematic only; not to scale. A and B indicate the two intended training landmarks.")
    with c2:
        st.markdown("**Landmark A — upper right chest**")
        a = st.selectbox("Choose location for paddle A", ["Select a location","Upper right chest, below clavicle and to the right of sternum","Left lateral chest","Centre of sternum","Lower abdomen"], key="loc_a")
        st.markdown("**Landmark B — left lateral chest**")
        b = st.selectbox("Choose location for paddle B", ["Select a location","Left lateral chest, below armpit","Upper right chest, below clavicle","Centre of sternum","Lower abdomen"], key="loc_b")
        correct = (a == "Upper right chest, below clavicle and to the right of sternum" and b == "Left lateral chest, below armpit")
        if correct:
            st.success("Both virtual electrode locations are correct for this simplified anterolateral training setup.")
        elif a != "Select a location" or b != "Select a location":
            st.error("At least one landmark is incorrect. Review the labels and try again.")
        if st.button("Confirm placement & continue", type="primary", disabled=not correct):
            st.session_state.pad_positions = {"Right upper chest":True,"Left lateral chest":True}
            log_event("Correct simulated anterolateral electrode placement")
            go_stage(3); st.rerun()

elif stage == 3:
    st.header("04 · Defibrillator controls")
    st.write("Choose the operating mode, set a training energy level, charge the device, complete the safety check and deliver a simulated intervention only when indicated.")
    rhythm = st.session_state.scenario
    if rhythm == "Ventricular fibrillation (VF)":
        recommended_mode = "Manual / unsynchronized"
        indication = "VF is a shockable rhythm in this educational scenario. The simulation uses unsynchronized defibrillation."
    elif rhythm == "Atrial fibrillation (AF)":
        recommended_mode = "Synchronized cardioversion"
        indication = "AF may require synchronized cardioversion in selected clinical situations. This scenario is educational and does not determine real treatment."
    else:
        recommended_mode = "No shock indicated"
        indication = "Normal sinus rhythm is not an indication for a shock in this scenario."
    st.info(indication)
    st.plotly_chart(ecg_figure(rhythm), use_container_width=True)
    st.caption("ECG before simulated intervention")
    st.session_state.mode = st.radio("Operating mode", ["Manual / unsynchronized","Synchronized cardioversion","No shock indicated"],
                                      index=["Manual / unsynchronized","Synchronized cardioversion","No shock indicated"].index(st.session_state.mode if st.session_state.mode in ["Manual / unsynchronized","Synchronized cardioversion","No shock indicated"] else recommended_mode))
    st.session_state.energy = st.select_slider("Select training energy (J)", options=[50,70,100,120,150,200,250,300,360], value=int(st.session_state.energy))
    st.caption("Energy values are exposed for the educational experiment only. Appropriate settings depend on device type, waveform, rhythm and current protocol; do not use this simulator to choose treatment for a real patient.")
    if rhythm == "Normal sinus rhythm" or st.session_state.mode == "No shock indicated":
        st.warning("This scenario should be completed without delivering a shock. Demonstrate the controls and proceed to the assessment.")
        if st.button("Complete no-shock scenario", type="primary"):
            st.session_state.shock_delivered = True
            st.session_state.post_rhythm = "Normal sinus rhythm"
            log_event("No shock delivered: scenario not shock-indicated")
            go_stage(4); st.rerun()
    else:
        if st.button("1. Charge device", type="primary"):
            st.session_state.charged = True
            st.session_state.safety_clear = False
            log_event(f"Device charged to simulated setting {st.session_state.energy} J")
            st.rerun()
        if st.session_state.charged:
            st.success(f"Virtual device charged to {st.session_state.energy} J.")
            st.session_state.safety_clear = st.checkbox("Safety check: announce clear, ensure nobody is touching the patient/bed, and confirm the scene is clear.", value=st.session_state.safety_clear)
            mode_ok = (rhythm == "Ventricular fibrillation (VF)" and st.session_state.mode == "Manual / unsynchronized") or (rhythm == "Atrial fibrillation (AF)" and st.session_state.mode == "Synchronized cardioversion")
            if not mode_ok:
                st.error("The selected mode does not match this teaching scenario. Review the scenario and mode before proceeding.")
            if st.button("2. Deliver simulated shock", type="primary", disabled=not (st.session_state.safety_clear and mode_ok)):
                st.session_state.shock_delivered = True
                st.session_state.charged = False
                if rhythm == "Ventricular fibrillation (VF)":
                    st.session_state.post_rhythm = "Normal sinus rhythm" # simplified illustrative outcome
                    log_event(f"Simulated unsynchronized shock delivered at {st.session_state.energy} J; post-shock rhythm shown for teaching")
                else:
                    st.session_state.post_rhythm = "Normal sinus rhythm"
                    log_event(f"Simulated synchronized cardioversion at {st.session_state.energy} J; post-intervention rhythm shown for teaching")
                go_stage(4); st.rerun()

elif stage == 4:
    st.header("05 · Post-treatment observation")
    if not st.session_state.shock_delivered:
        st.warning("Complete the simulated intervention first.")
        if st.button("Return to defibrillator controls"): go_stage(3); st.rerun()
    else:
        before = st.session_state.scenario
        after = st.session_state.post_rhythm or "Normal sinus rhythm"
        c1,c2 = st.columns(2)
        with c1:
            st.subheader("Before")
            st.plotly_chart(ecg_figure(before), use_container_width=True)
            st.caption(before)
        with c2:
            st.subheader("After (simulated)")
            st.plotly_chart(ecg_figure(after, after=True), use_container_width=True)
            st.caption(after)
        st.info("The post-intervention waveform is a predetermined educational illustration, not a prediction of real treatment success. In real VF/pulseless VT, immediately resume CPR and follow the current resuscitation algorithm; reassess rhythm as directed.")
        st.subheader("Observation table")
        table = pd.DataFrame([{
            "Initial rhythm": before,
            "Mode": st.session_state.mode,
            "Selected energy (J)": st.session_state.energy,
            "Initial heart rate (bpm)": st.session_state.vitals.get("hr","—"),
            "Post-simulation rhythm": after,
            "Shock delivered": "Yes" if before != "Normal sinus rhythm" and st.session_state.mode != "No shock indicated" else "No"
        }])
        st.dataframe(table, use_container_width=True, hide_index=True)
        if st.button("Proceed to viva & patient summary", type="primary"):
            go_stage(5); st.rerun()

elif stage == 5:
    st.header("06 · Viva & patient summary")
    st.write("Answer the viva questions to check your understanding. The score is educational and does not certify clinical competence.")
    questions = [
        ("What is the main purpose of a defibrillator?", ["To measure blood pressure","To deliver a controlled electrical shock for certain life-threatening arrhythmias","To provide oxygen","To record body temperature"], 1,
         "A defibrillator delivers a controlled electrical shock to treat selected shockable arrhythmias."),
        ("Which rhythm in this lab is treated as shockable?", ["Normal sinus rhythm","Ventricular fibrillation (VF)","A normal ECG","All rhythms"], 1,
         "VF is a shockable rhythm. Not every abnormal rhythm requires a shock."),
        ("Why is synchronized mode used for selected cardioversion procedures?", ["To time the shock with the QRS complex","To increase heart rate continuously","To measure SpO₂","To turn off the ECG"], 0,
         "Synchronization aims to deliver the shock in relation to the QRS complex and avoid vulnerable timing."),
        ("What must the operator confirm immediately before a simulated shock?", ["That nobody is touching the patient and the area is clear","That the room lights are off","That the ECG cable is removed in every case","That the patient is standing"], 0,
         "A clear-scene safety check is essential in the simulation and in real procedures."),
        ("What should be done immediately after a shock for VF/pulseless VT in a real resuscitation scenario?", ["Stop all care and leave","Resume CPR promptly and follow the current resuscitation algorithm","Give a drink of water","Wait several minutes without reassessment"], 1,
         "Follow current BLS/ACLS guidance; after a shock for VF/pulseless VT, CPR is resumed promptly.")
    ]
    with st.form("viva_form"):
        answers = {}
        for i,(q,opts,correct,explain) in enumerate(questions):
            answers[i] = st.radio(f"{i+1}. {q}", opts, index=None, key=f"viva_{i}")
        submitted = st.form_submit_button("Submit viva answers", type="primary")
    if submitted:
        if any(v is None for v in answers.values()):
            st.error("Please answer all questions before submitting.")
        else:
            score = sum(answers[i] == questions[i][1][questions[i][2]] for i in range(len(questions)))
            st.session_state.viva_answers = {"answers":answers,"score":score,"total":len(questions)}
            log_event(f"Viva completed: {score}/{len(questions)}")
            st.rerun()
    if st.session_state.viva_answers:
        va = st.session_state.viva_answers
        st.metric("Viva score", f"{va['score']} / {va['total']}", f"{round(100*va['score']/va['total'])}%")
        with st.expander("Review answers and explanations", expanded=True):
            for i,(q,opts,correct,explain) in enumerate(questions):
                is_correct = va["answers"][i] == opts[correct]
                st.markdown(f"**{i+1}. {'Correct' if is_correct else 'Review'}** — {q}")
                st.write(f"Correct answer: {opts[correct]}")
                st.caption(explain)
        st.subheader("Patient summary")
        p = st.session_state.patient
        v = st.session_state.vitals
        summary = f"""DEFIBLAB — VIRTUAL LAB PATIENT SUMMARY
Experiment: Study the Working of a Defibrillator
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
SIMULATION ONLY — NOT A CLINICAL RECORD

Patient/case ID: {p.get('name','—')}
Age: {p.get('age','—')}
Sex: {p.get('sex','—')}
Presenting symptoms: {p.get('symptoms','—')}
Relevant history/allergies: {p.get('history','—')}

Initial simulated observations:
Heart rate: {v.get('hr','—')} bpm
Blood pressure: {v.get('bp','—')}
SpO2: {v.get('spo2','—')}%

Scenario: {st.session_state.scenario}
Operating mode selected: {st.session_state.mode}
Selected training energy: {st.session_state.energy} J
Virtual paddles connected: {st.session_state.pads_connected}
Electrode placement verified: {all(st.session_state.pad_positions.values())}
Simulated intervention completed: {st.session_state.shock_delivered}
Post-simulation rhythm: {st.session_state.post_rhythm or 'Not recorded'}

Viva score: {va['score']}/{va['total']} ({round(100*va['score']/va['total'])}%)

Important: ECGs and treatment outcomes are synthetic illustrations. This report must not be used for diagnosis, treatment, or clinical decision-making.
"""
        st.text_area("Summary preview", summary, height=380)
        st.download_button("Download patient summary (.txt)", summary, file_name="defiblab_patient_summary.txt", mime="text/plain")
        st.download_button("Download experiment observations (.csv)", pd.DataFrame([{
            "Patient/case ID":p.get("name",""),"Age":p.get("age",""),"Scenario":st.session_state.scenario,
            "Mode":st.session_state.mode,"Energy_J":st.session_state.energy,
            "Initial_HR_bpm":v.get("hr",""),"Initial_BP":v.get("bp",""),"Initial_SpO2":v.get("spo2",""),
            "Post_simulation_rhythm":st.session_state.post_rhythm or "",
            "Viva_score":va["score"],"Viva_total":va["total"]
        }]).to_csv(index=False), file_name="defiblab_observations.csv", mime="text/csv")
        with st.expander("Experiment event log"):
            st.dataframe(pd.DataFrame(st.session_state.events), use_container_width=True, hide_index=True)
        if st.button("Start a new patient experiment"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

st.divider()
st.caption("DefibLab is a software-only educational prototype. It does not connect to a real defibrillator, ECG, or patient. All vitals, waveforms, and outcomes are simulated.")
