<p align="center">
  <img src="docs/header.svg" alt="FID Push – Firebase Installation ID notifications" width="100%">
</p>

# FID Push

A Flutter demo that sends push notifications to a device using its **Firebase Installation ID (FID)** instead of an FCM registration token. Includes a Python (`firebase_admin`) script to send test notifications.

By [shakilofficial0](https://github.com/shakilofficial0).

---

## Requirements

| Tool / Package | Version |
| --- | --- |
| Flutter SDK (Dart) | Dart `^3.13.0` |
| `firebase_core` | latest |
| `firebase_app_installations` | `>= 0.4.4` |
| `firebase_messaging` | `>= 16.7.0` |
| Firebase CLI + FlutterFire CLI | latest |
| Python | 3.10+ |
| `firebase-admin` (Python) | `7.7.0` (FID multicast support) |
| Xcode (iOS only) | recent, on macOS |
| Apple Developer account (iOS only) | needed for the APNs `.p8` key |

---

## 1. Connect the project to Firebase

Skip this step if the app is already connected to the Firebase project.

```bash
dart pub global activate flutterfire_cli
flutterfire configure --project=<project_id>
```

This generates the platform config files. Check they exist:

| File | Purpose |
| --- | --- |
| `firebase.json` | FlutterFire CLI config |
| `lib/firebase_options.dart` | Dart Firebase options |
| `android/app/google-services.json` | Android config |
| `ios/Runner/GoogleService-Info.plist` | iOS config |

> These are git-ignored in this repo. Each developer generates their own.

## 2. Add the packages

```bash
flutter pub add firebase_core
flutter pub add firebase_app_installations   # keep >= 0.4.4
flutter pub add firebase_messaging           # keep >= 16.7.0
```

## 3. Android setup

Edit `android/app/src/main/AndroidManifest.xml`.

**Permissions** (outside `<application>`):

```xml
<uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
<uses-permission android:name="android.permission.WAKE_LOCK" />
```

**Enable FID targeting** (inside `<application>`):

```xml
<meta-data
    android:name="firebase_messaging_installation_id_enabled"
    android:value="true" />
```

`POST_NOTIFICATIONS` is a runtime permission on Android 13+, requested by `requestPermission()` below.

## 4. iOS setup (step by step)

Do this on a Mac with Xcode. Push notifications do **not** work on the iOS Simulator for APNs-delivered messages; use a real device.

### 4.1 Register the iOS app in Firebase

`flutterfire configure` (step 1) registers it. Confirm `ios/Runner/GoogleService-Info.plist` exists and is added to the **Runner** target in Xcode (drag it into Runner, tick *Copy items if needed*).

### 4.2 Edit `ios/Runner/Info.plist`

Add these keys inside the top-level `<dict>`:

```xml
<key>FirebaseAppDelegateProxyEnabled</key>
<true/>
<key>FirebaseMessagingInstallationIdEnabled</key>
<true/>
<key>UIBackgroundModes</key>
<array>
    <string>remote-notification</string>
</array>
```

- `FirebaseAppDelegateProxyEnabled`: lets Firebase handle the APNs token automatically (method swizzling).
- `FirebaseMessagingInstallationIdEnabled`: enables FID-based targeting on iOS.
- `UIBackgroundModes` → `remote-notification`: lets the app receive background pushes.

### 4.3 Enable capabilities in Xcode

1. Open `ios/Runner.xcworkspace`.
2. Select **Runner** target → **Signing & Capabilities**.
3. Pick your Team and a unique Bundle Identifier (must match the one registered in Firebase).
4. Click **+ Capability** and add:
   - **Push Notifications**
   - **Background Modes** → tick **Remote notifications**

### 4.4 Create the APNs authentication key (`.p8`)

1. Go to [developer.apple.com/account](https://developer.apple.com/account) → **Certificates, Identifiers & Profiles** → **Keys**.
2. Click **+**, name it (e.g. `FID Push APNs`), tick **Apple Push Notifications service (APNs)**, then **Continue → Register**.
3. **Download** the `AuthKey_XXXXXXXXXX.p8` file. Apple lets you download it **only once**, so store it safely (never commit it).
4. Note two values:
   - **Key ID**: the 10 characters in the file name / key page.
   - **Team ID**: shown top-right of the Apple Developer page, or under **Membership details**.

### 4.5 Upload the `.p8` to Firebase

1. Firebase Console → **Project settings** → **Cloud Messaging** tab.
2. Under **Apple app configuration → APNs Authentication Key**, click **Upload**.
3. Select the `.p8` file, enter the **Key ID** and **Team ID**, then **Upload**.

One `.p8` key works for all your apps and for both sandbox and production.

### 4.6 Run on a device

```bash
flutter clean
flutter pub get
cd ios && pod install --repo-update && cd ..
flutter run --release   # or run from Xcode on a connected iPhone
```

Accept the notification permission prompt when it appears.

## 5. Dart code

Imports:

```dart
import 'package:firebase_app_installations/firebase_app_installations.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
```

Initialise, ask permission, read the FID:

```dart
await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

final settings = await FirebaseMessaging.instance.requestPermission();
debugPrint('Notification permission: ${settings.authorizationStatus}');

final fid = await FirebaseInstallations.instance.getId();
debugPrint('Firebase Installation ID: $fid');
```

Copy the printed FID; it is the notification target.

## 6. Test with the Python sender

The script in [notification_test_system/](notification_test_system/) uses the `firebase_admin` SDK to send a multicast message to one or more FIDs.

### 6.1 Get a service account key

Firebase Console → **Project settings → Service accounts → Generate new private key**. Save it as `notification_test_system/development.json`.

> ⚠️ This file is a secret. Do **not** commit it. If it was ever committed, rotate the key in the Google Cloud console and remove it from git history.

### 6.2 Install and run

```bash
cd notification_test_system
python -m venv .venv && source .venv/bin/activate
pip install firebase-admin==7.7.0
```

Set `projectId` in `main.py` to your project, then:

```bash
python main.py                      # sends to the demo FID in the file
python main.py <fid1> <fid2> ...    # sends to the FIDs you pass
```

> `main.py` currently uses the demo FID constant. Replace `FIREBASE_INSTALLATION_ID` with your own, or pass FIDs as arguments once the script is updated to read `sys.argv`.

The script prints success/failure counts per FID, including the error code and HTTP body on failure.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| No notification on Android 13+ | Grant the notification permission; check `POST_NOTIFICATIONS` is in the manifest. |
| FID send returns `NOT_FOUND` / `UNREGISTERED` | App must be installed and have run once with the `meta-data` / plist key enabled; re-copy the FID (it changes after reinstall). |
| iOS: nothing arrives | Use a real device, confirm the `.p8` is uploaded with the correct Key ID and Team ID, and that Push Notifications capability is enabled. |
| iOS: `APNS token has not been set` | Check `FirebaseAppDelegateProxyEnabled` is `true` and Background Modes → Remote notifications is on. |
| `PERMISSION_DENIED` from Python | Service account needs the *Firebase Cloud Messaging API Admin* role and the FCM API must be enabled. |

## Project layout

```
lib/                          Flutter app
android/  ios/                Platform projects
docs/header.svg               README header image
notification_test_system/     Python sender (firebase_admin)
```
