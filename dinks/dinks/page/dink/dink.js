frappe.pages['dink'].on_page_load = function(wrapper) {
    new DinkCourtPage(wrapper);
}

DinkCourtPage = Class.extend({
    init: function(wrapper) {
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: 'Dink Court Booking',
            single_column: true
        });
        this.current_court = ''; // Initialize to empty string, it's determined dynamically
        this.courts = []; // Will hold the courts fetched from the backend
        this.make();
    },

    make: function() {
        let me = this;

        $(this.page.main).html('<div class="dink-court-container"></div>');
        this.container = $(this.page.main).find('.dink-court-container');

        this.fetch_courts(() => { // Fetch courts before rendering anything else
            this.add_court_filters();
            this.add_booking_calendar();
        });
    },

    fetch_courts: function(callback) {
        let me = this;
        frappe.call({
            method: "dinks.dinks.page.dink.dink.get_courts", //Backend method to get the courts
            callback: function(r) {
                if (r.message) {
                    me.courts = r.message;
                    if (me.courts.length > 0) {
                        me.current_court = me.courts[0]; // Set initial court
                    }
                    callback(); // Execute the callback function to continue rendering
                } else {
                    frappe.msgprint("Failed to fetch courts.");
                }
            },
            async: true // Ensure asynchronous loading
        });
    },

    add_court_filters: function() {
        let me = this;

        let filterHtml = `
            <div class="court-filters-wrapper">
                <div class="court-filters d-flex gap-4 mb-4 p-3">
                    ${this.courts.map((court, index) => `
                        <button class="btn court-btn ${court === this.current_court ? 'btn-primary active' : 'btn-outline-primary'}"
                                data-court="${court}">
                            ${court}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        this.container.append(filterHtml);

        this.container.find('.court-btn').on('click', function() {
            let courtName = $(this).data('court');
            me.update_court_view(courtName);
        });
    },

    add_booking_calendar: function() {
        let me = this;
        let dates = this.get_next_dates(30);

        let calendarHtml = `<div class="booking-calendar-wrapper"><div class="booking-calendar">`;

        dates.forEach(date => {
            calendarHtml += `<div class="date-column"><div class="date-header">${date}</div><div class="time-slots-container">`;

            frappe.call({
                method: "dinks.dinks.page.dink.dink.get_court_time_slots",
                args: {
                    court: me.current_court,
                    date: date
                },
                callback: function(r) {
                    if (r.message) {
                        r.message.forEach(slot => {
                            calendarHtml += `
                                <div class="time-slot ${slot.is_available ? 'available' : 'booked'}"
                                     data-court="${me.current_court}"
                                     data-slots="${slot.is_available ? '1' : '0'}"
                                     data-time="${slot.time_slot}"
                                     data-date="${date}"
                                     data-is-available="${slot.is_available}">
                                    <div class="time">${slot.time_slot}</div>
                                    <div class="amount">₹600</div>
                                    <div class="slot-left">Slot Left: ${slot.is_available ? (slot.is_available ? '1' : '0') : (slot.customer_name ? 'Booked by: ' + slot.customer_name : 'Booked')}</div>
                                </div>
                            `;
                        });
                        calendarHtml += `</div></div>`; // Close time-slots-container and date-column

                        if (dates.indexOf(date) === dates.length - 1) {
                            calendarHtml += `</div></div>`; // Close booking-calendar and booking-calendar-wrapper
                            me.container.append(calendarHtml); // Append instead of overwrite
                            me.add_custom_styles();
                            me.attach_time_slot_click_event();
                        } else {
                            me.container.find(".booking-calendar").html(calendarHtml.substring(calendarHtml.indexOf("<div class=\"booking-calendar\">") + "<div class=\"booking-calendar\">".length)); //update the booking calendar part only
                        }
                    }
                },
                async: false
            });
        });
    },

    attach_time_slot_click_event: function() {
        let me = this;
        this.container.find('.time-slot').on('click', function() { // Attach click event to all slots
            let selectedDate = $(this).data('date');
            let selectedTime = $(this).data('time');
            let court = $(this).data('court'); // get the court name also
            let isAvailable = $(this).data('is-available');

            if (isAvailable) {
                me.show_booking_popup(selectedDate, selectedTime, court); // Pass the court to the popup
            } else {
                me.show_view_details_popup(selectedDate, selectedTime, court);
            }
        });
    },

    show_booking_popup: function(date, time, court) { // Receive the court as parameter
        let popupHtml = `
            <div class="booking-popup-overlay">
                <div class="booking-popup">
                    <p><strong>Court:</strong> ${court} <strong>Date:</strong> ${date} <strong>Time:</strong> ${time}</p>
                    <button class="btn btn-primary book-btn">BOOK</button>
                    <button class="btn btn-outline-primary partial-book-btn">Partial Booking</button>
                    <button class="btn btn-danger close-popup">Close</button>
                </div>
            </div>
        `;
        $('body').append(popupHtml);

        // Close popup
        $('.close-popup').on('click', function() {
            $('.booking-popup-overlay').remove();
        });

        // Booking confirmation
        $('.book-btn').on('click', function() {
            //add input fields only when book button is clicked.
            let inputHtml = `<input type="text" id="booking-name" placeholder="Name" class="form-control mb-2">
            <input type="text" id="booking-phone" placeholder="Phone Number" class="form-control mb-2">`;
            $('.booking-popup').prepend(inputHtml);

            //overwrite the click event to get the values.
            $('.book-btn').off('click').on('click', function(){
                let name = $('#booking-name').val();
                let phone = $('#booking-phone').val();
                if(!name || !phone){
                    frappe.msgprint("Please enter name and phone number.");
                    return;
                }
                frappe.msgprint(`Booking confirmed for ${name} with phone ${phone} on ${date} at ${time} on ${court}`);
                $('.booking-popup-overlay').remove();
            });

        });

        $('.partial-book-btn').on('click', function() {
            frappe.msgprint(`Partial booking initiated for ${date} at ${time} on ${court}`);
            $('.booking-popup-overlay').remove();
        });
    },

    show_view_details_popup: function(date, time, court) {
        let me = this;
        frappe.call({
            method: "dinks.dinks.page.dink.dink.get_booking_details",
            args: {
                court: court,
                date: date,
                time: time
            },
            callback: function(r) {
                if (r.message) {
                    let customerName = r.message.customer_name || 'N/A';
                    let customerPhone = r.message.customer_phone || 'N/A';

                    let popupHtml = `
                        <div class="booking-popup-overlay">
                            <div class="booking-popup">
                                <p><strong>Court:</strong> ${court} <strong>Date:</strong> ${date} <strong>Time:</strong> ${time}</p>
                                <p><strong>Customer Name:</strong> ${customerName}</p>
                                <p><strong>Customer Phone:</strong> ${customerPhone}</p>
                                <button class="btn btn-danger close-popup">Close</button>
                            </div>
                        </div>
                    `;
                    $('body').append(popupHtml);

                    // Close popup
                    $('.close-popup').on('click', function() {
                        $('.booking-popup-overlay').remove();
                    });
                } else {
                    frappe.msgprint("Could not retrieve booking details.");
                }
            },
            async: false
        });
    },

    update_court_view: function(courtName) {
        this.current_court = courtName;
        this.container.find('.court-btn').removeClass('btn-primary active').addClass('btn-outline-primary');
        this.container.find(`.court-btn[data-court="${courtName}"]`).removeClass('btn-outline-primary').addClass('btn-primary active');

        frappe.show_alert({
            message: `Viewing ${courtName}`,
            indicator: 'green'
        }, 3);

        this.refresh_booking_data(courtName);
        this.update_booking_calendar();
    },

    update_booking_calendar: function() {
        // Clear the existing calendar and rebuild it
        this.container.find('.booking-calendar-wrapper').remove();
        this.add_booking_calendar();
    },

    refresh_booking_data: function(courtName) {
        console.log(`Refreshing booking data for ${courtName}`);
    },

    get_next_dates: function(count) {
        let dates = [];
        let currentDate = new Date();

        for(let i = 0; i < count; i++) {
            let date = new Date(currentDate);
            date.setDate(date.getDate() + i);
            dates.push(date.toLocaleDateString('en-US', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            }));
        }

        return dates;
    },

    add_custom_styles: function() {
    $('<style>')
        .prop('type', 'text/css')
        .html(`
            .dink-court-container {
                height: calc(100vh - 60px);
                display: flex;
                flex-direction: column;
                width: 100%; /* Make the container full width */
            }

            .court-filters-wrapper {
                position: sticky;
                top: 0;
                z-index: 100;
                background: white;
                border-bottom: 1px solid #e5e7eb;
                width: 100%; /* Make the filter wrapper full width */
            }

            .court-filters {
                padding: 1rem;
                display: flex;
                gap: 1rem;
                justify-content: flex-start; /* Align items to the left */
                align-items: flex-start; /* Align items to the left */
                width: 100%; /* Make the filters full width */
            }

            .booking-calendar-wrapper {
                flex: 1;
                overflow: hidden;
                position: relative;
                width: 100%; /* Make the calendar wrapper full width */
            }

            .booking-calendar {
                display: flex;
                height: 100%;
                overflow-x: auto;
                gap: 1px;
                background: #f0f0f0;
                width: 100%; /* Make the calendar full width */
            }

            .date-column {
                flex: 0 0 180px;
                display: flex;
                flex-direction: column;
                background: white;
                height: 100%;
            }

            .date-header {
                padding: 1rem;
                background: #1a1a1a;
                color: white;
                text-align: center;
                font-weight: 500;
            }

            .time-slots-container {
                flex: 1;
                overflow-y: auto;
                overflow-x: hidden;
            }

            .time-slot {
                padding: 1rem;
                border-bottom: 1px solid #e5e7eb;
                cursor: pointer;
                transition: all 0.2s;
                background: white;
                margin: 5px; /* Add space around each time slot */
                border: 1px solid #ccc; /* Add a border */
                border-radius: 5px; /* Add rounded corners */
            }

            .time-slot:hover {
                background: #f8f9fa;
                transform: scale(1.02);
            }

            .time-slot.booked {
                background: #0066FF;
                color: white;
            }

            .court-btn {
                min-width: 150px; /* Increased width */
                padding: 0.75rem 1.5rem; /* Increased padding */
                font-size: 1.1rem; /* Increased font size for better readability */
                /*border: 2px solid transparent; /* Removed border */
                border-radius: 0.5rem; /* Added border radius */
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* Added shadow */
                transition: all 0.3s ease;
                text-align: center; /* Center the text */
            }

            .court-btn:hover {
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); /* Increased shadow on hover */
                transform: translateY(-2px); /* Slight lift on hover */
            }

            .btn-primary {
                background-color: #0066FF !important;
                border-color: transparent !important; /* Remove border color */
                color: white !important;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); /* Added shadow */
            }

            .btn-primary:hover {
                background-color: #0052CC !important;
                border-color: transparent !important; /* Remove border color */
                color: white !important;
            }

            .btn-outline-primary {
                color: black; /* Set default text color to black */
                border-color: transparent; /* Remove border color */
                background-color: white; /* Ensure a white background */
            }

            .btn-outline-primary:hover {
                background-color: #0066FF;
                border-color: transparent; /* Remove border color */
                color: white;
            }

            .time { font-weight: 500; margin-bottom: 0.5rem; }
            .amount { color: #666; margin-bottom: 0.5rem; }
            .slot-left { font-size: 0.9em; }

            /* Custom scrollbars */
            .booking-calendar::-webkit-scrollbar {
                height: 8px;
            }

            .booking-calendar::-webkit-scrollbar-track {
                background: #f1f1f1;
            }

            .booking-calendar::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 4px;
            }

            .booking-calendar::-webkit-scrollbar-thumb:hover {
                background: #555;
            }

            .time-slots-container::-webkit-scrollbar {
                width: 8px;
            }

            .time-slots-container::-webkit-scrollbar-track {
                background: #f1f1f1;
            }

            .time-slots-container::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 4px;
            }

            .time-slots-container::-webkit-scrollbar-thumb:hover {
                background: #555;
            }

            .booking-popup-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }

            .booking-popup {
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
                text-align: center;
                display: flex;
                flex-direction: column;
                gap: 10px;
                width: 300px;
            }

            .booking-popup button {
                width: 100%;
            }

        `)
        .appendTo('head');

    }
});
