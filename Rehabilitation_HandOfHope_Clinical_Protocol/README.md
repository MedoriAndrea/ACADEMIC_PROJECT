# Clinical Investigation Protocol: Hand of Hope Exoskeleton for Post-Stroke Hand Rehabilitation

Group project (**Group 25**, 4 students) for the **Rehabilitation Bioengineering** course (*Bioingegneria della Riabilitazione*), MSc in Biomedical Engineering, Università Campus Bio-Medico di Roma. Protocol v1.0, dated 21 January 2026.

We wrote a **clinical investigation protocol**, following the structure required by the EU Medical Device Regulation (MDR), for a pilot study of the **Hand of Hope (HOH)**. HOH is a commercial hand exoskeleton driven by surface EMG, made by Rehab-Robotics. The rehabilitation plan was designed **together with physiotherapists**.

---

## Device
- **Intention-driven philosophy:** surface EMG sensors on the forearm detect the patient's attempt to move, a pattern-recognition algorithm (SVM) classifies it, and the exoskeleton completes the movement. This closes a 5-step neuro-functional loop.
- **Hardware:** independent actuation of each finger with virtual MCP and PIP joints, 6 movement patterns, and active forearm support.
- **Operating modes:**
  - passive, continuous passive motion (CPM);
  - active, with EMG biofeedback: *Trigger & Go* (the robot completes the movement once the EMG passes a threshold) and *Trigger & Maintain* (the patient must keep the activation above threshold for the whole movement);
  - EMG-driven games, to keep the patient engaged.

## Rationale (literature review)
- After a stroke, motor deficits of the hand are common and often persistent, and conventional therapy cannot always deliver enough intensity and repetitions.
- Meta-analyses show that robot-assisted therapy improves motor impairment of the upper limb (FMA). EMG-driven approaches strengthen the link between the intention to move and the movement itself.
- The reference randomised trial on HOH (24 patients in the acute phase, 15 sessions over 3 weeks) found improvements within each group but **no difference between the groups**. Its authors pointed to the short treatment, the spontaneous recovery of the acute phase, and the weak differences between the two treatment protocols.
- **This protocol addresses those limits:** a higher dose, a longer treatment, more specific exercises, and sub-acute or chronic patients.

## Study design
| Item | Choice |
|---|---|
| Design | Controlled pilot study, 3 parallel groups |
| Participants | 30 adults after ischaemic or haemorrhagic stroke, sub-acute (1–6 months) or chronic (> 6 months), n = 10 per group |
| Groups | **A**: conventional physiotherapy · **B**: Hand of Hope only (CPM → EMG Trigger & Go / Trigger & Maintain → assisted functional exercises → gamification) · **C**: combined, 30 min conventional + 15–20 min HOH per session |
| Dose | 45-minute sessions, 5 per week for 6 weeks (**30 sessions**) |
| Assessments | Baseline (T0) and end of treatment (T1, within 24–48 h) |

- **Key inclusion criteria:** residual muscle activity detectable by sEMG in the hand flexors or extensors; Modified Ashworth Scale (MAS) ≤ 3; enough passive range of motion to wear the device; able to follow instructions; written informed consent.
- **Key exclusion criteria:** fixed contractures; severe spasticity; pain on passive mobilisation; skin lesions; severe cognitive deficits; other neurological or orthopaedic conditions.

## Endpoints
- **Primary:** change in **Fugl-Meyer Assessment – Upper Extremity (FMA-UE)** from T0 to T1.
- **Secondary:**
  - **ARAT**, for function;
  - **Nine Hole Peg Test**, for fine dexterity;
  - **grip dynamometry**, for grip strength;
  - **Modified Ashworth Scale**, for spasticity;
  - **Motor Activity Log**, for use of the hand in daily life;
  - **feasibility** (adherence, sessions completed) and **adverse events**.

## Statistical analysis plan
- **Descriptive statistics:** mean ± SD or median (IQR), depending on normality, tested with **Shapiro–Wilk**.
- **Baseline comparability between groups:** one-way ANOVA or Kruskal–Wallis for continuous variables; χ² or Fisher's exact test for categorical variables.
- **Within each group (effect of time):** paired t-test or Wilcoxon signed-rank test.
- **Between groups (effect of treatment)**, on the change Δ = T1 − T0: one-way ANOVA with Tukey or Bonferroni post-hoc tests, or Kruskal–Wallis with Dunn's post-hoc test. The MAS is ordinal, so it is analysed only with non-parametric tests.
- **Feasibility:** described with counts and percentages only, no inferential tests.
- Significance level α = 0.05.

## Ethics and safety
- Informed consent procedures, protections for vulnerable populations (MDR articles 64–65), and processing of personal data under GDPR.
- Clear criteria for stopping a participant's treatment: adverse events, clinical worsening, intolerance, poor compliance.
- A monitoring plan for the investigation.

---

## Repository structure
```
└── clinical_investigation_protocol.pdf   # Full protocol (in Italian)
```

*Group project developed with fellow students at Università Campus Bio-Medico di Roma, in collaboration with physiotherapists.*
