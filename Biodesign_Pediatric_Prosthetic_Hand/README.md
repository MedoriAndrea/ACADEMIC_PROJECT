# AddiKid Hand: Bio-Inspired Underactuated Pediatric Prosthetic Hand

Group project (**Group E**, 11 students) for the **Biodesign** course, MSc in Biomedical Engineering, Università Campus Bio-Medico di Roma, A.Y. 2025/2026 (Sep 2025 – Jan 2026).

The goal was to design a **low-cost, bio-inspired prosthetic hand for a 12-year-old child**, combining additive manufacturing, flexure hinges, an underactuated tendon transmission, and hybrid sensing for myoelectric control.

---

## Requirements
- **Functional:** the main daily grasps (lateral, cylindrical, spherical); smooth and coordinated finger motion; intuitive control with low cognitive load.
- **Pediatric safety:** intrinsic passive safety, limited force and speed, low weight, quiet operation, biocompatible materials.
- **Mechanical:** pediatric anatomy (palm sized from anthropometric data for children aged 5–13), modular parts that can follow the child's growth, robustness to impacts.
- **System:** daily-use battery life, compatibility with EMG control, fail-safe behaviour, **cost under €1,000**.

## Mechanical design and actuation
- **Actuation options compared:** dielectric elastomer actuators (DEA), vacuum-driven pneumatic actuators (VAMP, with micro pump and microvalve), and **electric actuation**.
- **Selected actuator:** FAULHABER 1627 GXR DC micromotor with a 16GPT planetary gearhead (116:1), sized for 100 N maximum tendon tension, 25 mm stroke and a 2 s closing time, which requires about 300 mNm of output torque.
- **Underactuated differential transmission:** a single motor drives all five fingers through a cascade of mobile pulleys. Each finger stops on its own when it touches the object, and the force is passively redistributed: 100 N → 50/50 N → 25 N for thumb, index and middle, 12.5 N for ring and little finger.
- **Thumb:** a cam-based passive locking mechanism with 3 stable positions: 20° for lateral grasp, 50° for cylindrical grasp, 90° for full opposition.
- **Fingertip force:** each finger is modelled as a planar 2-DoF manipulator, and the fingertip force comes from τ = Jᵀ F (virtual work). With 25 N of tendon tension in a pinch grip: **thumb ≈ 11.3 N, index ≈ 8.7 N**, consistent with values reported in the literature.

## Electronic design
- **Hybrid sensing for pattern-recognition control (regression-based, simultaneous and proportional):**
  - **sEMG** (OYMotion analog EMG sensor) captures early muscle activation;
  - **FMG** (Interlink FSR400 force sensors) is robust to environmental and physiological factors;
  - **IMU** (Bosch BNO055) compensates for arm position and enables a smart standby mode.
- **Custom PCB (Eagle/Fusion), V7**, organised in 3 areas:
  - **Logic and control:** ATmega328P, ICSP programming port, reset button, sleep button.
  - **Sensing and communication:** sensor inputs (with voltage dividers for the FSRs), IMU interrupt line, nRF51822 Bluetooth Low Energy chip with meander antenna, Bluetooth on/off button.
  - **Power and actuation:** 3.7 V 4000 mAh LiPo battery, Schottky diode against reverse current, LM1117 5 V regulator, TPS22918 load switch, INA219 voltage/current monitor with battery LED, DRV8837 motor driver.
- **Firmware (designed at block level):** synchronised acquisition of sEMG, FMG and IMU; conversion of the signals into proportional, low-latency motor commands; Bluetooth link to a smartphone app for recalibration and saving user profiles.

## Results
| Metric | Value |
|---|---|
| Estimated battery life | ~10 h |
| Total weight | 254.6 g |
| Total cost (bill of materials) | €585.90 (< €1,000 target) |
| Grasps | Lateral, cylindrical, spherical |

**Future work:** a rotating wrist module, more grasp types through adaptive control, use of the IMU to detect impacts, a soft outer covering, and a Bluetooth app for rehabilitation exercises (also in VR/AR).

---

## Repository structure
```
├── cad/hand_group_E.stl         # 3D model of the hand (STL)
├── pcb/
│   ├── BioDes_HandProsthesis_PCB_V7.sch   # Schematic (Eagle)
│   ├── BioDes_HandProsthesis_PCB_V7.brd   # PCB layout (Eagle)
│   └── BioDes_HandProsthesis_PCB_V7.f3d   # Fusion 360 design
└── docs/final_presentation.pdf  # Final presentation (with references)
```

The component datasheets (FAULHABER motor and gearhead, BNO055, FSR, INA219, nRF51822, DRV883x, TPS22918, NeoPixel, LiPo LP105068, Memetis microvalve, vacuum pump) are not included because they belong to their manufacturers. They are available on the manufacturers' websites.

---

*Group project developed with fellow students at Università Campus Bio-Medico di Roma.*
