# DefibLab — Virtual Defibrillator Experiment

A mobile-friendly Streamlit prototype for a software-only biomedical engineering teaching lab.

## Features
- Emergency-room patient registration and simulated history/vitals
- Patient transfer to a treatment room
- Virtual defibrillator power and paddle connection controls
- Synthetic ECG waveforms for normal sinus rhythm, atrial fibrillation, and ventricular fibrillation
- Guided virtual electrode placement check
- Simulated mode and joule selection, charge, safety clearance, and shock sequence
- Before/after waveform comparison and observation table
- Five viva questions with scoring and explanations
- Downloadable patient summary (`.txt`) and experiment observations (`.csv`)

## Run locally in VS Code

Install Python 3.10 or newer, then open this folder in VS Code.

### Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit will show a local URL, usually `http://localhost:8501`. To test on a phone, the phone and computer must be on the same Wi-Fi network; run Streamlit with `streamlit run app.py --server.address 0.0.0.0` and open the computer's local IP plus `:8501` on the phone. Firewall settings may need adjustment.

## Safety and scope
This is an educational prototype only. It does not control medical equipment and is not for real patient care. ECG traces and post-intervention outcomes are synthetic illustrations. Real-world energy selection, synchronization, electrode placement, CPR, and rhythm management must follow current resuscitation guidance, device instructions, and qualified supervision. The simulated successful post-shock rhythm is deliberately not a prediction of real treatment success.
