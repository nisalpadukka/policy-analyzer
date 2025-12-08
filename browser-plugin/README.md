# Browser Extension

This directory contains the browser extension for the Privacy Policy Analyzer application.

## Overview

The browser extension provides a user-friendly interface for analyzing privacy policies. Users can paste privacy policy text and receive structured summaries with severity ratings across four dimensions: data collection, data sharing, data retention, and overall privacy risk.

## Architecture

The extension is built using Manifest V3 and consists of:

- **popup.html**: User interface structure
- **popup.js**: UI logic and API communication
- **popup.css**: Styling and visual design
- **background.js**: Service worker for API calls
- **manifest.json**: Extension configuration
- **assets/**: Icons and visual assets

## Implementation Details

### Popup Interface

The popup (`popup.html/js/css`) provides:

- **Text Input**: Textarea for pasting privacy policy text
- **Summarize Button**: Triggers analysis request
- **Status Display**: Shows processing status
- **Summary Sections**: Four blocks displaying analysis results
- **Severity Badges**: Color-coded indicators (green/yellow/red)

### Background Service Worker

The background script (`background.js`) handles:

- **Message Handling**: Listens for `SUMMARIZE_POLICY` messages from popup
- **API Communication**: Makes HTTP POST requests to Lambda endpoint
- **Response Transformation**: Maps API response to frontend format
- **Error Handling**: Falls back to mock summary on API failure
- **Async Processing**: Uses async/await for non-blocking operations

### User Workflow

1. User opens extension popup
2. Pastes privacy policy text into textarea
3. Clicks "Summarize" button
4. Extension sends text to background worker
5. Background worker calls API Gateway endpoint
6. Results displayed in popup with severity badges

## Installation

### For End Users

**Option 1: Install from Chrome Web Store (Recommended)**

The extension is published and available on the Chrome Web Store:

🔗 **[Install Privacy Policy Analyzer from Chrome Web Store](https://chromewebstore.google.com/detail/mlmdjpffmmojkiidoleibkpjnaabpndd)**

Simply click "Add to Chrome" to install. The extension is pre-configured and ready to use immediately.

**Option 2: Manual Installation (For Development)**

1. Open Chrome/Edge and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `privacy-policy-analyzer-extension/` directory
5. The extension icon should appear in your toolbar

### Configuration

**For Chrome Web Store Version**: No configuration needed - the extension is pre-configured with the production API endpoint.

**For Manual Installation**: Before use, update the API endpoint URL in `background.js`:

```javascript
const ANALYSIS_API_URL = "https://your-api-gateway-url.execute-api.region.amazonaws.com/analyze";
```

Replace with your actual API Gateway endpoint URL from Terraform deployment.

## Development

### File Structure

```
privacy-policy-analyzer-extension/
├── popup.html          # Main UI structure
├── popup.js            # UI logic and event handlers
├── popup.css           # Styling and layout
├── background.js       # Service worker for API calls
├── manifest.json       # Extension configuration
└── assets/
    └── icons/          # Extension icons (16px, 48px, 128px)
```

### Key Components

**popup.js**:
- `setBadge()`: Updates severity badge styling and text
- Event listener for "Summarize" button
- Message passing to background script
- Result display logic

**background.js**:
- `summarizeViaBackend()`: API call implementation
- `mockSummarize()`: Fallback for offline/error scenarios
- Message listener for popup communication
- Response normalization

**manifest.json**:
- Manifest V3 configuration
- Minimal permissions (no active tab access)
- Service worker declaration
- Icon definitions

### Testing

1. Load extension in developer mode
2. Open popup and paste test privacy policy text
3. Click "Summarize" and verify API call in Network tab
4. Check console for errors (popup and background)
5. Test error handling by using invalid API URL

### Debugging

- **Popup Console**: Right-click popup → Inspect
- **Background Console**: Go to `chrome://extensions/` → Service Worker link
- **Network Tab**: Monitor API requests in DevTools
- **Extension Reload**: Click reload icon in `chrome://extensions/`

## Features

- **Manual Text Input**: Users paste text (no automatic extraction)
- **Visual Severity Indicators**: Color-coded badges for quick assessment
- **Structured Output**: Four distinct analysis dimensions
- **Error Handling**: Graceful fallback on API failures
- **Minimal Permissions**: Only activates when user opens popup
- **Cross-Browser Support**: Works with Chrome and Edge (Chromium-based)

## Privacy Considerations

The extension implements privacy-by-design:

- No automatic content extraction
- No browsing history access
- No persistent storage
- User-initiated actions only
- No tracking or analytics

## Future Enhancements

Potential improvements:

- **Content Script**: Automatic text selection from web pages
- **History Storage**: Save analysis history (with user consent)
- **Export Functionality**: Download summaries as PDF/text
- **Policy Comparison**: Compare multiple policies side-by-side
- **Bookmarking**: Save favorite analyses
- **Dark Mode**: Theme customization

## Browser Compatibility

- Chrome 88+ (Manifest V3 support)
- Edge 88+ (Chromium-based)
- Firefox (requires Manifest V2 conversion)
- Safari (requires Web Extension conversion)

