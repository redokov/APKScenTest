# -*- coding: utf-8 -*-
"""Append progress notes to tmp/t8/PROGRESS.md."""
import io

with io.open(r"c:\MyProjects\APKScenTest\tmp\t8\PROGRESS.md", "a", encoding="utf-8") as f:
    f.write("""
### t8-finish-6: license + probe6
- FLUCTUATING license: 21:20-21:27 COM/DESIGNER/stub-build fell with "License not found", at 21:32 the probe6-runner connected fine, at 21:35 COM connect OK. KZT-log (C:\\ProgramData\\1C\\Licence\\3.0\\logs\\licenceserver.20261002-100037.4732.log): "Serie 4135 licences not found" on rphost all day (854 fails since 05.10) - clients are licensed by ANOTHER source (not KZT), few seats; competition for seats. 12 rac sessions (BackgroundJob/RAS), no client processes. Service "1C:Enterprise 8 License manager" stopped (not started without elevation) - did NOT touch anything (it worked while stopped).
- CONCLUSION: on "License not found" - do NOT panic, retry later (seats free up); do NOT restart services/server.
- F3 probe6 RESULT (ReturnStatus=1, 110 sec, tmp/t8/probe6-run-gektarov/):
  * Step "And In the tabular section from the drop-down list I select with choice ... "For direct costs" PASSED (tree reached line 30)! The t8-finish-5 derivation mechanism confirmed WORKING.
  * FAILED step AnalyticsExpenses "by row" "115, Wheat": "Failed to select from the choice list by row <115, Wheat>. Number of attempts <3>" (line 36 of the feature). The active form is correct (TRACTOR driver waybill, Creation). Hypothesis: the list does not contain "115, Wheat" (perhaps the full representation "115, Winter wheat 2015" is needed, or the choice list depends on previously entered values / list formation mechanism).
""")
print("ok")
