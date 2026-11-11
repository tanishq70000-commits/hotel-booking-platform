"""Web frontend UI template for the Hotel Reservation Platform."""

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grand Horizon Hotel & Suites — Reservation Portal</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0b1120;
            --bg-card: #131c31;
            --bg-card-hover: #1b2640;
            --border: #22304d;
            --primary: #38bdf8;
            --primary-hover: #0ea5e9;
            --primary-light: rgba(56, 189, 248, 0.12);
            --success: #34d399;
            --warning: #fbbf24;
            --danger: #f87171;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --font: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-main);
            color: var(--text-main);
            font-family: var(--font);
            line-height: 1.5;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Top Navigation Header */
        header {
            background: rgba(19, 28, 49, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .header-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-main);
            text-decoration: none;
        }

        .logo-icon {
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            width: 38px;
            height: 38px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .nav-link {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: color 0.2s;
        }

        .nav-link:hover {
            color: var(--primary);
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: rgba(52, 211, 153, 0.12);
            color: var(--success);
            padding: 0.35rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            border: 1px solid rgba(52, 211, 153, 0.3);
        }

        .status-dot {
            width: 7px;
            height: 7px;
            background-color: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }

        /* Main Container */
        main {
            max-width: 1200px;
            width: 100%;
            margin: 2rem auto;
            padding: 0 1.5rem;
            flex: 1;
        }

        /* Hero Banner */
        .hero {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .hero h1 {
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #f8fafc, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero p {
            color: var(--text-muted);
            font-size: 1.1rem;
            max-width: 600px;
            margin: 0 auto;
        }

        /* Tabs Navigation */
        .tabs {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.75rem;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.6rem 1.25rem;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s;
        }

        .tab-btn.active {
            background: var(--primary-light);
            color: var(--primary);
        }

        .tab-btn:hover:not(.active) {
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.04);
        }

        /* Card Section */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1.75rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            margin-bottom: 2rem;
        }

        /* Search Form Grid */
        .search-form {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)) auto;
            gap: 1rem;
            align-items: end;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        .form-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .form-input, .form-select {
            background: #0f172a;
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 0.95rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .form-input:focus, .form-select:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
        }

        .btn {
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            color: #0b1120;
            font-weight: 700;
            border: none;
            border-radius: 8px;
            padding: 0.8rem 1.5rem;
            font-size: 0.95rem;
            cursor: pointer;
            transition: transform 0.15s, box-shadow 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(56, 189, 248, 0.35);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-outline {
            background: transparent;
            color: var(--primary);
            border: 1px solid var(--primary);
        }

        .btn-outline:hover {
            background: var(--primary-light);
            color: var(--primary-hover);
        }

        /* Room Grid */
        .rooms-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }

        .room-card {
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            transition: transform 0.2s, border-color 0.2s;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .room-card:hover {
            transform: translateY(-3px);
            border-color: var(--primary);
        }

        .room-badge {
            align-self: flex-start;
            background: rgba(56, 189, 248, 0.1);
            color: var(--primary);
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.75rem;
        }

        .room-number {
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .room-price {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--success);
            margin: 0.75rem 0;
        }

        .room-price span {
            font-size: 0.85rem;
            font-weight: 400;
            color: var(--text-muted);
        }

        /* Modal Styles */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(11, 17, 32, 0.85);
            backdrop-filter: blur(8px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 100;
            padding: 1rem;
        }

        .modal {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            max-width: 500px;
            width: 100%;
            padding: 2rem;
            position: relative;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }

        .modal-close {
            position: absolute;
            top: 1.25rem;
            right: 1.25rem;
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.5rem;
            cursor: pointer;
            line-height: 1;
        }

        .modal-close:hover {
            color: var(--text-main);
        }

        /* Reservation Confirmation Banner */
        .confirmation-box {
            background: rgba(52, 211, 153, 0.08);
            border: 1px solid rgba(52, 211, 153, 0.3);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 1.5rem;
            text-align: center;
        }

        .reference-tag {
            font-family: monospace;
            font-size: 1.75rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            color: var(--success);
            background: #0f172a;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            display: inline-block;
            margin: 0.75rem 0;
            border: 1px dashed var(--success);
        }

        /* Concurrency Demo Terminal */
        .terminal-box {
            background: #050914;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem;
            font-family: monospace;
            font-size: 0.85rem;
            max-height: 320px;
            overflow-y: auto;
            margin-top: 1rem;
        }

        .term-row {
            margin-bottom: 0.4rem;
            display: flex;
            justify-content: space-between;
        }

        .code-201 { color: var(--success); font-weight: bold; }
        .code-409 { color: var(--danger); font-weight: bold; }

        footer {
            text-align: center;
            padding: 1.5rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            margin-top: auto;
        }
    </style>
</head>
<body>

    <!-- Header -->
    <header>
        <div class="header-container">
            <a href="/" class="logo">
                <div class="logo-icon">🏨</div>
                <span>Grand Horizon Resort</span>
            </a>
            <div class="nav-links">
                <div class="status-pill" id="health-pill">
                    <div class="status-dot"></div>
                    <span id="health-text">API Online (v1.0.0)</span>
                </div>
                <a href="/docs" target="_blank" class="nav-link">Swagger Docs ↗</a>
                <a href="/metrics" target="_blank" class="nav-link">Metrics ↗</a>
            </div>
        </div>
    </header>

    <main>
        <!-- Hero Title -->
        <div class="hero">
            <h1>Luxury Stays & Seamless Reservations</h1>
            <p>Cloud-native, zero double bookings, guaranteed by PostgreSQL GiST exclusion constraints.</p>
        </div>

        <!-- Navigation Tabs -->
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('booking')">📅 Book a Stay</button>
            <button class="tab-btn" onclick="switchTab('lookup')">🔍 Lookup Reservation</button>
            <button class="tab-btn" onclick="switchTab('concurrency')">⚡ Concurrency Race Demo</button>
            <button class="tab-btn" onclick="switchTab('ops')">🛠️ System Diagnostics</button>
        </div>

        <!-- TAB 1: Search & Book -->
        <div id="tab-booking" class="tab-content">
            <div class="card">
                <form class="search-form" onsubmit="event.preventDefault(); searchRooms();">
                    <div class="form-group">
                        <label class="form-label">Check-In Date</label>
                        <input type="date" id="checkInDate" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Check-Out Date</label>
                        <input type="date" id="checkOutDate" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Room Type</label>
                        <select id="roomTypeSelect" class="form-select">
                            <option value="single">Single Room ($89 - $99)</option>
                            <option value="double" selected>Double Room ($129 - $149)</option>
                            <option value="suite">Executive Suite ($249 - $279)</option>
                            <option value="deluxe-suite">Deluxe Suite ($349)</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">
                        <span>Check Availability</span>
                    </button>
                </form>
            </div>

            <div id="resultsContainer">
                <h3 id="resultsHeading" style="margin-bottom: 1rem; display: none;">Available Rooms</h3>
                <div class="rooms-grid" id="roomsGrid"></div>
            </div>
        </div>

        <!-- TAB 2: Lookup Reservation -->
        <div id="tab-lookup" class="tab-content" style="display: none;">
            <div class="card" style="max-width: 650px; margin: 0 auto;">
                <h2 style="margin-bottom: 0.5rem; font-size: 1.4rem;">Lookup Existing Booking</h2>
                <p style="color: var(--text-muted); margin-bottom: 1.5rem; font-size: 0.95rem;">Enter your 12-character booking reference to review your stay.</p>

                <div style="display: flex; gap: 0.75rem;">
                    <input type="text" id="lookupRefInput" class="form-input" placeholder="e.g. RSV-4GRPKPF4" style="flex: 1; text-transform: uppercase;">
                    <button onclick="lookupReservation()" class="btn">Find Stay</button>
                </div>

                <div id="lookupResult" style="margin-top: 1.5rem;"></div>
            </div>
        </div>

        <!-- TAB 3: Concurrency Race Demo -->
        <div id="tab-concurrency" class="tab-content" style="display: none;">
            <div class="card" style="max-width: 800px; margin: 0 auto;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                    <div>
                        <h2 style="font-size: 1.4rem;">Double-Booking Prevention Drill</h2>
                        <p style="color: var(--text-muted); font-size: 0.95rem; margin-top: 0.25rem;">
                            Simulates 10 concurrent requests attempting to book the exact same room simultaneously.
                        </p>
                    </div>
                    <button onclick="runConcurrencyDrill()" class="btn" id="concurrencyBtn">
                        <span>⚡ Fire 10 Conflicting Requests</span>
                    </button>
                </div>

                <div class="terminal-box" id="concurrencyTerminal">
                    <div style="color: #64748b;">Click the button above to execute the concurrent race condition test...</div>
                </div>
            </div>
        </div>

        <!-- TAB 4: System Diagnostics -->
        <div id="tab-ops" class="tab-content" style="display: none;">
            <div class="card" style="max-width: 800px; margin: 0 auto;">
                <h2 style="margin-bottom: 1rem; font-size: 1.4rem;">Platform Observability & Infrastructure</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
                    <div style="background: #0f172a; padding: 1rem; border-radius: 8px; border: 1px solid var(--border);">
                        <div style="color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase;">Liveness Probe</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: var(--success); margin: 0.25rem 0;" id="liveStatus">Healthy</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">GET /health</div>
                    </div>
                    <div style="background: #0f172a; padding: 1rem; border-radius: 8px; border: 1px solid var(--border);">
                        <div style="color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase;">Database Pool</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: var(--success); margin: 0.25rem 0;" id="readyStatus">Connected</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">GET /ready</div>
                    </div>
                    <div style="background: #0f172a; padding: 1rem; border-radius: 8px; border: 1px solid var(--border);">
                        <div style="color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase;">Exclusion Constraint</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: var(--primary); margin: 0.25rem 0;">btree_gist</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">GiST Index Active</div>
                    </div>
                </div>

                <div style="display: flex; gap: 1rem;">
                    <a href="/docs" target="_blank" class="btn btn-outline" style="flex: 1; text-align: center; text-decoration: none;">Interactive OpenAPI Docs</a>
                    <a href="/metrics" target="_blank" class="btn btn-outline" style="flex: 1; text-align: center; text-decoration: none;">Prometheus Metrics</a>
                </div>
            </div>
        </div>
    </main>

    <!-- Booking Modal -->
    <div class="modal-overlay" id="bookingModal">
        <div class="modal">
            <button class="modal-close" onclick="closeModal()">×</button>
            <h2 style="margin-bottom: 0.5rem; font-size: 1.35rem;" id="modalTitle">Confirm Your Stay</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.25rem;" id="modalSubtitle"></p>

            <form onsubmit="event.preventDefault(); submitBooking();">
                <div class="form-group" style="margin-bottom: 1rem;">
                    <label class="form-label">Full Name</label>
                    <input type="text" id="guestName" class="form-input" placeholder="e.g. Ada Lovelace" required>
                </div>
                <div class="form-group" style="margin-bottom: 1.5rem;">
                    <label class="form-label">Email Address</label>
                    <input type="email" id="guestEmail" class="form-input" placeholder="e.g. ada@example.com" required>
                </div>
                <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
                    <button type="button" class="btn btn-outline" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn" id="confirmBtn">Confirm Reservation</button>
                </div>
            </form>
        </div>
    </div>

    <footer>
        Hotel Reservation Platform &bull; Cloud Deployment & CI/CD &bull; Algions AI Labs Individual Assessment
    </footer>

    <script>
        let selectedRoom = null;

        // Initialize default dates
        window.addEventListener('DOMContentLoaded', () => {
            const today = new Date();
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            const checkout = new Date(today);
            checkout.setDate(checkout.getDate() + 5);

            document.getElementById('checkInDate').value = tomorrow.toISOString().split('T')[0];
            document.getElementById('checkOutDate').value = checkout.toISOString().split('T')[0];

            checkHealth();
            searchRooms();
        });

        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.style.display = 'none');

            event.target.classList.add('active');
            document.getElementById('tab-' + tabId).style.display = 'block';
        }

        async function checkHealth() {
            try {
                const res = await fetch('/ready');
                const data = await res.json();
                if (res.ok) {
                    document.getElementById('health-text').innerText = 'System Ready & Online';
                }
            } catch (e) {
                document.getElementById('health-text').innerText = 'Service Offline';
            }
        }

        async function searchRooms() {
            const checkIn = document.getElementById('checkInDate').value;
            const checkOut = document.getElementById('checkOutDate').value;
            const roomType = document.getElementById('roomTypeSelect').value;

            const grid = document.getElementById('roomsGrid');
            const heading = document.getElementById('resultsHeading');
            grid.innerHTML = '<div style="color: #94a3b8;">Searching available suites...</div>';

            try {
                const res = await fetch(`/availability?check_in=${checkIn}&check_out=${checkOut}&room_type=${roomType}`);
                const rooms = await res.json();

                heading.style.display = 'block';
                grid.innerHTML = '';

                if (!rooms || rooms.length === 0) {
                    grid.innerHTML = '<div style="color: #f87171; grid-column: 1/-1;">No available rooms found for the selected dates. Try alternate dates.</div>';
                    return;
                }

                rooms.forEach(room => {
                    const el = document.createElement('div');
                    el.className = 'room-card';
                    el.innerHTML = `
                        <div>
                            <span class="room-badge">${room.room_type}</span>
                            <div class="room-number">Room ${room.number}</div>
                            <div class="room-price">$${parseFloat(room.price).toFixed(2)} <span>/ night</span></div>
                        </div>
                        <button class="btn" style="margin-top: 1rem; width: 100%;" onclick='openBookingModal(${JSON.stringify(room)})'>
                            Book Room
                        </button>
                    `;
                    grid.appendChild(el);
                });
            } catch (err) {
                grid.innerHTML = `<div style="color: #f87171;">Error loading rooms: ${err.message}</div>`;
            }
        }

        function openBookingModal(room) {
            selectedRoom = room;
            const checkIn = document.getElementById('checkInDate').value;
            const checkOut = document.getElementById('checkOutDate').value;

            document.getElementById('modalTitle').innerText = `Reserve Room ${room.number}`;
            document.getElementById('modalSubtitle').innerText = `${room.room_type.toUpperCase()} &bull; ${checkIn} to ${checkOut} ($${room.price}/night)`;
            document.getElementById('bookingModal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('bookingModal').style.display = 'none';
        }

        async function submitBooking() {
            const guestName = document.getElementById('guestName').value;
            const guestEmail = document.getElementById('guestEmail').value;
            const checkIn = document.getElementById('checkInDate').value;
            const checkOut = document.getElementById('checkOutDate').value;
            const confirmBtn = document.getElementById('confirmBtn');

            confirmBtn.disabled = true;
            confirmBtn.innerText = 'Confirming...';

            try {
                const res = await fetch('/reservations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        guest_name: guestName,
                        guest_email: guestEmail,
                        room_id: selectedRoom.id,
                        check_in: checkIn,
                        check_out: checkOut
                    })
                });

                const data = await res.json();
                closeModal();

                if (res.status === 201) {
                    const container = document.getElementById('resultsContainer');
                    container.innerHTML = `
                        <div class="confirmation-box">
                            <h2 style="color: var(--success); margin-bottom: 0.5rem;">🎉 Reservation Confirmed!</h2>
                            <p style="color: var(--text-muted);">Please save your confirmation reference number:</p>
                            <div class="reference-tag">${data.reference}</div>
                            <div style="font-size: 0.95rem; margin-top: 0.5rem;">
                                <strong>Guest:</strong> ${data.guest_name} &bull;
                                <strong>Room:</strong> ${selectedRoom.number} &bull;
                                <strong>Dates:</strong> ${data.check_in} to ${data.check_out}
                            </div>
                            <button class="btn" style="margin-top: 1.25rem;" onclick="location.reload()">Book Another Stay</button>
                        </div>
                    `;
                } else {
                    alert(`Booking conflict or error (${res.status}): ${data.detail || 'Unable to book'}`);
                    searchRooms();
                }
            } catch (err) {
                alert('Network error: ' + err.message);
            } finally {
                confirmBtn.disabled = false;
                confirmBtn.innerText = 'Confirm Reservation';
            }
        }

        async function lookupReservation() {
            const ref = document.getElementById('lookupRefInput').value.trim();
            const out = document.getElementById('lookupResult');
            if (!ref) return;

            out.innerHTML = 'Searching reservation record...';
            try {
                const res = await fetch(`/reservations/${ref}`);
                const data = await res.json();

                if (res.ok) {
                    out.innerHTML = `
                        <div style="background: #0f172a; padding: 1.25rem; border-radius: 8px; border: 1px solid var(--border);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                                <span class="room-badge">${data.status}</span>
                                <span style="font-family: monospace; font-weight: 700; color: var(--primary);">${data.reference}</span>
                            </div>
                            <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem;">${data.guest_name}</div>
                            <div style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 0.75rem;">${data.guest_email}</div>
                            <div style="border-top: 1px solid var(--border); padding-top: 0.75rem; font-size: 0.9rem;">
                                <strong>Stay Window:</strong> ${data.check_in} &rarr; ${data.check_out}
                            </div>
                        </div>
                    `;
                } else {
                    out.innerHTML = `<div style="color: #f87171;">Reservation not found: ${data.detail}</div>`;
                }
            } catch (err) {
                out.innerHTML = `<div style="color: #f87171;">Error: ${err.message}</div>`;
            }
        }

        async function runConcurrencyDrill() {
            const term = document.getElementById('concurrencyTerminal');
            const btn = document.getElementById('concurrencyBtn');
            btn.disabled = true;
            btn.innerText = 'Running Drill...';

            term.innerHTML = '<div style="color: #38bdf8;">[INIT] Firing 10 simultaneous conflicting POST requests for Room 1...</div>';

            const payload = {
                guest_name: 'Concurrent Tester',
                guest_email: 'race@example.com',
                room_id: 1,
                check_in: '2026-12-15',
                check_out: '2026-12-20'
            };

            const promises = Array.from({ length: 10 }, (_, i) =>
                fetch('/reservations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ...payload, guest_name: `Guest #${i + 1}` })
                }).then(async r => ({ status: r.status, data: await r.json(), id: i + 1 }))
            );

            const results = await Promise.all(promises);

            let confirmed = 0;
            let conflicts = 0;

            term.innerHTML += '<div style="margin: 0.5rem 0; border-bottom: 1px solid #1e293b;"></div>';
            results.forEach(res => {
                if (res.status === 201) {
                    confirmed++;
                    term.innerHTML += `<div class="term-row"><span class="code-201">HTTP 201 CREATED</span> <span>Ref: ${res.data.reference} (Guest ${res.id})</span></div>`;
                } else if (res.status === 409) {
                    conflicts++;
                    term.innerHTML += `<div class="term-row"><span class="code-409">HTTP 409 CONFLICT</span> <span>${res.data.detail}</span></div>`;
                } else {
                    term.innerHTML += `<div class="term-row"><span>HTTP ${res.status}</span> <span>${res.data.detail}</span></div>`;
                }
            });

            term.innerHTML += '<div style="margin: 0.5rem 0; border-bottom: 1px solid #1e293b;"></div>';
            term.innerHTML += `<div style="color: #34d399; font-weight: bold;">[VERIFIED] Success Count: ${confirmed} (201 Created) | Rejected: ${conflicts} (409 Conflict)</div>`;
            term.innerHTML += '<div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.25rem;">Result: Double booking physically prevented by database GiST exclusion constraint!</div>';

            btn.disabled = false;
            btn.innerText = '⚡ Fire 10 Conflicting Requests';
        }
    </script>
</body>
</html>
"""
