import os
import sys
from pathlib import Path
from decimal import Decimal
from flask import Flask, render_template, jsonify, request, send_file

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.engine import CustomsAssessmentEngine, fmt_money, round_rupee

app = Flask(__name__)

# Initialize engine and load dataset
engine = CustomsAssessmentEngine()
engine.load_all_data()
# Run initial simulation so all assessed records and challans are pre-computed
engine.process_command_file(PROJECT_ROOT / "commands" / "commands.txt")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def get_stats():
    total_bills = len(engine.bills)
    total_lines = len(engine.bill_lines)
    total_importers = len(engine.importers)
    
    total_av = sum(c["total_av"] for c in engine.challans.values())
    total_duty = sum(c["total_duty"] for c in engine.challans.values())
    total_collected = sum(c["total_paid"] for c in engine.challans.values())
    total_interest = sum(c["interest"] for c in engine.challans.values())
    total_penalties = sum(c["penalty"] for c in engine.challans.values())
    
    channels = {"GREEN": 0, "ORANGE": 0, "RED": 0}
    for c in engine.challans.values():
        ch = c["channel"]
        channels[ch] = channels.get(ch, 0) + 1
        
    ports = {}
    for b in engine.bills.values():
        p = b["port_code"]
        ports[p] = ports.get(p, 0) + 1
        
    # Duty component breakdown across all lines
    duty_components = {
        "bcd": float(sum(r["bcd"] for r in engine.assessed_lines_record.values())),
        "sws": float(sum(r["sws"] for r in engine.assessed_lines_record.values())),
        "antidumping": float(sum(r["antidumping"] for r in engine.assessed_lines_record.values())),
        "igst": float(sum(r["igst"] for r in engine.assessed_lines_record.values())),
        "cess": float(sum(r["cess"] for r in engine.assessed_lines_record.values()))
    }

    return jsonify({
        "total_bills": total_bills,
        "total_lines": total_lines,
        "total_importers": total_importers,
        "total_av": float(total_av),
        "total_duty": float(total_duty),
        "total_collected": float(total_collected),
        "total_interest": float(total_interest),
        "total_penalties": float(total_penalties),
        "channels": channels,
        "ports": ports,
        "duty_components": duty_components
    })

@app.route("/api/bills")
def get_bills():
    bills_list = []
    for bid, b in sorted(engine.bills.items()):
        c = engine.challans.get(bid, {})
        imp = engine.importers.get(b["importer_id"], {})
        
        # Calculate line count
        lines_count = sum(1 for (k_bid, _) in engine.bill_lines.keys() if k_bid == bid)
        
        bills_list.append({
            "bill_id": bid,
            "importer_id": b["importer_id"],
            "importer_name": imp.get("importer_name", ""),
            "port_code": b["port_code"],
            "vessel_arrival_date": b["vessel_arrival_date"],
            "filing_ts": b["filing_ts"],
            "bill_date": b["bill_date"],
            "total_packages": b["total_packages"],
            "customs_system_delay": b["customs_system_delay"],
            "random_red_flag": b["random_red_flag"],
            "status": c.get("status", b["status"]),
            "channel": c.get("channel", "PENDING"),
            "channel_reason": c.get("channel_reason", ""),
            "total_av": float(c.get("total_av", 0)),
            "total_duty": float(c.get("total_duty", 0)),
            "late_filing_charge": float(c.get("late_filing_charge", 0)),
            "interest": float(c.get("interest", 0)),
            "penalty": float(c.get("penalty", 0)),
            "total_payable": float(c.get("total_payable", 0)),
            "total_paid": float(c.get("total_paid", 0)),
            "outstanding": float(c.get("outstanding", 0)),
            "line_count": lines_count
        })
    return jsonify(bills_list)

