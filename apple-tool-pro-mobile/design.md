# Apple Tool Pro Mobile — Interface Design

## Design Objective

The Android application will reproduce the operational dashboard shown in the supplied video in a mobile portrait layout. The interface will use a dark navy background, blue outlines and progress accents, green success states, and red failure states. The app will be a controller and live monitor for the automation runner, while the runner itself remains headless.

## Screen List

| Screen | Primary content and functionality |
|---|---|
| Runner | Application header, PRO badge, live Total/Active/Success/Failed statistics, phone-number input, Load and Clear actions, status text, progress bar, Start Automation and Stop buttons. |
| Logs | Timestamped live execution logs, copy action, clear action, and a scrollable log feed with semantic success, warning, and error colors. |
| Settings | Runner connection address, connection status, and an Android headless-mode indicator that cannot be disabled. |

## Primary User Flows

The user opens Runner, pastes or loads a phone-number list, verifies the headless indicator, and taps Start Automation. The mobile interface sends the request to a compatible headless runner and immediately reflects state, counters, progress, and logs. The user can change to Logs while processing continues, return to Runner to stop the task, then clear the in-memory list after reviewing the completed operation.

## Color Choices

| Role | Color | Purpose |
|---|---|---|
| App background | `#071425` | Near-black navy background used throughout the video reference. |
| Panel background | `#0D2038` | Elevated card and input surface. |
| Blue accent | `#2693FF` | Borders, progress bar, focused controls, and navigation state. |
| Success | `#37D67A` | Successful counters and success logs. |
| Error | `#FF5C6C` | Failed counters, stop action, and error logs. |
| Primary text | `#F4F8FF` | Main titles and values. |
| Secondary text | `#95A8C1` | Supporting labels and status descriptions. |

## Interaction and Layout Principles

The app is optimized for one-handed portrait use. Primary actions sit within thumb reach above the bottom navigation bar. The four statistics remain compact and horizontally scroll-free. The Start action spans the available width, while Stop remains visually distinct but secondary until a run is active. Android headless operation is presented as a fixed operating state rather than a user-editable option.
