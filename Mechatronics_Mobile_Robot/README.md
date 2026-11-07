# Teleoperated Differential-Drive Mobile Robot: Odometry and EKF Localization

Group project (**Group 4**) for the **Mechatronics** course, MSc in Biomedical Engineering, Università Campus Bio-Medico di Roma, A.Y. 2024/2025 (Nov 2024 – Jun 2025).

We designed and programmed a small **differential-drive mobile robot** that is driven from a PC over Bluetooth. Its pose is estimated in real time in two ways:

1. **Odometry:** wheel encoders only, with second-order Runge–Kutta integration.
2. **Extended Kalman Filter (EKF):** odometry corrected by a distance sensor that measures the distance from a known wall.

---

## System overview

```
┌──────────────────────────┐   Bluetooth (serial)   ┌───────────────────────────────┐
│  PC – MATLAB             │ ─────────────────────► │  Robot – PIC16F887 @ 20 MHz   │
│  • GUI teleoperation     │   wheel commands       │  • 2 motors (pulse-width ctrl)│
│  • Odometry / EKF        │ ◄───────────────────── │  • 2 × AS5600 encoders (I²C)  │
│  • Real-time pose plot   │   encoders + distance  │  • Distance sensor (ADC)      │
└──────────────────────────┘                        └───────────────────────────────┘
```

### Hardware
- **Microcontroller:** PIC16F887 (20 MHz clock), programmed in C with the CCS compiler.
- **Motors:** left and right wheel motors controlled by pulse width. 1500 µs is the neutral (stop) value, and the pulse varies by ±200 µs at the maximum wheel speed (5.23 rad/s).
- **Encoders:** two AS5600 12-bit magnetic angle sensors (4096 counts per revolution), on two separate I²C buses.
- **Distance sensor:** analog distance sensor (called `lidar` in the code), read by the 10-bit ADC and converted from voltage to metres with a power-law calibration curve.
- **Communication:** Bluetooth serial module at 9600 baud.
- **Geometry:** wheel radius r = 0.035 m, wheel distance d = 0.105 m.

### Communication protocol
| Direction | Packet |
|---|---|
| PC → robot | `[0x01, tR_MSB, tR_LSB, tL_MSB, tL_LSB]`: pulse widths (µs) for the right and left motors |
| Robot → PC | `[0x01, encR_MSB, encR_LSB, encL_MSB, encL_LSB, dist_MSB, dist_LSB]`: raw encoder angles and the ADC distance reading |

The `0x01` byte acts as a header, or acknowledgement, to keep the packets synchronised.

---

## Firmware (`firmware/ccs_GRUPPO4.c`)

- **Timer2 interrupt:** sets the control rate. On every tick the motor pulses are generated, and every 3 ticks the sensor data are read and sent over Bluetooth.
- **Encoders:** each AS5600 angle register (`0x0E`) is read over I²C.
- **Distance sensor:** read through the ADC on channel AN2.
- **Commands:** new pulse widths are received over Bluetooth, with the timer interrupt temporarily disabled while they are updated.

## MATLAB software (`matlab/`)

| File | Description |
|---|---|
| `GUI_interface_Speed.m` / `.fig` | GUIDE interface for teleoperation. It connects to the robot over Bluetooth and has buttons for forward, backward, left, right, the four diagonals, stop, and speed up/down. Wheel speeds (rad/s) are converted to pulse widths and sent as 5-byte packets. |
| `odometria_online.m` | Online odometry. Reads the encoders, unwraps the angle increments, computes the wheel speeds, then the linear and angular velocity (v, ω) of the robot, and integrates the pose. The trajectory is plotted live over a map with obstacles and waypoints. |
| `kalman_online.m` | Online EKF localisation. Same pipeline as odometry, plus the distance measurement, used to correct the pose against a known wall. |
| `f_k.m` | Motion model: second-order Runge–Kutta integration of the unicycle kinematics. |
| `ekf_2605.m` | EKF prediction and update step. |

### Kinematics
- Wheel angular speeds come from the differences between consecutive encoder readings, with wrap-around handled at ±π, over the sampling time Δt = 0.06 s.
- v = r/2 · (ω_R + ω_L), ω = r/d · (ω_R − ω_L)
- Pose update (Runge–Kutta, 2nd order):
  - x⁺ = x + Δt·v·cos(θ + Δt·ω/2)
  - y⁺ = y + Δt·v·sin(θ + Δt·ω/2)
  - θ⁺ = θ + Δt·ω

### Extended Kalman Filter
- **State:** [x, y, θ]
- **Prediction:** the Runge–Kutta motion model above, with Jacobian J₁ and process noise 0.01²·I.
- **Measurement:** distance from a wall at y = 1.4 m, so h(x) = y_wall − y with Jacobian [0, −1, 0], and measurement noise 0.05².
- **Update:** Kalman gain, innovation, and correction of the state and covariance.

---

## Experiments and results

- **Odometry test:** start at (0, 0), goal at (1.8, 1.66) m, passing through 3 waypoints on a map with 5 obstacles inside a bounded area.
- **EKF test:** start at (0, 1), goal at (3.5, 0.4) m, moving along a wall at y = 1.4 m, with 2 obstacles.

The `results/` folder contains the MATLAB figures of the estimated trajectories (`mappa_odometria.fig`, `kalman_gruppo_4.fig`) and the saved workspaces. The `media/` folder contains the videos of the two online tests.

### Limitations
- The single distance measurement only corrects the **y** coordinate. Errors in **x** and **θ** are not directly observable and still drift, as they do with odometry.
- The wheel speeds for each GUI command were tuned by hand on the real robot instead of being computed from inverse kinematics. The inverse kinematics formulas are still in the code, commented out.
- The sampling time Δt is fixed in MATLAB and not measured from the incoming packets.

---

## How to run

1. Flash `firmware/ccs_GRUPPO4.c` to the PIC16F887 with the CCS C compiler.
2. Pair the PC with the robot's Bluetooth module. In the GUI code the device is named `"LAZZARO"`.
3. In MATLAB, run `odometria_online.m` or `kalman_online.m`. The GUI opens automatically.
4. Press **Connessione** (Connect) to start, then drive the robot with the GUI buttons.

**Requirements:** MATLAB with the Instrument Control Toolbox (`bluetooth` / `serialport`), CCS C compiler, PIC programmer.

---

*Group project developed with fellow students at Università Campus Bio-Medico di Roma. Code comments are in Italian.*
