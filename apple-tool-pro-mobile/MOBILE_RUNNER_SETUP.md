# Apple Tool Pro — Android Runner Setup

The Windows desktop application remains the normal GUI entry point. The Android APK controls a separate Windows runner process over the same trusted local network. The runner uses the existing automation code and always creates the browser with `headless=True`.

## Build the Windows executables

On a Windows computer with Python installed, run `build_windows_exe.bat`. It produces `dist\AppleToolPro.exe` for the desktop interface and `dist\AppleToolProRunner.exe` for the Android-controlled runner.

## Start the Android runner

Open Command Prompt in the build folder and run the following command with a private token of your choice.

```bat
AppleToolProRunner.exe --mobile-runner --token YOUR_PRIVATE_TOKEN
```

The command prints the local address and port. Find the Windows computer's local IPv4 address, then enter `http://WINDOWS_IP:8787` and the same token in the Android application Settings screen. Keep both devices on the same private Wi-Fi network.

## Operating behavior

The APK sends the phone-number list to the runner, receives live progress and logs, and can request a graceful stop. The runner is headless by design for Android-controlled runs. The connection token is required for status, start, stop, and log-management requests.