@app.route("/api/bills/<bill_id>")
def get_bill_detail(bill_id):
    if bill_id not in engine.bills:
        return jsonify({"error": "Bill not found"}), 404
        
    b = engine.bills[bill_id]
    c = engine.challans.get(bill_id, {})
    imp = engine.importers.get(b["importer_id"], {})
    
    lines = []
    for (k_bid, lno), line_raw in sorted(engine.bill_lines.items()):
        if k_bid == bill_id:
            calc = engine.assessed_lines_record.get((bill_id, lno), {})
            tariff = engine.tariffs.get(line_raw["hs_code"], {})
            lines.append({
                "line_no": lno,
                "hs_code": line_raw["hs_code"],
                "description": line_raw["description"],
                "quantity": line_raw["quantity"],
                "unit": line_raw["unit"],
                "invoice_value": float(line_raw["invoice_value"]),
                "currency": line_raw["currency"],
                "incoterm": line_raw["incoterm"],
                "freight": float(line_raw["freight"]),
                "insurance": float(line_raw["insurance"]) if line_raw["insurance"] is not None else None,
                "origin_country": line_raw["origin_country"],
                "coo_flag": line_raw["coo_flag"],
                "value_addition_pct": float(line_raw["value_addition_pct"]),
                "auth_id": line_raw["auth_id"],
                "notification_id": line_raw["notification_id"],
                # Calculation results
                "exchange_rate": float(calc.get("exchange_rate", 1)),
                "fob_inr": float(calc.get("fob_inr", 0)),
                "freight_inr": float(calc.get("freight_inr", 0)),
                "insurance_inr": float(calc.get("insurance_inr", 0)),
                "cif_inr": float(calc.get("cif_inr", 0)),
                "landing_inr": float(calc.get("landing_inr", 0)),
                "av": float(calc.get("av", 0)),
                "bcd_basis": calc.get("bcd_basis", "STANDARD"),
                "bcd_rate": float(calc.get("bcd_rate", 0)),
                "bcd": float(calc.get("bcd", 0)),
                "sws": float(calc.get("sws", 0)),
                "antidumping": float(calc.get("antidumping", 0)),
                "igst_base": float(calc.get("igst_base", 0)),
                "igst_rate": float(tariff.get("igst_rate", 18)),
                "igst": float(calc.get("igst", 0)),
                "cess_rate": float(tariff.get("cess_rate", 0)),
                "cess": float(calc.get("cess", 0)),
                "line_duty": float(calc.get("line_duty", 0)),
                "scheme_exempt_qty": calc.get("scheme_exempt_qty", 0)
            })
            
    return jsonify({
        "bill": {
            "bill_id": bill_id,
            "importer_id": b["importer_id"],
            "importer_name": imp.get("importer_name", ""),
            "iec": imp.get("iec", ""),
            "aeo_status": imp.get("aeo_status", "NONE"),
            "compliance_score": imp.get("compliance_score", 0),
            "port_code": b["port_code"],
            "vessel_arrival_date": b["vessel_arrival_date"],
            "filing_ts": b["filing_ts"],
            "bill_date": b["bill_date"],
            "total_packages": b["total_packages"],
            "customs_system_delay": b["customs_system_delay"],
            "random_red_flag": b["random_red_flag"]
        },
        "challan": {
            "status": c.get("status", "PENDING"),
            "channel": c.get("channel", "PENDING"),
            "channel_reason": c.get("channel_reason", ""),
            "assessment_ts": c.get("assessment_ts", ""),
            "total_av": float(c.get("total_av", 0)),
            "total_duty": float(c.get("total_duty", 0)),
            "late_filing_charge": float(c.get("late_filing_charge", 0)),
            "interest": float(c.get("interest", 0)),
            "differential_duty": float(c.get("differential_duty", 0)),
            "penalty": float(c.get("penalty", 0)),
            "total_payable": float(c.get("total_payable", 0)),
            "total_paid": float(c.get("total_paid", 0)),
            "outstanding": float(c.get("outstanding", 0))
        },
        "lines": lines
    })

@app.route("/api/importers")
def get_importers():
    importers_list = []
    for imp_id, imp in sorted(engine.importers.items()):
        # Count bills for this importer
        bills_count = sum(1 for b in engine.bills.values() if b["importer_id"] == imp_id)
        importers_list.append({
            "importer_id": imp_id,
            "importer_name": imp["importer_name"],
            "iec": imp["iec"],
            "city": imp["city"],
            "aeo_status": imp["aeo_status"],
            "compliance_score": imp["compliance_score"],
            "forced_red_until": imp["forced_red_until"],
            "bills_count": bills_count
        })
    return jsonify(importers_list)

@app.route("/api/compliance_ledger")
def get_compliance_ledger():
    return jsonify(engine.compliance_ledger)

