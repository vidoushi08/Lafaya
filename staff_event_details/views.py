from django.shortcuts import render


TASK_DETAILS = {
    "floral-styling-review": {
        "title": "Liam's 7th Birthday",
        "status": "confirmed",
        "theme": "Birthday",
        "date": "25 August 2026",
        "time": "18:00 - 23:00",
        "guests": "120 Attendees",
        "venue": "Sunset Garden Venue",
        "role": "Decorator",
        "services": [
            "Balloon Decoration",
            "DJ & Sound",
            "Photography",
            "Cake Table Setup",
            "Birthday Backdrop",
        ],
        "tasks": [
            {"label": "Prepare Balloon Decoration", "status": "In Progress", "status_class": "in-progress", "button": "View / Update"},
            {"label": "Set Up Birthday Backdrop", "status": "Pending", "status_class": "pending", "button": "View / Update"},
            {"label": "Prepare Table Decorations", "status": "Pending", "status_class": "pending", "button": "View / Update"},
        ],
    },
    "guest-list-check-in": {
        "title": "Leah's Birthday Bash",
        "status": "in progress",
        "theme": "Birthday",
        "date": "27 August 2026",
        "time": "19:00 - 23:30",
        "guests": "85 Attendees",
        "venue": "Palm Court Lounge",
        "role": "Guest Experience Lead",
        "services": [
            "Welcome Desk",
            "Seating Plan",
            "Name Tags",
            "Photo Booth",
            "Stage Styling",
        ],
        "tasks": [
            {"label": "Confirm RSVP arrivals", "status": "In Progress", "status_class": "in-progress", "button": "View / Update"},
            {"label": "Arrange welcome signage", "status": "Pending", "status_class": "pending", "button": "View / Update"},
            {"label": "Assign check-in team", "status": "Pending", "status_class": "pending", "button": "View / Update"},
        ],
    },
    "stage-sound-check": {
        "title": "Harbor Summit",
        "status": "scheduled",
        "theme": "Conference",
        "date": "03 September 2026",
        "time": "09:00 - 17:00",
        "guests": "380 Attendees",
        "venue": "Trianon Convention Centre",
        "role": "Audio Lead",
        "services": [
            "Stage Setup",
            "Live Streaming",
            "Recording",
            "Brand Signage",
            "Catering Support",
        ],
        "tasks": [
            {"label": "Test audio equipment", "status": "In Progress", "status_class": "in-progress", "button": "View / Update"},
            {"label": "Check streaming link", "status": "Pending", "status_class": "pending", "button": "View / Update"},
            {"label": "Brief presenters", "status": "Pending", "status_class": "pending", "button": "View / Update"},
        ],
    },
    "catering-schedule": {
        "title": "Oceanview Villa Event",
        "status": "needs review",
        "theme": "Seaside",
        "date": "11 September 2026",
        "time": "12:00 - 18:00",
        "guests": "160 Attendees",
        "venue": "Oceanview Villa",
        "role": "Catering Coordinator",
        "services": [
            "Appetizer Service",
            "Bar Setup",
            "Catering Team",
            "Guest Seating",
            "Table Styling",
        ],
        "tasks": [
            {"label": "Confirm supplier arrivals", "status": "In Progress", "status_class": "in-progress", "button": "View / Update"},
            {"label": "Review guest flow", "status": "Pending", "status_class": "pending", "button": "View / Update"},
            {"label": "Finalize beverage stations", "status": "Pending", "status_class": "pending", "button": "View / Update"},
        ],
    },
}


def detail(request, task_id):
    task = TASK_DETAILS.get(task_id, TASK_DETAILS["floral-styling-review"])
    return render(request, "staff_event_details/detail.html", {"task": task})
