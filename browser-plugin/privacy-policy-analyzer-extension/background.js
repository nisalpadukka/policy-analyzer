// background.js
// Background / service worker script.
// Calls backend Lambda API to analyse privacy policies.
// Falls back to a local mock summariser on error.

const ext = typeof browser !== "undefined" ? browser : chrome;

// TODO: put your real API Gateway / Lambda URL here
const ANALYSIS_API_URL =
  "https://abc123xyz.execute-api.ca-central-1.amazonaws.com/prod/analyz";

ext.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "SUMMARIZE_POLICY") {
    const policyText = request.text || "";

    (async () => {
      try {
        let summary = await summarizeViaBackend(policyText);
        sendResponse({ ok: true, summary });
      } catch (err) {
        console.error("Error during summarisation via backend:", err);
        const summary = mockSummarize(policyText);
        sendResponse({
          ok: false,
          summary,
          error: err && err.message ? err.message : String(err)
        });
      }
    })();

    // Keep the message channel open for async response.
    return true;
  }

  return false;
});

/**
 * Call the Lambda / API Gateway endpoint with the policy text.
 * Maps Lambda JSON into the structure expected by popup.js.
 */
async function summarizeViaBackend(policyText) {
  const trimmed = policyText.trim();
  const truncated =
    trimmed.length > 3000 ? trimmed.slice(0, 3000) : trimmed || "No text provided.";

  if (!ANALYSIS_API_URL || ANALYSIS_API_URL.startsWith("https://YOUR-API-ID")) {
    throw new Error("ANALYSIS_API_URL is not set.");
  }

  const resp = await fetch(ANALYSIS_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ policy_text: truncated })
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Backend API error: ${resp.status} ${text}`);
  }

  const data = await resp.json();

  if (!data || data.status !== "success" || !data.summary) {
    throw new Error("Backend response missing expected 'summary' field.");
  }

  const s = data.summary;

  // Map Lambda fields -> shape expected by popup.js
  const collect = s.data_collecting || {};
  const share = s.data_sharing || {};
  const retention = s.data_retention || {};
  const overallSeverity = s.overall_privacy_risk || "Unknown";

  const normaliseSeverity = (val) =>
    typeof val === "string" ? val.toLowerCase() : "";

  return {
    originalExcerpt: truncated,
    collection: {
      text: collect.details || "Not specified",
      severity: normaliseSeverity(collect.severity)
    },
    sharing: {
      text: share.details || "Not specified",
      severity: normaliseSeverity(share.severity)
    },
    retention: {
      text: retention.details || "Not specified",
      severity: normaliseSeverity(retention.severity)
    },
    overallRisk: {
      text: `Overall privacy risk assessed as ${overallSeverity}.`,
      severity: normaliseSeverity(overallSeverity)
    }
  };
}

/**
 * Mock summariser used as a fallback and for offline testing.
 */
function mockSummarize(policyText) {
  const truncated =
    policyText.length > 300
      ? policyText.slice(0, 300) + "..."
      : policyText || "No text selected.";

  return {
    originalExcerpt: truncated,
    collection: {
      text:
        "The policy appears to describe collection of limited personal information, such as basic identifiers and usage data needed to provide the service.",
      severity: "low"
    },
    sharing: {
      text:
        "The policy may allow sharing of information with service providers and other partners.",
      severity: "high"
    },
    retention: {
      text:
        "The policy suggests data is retained for as long as necessary to provide services or meet legal obligations.",
      severity: "medium"
    },
    overallRisk: {
      text:
        "Overall, this suggests a moderate privacy risk, especially due to third-party sharing and broad retention terms.",
      severity: "high"
    }
  };
}
