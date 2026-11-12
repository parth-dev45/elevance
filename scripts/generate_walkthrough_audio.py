import os
import subprocess

AUDIO_DIR = "/tmp/elevance_walkthrough/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

scripts = [
    ("intro", "Welcome to the live interactive demonstration of the Elevance Enterprise Customer Support AI Platform. We are running our modern FastAPI web application locally at port 8000. Here on the main dashboard, you can see our top navigation bar connecting all five operational modules: Live Chat with Multilingual Sentiment, Tickets and Dynamic SLA Management, Knowledge Base Pipeline CI/CD, Multimodal OCR Lab, and the Virtual Time Machine with real-time telemetry."),
    ("chat", "Starting on the Live Chat tab, we demonstrate our real-time sentiment analysis and tone adaptation. First, we trigger a sarcastic complaint. Notice how our engine detects high sarcasm with ninety-four percent confidence, alongside customer frustration, dynamically adapting its response to be calm and empathetic while strictly preserving our return policies. Next, we test a calm legal threat. The system immediately activates our high-risk escalation engine, logging an audit trail and assigning the request to the on-call queue. Then, we demonstrate Hinglish code-switching. The customer asks 'Mera refund kab aayega for order ORD-9912?'. The engine accurately detects Hinglish, normalizes transliterated text, preserves the order ID, and responds contextually. Finally, we simulate a negative conversation exceeding fifteen minutes, which triggers an automated supervisor handoff."),
    ("tickets", "Switching over to the Tickets and Dynamic SLA tab, we see our live triage queue. Raw customer interactions have been automatically extracted into structured tickets, capturing customer details, order IDs, issue summaries, and multi-factor priority scores. Notice the real-time SLA consumption progress bars. Our engine excludes weekends and configured holidays, alerting at seventy-five percent time consumption and auto-escalating on breach. Here, we demonstrate our runtime SLA policy modification engine. By adjusting the high-priority tier down to one point five business hours and applying the change, all open tickets immediately recalculate their deadlines and trigger instant warning updates."),
    ("kb", "Next, in the Knowledge Base Pipeline tab, we inspect the automated CI/CD lifecycle. The system enforces deployment within our configured maintenance window between 1 AM and 5 AM. Before activating any update, we trigger the automated pre-activation quality gate. Notice that our semantic accuracy score reaches ninety-six percent and grounding reaches ninety-eight percent, easily clearing our quality thresholds. We can also simulate a five-minute canary health failure, which instantly triggers an automated rollback to our previous stable snapshot, safeguarding production availability."),
    ("ocr", "Now, let's explore the Multimodal OCR Lab. Here, we upload a customer invoice receipt for order ORD-1111 with a customer claim of four hundred and fifty dollars. When we run the analysis, the OCR engine extracts the invoice date, billed amount of three hundred and fifty dollars, and order code. The cross-validation engine instantly detects the discrepancy between the claimed four hundred and fifty dollars and the actual invoice total, generating a polite clarification prompt without hallucinating missing values. If processing exceeds thirty seconds, the system seamlessly moves the request to an asynchronous background worker."),
    ("time_metrics", "Finally, we enter the Virtual Time Machine and Metrics tab. Here we can simulate evaluation time-travel conditions, advancing the system clock by hours or days to test after-hours routing and weekend SLA boundaries in real time. We also observe live telemetry metrics: average latency of twelve milliseconds, total request throughput, and active escalation rates. All forty-one unit and integration tests are passing, and all code is published on GitHub. Thank you for watching.")
]

durations = {}

for name, text in scripts:
    aiff_path = os.path.join(AUDIO_DIR, f"{name}.aiff")
    m4a_path = os.path.join(AUDIO_DIR, f"{name}.m4a")
    subprocess.run(["say", "-v", "Rishi", "-r", "190", "-o", aiff_path, text], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", aiff_path, "-c:a", "aac", "-b:a", "128k", m4a_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", m4a_path], capture_output=True, text=True, check=True)
    dur = float(res.stdout.strip())
    durations[name] = dur
    print(f"{name}: {dur:.2f} seconds")

total_dur = sum(durations.values())
print(f"\nTOTAL AUDIO DURATION: {total_dur:.2f} seconds ({total_dur/60:.2f} minutes)")

with open(os.path.join(AUDIO_DIR, "durations.py"), "w") as f:
    f.write(f"DURATIONS = {durations}\n")

