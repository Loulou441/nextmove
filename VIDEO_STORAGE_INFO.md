# Video Storage Information

## ✅ Videos Are Stored Permanently

Your videos are saved in the app's **Documents directory** and will NOT be lost.

### Storage Location
```
App Documents Directory/
├── [UUID].mov  (recorded videos)
├── [UUID].mov  (imported videos)
└── ...
```

### How It Works

1. **Recording Videos**
   - Saved to: `Documents/[UUID].mov`
   - Location: `RecordingView.swift` line 203-206

2. **Importing Videos**
   - Copied to: `Documents/[UUID].mov`
   - Location: `VideoImportView.swift` line 112-115

3. **Storage Persistence**
   - Videos persist across app launches
   - Stored in UserDefaults as `GameRecording` objects
   - Video files remain in Documents directory
   - Only deleted when you explicitly delete a recording

### Video URL Structure
```swift
struct GameRecording {
    var videoURL: URL?  // Points to Documents/[UUID].mov
    // ... other properties
}
```

### Deletion Behavior
Videos are only deleted when:
- You delete a specific recording: `deleteRecording(_:)`
- You delete all recordings: `deleteAllRecordings()`

Both methods remove:
1. The video file from disk
2. The recording metadata from UserDefaults

### Backup Recommendations
Videos are stored in the app's Documents directory, which:
- ✅ Is backed up by iCloud (if enabled)
- ✅ Is backed up by iTunes/Finder
- ✅ Persists across app updates
- ❌ Is deleted if you uninstall the app

For extra safety, consider:
- Exporting important videos to Photos app
- Backing up via iCloud or iTunes
- Sharing videos before deleting the app

## Video Player Updates

The video player now:
- ✅ Plays inline (same size as thumbnail)
- ✅ Shows play button overlay when paused
- ✅ Shows pause button when playing
- ✅ Tap anywhere to pause
- ✅ Maintains 16:9 aspect ratio
- ✅ Shows duration in bottom-left
- ✅ Handles missing videos gracefully

### Controls
- **Tap play button** → Start playback
- **Tap video while playing** → Pause
- **Tap pause button** → Pause
- **Navigate away** → Video pauses automatically
