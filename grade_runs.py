#!/usr/bin/env python3
"""Grade advertorial test run outputs against assertions."""

import json
import os
import re

WORKSPACE = "/Volumes/JULIANMEDIA/advertorial-workspace/iteration-1"

EVALS = [
    {
        "eval_id": 1,
        "eval_name": "lumiglow-collagen",
        "assertions": [
            ("html_doctype", "The output is a complete HTML file starting with <!DOCTYPE html>",
             lambda h: h.strip().lower().startswith("<!doctype html")),
            ("expert_headline", "The file contains a headline with expert title and conspiracy/dramatic claim",
             lambda h: ("dr." in h.lower() or "dermatologist" in h.lower()) and ("conspiracy" in h.lower() or "lie" in h.lower() or "billion" in h.lower() or "exposes" in h.lower() or "hiding" in h.lower())),
            ("major_narrative_sections", "Contains major narrative sections: Moment Everything Broke, billion lie, why everything failed, simple truth, discovery, self-test, patient revolution",
             lambda h: all(phrase in h.lower() for phrase in ["moment everything", "billion", "everything you've tried", "simple truth", "discovery", "test subject", "patient revolution"])),
            ("product_named", "Product LumiGlow Collagen Serum is named in the product introduction section",
             lambda h: "lumiglow" in h.lower()),
            ("all_ingredients", "All 4 ingredients mentioned: Marine Collagen Peptides, Astaxanthin, Peptide Complex GF-7, Ceramide NP",
             lambda h: all(i in h.lower() for i in ["marine collagen", "astaxanthin", "peptide complex gf-7", "ceramide"])),
            ("pricing_49", "The file contains a pricing section mentioning $49",
             lambda h: "$49" in h),
            ("guarantee_120", "The file contains a 120-day guarantee section",
             lambda h: "120" in h and ("guarantee" in h.lower() or "day" in h.lower())),
            ("facebook_comments", "The file contains a Facebook-style comments section with at least 5 comments",
             lambda h: h.lower().count("fb-name") >= 5 or h.lower().count("fb-comment") >= 5),
            ("sticky_bar_js", "JavaScript for sticky bar is embedded",
             lambda h: "sticky" in h.lower() and ("scroll" in h.lower()) and ("javascript" in h.lower() or "<script" in h.lower())),
            ("two_paths", "The file contains a Two Paths section with PATH 1 and PATH 2",
             lambda h: "path 1" in h.lower() and "path 2" in h.lower()),
            ("fda_disclaimer", "The file contains a footer with medical/FDA disclaimer",
             lambda h: "fda" in h.lower() or "food and drug" in h.lower()),
        ]
    },
    {
        "eval_id": 2,
        "eval_name": "metafire-drops",
        "assertions": [
            ("html_doctype", "The output is a complete HTML file starting with <!DOCTYPE html>",
             lambda h: h.strip().lower().startswith("<!doctype html")),
            ("expert_named", "Dr. James Holloway and CDC background are mentioned",
             lambda h: "holloway" in h.lower() and "cdc" in h.lower()),
            ("bat_mechanism", "The BAT (brown adipose tissue) mechanism is explained",
             lambda h: "brown adipose" in h.lower() or ("bat" in h.lower() and "adipose" in h.lower())),
            ("all_ingredients", "All 4 ingredients present: Perilla Frutescens, Kudzu Root, Holy Basil, White Korean Ginseng",
             lambda h: all(i in h.lower() for i in ["perilla", "kudzu", "holy basil", "ginseng"])),
            ("patient_story", "Dave's patient story is in The Moment Everything Broke section",
             lambda h: "dave" in h.lower() and ("truck" in h.lower() or "cardiolog" in h.lower())),
            ("product_named", "The product MetaFire Drops is named",
             lambda h: "metafire" in h.lower()),
            ("pricing", "Pricing of $39 or $33 per bottle is mentioned",
             lambda h: "$39" in h or "$33" in h),
            ("guarantee_180", "180-day guarantee section is present",
             lambda h: "180" in h and "guarantee" in h.lower()),
            ("facebook_comments", "Facebook-style comments section is present",
             lambda h: "fb-comment" in h.lower() or ("like" in h.lower() and "reply" in h.lower())),
            ("two_paths", "Two Paths section is present",
             lambda h: "path 1" in h.lower() and "path 2" in h.lower()),
            ("sticky_bar_js", "JavaScript for sticky bar is embedded",
             lambda h: "sticky" in h.lower() and "scroll" in h.lower() and "<script" in h.lower()),
            ("fda_disclaimer", "Medical and FDA disclaimer is present in footer",
             lambda h: "fda" in h.lower() or "food and drug" in h.lower()),
        ]
    },
    {
        "eval_id": 3,
        "eval_name": "sleepwave-patches",
        "assertions": [
            ("html_doctype", "The output is a complete HTML file starting with <!DOCTYPE html>",
             lambda h: h.strip().lower().startswith("<!doctype html")),
            ("expert_named", "Dr. Priya Nair and Johns Hopkins background are mentioned",
             lambda h: "nair" in h.lower() and "johns hopkins" in h.lower()),
            ("mechanism", "The adenosine receptor desensitization mechanism is explained",
             lambda h: "adenosine" in h.lower()),
            ("all_ingredients", "All 4 ingredients present: Magnesium Glycinate, L-Theanine, Ashwagandha KSM-66, Lemon Balm",
             lambda h: all(i in h.lower() for i in ["magnesium glycinate", "l-theanine", "ashwagandha", "lemon balm"])),
            ("patient_story", "Susan's patient story (nurse, 4 years of insomnia) is in The Moment Everything Broke section",
             lambda h: "susan" in h.lower() and ("nurse" in h.lower() or "3am" in h.lower() or "insomnia" in h.lower())),
            ("product_named", "SleepWave Patches named in product introduction",
             lambda h: "sleepwave" in h.lower()),
            ("pricing", "Pricing of $34 mentioned",
             lambda h: "$34" in h),
            ("guarantee_90", "90-day guarantee section present",
             lambda h: "90" in h and "guarantee" in h.lower()),
            ("facebook_comments", "Facebook-style comments present",
             lambda h: "fb-comment" in h.lower() or ("like" in h.lower() and "reply" in h.lower())),
            ("sticky_bar_js", "Sticky bar JavaScript is present",
             lambda h: "sticky" in h.lower() and "scroll" in h.lower() and "<script" in h.lower()),
            ("fda_disclaimer", "Footer contains medical and FDA disclaimer",
             lambda h: "fda" in h.lower() or "food and drug" in h.lower()),
        ]
    }
]

