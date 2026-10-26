const demoPaymentForm = document.getElementById("demoPaymentForm");

if (demoPaymentForm) {
  const cardNumber = document.getElementById("demoCardNumber");
  const cardholderName = document.getElementById("demoCardholderName");
  const expiryDate = document.getElementById("demoCardExpiry");
  const cvv = document.getElementById("demoCardCvv");
  const status = document.getElementById("demoPaymentStatus");

  function setFieldError(input, message) {
    const error = document.getElementById(`${input.id}Error`);
    const group = input.closest(".payment-form-group");
    error.textContent = message;
    input.setAttribute("aria-invalid", String(Boolean(message)));
    group.classList.toggle("payment-form-group-invalid", Boolean(message));
  }

  function passesLuhn(number) {
    const digits = number.replace(/\D/g, "");
    if (digits.length < 13 || digits.length > 19) {
      return false;
    }

    let sum = 0;
    for (let index = 0; index < digits.length; index += 1) {
      let digit = Number(digits[digits.length - 1 - index]);
      if (index % 2 === 1) {
        digit *= 2;
        if (digit > 9) {
          digit -= 9;
        }
      }
      sum += digit;
    }
    return sum % 10 === 0;
  }

  function isFutureExpiry(value) {
    const match = value.match(/^(0[1-9]|1[0-2])\s*\/\s*(\d{2}|\d{4})$/);
    if (!match) {
      return false;
    }

    const month = Number(match[1]);
    let year = Number(match[2]);
    if (match[2].length === 2) {
      year += 2000;
    }
    const now = new Date();
    return year > now.getFullYear()
      || (year === now.getFullYear() && month >= now.getMonth() + 1);
  }

  cardNumber.addEventListener("input", () => {
    const digits = cardNumber.value.replace(/\D/g, "").slice(0, 19);
    cardNumber.value = digits.replace(/(.{4})/g, "$1 ").trim();
    setFieldError(cardNumber, "");
  });

  expiryDate.addEventListener("input", () => {
    const digits = expiryDate.value.replace(/\D/g, "").slice(0, 6);
    if (digits.length > 2) {
      expiryDate.value = `${digits.slice(0, 2)} / ${digits.slice(2)}`;
    } else {
      expiryDate.value = digits;
    }
    setFieldError(expiryDate, "");
  });

  cvv.addEventListener("input", () => {
    cvv.value = cvv.value.replace(/\D/g, "").slice(0, 4);
    setFieldError(cvv, "");
  });

  [cardholderName, cardNumber, expiryDate, cvv].forEach((input) => {
    input.addEventListener("input", () => {
      status.textContent = "";
      status.className = "payment-form-status";
    });
  });

  demoPaymentForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const validNumber = passesLuhn(cardNumber.value);
    const validName = cardholderName.value.trim().length >= 2;
    const validExpiry = isFutureExpiry(expiryDate.value.trim());
    const validCvv = /^\d{3,4}$/.test(cvv.value);

    setFieldError(cardNumber, validNumber ? "" : "Enter a valid card number.");
    setFieldError(cardholderName, validName ? "" : "Enter the name shown on the card.");
    setFieldError(expiryDate, validExpiry ? "" : "Enter a valid future expiry date (MM / YY).");
    setFieldError(cvv, validCvv ? "" : "Enter a 3 or 4-digit security code.");

    if (!validNumber || !validName || !validExpiry || !validCvv) {
      status.textContent = "Please correct the highlighted card fields.";
      status.classList.add("payment-form-status-error");
      demoPaymentForm.querySelector('[aria-invalid="true"]')?.focus();
      return;
    }

    status.textContent = "Completing demo payment. No real charge will be made.";
    status.classList.add("payment-form-status-success");

    cardNumber.value = "";
    cardholderName.value = "";
    expiryDate.value = "";
    cvv.value = "";
    demoPaymentForm.submit();
  });
}
