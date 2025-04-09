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
        this.current_court = 'DINK COURT 1';
        this.make();
    },

    make: function() {
        let me = this;

        $(this.page.main).html('<div class="dink-court-container"></div>');
        this.container = $(this.page.main).find('.dink-court-container');

        this.add_court_filters();
        this.add_booking_calendar();
        this.update_court_view(this.current_court);
    },

    add_court_filters: function() {
        let courts = ['DINK COURT 1', 'DINK COURT 2', 'DINK COURT 3', 'DINK COURT 4',
                     'DINK COURT 5', 'DINK COURT 6'];

        let filterHtml = `
            <div class="court-filters-wrapper">
                <div class="court-filters d-flex gap-4 mb-4 p-3">
                    ${courts.map((court) => `
                        <button class="btn court-btn ${court === this.current_court ? 'btn-primary active' : 'btn-outline-primary'}"
                                data-court="${court}">
                            ${court}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        this.container.append(filterHtml);

        let me = this;
        this.container.find('.court-btn').on('click', function() {
            let courtName = $(this).data('court');
            me.update_court_view(courtName);
        });
    },

    add_booking_calendar: function() {
        let me = this;
        let timeSlots = [
            '6:00 am', '7:00 am', '8:00 am', '9:00 am', '10:00 am',
            '11:00 am', '12:00 pm', '1:00 pm'
        ];

        let dates = this.get_next_dates(30); // 30 days

        let calendarHtml = `
            <div class="booking-calendar-wrapper">
                <div class="booking-calendar">
                    ${dates.map(date => `
                        <div class="date-column">
                            <div class="date-header">${date}</div>
                            <div class="time-slots-container">
                                ${timeSlots.map(time => {
                                    let isBooked = time.includes('10:00') || time.includes('11:00') || time.includes('12:00');
                                    return `
                                        <div class="time-slot ${isBooked ? 'booked' : ''}"
                                             data-date="${date}"
                                             data-time="${time}">
                                            <div class="time">${time}</div>
                                            <div class="amount">₹${isBooked ? '700' : '600'}</div>
                                            <div class="slot-left">Slot Left: ${isBooked ? '0' : '1'}</div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        this.container.append(calendarHtml);
        this.add_custom_styles();

        // Click event for available slots
        this.container.on('click', '.time-slot:not(.booked)', function() {
            let selectedDate = $(this).data('date');
            let selectedTime = $(this).data('time');
            me.show_booking_popup(selectedDate, selectedTime);
        });
    },

    show_booking_popup: function(date, time) {
        let popupHtml = `
            <div class="booking-popup-overlay">
                <div class="booking-popup">
                    <p><strong>Date:</strong> ${date} <strong>Time:</strong> ${time}</p>
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
            frappe.msgprint(`Booking confirmed for ${date} at ${time}`);
            $('.booking-popup-overlay').remove();
        });

        $('.partial-book-btn').on('click', function() {
            frappe.msgprint(`Partial booking initiated for ${date} at ${time}`);
            $('.booking-popup-overlay').remove();
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
    },

    refresh_booking_data: function(courtName) {
        console.log(`Refreshing booking data for ${courtName}`);
    },

    get_next_dates: function(count) {
        let dates = [];
        let currentDate = new Date();

        for (let i = 0; i < count; i++) {
            let date = new Date(currentDate);
            date.setDate(date.getDate() + i);
            dates.push(date.toLocaleDateString('en-GB')); // Adjusted to match your format
        }

        return dates;
    },

    add_custom_styles: function() {
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .booking-popup-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                }

                .booking-popup {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
                }

                .booking-popup button {
                    display: block;
                    width: 100%;
                    margin-top: 10px;
                }

                .time-slot {
                    padding: 1rem;
                    border-bottom: 1px solid #e5e7eb;
                    cursor: pointer;
                    transition: all 0.2s;
                    background: white;
                }

                .time-slot:hover {
                    background: #f8f9fa;
                    transform: scale(1.02);
                }

                .time-slot.booked {
                    background: #0066FF;
                    color: white;
                    pointer-events: none;
                }

                .btn-primary {
                    background-color: #0066FF;
                    color: white;
                }

                .btn-outline-primary {
                    background-color: white;
                    color: black;
                    border: 1px solid black;
                }

                .btn-danger {
                    background-color: red;
                    color: white;
                }
            `)
            .appendTo('head');
    }
});
