# PillBro: IoMT Smart Pill Dispenser with Cognitive Companion

Group project (**Group 2**, 3 students) for the **Internet of Medical Things (IoMT)** course, MSc in Biomedical Engineering, Università Campus Bio-Medico di Roma, A.Y. 2025/2026 (May–Jun 2026).

PillBro is a concept for a home **IoMT device** for **elderly people who live alone and take many medications**. It dispenses pills at scheduled times and checks that each dose is actually taken. It identifies the patient by fingerprint and notifies a remote caregiver. It also includes a voice-based **cognitive companion** that runs short daily cognitive checks.

The communication architecture was designed and **simulated in Cisco Packet Tracer 9**.

---

## Problem
- **Low adherence** to prescribed treatment is estimated to cost Europe **€80–125 billion a year** (MEDI-VOICE report, 2011).
- In Italy, a quarter of the population is over 65 and about 2.7 million people over 75 live alone. Most over-65s take several medications every day.
- Existing products, such as reminder apps, pill boxes and commercial dispensers, do not combine verified dispensing, patient authentication, remote caregiver control and cognitive monitoring in a single device.

## Architecture (3-tier IoMT)
```
PHYSICAL LAYER (MCU + sensors) ──UART──► EDGE LAYER (single-board computer) ──MQTT──► CLOUD LAYER
 • stepper-driven rotating disc            • dispensing logic and scheduling         • MQTT broker
   (28 compartments = 9 days × 3 + 1)      • bridge to the cloud (MQTT client)       • LLM API (HTTPS)
 • fingerprint sensor (authentication)     • voice pipeline: offline STT → LLM        │
 • photodiode (pill pick-up check)           → local TTS                              ▼
 • LEDs, LCD, speaker, battery             • keeps dispensing even if offline       Caregiver app
                                                                                     (MQTT client)
```
- **Physical layer:** a microcontroller runs the dispensing mechanism, the biometric authentication, the visual and audio alerts, and the photodiode check that the pill was taken.
- **Edge layer:** a single-board computer runs the dispensing logic and relays events and configuration over **MQTT**. It also hosts the voice companion: offline speech-to-text, an LLM in the cloud with **tool calling** that publishes test results over MQTT, and local text-to-speech. If the connection drops, dispensing keeps working on the last schedule, and only the companion is disabled.
- **Cloud layer:** an MQTT publish/subscribe broker, reachable from both the patient's home network and the caregiver's network, plus the LLM API.

## Packet Tracer simulation (`simulation/PillBro_simulation.pkt`)
The three layers are reproduced as separate subnets:
- **Physical layer:** a programmable MCU with an LCD, photodiode, motor, RGB LED, battery and push button.
- **Edge layer:** an SBC acting as the MQTT client.
- **Cloud layer:** a server acting as the MQTT broker, and a smartphone as the caregiver's client.

Scenarios tested, with the MQTT topics used:
| Scenario | Flow |
|---|---|
| Correct dispensing | Scheduled time → LCD and blue LED alert → authentication → motor turns → photodiode detects pick-up → `/presenza`, `/assunzione` |
| Access outside the schedule | Authentication outside the scheduled time → access denied on the LCD → `/presenza` (caregiver notified) |
| Missed dose | No authentication within the time window → `/alert`, `/assunzione` |
| Schedule update | Caregiver publishes new times on `/config` → SBC → MCU updates the program |
| Low battery | SBC detects critical charge → `/alert` |

**Simplifications compared with the real system:**
- the fingerprint sensor is replaced by a push button;
- UART is emulated with digital Tx/Rx pins;
- the broker is Packet Tracer's built-in MQTT server;
- the cognitive companion and the voice interaction were not simulated.

## Business model
The report and the presentation include a Business Model Canvas:
- **Customer segments:** elderly people as primary users, remote caregivers as secondary users.
- **Revenue:** sale of the device, plus an optional subscription for the companion's cloud services.
- **Regulation:** the companion requires MDR certification.

## Future work
- Build and validate a physical prototype.
- Check the shape and colour of each dispensed pill.
- Long-term charging.
- Integration with healthcare providers.
- Clinical validation of the companion, followed by MDR certification.

---

## Repository structure
```
├── simulation/PillBro_simulation.pkt   # Cisco Packet Tracer 9 project
└── docs/
    ├── report.pdf                      # Project report (in Italian)
    └── presentation.pptx               # Final presentation (in Italian)
```
Open the `.pkt` file with **Cisco Packet Tracer 9**.

---

*Group project developed with fellow students at Università Campus Bio-Medico di Roma.*
