// Handles updating the UI.

import {
  statusElement,
  instructionsElement,
  spinnerElement,
} from "./elements.js";

/**
 * Sets the status message in the UI with appropriate styling.
 * @param {string} message - The message to display.
 * @param {string} type - The type of message ('default', 'error', 'success', 'warning', 'info').
 */
export function setStatus(message, type = "default") {
  statusElement.textContent = message;
  statusElement.className = "status-message";
  switch (type) {
    case "error":
      statusElement.classList.add("status-red");
      break;
    case "success":
      statusElement.classList.add("status-green");
      break;
    case "warning":
      statusElement.classList.add("status-orange");
      break;
  }
}

/**
 * Sets the instructions HTML content in the UI.
 * @param {string} htmlContent - The HTML content to display in the instructions section.
 */
export function setInstructions(htmlContent) {
  instructionsElement.innerHTML = htmlContent;
}

/**
 * Shows the loading spinner.
 */
export function showSpinner() {
  spinnerElement.style.display = "inline-block"; // Use inline-block to keep it next to text
}

/**
 * Hides the loading spinner.
 */
export function hideSpinner() {
  spinnerElement.style.display = "none";
}
