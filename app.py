"""
Vireo Audio Support Intelligence & AI Triage Platform
Production-Grade Local Application Server (Port 8000)
"""

import os
import re
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import pandas as pd
import numpy as np

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKSPACE, "data")
OUTPUT_DIR = os.path.join(WORKSPACE, "analysis", "output")

# Load datasets and precompute models
print("Initializing Vireo Support Intelligence Engine...")

# Load pre-computed CSVs for instant loading
monthly_team_df = pd.read_csv(os.path.join(OUTPUT_DIR, "monthly_team_volume.csv")).fillna(0)
monthly_cat_df = pd.read_csv(os.path.join(OUTPUT_DIR, "monthly_category_volume.csv")).fillna(0)
staffing_scenarios_df = pd.read_csv(os.path.join(OUTPUT_DIR, "staffing_scenario.csv")).fillna('')

# Load validation metrics JSON
with open(os.path.join(OUTPUT_DIR, "human_validation_metrics.json"), "r", encoding="utf-8") as f:
    validation_metrics = json.load(f)

# Load tickets for Tab 4 Explorer (Jan 1, 2025 to Jun 30, 2026 reporting window)
raw_tickets = pd.read_csv(os.path.join(DATA_DIR, "tickets.csv"))
raw_agents = pd.read_csv(os.path.join(DATA_DIR, "agents.csv"))

raw_tickets['created_at_dt'] = pd.to_datetime(raw_tickets['created_at'])
raw_tickets['first_response_at_dt'] = pd.to_datetime(raw_tickets['first_response_at'])
raw_tickets['resolved_at_dt'] = pd.to_datetime(raw_tickets['resolved_at'])
raw_tickets['channel_clean'] = raw_tickets['channel'].str.strip().str.capitalize()

# Merge resolving agent info
raw_agents['start_dt'] = pd.to_datetime(raw_agents['from_date'])
raw_agents['end_dt'] = pd.to_datetime(raw_agents['to_date']).fillna(pd.to_datetime('2099-12-31'))

merged = pd.merge(raw_tickets, raw_agents, on='agent_id', how='left', suffixes=('', '_agent'))
valid_merged = merged[(merged['created_at_dt'] >= merged['start_dt']) & (merged['created_at_dt'] <= merged['end_dt'])].copy()

# Filter reporting window: 11,641 tickets
rep_mask = (valid_merged['created_at_dt'] >= '2025-01-01') & (valid_merged['created_at_dt'] <= '2026-06-30 23:59:59')
window_tickets = valid_merged[rep_mask].copy()

# Calculate SLA and resolution latencies
sla_targets = {'Chat': 15.0, 'Voice': 120.0, 'Social': 240.0, 'Email': 480.0}
window_tickets['first_response_min'] = (window_tickets['first_response_at_dt'] - window_tickets['created_at_dt']).dt.total_seconds() / 60.0
window_tickets['sla_target_min'] = window_tickets['channel_clean'].map(sla_targets)
window_tickets['sla_status'] = np.where(window_tickets['first_response_min'] > window_tickets['sla_target_min'], 'Breached', 'Met')
window_tickets['resolution_hours'] = (window_tickets['resolved_at_dt'] - window_tickets['created_at_dt']).dt.total_seconds() / 3600.0

# Prepare clean dictionary for quick filtering
explorer_records = []
for _, r in window_tickets.iterrows():
    res_hr = f"{r['resolution_hours']:.1f}h" if pd.notna(r['resolution_hours']) and r['resolution_hours'] >= 0 else "N/A"
    csat_str = f"{int(r['csat_score'])} ★" if pd.notna(r['csat_score']) and r['csat_score'] != '' else "—"
    explorer_records.append({
        "id": str(r['ticket_id']),
        "date": r['created_at'][:10],
        "channel": str(r['channel_clean']),
        "category": str(r['category']),
        "initial_team": str(r['assigned_team']),
        "resolving_team": str(r['team']),
        "sla_status": str(r['sla_status']),
        "resolution_time": res_hr,
        "csat": csat_str,
        "customer_message": str(r['customer_message']) if pd.notna(r['customer_message']) else '',
        "agent_notes": str(r['agent_notes']) if pd.notna(r['agent_notes']) else ''
    })

