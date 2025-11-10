# PAMS Mobile App Build Instructions

## 🍎 iOS App (iPhone/iPad)

### Prerequisites
- macOS with Xcode 15+
- Apple Developer Account ($99/year)
- iOS 15+ target devices

### Build Steps
1. **Create Xcode Project**:
   ```bash
   # Open Xcode → Create New Project → iOS → App
   # Use SwiftUI interface
   # Bundle ID: com.pams.athlete
   ```

2. **Add Files**:
   - Copy `PAMSApp.swift` to project
   - Copy `Info.plist` configuration
   - Add app icons (1024x1024 required)

3. **Configure Settings**:
   - Deployment Target: iOS 15.0
   - Team: Your Apple Developer Team
   - Bundle Identifier: com.pams.athlete
   - Version: 1.0

4. **Build & Test**:
   ```bash
   # Test on simulator
   Cmd+R in Xcode
   
   # Test on device
   Connect iPhone/iPad → Select device → Cmd+R
   ```

5. **App Store Submission**:
   - Archive build (Product → Archive)
   - Upload to App Store Connect
   - Fill app metadata
   - Submit for review

## 🤖 Android App

### Prerequisites
- Android Studio Arctic Fox+
- Google Play Developer Account ($25 one-time)
- Android 8+ target devices

### Build Steps
1. **Create Android Project**:
   ```bash
   # Open Android Studio → New Project → Empty Activity
   # Package: com.pams.athlete
   # Language: Kotlin
   # Minimum SDK: API 26 (Android 8.0)
   ```

2. **Add Files**:
   - Copy `MainActivity.kt` to app/src/main/java/com/pams/athlete/
   - Copy `AndroidManifest.xml` to app/src/main/
   - Add app icons in res/mipmap/

3. **Configure Gradle**:
   ```kotlin
   // app/build.gradle
   android {
       compileSdk 34
       defaultConfig {
           applicationId "com.pams.athlete"
           minSdk 26
           targetSdk 34
           versionCode 1
           versionName "1.0"
       }
   }
   ```

4. **Build & Test**:
   ```bash
   # Test on emulator
   Run → Run 'app' in Android Studio
   
   # Test on device
   Enable Developer Options → USB Debugging → Run
   ```

5. **Play Store Submission**:
   - Build → Generate Signed Bundle/APK
   - Upload to Google Play Console
   - Complete store listing
   - Submit for review

## 🔧 Configuration

### Update Server URL
Both apps need server URL updated:

**iOS (PAMSApp.swift)**:
```swift
let url = URL(string: "https://YOUR-HEROKU-APP.herokuapp.com/mobile")!
```

**Android (MainActivity.kt)**:
```kotlin
webView.loadUrl("https://YOUR-HEROKU-APP.herokuapp.com/mobile")
```

### App Icons Required
- **iOS**: 1024x1024 PNG (App Store), various sizes for app
- **Android**: 512x512 PNG (Play Store), various densities

### Screenshots Needed
- **iOS**: iPhone 6.7", 6.5", 5.5", iPad Pro 12.9", iPad Pro 11"
- **Android**: Phone, 7" tablet, 10" tablet

## 📱 Testing Checklist

### Functionality
- [ ] App launches successfully
- [ ] WebView loads PAMS mobile interface
- [ ] Touch interactions work properly
- [ ] Offline error handling works
- [ ] Back button navigation (Android)
- [ ] Portrait/landscape orientation

### Performance
- [ ] Fast loading times
- [ ] Smooth scrolling
- [ ] Memory usage acceptable
- [ ] Battery usage reasonable

### Security
- [ ] HTTPS connections only
- [ ] No file system access
- [ ] No sensitive data stored locally
- [ ] Network security policies active

## 🚀 Deployment Timeline

### Week 1: Development
- Set up development environment
- Create basic app structure
- Implement WebView wrapper
- Test on simulators/emulators

### Week 2: Testing
- Test on physical devices
- Performance optimization
- Security audit
- User acceptance testing

### Week 3: Store Preparation
- Create app store assets
- Write descriptions
- Prepare screenshots
- Set up developer accounts

### Week 4: Submission
- Submit to App Store
- Submit to Play Store
- Monitor review process
- Address any feedback

## 📞 Support

For build issues:
1. Check Xcode/Android Studio console
2. Verify all files copied correctly
3. Ensure server URL is accessible
4. Test WebView functionality separately

Expected review time:
- **iOS**: 1-7 days
- **Android**: 1-3 days