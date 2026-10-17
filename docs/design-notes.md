# Design notes

Decisions and the reasons behind them. Newest section last.

## 2026-10-10: Manual investigation of T1003.001 (eval case 1)

Investigated `T1003.001/atomic_red_team/windows-sysmon.log` by hand with grep before any model touched it. Goal: understand the task the agent will face, and build a ground truth to score it against.

### What the data turned out to be

- **Not one incident.** The file contains two capture runs on two different domain controllers, three months apart (run A: win-dc-807, 2020-11-03, 7,171 events; run B: win-dc-262, 2021-02-03, 789 events).
- **Not in time order.** File order differs from UtcTime order (e.g. Dumpert appears after rundll32 but ran 16 ms before it).
- **Mostly noise.** The Splunk Universal Forwarder, the Atomic Red Team harness (prerequisite checks, installs, cleanup) and routine OS activity outnumber the attack events.
- **Labels under-describe the activity.** The YAML lists only T1003.001; the logs also support T1059.001, T1218.011, T1036.003 and T1105.
- **Some actions have no proof of outcome.** Mimikatz and pypykatz were executed, but there is no LSASS access event from pypykatz and no input dump for Mimikatz in run A.

### Decisions

**Ground truth is hand-labelled, not model-generated.**
If a model wrote the answer key, it would score itself highly by construction, and the Haiku / Sonnet / Opus comparison would measure agreement with that model, not accuracy. Later, an independent Opus labelling of the same log will be compared with the hand labels; each difference is either a gap in the key or a model failure.

**Scoring uses tiers, not the YAML alone.**
- Required: techniques in the YAML (here T1003.001). Missing one is a fail.
- Acceptable: techniques supported by the evidence but not in the YAML. Neutral.
- Wrong: anything else. Counts against precision.

Scoring strictly against the YAML would penalise an agent for correct findings.

**Attempted versus succeeded.**
The agent may only say an action succeeded when telemetry proves it (a dump file written, an LSASS access event). Otherwise it must say "executed" or "attempted". Overclaiming is the main factual-accuracy check.

**Evasion techniques are scored as attempts.**
The agent must not claim evasion succeeded when the telemetry shows it was observed. Example: Dumpert bypasses user-mode hooks, but Sysmon EID 10 (kernel callback) still logged its LSASS access.

**Lab artefacts are not attacker actions.**
Splunk forwarder activity, Atomic Red Team staging and Atomic Red Team cleanup are excluded from the incident. Presenting them as attacker behaviour counts as a factual error.

**Atomic Red Team: note it, don't dismiss it.**
Recognising `C:\AtomicRedTeam\` artefacts and recommending that authorisation be confirmed is credited. Closing the incident because ART was used is a fail, since real attackers can use the same tooling.

**Separate runs stay separate.**
One eval case covers both runs, but the report must treat them as separate activity on separate hosts. Stitching them into one intrusion, or claiming lateral movement between them, is a fail.

**Remediation is credited, not required.**
A report that recommends resetting exposed credentials, including KRBTGT twice with at least the maximum ticket lifetime (10 h default) between resets, is credited. The exact procedure is not required, because it can't be checked against the logs.

### Implications for the agent (Phase 2)

**Pivots used by hand, as candidate tools:**

| Manual pivot | Candidate agent tool |
| --- | --- |
| Count events by EventID | summarise the log (event types, hosts, time range) |
| Filter events touching a process (e.g. lsass.exe) | search events by field and value |
| List distinct command lines, with counts | distinct values of a field |
| Exclude known noise (splunk, etc.) | pre-filter step, or a filter argument on search |
| Follow ProcessGuid / ParentProcessGuid | get process tree / related events |
| Pull UtcTime + Image + CommandLine for matches | return selected fields only, sorted by time |
| Decode `-EncodedCommand` (base64 of UTF-16LE) | decode PowerShell command |
| Check OriginalFileName and Hashes | get process metadata (spot renamed binaries) |

**Log size:**
- Naive truncation or sampling is ruled out: run B is about 10% of the file and holds the masquerading and the interactive Task Manager dump, so it is the part most likely to be lost.
- Events must be sorted by UtcTime before the agent reasons about order.
- Grouping by host and date surfaces the two runs immediately; the summary tool should report both.

### Open questions

- Pre-filter versus query tools versus both: decide in Phase 2 against eval results.
- How much noise does the exclusion list remove? Measure the event count before and after.
- How to score the timeline automatically (match on timestamp, process and artefact, with a tolerance?).
- Does the agent handle the CrowdStrike log in the same folder, or Sysmon only for now?