print(f"Loaded {len(explorer_records)} reporting window tickets into memory.")

# 10-Category Semantic Classification Engine
TAXONOMY_MAP = {
    "Delivery & Logistics": {
        "owning_team": "Logistics",
        "description": "Courier tracking, shipment delays, lost in transit, wrong item received, delivery attempts."
    },
    "Billing, Payments & Invoices": {
        "owning_team": "Billing",
        "description": "Payment gateway failures, double debits, GST invoice requests, coupon codes, price match."
    },
    "Returns & Refund Processing": {
        "owning_team": "Returns Desk",
        "description": "Return pickup scheduling, missed reverse pickups, return inspection status, return refund credit."
    },
    "Order Cancellation & Modification": {
        "owning_team": "Logistics / Frontline",
        "description": "Pre-dispatch cancellations, delivery address/pincode updates before warehouse dispatch."
    },
    "Hardware & Battery Defects": {
        "owning_team": "Frontline / Escalations",
        "description": "Battery draining, earbud not charging in case, device not turning on, physical/power defects."
    },
    "Audio Quality & Performance": {
        "owning_team": "Frontline",
        "description": "Static noise, crackling audio, microphone not working, sound distortion, low volume."
    },
    "Connectivity, App & Firmware": {
        "owning_team": "Frontline",
        "description": "Bluetooth pairing failure, device not discoverable, companion app bugs/crashes, firmware update hang."
    },
    "Warranty, RMA & Repair Claims": {
        "owning_team": "Escalations & Warranty",
        "description": "Formal warranty service, active RMA status tracking, service center logistics, warranty buyback."
    },
    "Account, Profile & Login": {
        "owning_team": "Frontline",
        "description": "OTP not arriving, login lockout, password resets, user profile updates, Care+ membership."
    },
    "Pre-Sales & Product Information": {
        "owning_team": "Frontline",
        "description": "Pre-purchase queries, specifications, IPX water resistance rating, compatibility with Mac/TV."
    }
}

