const form = document.getElementById("paymentForm");

if (form) {
  const paymentOptions = document.querySelectorAll(".payment-option");
  const paymentRadios = document.querySelectorAll('input[name="paymentMethod"]');
  const cardDetails = document.getElementById("cardDetails");
  const alternatePayment = document.getElementById("alternatePayment");
  const alternateMessage = document.getElementById("alternateMessage");
  const formStatus = document.getElementById("formStatus");
  const cardNumber = document.getElementById("cardNumber");
  const expiryDate = document.getElementById("expiryDate");
  const cvv = document.getElementById("cvv");

  function setError(input, message) {
    const group = input.closest(".payment-form-group");
    group.classList.toggle("payment-form-group-invalid", Boolean(message));
    group.querySelector(".payment-error-message").textContent = message;
  }

  function validateRequired(input, label) {
    const valid = input.value.trim() !== "";
    setError(input, valid ? "" : `${label} is required.`);
    return valid;
  }

  function clearErrors() {
    form.querySelectorAll(".payment-form-group").forEach((group) => {
      group.classList.remove("payment-form-group-invalid");
      group.querySelector(".payment-error-message").textContent = "";
    });
  }

  paymentRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
      paymentOptions.forEach((option) => {
        option.classList.toggle("payment-option-selected", option.contains(radio));
      });

      const isCard = radio.value === "card";
      cardDetails.hidden = !isCard;
      cardDetails.querySelectorAll("input").forEach((input) => {
        input.disabled = !isCard;
      });
      alternatePayment.hidden = isCard;

      if (!isCard) {
        const names = { paypal: "PayPal", applepay: "Apple Pay" };
        alternateMessage.textContent = `${names[radio.value]} processing is not connected in this demo.`;
      }

      clearErrors();
      formStatus.textContent = "";
      formStatus.className = "payment-form-status";
    });
  });

  cardNumber.addEventListener("input", (event) => {
    const digits = event.target.value.replace(/\D/g, "").slice(0, 16);
    event.target.value = digits.replace(/(.{4})/g, "$1 ").trim();
  });

  expiryDate.addEventListener("input", (event) => {
    let digits = event.target.value.replace(/\D/g, "").slice(0, 4);
    if (digits.length > 2) {
      digits = `${digits.slice(0, 2)} / ${digits.slice(2)}`;
    }
    event.target.value = digits;
  });

  cvv.addEventListener("input", (event) => {
    event.target.value = event.target.value.replace(/\D/g, "").slice(0, 4);
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    formStatus.textContent = "";
    formStatus.className = "payment-form-status";

    const selectedMethod = form.querySelector('input[name="paymentMethod"]:checked').value;
    let valid = true;

    if (selectedMethod === "card") {
      const cardDigits = cardNumber.value.replace(/\D/g, "");
      const name = document.getElementById("cardholderName");
      const expiryMatch = expiryDate.value.match(/^(0[1-9]|1[0-2])\s\/\s\d{2}$/);
      const cvvValid = /^\d{3,4}$/.test(cvv.value);
      const cardValid = cardDigits.length === 16;
      const expiryValid = Boolean(expiryMatch);

      setError(cardNumber, cardValid ? "" : "Enter a valid 16-digit card number.");
      setError(expiryDate, expiryValid ? "" : "Use a valid MM / YY date.");
      setError(cvv, cvvValid ? "" : "Enter a valid 3 or 4-digit CVV.");

      valid = validateRequired(name, "Cardholder name") && cardValid && expiryValid && cvvValid;
    }

    valid = validateRequired(document.getElementById("streetAddress"), "Street address") && valid;
    valid = validateRequired(document.getElementById("city"), "City") && valid;
    valid = validateRequired(document.getElementById("postalCode"), "Postal code") && valid;
    valid = validateRequired(document.getElementById("country"), "Country") && valid;

    if (!valid) {
      formStatus.textContent = "Please correct the highlighted fields.";
      formStatus.classList.add("payment-form-status-error");
      form.querySelector(".payment-form-group-invalid input:not(:disabled), .payment-form-group-invalid select:not(:disabled)")?.focus();
      return;
    }

    formStatus.textContent = "Your details pass the demo checks. No payment was submitted or charged.";
    formStatus.classList.add("payment-form-status-success");
  });
}