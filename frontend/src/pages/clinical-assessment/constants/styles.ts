/**
 * Clinical Assessment Styles
 *
 * CSS styles to fix input/radio button blocking issues in assessment components.
 */

export const assessmentStyles = `
  input[type="checkbox"],
  input[type="radio"] {
    pointer-events: auto !important;
    z-index: 9999 !important;
    position: relative !important;
    opacity: 1 !important;
    visibility: visible !important;
  }

  /* Radio button checked state styling */
  input[type="radio"]:checked {
    background-color: #3b82f6 !important;
    border-color: #3b82f6 !important;
    color: white !important;
  }

  input[type="radio"]:checked::before {
    content: '' !important;
    display: block !important;
    width: 6px !important;
    height: 6px !important;
    border-radius: 50% !important;
    background-color: white !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
  }

  input[type="radio"]:checked + span {
    color: #3b82f6 !important;
    font-weight: 600 !important;
  }

  /* Ensure radio buttons are visible */
  input[type="radio"] {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 20px !important;
    height: 20px !important;
    border: 2px solid #d1d5db !important;
    border-radius: 50% !important;
    background-color: white !important;
    cursor: pointer !important;
    position: relative !important;
    transition: all 0.2s ease !important;
  }

  input[type="radio"]:hover {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
  }
`;