def semantic_classify(customer_message: str, agent_notes: str = ""):
    """
    Transparent Hybrid Semantic Classifier.
    Evaluates customer intent, agent resolution actions, and flags payment-delivery keyword traps.
    """
    text = (customer_message + " " + agent_notes).lower()
    msg_only = customer_message.lower()
    notes_only = agent_notes.lower() if agent_notes else ""
    
    # Check for delivery vs payment keyword trap
    has_payment_words = bool(re.search(r'\b(paid|money|deducted|debited|amount|rs\.?|inr|bank|account|gateway|charged)\b', msg_only))
    has_delivery_intent = bool(re.search(r'\b(track|tracking|courier|shipment|delivery|deliver|arrived|received|package|parcel|awb|dispatch|dispatching|transit|out for delivery|not reached|still waiting|5 days|order not delivered)\b', text))
    has_pickup_intent = bool(re.search(r'\b(pickup|pick-up|reverse pickup|nobody came|return pickup|courier not visited)\b', text))
    has_refund_wait = bool(re.search(r'\b(refund.*promised|arn|utr|refund.*pending|return.*reached|where is.*refund|refund after return)\b', text))
    
    # 1. Reverse Pickup & Return Refund
    if has_pickup_intent or has_refund_wait or "reverse pkp" in text or "pickup not done" in text or "return qc" in text:
        evidence = "Matched return logistics / reverse pickup / return refund flow in notes & message."
        return {
            "category": "Returns & Refund Processing",
            "owning_team": "Returns Desk",
            "confidence": 0.94,
            "primary_evidence": evidence,
            "routing_recommendation": "Route to Returns Desk for reverse AWB tracking and return refund clearance.",
            "misrouting_warning": "Payment/refund keywords present, but issue is governed by reverse logistics / returns workflow." if has_payment_words else None
        }

    # 2. Delivery & Logistics (with Payment Keyword Misroute Trap Detection)
    if (has_payment_words and has_delivery_intent) or has_delivery_intent or "awb" in text or "lost in transit" in text or "wrong item" in text or "wrong color" in text:
        warning = None
        if has_payment_words:
            warning = "Potential Billing keyword misroute detected — payment language appears ('" + re.findall(r'\b(paid|money|deducted|debited|amount|rs\.?|inr|bank)\b', msg_only)[0] + "'), but root-cause is shipment transit / tracking."
        evidence = "Identified shipment transit / tracking inquiry ('" + (re.findall(r'\b(track|tracking|courier|shipment|delivery|deliver|arrived|received|package|parcel|awb|transit)\b', text) or ['delivery'])[0] + "')."
        return {
            "category": "Delivery & Logistics",
            "owning_team": "Logistics",
            "confidence": 0.96,
            "primary_evidence": evidence,
            "routing_recommendation": "Route directly to Logistics queue for carrier partner AWB escalation.",
            "misrouting_warning": warning
        }

    # 3. Order Cancellation & Modification (Pre-dispatch)
    if re.search(r'\b(cancel.*order|ordered by mistake|wrong address|change address|change pincode|update flat|wrong pin|cancel button greyed)\b', text) or "cancelled before dispatch" in text:
        return {
            "category": "Order Cancellation & Modification",
            "owning_team": "Logistics / Frontline",
            "confidence": 0.92,
            "primary_evidence": "Customer requested order cancellation or address modification prior to dispatch.",
            "routing_recommendation": "Route to Frontline / Logistics dispatch desk for manifest amendment.",
            "misrouting_warning": None
        }

    # 4. Billing, Payments & Invoices (Genuine payment issues)
    if re.search(r'\b(gst|gstin|invoice|tax invoice|coupon|promo code|double debit|duplicate deduction|charged twice|two times|arn|payment failed.*money deducted)\b', text) or "arn shared" in text or "gstin" in text:
        return {
            "category": "Billing, Payments & Invoices",
            "owning_team": "Billing",
            "confidence": 0.95,
            "primary_evidence": "Identified genuine financial / invoice / payment gateway query.",
            "routing_recommendation": "Route to Billing team for gateway ledger check or tax invoice generation.",
            "misrouting_warning": None
        }

    # 5. Warranty, RMA & Repair Claims
    if re.search(r'\b(rma\d+|claim number|service cent(er|re)|repair status|warranty claim|bengaluru service center|wty buyback)\b', text) or "esc to wty" in text or "rma" in text:
        return {
            "category": "Warranty, RMA & Repair Claims",
            "owning_team": "Escalations & Warranty",
            "confidence": 0.93,
            "primary_evidence": "Reference to active RMA claim number or authorized service center repair.",
            "routing_recommendation": "Route to Tier 2 Escalations & Warranty for RMA governance and replacement authorization.",
            "misrouting_warning": None
        }

    # 6. Connectivity, App & Firmware
    if re.search(r'\b(bluetooth|pair|pairing|connect|disconnect|ios 18|android 15|app crash|app not opening|firmware|update hang|reinstalled app|stuck at 50%|not discoverable)\b', text) or "bug logged" in text or "reset device" in text:
        return {
            "category": "Connectivity, App & Firmware",
            "owning_team": "Chat / Email Frontline",
            "confidence": 0.95,
            "primary_evidence": "Wireless Bluetooth handshake, firmware update, or companion app bug identified.",
            "routing_recommendation": "Route to Frontline Tier 1 for standard device reset and firmware troubleshooting SOP.",
            "misrouting_warning": None
        }

    # 7. Hardware & Battery Defects
    if re.search(r'\b(battery|drain|charging|case dead|left bud|right bud|no light|green light|power button|won\'t turn on|dead|not charging|hinge|headband|touch not responding)\b', text) or "battery draining fast" in text or "charging case dead" in text:
        return {
            "category": "Hardware & Battery Defects",
            "owning_team": "Frontline / Escalations",
            "confidence": 0.94,
            "primary_evidence": "Physical power supply, charging case LED, battery cell, or transducer hardware failure.",
            "routing_recommendation": "Route to Frontline Tier 1 for power cycle check, with Tier 2 escalation if DOA/hardware failure is confirmed.",
            "misrouting_warning": None
        }

    # 8. Audio Quality & Performance
    if re.search(r'\b(static|noise|crackling|buzzing|echo|mic|microphone|low volume|sound|distortion|bass|one side low|caller cannot hear|anc)\b', text) or "static noise" in text or "mic issue" in text:
        return {
            "category": "Audio Quality & Performance",
            "owning_team": "Frontline",
            "confidence": 0.93,
            "primary_evidence": "Acoustic distortion, driver imbalance, microphone transmission, or ANC performance query.",
            "routing_recommendation": "Route to Frontline Tier 1 for audio equalization and microphone diagnostic protocol.",
            "misrouting_warning": None
        }

    # 9. Account, Profile & Login
    if re.search(r'\b(otp|login|log in|lockout|locked out|password|reset code|care\+|care plus|mobile number|profile|verification code)\b', text) or "otp logs" in text:
        return {
            "category": "Account, Profile & Login",
            "owning_team": "Frontline",
            "confidence": 0.95,
            "primary_evidence": "Customer identity authentication, OTP SMS delivery, or profile subscription query.",
            "routing_recommendation": "Route to Frontline Tier 1 for OTP gateway log check and account unlock.",
            "misrouting_warning": None
        }

    # 10. Pre-Sales & Product Information
    if re.search(r'\b(compatible|compatibility|ipx|waterproof|shower|swimming|specs|specifications|battery life|tv|mac|iphone|two speakers|stereo|buy.*separately|spare)\b', text) or "spec sheet" in text or "compatibility" in text:
        return {
            "category": "Pre-Sales & Product Information",
            "owning_team": "Frontline",
            "confidence": 0.91,
            "primary_evidence": "Pre-purchase technical inquiry, compatibility verification, or product catalog question.",
            "routing_recommendation": "Route to Frontline Tier 1 for product datasheet and compatibility guidance.",
            "misrouting_warning": None
        }

    # Fallback
    return {
        "category": "Pre-Sales & Product Information",
        "owning_team": "Frontline",
        "confidence": 0.72,
        "primary_evidence": "General customer inquiry mapped to frontline triage queue.",
        "routing_recommendation": "Route to Frontline Tier 1 general triage queue.",
        "misrouting_warning": None
    }