@app.route("/api/tariffs")
def get_tariffs():
    tariff_list = []
    for hs, t in sorted(engine.tariffs.items()):
        tariff_list.append({
            "hs_code": hs,
            "description": t["description"],
            "unit": t["unit"],
            "bcd_rate": float(t["bcd_rate"]),
            "igst_rate": float(t["igst_rate"]),
            "cess_rate": float(t["cess_rate"]),
            "fta_rate": float(t["fta_rate"]),
            "sensitive": t["sensitive"]
        })
    return jsonify(tariff_list)

@app.route("/api/calculate", methods=["POST"])
def calculate_sandbox():
    data = request.json or {}
    try:
        hs_code = data.get("hs_code", "84711000")
        qty = int(data.get("quantity", 10))
        inv_val = Decimal(str(data.get("invoice_value", 1000)))
        curr = data.get("currency", "USD").upper()
        incoterm = data.get("incoterm", "FOB").upper()
        freight = Decimal(str(data.get("freight", 150)))
        ins_raw = data.get("insurance")
        insurance = Decimal(str(ins_raw)) if ins_raw not in (None, "") else None
        rate = Decimal(str(data.get("exchange_rate", 84.04)))
        origin = data.get("origin_country", "US").upper()
        coo_flag = bool(data.get("coo_flag", False))
        val_add = Decimal(str(data.get("value_addition_pct", 40)))
        
        tariff = engine.tariffs.get(hs_code, {
            "description": "Custom Item",
            "unit": "NOS",
            "bcd_rate": Decimal("10"),
            "igst_rate": Decimal("18"),
            "cess_rate": Decimal("0"),
            "fta_rate": Decimal("5"),
            "sensitive": False
        })
        
        dummy_line = {
            "bill_id": "DEMO-001",
            "line_no": 1,
            "hs_code": hs_code,
            "description": tariff["description"],
            "quantity": qty,
            "unit": tariff["unit"],
            "invoice_value": inv_val,
            "currency": curr,
            "incoterm": incoterm,
            "freight": freight,
            "insurance": insurance,
            "origin_country": origin,
            "coo_flag": coo_flag,
            "coo_date": "2026-10-15",
            "value_addition_pct": val_add,
            "notification_id": "",
            "bond_flag": False,
            "auth_id": ""
        }
        
        # Override exchange rate for simulation
        engine.exchange_rates[("2026-10-15", curr)] = rate
        calc = engine.assess_line(dummy_line, "2026-10-15")
        
        return jsonify({
            "status": "success",
            "fob_inr": float(calc["fob_inr"]),
            "freight_inr": float(calc["freight_inr"]),
            "insurance_inr": float(calc["insurance_inr"]),
            "cif_inr": float(calc["cif_inr"]),
            "landing_inr": float(calc["landing_inr"]),
            "av": float(calc["av"]),
            "bcd_basis": calc["bcd_basis"],
            "bcd_rate": float(calc["bcd_rate"]),
            "bcd": float(calc["bcd"]),
            "sws": float(calc["sws"]),
            "antidumping": float(calc["antidumping"]),
            "igst_base": float(calc["igst_base"]),
            "igst": float(calc["igst"]),
            "cess": float(calc["cess"]),
            "line_duty": float(calc["line_duty"])
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/simulate", methods=["POST"])
def rerun_simulation():
    global engine
    engine = CustomsAssessmentEngine()
    engine.load_all_data()
    engine.process_command_file(PROJECT_ROOT / "commands" / "commands.txt")
    return jsonify({
        "status": "success",
        "message": "Engine simulation re-executed successfully",
        "assessed_lines": len(engine.assessed_lines_record),
        "challans_generated": len(engine.challans),
        "ledger_entries": len(engine.compliance_ledger),
        "errors_count": len(engine.errors)
    })

@app.route("/api/download/<filename>")
def download_report(filename):
    allowed_files = ["assessment_lines.csv", "challans.csv", "compliance_ledger.csv", "errors.csv"]
    if filename not in allowed_files:
        return jsonify({"error": "File not found"}), 404
    filepath = engine.output_dir / filename
    if not filepath.exists():
        return jsonify({"error": "File has not been generated yet"}), 404
    return send_file(str(filepath), as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Customs Duty Assessment Engine Web Server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
