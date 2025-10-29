# DL regiosport codefixer

Webapp die twee Colab-notebooks (“voetbal” en “overig”) achter één interface draait en een CUE-tekstbestand produceert.

## Lokale setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000.

## Bestanden toevoegen

- Plaats je notebooks in `notebooks/`:
  - `DL_amateursport_voetbal.ipynb`
  - `DL_amateursport_overig.ipynb`
- Plaats templates in `templates_src/`:
  - `Invulbestand_amateursport_voetbal.xlsx`
  - `Invulbestand_amateursport_overig.xlsx`

## Variabelen beschikbaar in notebooks
De app injecteert vóór de eerste cel deze variabelen:
```python
INPUT_XLSX  # pad naar het geüploade .xlsx
OUTPUT_TXT  # pad voor export .txt
MODE        # 'voetbal' of 'overig'
```

Zorg dat je notebook uit `INPUT_XLSX` leest en naar `OUTPUT_TXT` schrijft.

## Deploy op Render
1. Push deze map als GitHub-repo.
2. Render → New → Web Service → kies repo (detecteert `render.yaml`).
3. Na de build open de URL; upload Excel → “Maak CUE export (.txt)”.

## Troubleshooting
- Export ontbreekt: notebook schrijft niet naar `OUTPUT_TXT` → pas laatste cel aan.
- Langzame start: cold start on free plan.