class VireoAppHandler(BaseHTTPRequestHandler):
    def send_utf8(self, code, content_type, body):
        encoded = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ['/', '/index.html']:
            with open(os.path.join(WORKSPACE, 'app.html'), 'r', encoding='utf-8') as f:
                self.send_utf8(200, 'text/html; charset=utf-8', f.read())
        elif path == '/app.css':
            with open(os.path.join(WORKSPACE, 'app.css'), 'r', encoding='utf-8') as f:
                self.send_utf8(200, 'text/css; charset=utf-8', f.read())
        elif path == '/app.js':
            with open(os.path.join(WORKSPACE, 'app.js'), 'r', encoding='utf-8') as f:
                self.send_utf8(200, 'application/javascript; charset=utf-8', f.read())
        elif path == '/api/overview':
            # Format time series data for frontend chart
            months = monthly_team_df['year_month'].tolist()
            chart_data = {
                "months": months,
                "billing_intake": monthly_team_df['Billing_Initial_Assigned'].tolist(),
                "logistics_intake": monthly_team_df['Logistics_Initial_Assigned'].tolist(),
                "billing_resolving": monthly_team_df['Billing_Resolved'].tolist(),
                "logistics_resolving": monthly_team_df['Logistics_Resolved'].tolist(),
                "total_volume": monthly_team_df['Total_Tickets'].tolist()
            }
            payload = {
                "reporting_window": "1 Jan 2025 – 30 Jun 2026",
                "kpis": {
                    "reporting_volume": 11641,
                    "avg_monthly_volume": 646.7,
                    "sla_breach_cost": 452200,
                    "transfer_cost": 396195,
                    "contact_cost": 3182240,
                    "excluded_legacy_volume": 139
                },
                "billing_vs_logistics": {
                    "billing_intake": 2425,
                    "billing_intake_pct": 20.83,
                    "billing_intake_mo": 134.7,
                    "logistics_intake": 1905,
                    "logistics_intake_pct": 16.36,
                    "logistics_intake_mo": 105.8,
                    "billing_resolving": 1798,
                    "billing_resolving_pct": 15.45,
                    "billing_resolving_mo": 99.9,
                    "logistics_resolving": 2574,
                    "logistics_resolving_pct": 22.11,
                    "logistics_resolving_mo": 143.0,
                    "billing_to_logistics_count": 696,
                    "billing_to_logistics_pct": 28.70,
                    "logistics_to_billing_count": 35,
                    "logistics_to_billing_pct": 1.84,
                    "billing_median_latency": 1.23,
                    "logistics_median_latency": 26.16,
                    "billing_p90_latency": 48.80,
                    "logistics_p90_latency": 120.61,
                    "historical_transfer_spend": 396195,
                    "billing_transfer_share": 192760,
                    "billing_transfer_share_pct": 48.65,
                    "modeled_transfer_savings": 192760
                },
                "chart": chart_data,
                "validation": validation_metrics
            }
            self.send_utf8(200, 'application/json; charset=utf-8', json.dumps(payload))

        elif path == '/api/staffing':
            scenarios = staffing_scenarios_df.to_dict('records')
            self.send_utf8(200, 'application/json; charset=utf-8', json.dumps(scenarios))

        elif path == '/api/tickets':
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get('q', [''])[0].lower().strip()
            team_filter = query_params.get('team', [''])[0]
            cat_filter = query_params.get('category', [''])[0]
            chan_filter = query_params.get('channel', [''])[0]
            sla_filter = query_params.get('sla', [''])[0]
            page = int(query_params.get('page', ['1'])[0])
            limit = int(query_params.get('limit', ['25'])[0])

            filtered = explorer_records
            if q:
                filtered = [
                    t for t in filtered 
                    if q in t['id'].lower() or q in t['customer_message'].lower() or q in t['agent_notes'].lower()
                ]
            if team_filter:
                filtered = [t for t in filtered if t['resolving_team'] == team_filter or t['initial_team'] == team_filter]
            if cat_filter:
                filtered = [t for t in filtered if t['category'] == cat_filter]
            if chan_filter:
                filtered = [t for t in filtered if t['channel'].lower() == chan_filter.lower()]
            if sla_filter:
                filtered = [t for t in filtered if t['sla_status'].lower() == sla_filter.lower()]

            total_count = len(filtered)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            page_data = filtered[start_idx:end_idx]

            resp = {
                "total": total_count,
                "page": page,
                "limit": limit,
                "total_pages": int(np.ceil(total_count / limit)) if total_count > 0 else 1,
                "tickets": page_data
            }
            self.send_utf8(200, 'application/json; charset=utf-8', json.dumps(resp))
        else:
            self.send_utf8(404, 'text/plain; charset=utf-8', 'Not Found')

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/classify':
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                data = json.loads(body)
                cust_msg = data.get('customer_message', '')
                agent_notes = data.get('agent_notes', '')
                res = semantic_classify(cust_msg, agent_notes)
                self.send_utf8(200, 'application/json; charset=utf-8', json.dumps(res))
            except Exception as e:
                self.send_utf8(400, 'application/json; charset=utf-8', json.dumps({"error": str(e)}))
        else:
            self.send_utf8(404, 'text/plain; charset=utf-8', 'Not Found')

    def log_message(self, format, *args):
        pass


def run_app(port=8000):
    server = HTTPServer(('127.0.0.1', port), VireoAppHandler)
    print("="*70)
    print(f"VIREO AUDIO SUPPORT INTELLIGENCE & AI TRIAGE PLATFORM")
    print(f"Local Server running at http://127.0.0.1:{port}")
    print("="*70)
    server.serve_forever()


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_app(port)
