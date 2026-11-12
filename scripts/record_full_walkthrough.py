import os
import time
import subprocess
from playwright.sync_api import sync_playwright

VIDEO_DIR = "/tmp/elevance_walkthrough/video_raw"
os.makedirs(VIDEO_DIR, exist_ok=True)

# Sample invoice generation
invoice_path = "/tmp/elevance_walkthrough/test_invoice.png"
if not os.path.exists(invoice_path):
    from PIL import Image, ImageDraw, ImageFont
    inv = Image.new("RGB", (650, 420), color=(255, 255, 255))
    d = ImageDraw.Draw(inv)
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    d.text((40, 30), "ELEVANCE OFFICIAL INVOICE", fill=(15, 23, 42), font=font)
    d.text((40, 80), "Order ID: ORD-1111", fill=(15, 23, 42), font=font)
    d.text((40, 130), "Date: 2024-11-08", fill=(15, 23, 42), font=font)
    d.text((40, 180), "Product: Elevance Pro Headset", fill=(15, 23, 42), font=font)
    d.text((40, 230), "Total Billed: $350.00", fill=(15, 23, 42), font=font)
    d.text((40, 280), "Payment Status: SETTLED", fill=(16, 185, 129), font=font)
    inv.save(invoice_path)

durations = {
    "intro": 29.20,
    "chat": 56.49,
    "tickets": 42.57,
    "kb": 36.63,
    "ocr": 39.41,
    "time_metrics": 29.51
}