results = {}

for eval_def in EVALS:
    eval_name = eval_def["eval_name"]
    results[eval_name] = {}

    for variant in ["with_skill", "without_skill"]:
        html_path = os.path.join(WORKSPACE, eval_name, variant, "outputs", "advertorial.html")

        if not os.path.exists(html_path):
            print(f"  MISSING: {html_path}")
            continue

        with open(html_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

        grading = {"expectations": []}
        passed = 0
        total = 0

        for key, text, check_fn in eval_def["assertions"]:
            try:
                passed_check = check_fn(html)
            except Exception as e:
                passed_check = False

            grading["expectations"].append({
                "text": text,
                "passed": passed_check,
                "evidence": f"Checked '{key}' programmatically against HTML ({len(html)} chars)"
            })

            if passed_check:
                passed += 1
            total += 1

        grading["pass_rate"] = passed / total if total > 0 else 0
        grading["passed"] = passed
        grading["total"] = total

        out_path = os.path.join(WORKSPACE, eval_name, variant, "grading.json")
        with open(out_path, "w") as f:
            json.dump(grading, f, indent=2)

        results[eval_name][variant] = grading
        print(f"  {eval_name}/{variant}: {passed}/{total} ({grading['pass_rate']:.0%})")

print("\nAll grading complete.")
