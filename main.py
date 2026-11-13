import sys
from pathlib import Path

# Ensure project root is in sys.path so main.py runs from any working directory
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import load_shipments
from src.valuation import calculate_assessable_value
from src.duty_calculator import calculate_duties


def main():
    print("CUSTOMS DUTY AND IMPORT CLEARANCE ENGINE")
    print("----------------------------------------")

    shipments = load_shipments()

    for shipment in shipments:
        print(f"\nShipment ID: {shipment['shipment_id']}")

        assessable_value = calculate_assessable_value(
            invoice_value=shipment["invoice_value"],
            exchange_rate=shipment["exchange_rate"],
            incoterm=shipment["incoterm"],
            freight=shipment["freight"],
            insurance=shipment["insurance"]
        )

        duties = calculate_duties(
            assessable_value=assessable_value,
            bcd_rate=shipment["bcd_rate"],
            sws_rate=shipment["sws_rate"],
            igst_rate=shipment["igst_rate"]
        )

        print(f"Assessable Value: Rs. {assessable_value}")
        print("CUSTOMS DUTY BREAKDOWN")

        for duty, amount in duties.items():
            print(f"{duty}: Rs. {amount}")


if __name__ == "__main__":
    main()