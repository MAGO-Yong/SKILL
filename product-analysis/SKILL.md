---
name: product-analysis
description: Analyze product survey/questionnaire data to extract user insights, segment users, map journey pain points, and produce structured product planning reports. Use when: (1) a user uploads a survey Excel/CSV file and asks for analysis, (2) you need to identify valid vs. invalid responses and quality-tier respondents, (3) you need to map user journeys or usage patterns from open-ended responses, (4) you need to define and prioritize product features or capabilities (e.g., Skills/APIs) based on real user feedback, (5) the user asks to "analyze this questionnaire," "help me understand what users want," or "turn this survey into a product plan."
---

# Product Analysis

Analyze product survey/questionnaire data from a product manager perspective. Extract user insights, map journeys, and produce structured product planning decisions.

## Workflow

Follow this sequence:

1. Parse & clean the data
2. Filter invalid responses
3. Quality-tier valid responses
4. User segmentation (by usage pattern, not just role)
5. Journey mapping and pain point extraction
6. Feature/capability frequency analysis with cross-validation
7. Produce structured report
8. (Optional) Create atomic/composite/scenario skill definitions

See `references/analysis-framework.md` for detailed methodology.
See `references/skill-design-principles.md` for Agent Native skill design (atomic/composite/scenario layers).

## Data Parsing

Survey data almost always comes as `.xlsx`. Parse with Python/openpyxl:

```bash
python3 - << 'EOF'
import openpyxl
wb = openpyxl.load_workbook("survey.xlsx")
ws = wb.active
headers = [cell.value for cell in ws[1]]
rows = [[cell.value for cell in row] for row in ws.iter_rows(min_row=2)]
print(f"Headers: {headers}")
print(f"Rows: {len(rows)}")
EOF
```

Use `scripts/parse_survey.py` for full parsing including quality scoring.

## Invalidity Filters

Run `scripts/filter_invalid.py` or apply these rules manually:

- Fill time < 30s AND all open-ended answers empty or single character → **INVALID**
- All open-ended answers are test strings ("test", "1", "-", numbers only) → **INVALID**
- Duplicate submissions (same person, same content) → keep one, mark rest **INVALID**
- All open-ended answers empty (regardless of fill time) → **INVALID**

⚠️ Always show the invalid list with reasons before filtering — let the user confirm.

## Quality Tiering

After filtering, tier valid responses (HIGH / MID / LOW) based on:

| Signal | Weight |
|--------|--------|
| Fill time (normalized within dataset) | 30% |
| Total open-ended answer word count | 40% |
| Number of open-ended questions answered | 20% |
| Answer specificity (scenario > keyword > empty) | 10% |

HIGH = top ~25%, MID = middle ~50%, LOW = bottom ~25%. Adjust thresholds based on dataset size.

HIGH-tier respondents are the primary source for journey mapping and deep insights. Identify them by name for follow-up interview recommendations.

## Key Outputs

The final report must include all sections from `references/analysis-framework.md`. Minimum required sections:

1. Data quality summary (counts, filter reasons, tier distribution)
2. User segmentation by usage pattern (not job title)
3. Trigger source analysis (what causes users to open the product)
4. Core journey maps (3–6 journeys with explicit pain point callouts)
5. Feature frequency with cross-validation (selection rate vs. open-ended description rate)
6. Prioritized capability list (P0/P1/P2/hold)
7. Follow-up interview recommendations (HIGH-tier users, specific topics)

## Critical Cross-Validation Rule

Selection rate ≠ real demand. Always cross-validate:

- If a feature has high selection rate but 0 open-ended descriptions → flag as "likely casual selection, validate before building"
- If a feature has low selection rate but vivid open-ended descriptions → flag as underrepresented, may be high value

## Skill Design Output (Optional)

When the user asks to define product skills/capabilities based on analysis results, apply the three-layer model from `references/skill-design-principles.md`:

- **Atomic Skills**: Single data dimension, zero inference, reusable by any composite
- **Composite Skills**: Orchestrate atomics, solve complete task intent, output conclusions
- **Scenario Skills**: Domain-specific wrapping of composites with embedded role knowledge
