# Agent instructions

- This repository holds **fictional** dummy data for the Zenn × Microsoft Fabric article contest, plus the generator.
- Never hand-edit files under `data/`. Change the generator (`generator/contoso_data/*`) and regenerate:
  `cd generator && python generate.py --out ../data --organizer-out ../_organizer_only/expected_outputs`,
  then `python tools/build_docs.py` and `python tools/validate.py` (must print `ALL OK`).
- `tools/build_docs.py` fails when a CSV column has no description; add descriptions there when adding columns.
- Data conventions: UTF-8 without BOM, LF, JST timestamps `YYYY-MM-DD HH:MM:SS`, English snake_case columns, single-column primary keys where possible.
- `_organizer_only/` contains the answer key (embedded scenarios); keep it out of participant distributions.
- Keep each data file under 50 MB (GitHub limit 100 MB); split large tables by year/month into a per-table folder.
