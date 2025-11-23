// popup.js
// 1. On load, ask the content script for the current selection.
// 2. When "Summarize" is clicked, send text to background for summarisation.
// 3. Display structured summary + severity badges.

const ext = typeof browser !== "undefined" ? browser : chrome;

document.addEventListener("DOMContentLoaded", async () => {
  const selectedTextEl = document.getElementById("selectedText");
  const summarizeBtn = document.getElementById("summarizeBtn");
  const statusEl = document.getElementById("status");

  const collectionTextEl = document.getElementById("collectionText");
  const sharingTextEl = document.getElementById("sharingText");
  const retentionTextEl = document.getElementById("retentionText");
  const overallTextEl = document.getElementById("overallText");

  const collectionSeverityEl = document.getElementById("collectionSeverity");
  const sharingSeverityEl = document.getElementById("sharingSeverity");
  const retentionSeverityEl = document.getElementById("retentionSeverity");
  const overallSeverityEl = document.getElementById("overallSeverity");

  function setBadge(el, severity) {
    el.className = "badge";

    if (!severity) {
      el.textContent = "";
      return;
    }

    const level = severity.toLowerCase();
    if (level === "low") {
      el.classList.add("badge-low");
      el.textContent = "Low";
    } else if (level === "medium") {
      el.classList.add("badge-medium");
      el.textContent = "Medium";
    } else if (level === "high") {
      el.classList.add("badge-high");
      el.textContent = "High";
    } else {
      el.textContent = severity;
    }
  }

  // STEP 1: get selected text from the active tab.
  try {
    const tabs = await ext.tabs.query({ active: true, currentWindow: true });
    const tab = tabs && tabs[0];

    if (tab && tab.id != null) {
      const response = await ext.tabs.sendMessage(tab.id, {
        type: "GET_SELECTION"
      });

      if (response && response.text) {
        selectedTextEl.value = response.text;
      } else {
        selectedTextEl.value =
          "Could not read selection on this page. You can paste privacy policy text here and click Summarize.";
      }
    } else {
      selectedTextEl.value =
        "No active tab found. Open a page with a privacy policy and try again.";
    }
  } catch (err) {
    console.error("Error getting selection:", err);
    selectedTextEl.value =
      "Could not read selection. Make sure the page is fully loaded.";
  }

  // STEP 2: when user clicks "Summarize", call the background script.
  summarizeBtn.addEventListener("click", async () => {
    const text = selectedTextEl.value.trim();
    if (!text) {
      statusEl.textContent =
        "Please highlight some privacy policy text on the page first.";
      return;
    }

    statusEl.textContent = "Summarizing...";
    collectionTextEl.textContent = "";
    sharingTextEl.textContent = "";
    retentionTextEl.textContent = "";
    overallTextEl.textContent = "";

    setBadge(collectionSeverityEl, "");
    setBadge(sharingSeverityEl, "");
    setBadge(retentionSeverityEl, "");
    setBadge(overallSeverityEl, "");

    try {
      const response = await ext.runtime.sendMessage({
        type: "SUMMARIZE_POLICY",
        text
      });

      if (!response || !response.ok) {
        statusEl.textContent = "Error summarizing text.";
        return;
      }

      const summary = response.summary || {};
      statusEl.textContent = "Summary generated.";

      collectionTextEl.textContent = summary.collection?.text || "";
      sharingTextEl.textContent = summary.sharing?.text || "";
      retentionTextEl.textContent = summary.retention?.text || "";
      overallTextEl.textContent = summary.overallRisk?.text || "";

      setBadge(collectionSeverityEl, summary.collection?.severity);
      setBadge(sharingSeverityEl, summary.sharing?.severity);
      setBadge(retentionSeverityEl, summary.retention?.severity);
      setBadge(overallSeverityEl, summary.overallRisk?.severity);
    } catch (err) {
      console.error("Error calling background:", err);
      statusEl.textContent = "Unexpected error while summarizing.";
    }
  });
});
