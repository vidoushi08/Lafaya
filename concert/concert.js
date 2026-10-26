
document.addEventListener("DOMContentLoaded", function () {
    const dialog = document.getElementById("actionDialog");
    const dialogTitle = document.getElementById("dialogTitle");
    const dialogMessage = document.getElementById("dialogMessage");

    function showDialog(title, message) {
        dialogTitle.textContent = title;
        dialogMessage.textContent = message;

        if (typeof dialog.showModal === "function") {
            dialog.showModal();
        } else {
            alert(title + "\n\n" + message);
        }
    }

    // Mobile navigation
    const menuToggle = document.getElementById("menuToggle");
    const navigation = document.querySelector(".navbar nav");

    menuToggle.addEventListener("click", function () {
        navigation.classList.toggle("open");
    });

    navigation.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
            navigation.classList.remove("open");
        });
    });

    // Close the dialog
    document.getElementById("dialogClose").addEventListener("click", function () {
        dialog.close();
    });

    document.getElementById("dialogOkay").addEventListener("click", function () {
        dialog.close();
    });

    // Watch teaser
    document.getElementById("teaserButton").addEventListener("click", function () {
        showDialog(
            "Concert Teaser",
            "The concert teaser will be available here soon."
        );
    });

    // Ticket selection
    document.querySelectorAll(".select-button").forEach(function (button) {
        button.addEventListener("click", function () {
            const packageName = button.dataset.package;
            const price = Number(button.dataset.price).toLocaleString("en-US");

            showDialog(
                "Ticket Package Selected",
                packageName + " — Rs " + price +
                ". Booking functionality can be connected to the backend next."
            );
        });
    });

    // Compare ticket tiers
    document.getElementById("compareButton").addEventListener("click", function () {
        const packages = Array.from(
            document.querySelectorAll(".ticket-card")
        );

        const comparison = packages.map(function (card) {
            const name = card.querySelector(".ticket-header h3").textContent.trim();
            const price = card.querySelector(".price");

            return name + ": " + (price ? price.textContent.trim() : "Price unavailable");
        });

        showDialog("Compare Ticket Tiers", comparison.join("\n"));
    });

    // Card navigation controls
    document.querySelectorAll("[data-scroll]").forEach(function (button) {
        button.addEventListener("click", function () {
            const target = document.getElementById(button.dataset.scroll);

            if (!target) return;

            const direction = Number(button.dataset.direction);

            const cards = target.querySelectorAll(
                ".venue-card, .production-card, .ticket-card"
            );

            if (cards.length > 0) {
                const currentIndex = Number(target.dataset.cardIndex || 0);
                const nextIndex = Math.max(
                    0,
                    Math.min(cards.length - 1, currentIndex + direction)
                );

                target.dataset.cardIndex = nextIndex;

                cards[nextIndex].scrollIntoView({
                    behavior: "smooth",
                    block: "nearest",
                    inline: "nearest"
                });
            } else {
                target.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
            }
        });
    });
});