print("Starting Playwright live browser walkthrough recording...")

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        headless=True,
        args=["--disable-gpu", "--no-sandbox"]
    )
    context = browser.new_context(
        record_video_dir=VIDEO_DIR,
        record_video_size={"width": 1920, "height": 1080},
        viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()
    page.on("dialog", lambda dialog: dialog.accept())

    # ==================== 1. INTRO (29.2s) ====================
    print("Recording Section 1: Intro...")
    t0 = time.time()
    page.goto("http://127.0.0.1:8000")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Hover over branding and navigation tabs
    page.hover(".logo-group")
    time.sleep(2)
    page.hover("button[data-tab=\"tab-chat\"]")
    time.sleep(2)
    page.hover("button[data-tab=\"tab-tickets\"]")
    time.sleep(2)
    page.hover("button[data-tab=\"tab-kb\"]")
    time.sleep(2)
    page.hover("button[data-tab=\"tab-ocr\"]")
    time.sleep(2)
    page.hover("button[data-tab=\"tab-timemachine\"]")
    time.sleep(2)
    page.hover("#role-selector")
    time.sleep(2)
    page.hover("#tier-selector")
    time.sleep(2)
    # Wait until intro duration completes
    elapsed = time.time() - t0
    if elapsed < durations["intro"]:
        time.sleep(durations["intro"] - elapsed)

    # ==================== 2. CHAT TAB (56.5s) ====================
    print("Recording Section 2: Chat & Multilingual Sentiment...")
    t0 = time.time()
    # Ensure on chat tab
    page.click("button[data-tab=\"tab-chat\"]")
    time.sleep(1)

    # Sarcastic complaint
    page.click("button:has-text(\"Sarcastic Complaint\")")
    time.sleep(1)
    page.click(".chat-input-bar button")
    time.sleep(8)

    # Calm legal threat
    page.click("button:has-text(\"Calm Legal Threat\")")
    time.sleep(1)
    page.click(".chat-input-bar button")
    time.sleep(8)

    # Hinglish code switch
    page.click("button:has-text(\"Hinglish Code-Switch\")")
    time.sleep(1)
    page.click(".chat-input-bar button")
    time.sleep(8)

    # Unresolved 15m complaint
    page.click("button:has-text(\"Unresolved Complaint (>15m)\")")
    time.sleep(1)
    page.click(".chat-input-bar button")
    time.sleep(8)

    # Scroll through chat bubbles to showcase all responses
    page.evaluate("document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight")
    time.sleep(3)

    elapsed = time.time() - t0
    if elapsed < durations["chat"]:
        time.sleep(durations["chat"] - elapsed)

    # ==================== 3. TICKETS & SLA (42.6s) ====================
    print("Recording Section 3: Tickets & Dynamic SLA...")
    t0 = time.time()
    page.click("button[data-tab=\"tab-tickets\"]")
    time.sleep(3)

    # Scroll down table
    page.evaluate("window.scrollTo({top: 250, behavior: 'smooth'})")
    time.sleep(3)

    # View a handoff summary
    first_handoff = page.query_selector(".ticket-table button")
    if first_handoff:
        first_handoff.click()
        time.sleep(2)

    # Scroll down to Runtime SLA policy modification
    page.evaluate("window.scrollTo({top: 550, behavior: 'smooth'})")
    time.sleep(2)

    page.select_option("#sla-tier-select", "HIGH")
    time.sleep(1)
    page.fill("#sla-hours-input", "1.5")
    time.sleep(1)
    page.click("button:has-text(\"Apply Runtime SLA Change\")")
    time.sleep(3)

    # Scroll back up to see updated table
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    time.sleep(4)

    elapsed = time.time() - t0
    if elapsed < durations["tickets"]:
        time.sleep(durations["tickets"] - elapsed)

    # ==================== 4. KB PIPELINE (36.6s) ====================
    print("Recording Section 4: KB Pipeline & CI/CD...")
    t0 = time.time()
    page.click("button[data-tab=\"tab-kb\"]")
    time.sleep(3)

    # Quality Gate
    page.click("button:has-text(\"Run Automated Pre-Activation Quality Gate\")")
    time.sleep(5)

    # Scroll down to staged docs
    page.evaluate("window.scrollTo({top: 250, behavior: 'smooth'})")
    time.sleep(4)

    # Publish staged updates
    page.click("button:has-text(\"Publish Staged Updates\")")
    time.sleep(4)

    # Simulate canary failure
    page.click("button:has-text(\"Simulate 5-Min Canary Health Failure\")")
    time.sleep(4)

    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    time.sleep(3)

    elapsed = time.time() - t0
    if elapsed < durations["kb"]:
        time.sleep(durations["kb"] - elapsed)

    # ==================== 5. OCR LAB (39.4s) ====================
    print("Recording Section 5: Multimodal OCR Lab...")
    t0 = time.time()
    page.click("button[data-tab=\"tab-ocr\"]")
    time.sleep(3)

    # Set file input
    page.set_input_files("#ocr-file-input", invoice_path)
    time.sleep(2)
    page.fill("#ocr-customer-msg", "I was charged $450 for order ORD-1111")
    time.sleep(2)
    page.fill("#ocr-delay-input", "2")
    time.sleep(1)
    page.click("button:has-text(\"Run Multimodal OCR Analysis\")")
    time.sleep(6)

    # Trigger background queue (>30s)
    page.fill("#ocr-delay-input", "35")
    time.sleep(1)
    page.click("button:has-text(\"Run Multimodal OCR Analysis\")")
    time.sleep(5)

    elapsed = time.time() - t0
    if elapsed < durations["ocr"]:
        time.sleep(durations["ocr"] - elapsed)

    # ==================== 6. TIME MACHINE & OBSERVABILITY (29.5s) ====================
    print("Recording Section 6: Time Machine & Metrics...")
    t0 = time.time()
    page.click("button[data-tab=\"tab-timemachine\"]")
    time.sleep(3)

    # Advance time 4 hours to trigger after-hours
    adv_btns = page.query_selector_all("#tab-timemachine button")
    for btn in adv_btns:
        txt = btn.inner_text()
        if "+4 Hours" in txt or "After-Hours" in txt or "+1" in txt:
            btn.click()
            break
    time.sleep(4)

    # Scroll down to telemetry metrics
    page.evaluate("window.scrollTo({top: 350, behavior: 'smooth'})")
    time.sleep(6)

    # Scroll back up
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    time.sleep(3)

    elapsed = time.time() - t0
    if elapsed < durations["time_metrics"]:
        time.sleep(durations["time_metrics"] - elapsed)

    print("Walkthrough recording completed! Closing browser...")
    context.close()
    video_path = page.video.path()
    print("Raw recorded video at:", video_path)
    browser.close()

# Save recorded video path to file
with open("/tmp/elevance_walkthrough/raw_video_path.txt", "w") as f:
    f.write(video_path)

