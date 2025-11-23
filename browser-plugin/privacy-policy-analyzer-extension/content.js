// content.js
// Runs in the context of each web page.
// Responds to messages asking for the current text selection.

// Cross-browser alias: use `browser` if available, otherwise `chrome`.
const ext = typeof browser !== "undefined" ? browser : chrome;

ext.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "GET_SELECTION") {
    const selection = window.getSelection();
    const text = selection ? selection.toString().trim() : "";

    sendResponse({ text });

    // Synchronous response; no async work here.
    return false;
  }

  return false;
});
