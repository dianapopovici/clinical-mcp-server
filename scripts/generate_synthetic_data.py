"""Generate a synthetic, read-only clinical data view for the MCP server.

Every record is fabricated with Faker (Italian locale). No real patient data
is present, referenced, or required. The output mirrors the *structure* of an
Italian clinical record (anamnesi / diagnosi / terapia) only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from faker import Faker

# Diagnosis -> plausible first-line therapy (illustrative, not medical advice).
DIAGNOSES = {
    "Ipertensione arteriosa essenziale": "Ramipril 5mg",
    "Diabete mellito tipo 2": "Metformina 850mg",
    "Broncopneumopatia cronica ostruttiva (BPCO)": "Salbutamolo inal.",
    "Scompenso cardiaco cronico": "Bisoprololo 2.5mg",
    "Fibrillazione atriale": "Apixaban 5mg",
    "Insufficienza renale cronica": "Controllo dietetico",
    "Ipotiroidismo": "Levotiroxina 75mcg",
    "Asma bronchiale": "Beclometasone inal.",
    "Gastrite cronica": "Pantoprazolo 20mg",
    "Dislipidemia": "Atorvastatina 20mg",
}

SYMPTOMS = [
    "cefalea persistente",
    "astenia marcata",
    "dispnea da sforzo",
    "palpitazioni",
    "edemi declivi",
    "poliuria",
    "tosse produttiva",
    "dolore toracico atipico",
]


def build_note(fake: Faker, age: int, sex: str, diagnosis: str, therapy: str) -> str:
    s1, s2 = fake.random_elements(elements=SYMPTOMS, length=2, unique=True)
    weeks = fake.random_int(min=2, max=12)
    return (
        f"ANAMNESI: Paziente di {age} anni, sesso {sex}, riferisce {s1}, {s2} "
        f"da circa {weeks} settimane. "
        f"DIAGNOSI: {diagnosis}. TERAPIA: {therapy}."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic clinical records")
    parser.add_argument("--records", type=int, default=200)
    parser.add_argument("--out", type=str, default="data/synthetic/clinical_records.json")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    fake = Faker("it_IT")
    Faker.seed(args.seed)

    diagnoses = list(DIAGNOSES.items())
    records = []
    for i in range(1, args.records + 1):
        age = fake.random_int(min=18, max=92)
        sex = fake.random_element(elements=("M", "F"))
        diagnosis, therapy = fake.random_element(elements=diagnoses)
        records.append(
            {
                "pseudo_id": f"PT-{i:04d}",
                "age": age,
                "sex": sex,
                "diagnosis": diagnosis,
                "therapy": therapy,
                "note": build_note(fake, age, sex, diagnosis, therapy),
            }
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] Wrote {len(records)} synthetic records -> {out}")
    print("[note] All data is synthetic. No real patient information is present.")


if __name__ == "__main__":
    main()
