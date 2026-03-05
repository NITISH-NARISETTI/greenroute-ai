/**
 * GreenRoute - Frontend JavaScript
 * Handles user interactions, API calls, and map visualization
 */

// Configuration
// Configuration - dynamically set API base URL based on how the page is loaded
const API_BASE_URL = window.location.hostname === ""
    ? 'http://localhost:8000'  // Running locally by double-clicking index.html
    : window.location.origin;  // Running on a server (localhost or Render)

console.log('🌐 GreenRoute API Base URL:', API_BASE_URL);


// Global variables
let map = null;
let routeLayer = null;
let sequentialRouteLayer = null;  // For showing the non-optimized route
let markersLayer = null;
let legendControl = null;
let originalAddresses = [];  // Store original address order for sequential route

// ==================== Initialization ====================

document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    setupEventListeners();
    setupAutocompleteAll();
});

/**
 * Initialize Leaflet map
 */
function initializeMap() {
    // Create map centered on India
    map = L.map('map').setView([20.5937, 78.9629], 5);

    // Add tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // Create layer groups for markers and routes
    markersLayer = L.layerGroup().addTo(map);
    sequentialRouteLayer = L.layerGroup().addTo(map);  // Non-optimized route (shown first, underneath)
    routeLayer = L.layerGroup().addTo(map);  // Optimized route (shown on top)

    // Add click listener for map-based geocoding
    map.on('click', handleMapClick);

    console.log('✓ Map initialized');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Form submission
    document.getElementById('routeForm').addEventListener('submit', handleFormSubmit);

    // Add destination button
    document.getElementById('addDestination').addEventListener('click', addDestinationInput);

    console.log('✓ Event listeners setup');
}

// ==================== Form Handling ====================

/**
 * Handle form submission
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    // Clear previous results and errors
    hideResults();
    hideError();

    // Show loading state
    setLoadingState(true);

    try {
        // Collect form data
        const formData = collectFormData();

        // Validate form data
        if (!validateFormData(formData)) {
            throw new Error('Please fill in all required fields');
        }

        console.log('📤 Sending optimization request...', formData);

        // Call API
        // Use relative URL for mono-service deployment
        const url = '/optimize';
        console.log(`🚀 Sending request to: ${url}`, formData);

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const responseText = await response.text();
        let result;
        try {
            result = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse response as JSON:', responseText);
            throw new Error(`Server returned non-JSON response: ${responseText.substring(0, 100)}...`);
        }

        if (!response.ok) {
            let errorMsg = 'Optimization failed';
            const errorData = result;

            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    errorMsg = errorData.detail.map(err => {
                        const field = err.loc ? err.loc[err.loc.length - 1] : 'Field';
                        return `${field}: ${err.msg}`;
                    }).join(', ');
                } else if (typeof errorData.detail === 'string') {
                    errorMsg = errorData.detail;
                } else {
                    errorMsg = JSON.stringify(errorData.detail);
                }
            } else if (errorData.message) {
                errorMsg = errorData.message;
            }

            throw new Error(errorMsg);
        }

        console.log('✅ Optimization successful:', result);

        // Store original addresses for sequential route comparison
        originalAddresses = [formData.start_address, ...formData.destination_addresses];

        // Display results
        displayResults(result);

    } catch (error) {
        console.error('❌ Optimization error:', error);
        let errorMsg = error.message;

        if (errorMsg.includes('Failed to fetch')) {
            errorMsg = `Connection failed. Make sure the backend server and its port are accessible at ${API_BASE_URL}.\n\n(Tip: If you're running this from a local file, some browsers block requests. Try refreshing or use a local server like 'python -m http.server' in the frontend folder).`;
        }

        showError(`Optimization Failed: ${errorMsg}`);
    } finally {
        setLoadingState(false);
    }
}

/**
 * Collect form data
 */
function collectFormData() {
    const startAddress = document.getElementById('startAddress').value.trim();
    const vehicleType = document.getElementById('vehicleType').value;
    const cargoWeight = parseFloat(document.getElementById('cargoWeight').value);
    const avgSpeed = parseFloat(document.getElementById('avgSpeed').value);

    // Collect all destination addresses
    const destinationInputs = document.querySelectorAll('.destination-input');
    const destinationAddresses = Array.from(destinationInputs)
        .map(input => input.value.trim())
        .filter(addr => addr.length > 0);

    return {
        start_address: startAddress,
        destination_addresses: destinationAddresses,
        vehicle_type: vehicleType,
        cargo_weight: cargoWeight,
        avg_speed: avgSpeed
    };
}

/**
 * Validate form data
 */
function validateFormData(data) {
    if (!data.start_address) return false;
    if (data.destination_addresses.length === 0) return false;
    if (!data.vehicle_type) return false;
    if (isNaN(data.cargo_weight) || data.cargo_weight < 0) return false;
    if (isNaN(data.avg_speed) || data.avg_speed <= 0) return false;
    return true;
}

/**
 * Set loading state
 */
function setLoadingState(isLoading) {
    const btn = document.getElementById('optimizeBtn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');

    if (isLoading) {
        btn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
    } else {
        btn.disabled = false;
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
    }
}

// ==================== Destination Management ====================

/**
 * Add new destination input field
 */
function addDestinationInput() {
    const container = document.getElementById('destinationsContainer');
    const inputGroup = document.createElement('div');
    inputGroup.className = 'destination-input-group';

    const currentCount = container.children.length;

    inputGroup.innerHTML = `
        <div class="autocomplete-container">
            <input 
                type="text" 
                class="destination-input" 
                placeholder="Delivery stop ${currentCount + 1}"
                required
                autocomplete="off"
            >
        </div>
        <button type="button" class="btn-remove" onclick="removeDestination(this)" title="Remove stop">×</button>
    `;

    container.appendChild(inputGroup);

    // Initialize autocomplete for the new input
    const newInput = inputGroup.querySelector('.destination-input');
    setupAutocomplete(newInput);
}

/**
 * Remove destination input field
 */
function removeDestination(button) {
    const container = document.getElementById('destinationsContainer');

    // Don't allow removing if only one destination remains
    if (container.children.length <= 1) {
        alert('At least one destination is required');
        return;
    }

    button.parentElement.remove();

    // Update placeholder numbers
    updateDestinationPlaceholders();
}

/**
 * Update destination input placeholders
 */
function updateDestinationPlaceholders() {
    const inputs = document.querySelectorAll('.destination-input');
    inputs.forEach((input, index) => {
        input.placeholder = `Delivery stop ${index + 1}`;
    });
}

// ==================== Results Display ====================

/**
 * Display optimization results
 */
function displayResults(result) {
    if (!result.success) {
        showError(result.message || 'Optimization failed');
        return;
    }

    // Display metrics
    displayMetrics(result.metrics);

    // Display route sequence
    displayRouteSequence(result.route);

    // Visualize on map
    visualizeRoute(result.route);

    // Show results panel
    showResults();
}

/**
 * Display metrics
 */
function displayMetrics(metrics) {
    document.getElementById('metricDistance').textContent = `${metrics.total_distance_km} km`;
    document.getElementById('metricCO2').textContent = `${metrics.total_co2_kg} kg`;
    document.getElementById('metricTime').textContent = `${metrics.total_time_hours} hrs`;
    document.getElementById('metricCost').textContent = `₹${metrics.estimated_cost_inr}`;

    // Display savings if available
    if (metrics.savings) {
        const s = metrics.savings;
        document.getElementById('savingDistance').textContent =
            `${s.distance_saved_km} km (${s.distance_saved_percent}%)`;
        document.getElementById('savingCO2').textContent =
            `${s.co2_saved_kg} kg (${s.co2_saved_percent}%)`;
        document.getElementById('savingTime').textContent =
            `${s.time_saved_hours} hrs`;
        document.getElementById('savingCost').textContent =
            `₹${s.cost_saved_inr} (${s.cost_saved_percent}%)`;
    }
}

/**
 * Display route sequence
 */
function displayRouteSequence(route) {
    const container = document.getElementById('routeSequence');
    container.innerHTML = '';

    route.forEach((location, index) => {
        const item = document.createElement('div');
        item.className = 'sequence-item';

        const isStart = index === 0;
        const label = isStart ? 'START' : `STOP ${index}`;

        item.innerHTML = `
            <div class="sequence-number">${index + 1}</div>
            <div class="sequence-address">
                <strong>${label}</strong><br>
                <small>${location.address}</small>
            </div>
        `;

        container.appendChild(item);
    });
}

/**
 * Visualize route on map
 */
function visualizeRoute(route) {
    // Clear existing layers
    markersLayer.clearLayers();
    routeLayer.clearLayers();
    sequentialRouteLayer.clearLayers();

    if (route.length === 0) return;

    // Extract optimized route coordinates (route is already in optimized order from backend)
    const optimizedCoordinates = route.map(loc => [loc.latitude, loc.longitude]);

    // Create a map of addresses to their coordinates
    const addressMap = new Map();
    route.forEach(loc => {
        addressMap.set(loc.address, [loc.latitude, loc.longitude]);
    });

    // Create sequential route using ORIGINAL address order
    const sequentialCoordinates = [];
    console.log('Original addresses:', originalAddresses);
    console.log('Route addresses:', route.map(r => r.address));

    for (let i = 0; i < originalAddresses.length; i++) {
        const originalAddr = originalAddresses[i];
        // Try exact match first
        if (addressMap.has(originalAddr)) {
            sequentialCoordinates.push(addressMap.get(originalAddr));
        } else {
            // Try partial match (in case geocoding changed the address format)
            for (let [addr, coords] of addressMap.entries()) {
                if (addr.includes(originalAddr) || originalAddr.includes(addr.split(',')[0])) {
                    sequentialCoordinates.push(coords);
                    break;
                }
            }
        }
    }

    console.log('Sequential coordinates:', sequentialCoordinates.length);
    console.log('Optimized coordinates:', optimizedCoordinates.length);

    // Draw SEQUENTIAL route (non-optimized) - RED DASHED - Draw FIRST (underneath)
    if (sequentialCoordinates.length > 1) {
        const sequentialPolyline = L.polyline(sequentialCoordinates, {
            color: '#ef4444',  // Red color
            weight: 6,  // Thicker to be visible
            opacity: 0.8,  // More opaque
            dashArray: '15, 10',  // Longer dashes
            smoothFactor: 1,
            offset: -3  // Offset to the left
        });
        sequentialRouteLayer.addLayer(sequentialPolyline);
        console.log('✓ Sequential route drawn (RED DASHED)');
    } else {
        console.warn('⚠ Sequential route not drawn - insufficient coordinates');
    }

    // Draw OPTIMIZED route - GREEN SOLID - Draw SECOND (on top)
    const optimizedPolyline = L.polyline(optimizedCoordinates, {
        color: '#10b981',  // Green color
        weight: 5,
        opacity: 0.9,
        smoothFactor: 1,
        offset: 3  // Offset to the right
    });
    routeLayer.addLayer(optimizedPolyline);
    console.log('✓ Optimized route drawn (GREEN SOLID)');

    // Add markers
    route.forEach((location, index) => {
        const isStart = index === 0;
        const isEnd = index === route.length - 1;

        // Create custom icon
        const iconHtml = createMarkerIcon(index + 1, isStart, isEnd);
        const icon = L.divIcon({
            html: iconHtml,
            className: 'custom-marker',
            iconSize: [40, 40],
            iconAnchor: [20, 40],
            popupAnchor: [0, -40]
        });

        // Add marker
        const marker = L.marker([location.latitude, location.longitude], { icon })
            .bindPopup(`
                <div style="font-family: Inter, sans-serif;">
                    <strong>${isStart ? '🚀 START' : `📍 Stop ${index}`}</strong><br>
                    <small>${location.address}</small>
                </div>
            `);

        markersLayer.addLayer(marker);
    });

    // Add legend to map
    addMapLegend();

    // Fit map to route bounds (use optimized route)
    map.fitBounds(optimizedPolyline.getBounds(), { padding: [50, 50] });
}

/**
 * Create custom marker icon HTML
 */
function createMarkerIcon(number, isStart, isEnd) {
    const color = isStart ? '#10b981' : isEnd ? '#ef4444' : '#3b82f6';

    return `
        <div style="
            width: 40px;
            height: 40px;
            background: ${color};
            border: 3px solid white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            font-size: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        ">
            ${number}
        </div>
    `;
}

// ==================== UI State Management ====================

/**
 * Show results panel
 */
function showResults() {
    document.getElementById('resultsPanel').style.display = 'block';
}

/**
 * Hide results panel
 */
function hideResults() {
    document.getElementById('resultsPanel').style.display = 'none';
}

/**
 * Show error panel
 */
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorPanel').style.display = 'flex';
}

/**
 * Hide error panel
 */
function hideError() {
    document.getElementById('errorPanel').style.display = 'none';
}

/**
 * Close error panel
 */
function closeError() {
    hideError();
}

/**
 * Add legend to map showing route types
 */
function addMapLegend() {
    // Remove existing legend if present
    if (legendControl) {
        map.removeControl(legendControl);
    }

    // Create legend control
    legendControl = L.control({ position: 'bottomright' });

    legendControl.onAdd = function (map) {
        const div = L.DomUtil.create('div', 'map-legend');
        div.innerHTML = `
            <div style="
                background: white;
                padding: 12px 16px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                font-family: Inter, sans-serif;
                font-size: 13px;
                line-height: 1.8;
            ">
                <div style="font-weight: 600; margin-bottom: 8px; color: #1f2937;">Route Comparison</div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <div style="width: 30px; height: 3px; background: #10b981;"></div>
                    <span style="color: #374151;">Optimized (CO₂)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 30px; height: 3px; background: #ef4444; border-top: 3px dashed #ef4444;"></div>
                    <span style="color: #374151;">Sequential</span>
                </div>
            </div>
        `;
        return div;
    };

    legendControl.addTo(map);
}


// ==================== Map Interaction ====================

/**
 * Handle map click to add a stop (Reverse Geocoding)
 */
async function handleMapClick(e) {
    const { lat, lng } = e.latlng;

    // Show a temporary marker to indicate we are geocoding
    const tempMarker = L.marker([lat, lng]).addTo(map).bindPopup("🔍 Finding address...").openPopup();

    try {
        // Reverse Geocode using Nominatim
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
        const data = await response.json();

        if (data && data.display_name) {
            const address = data.display_name;

            // Find the last empty destination input or add a new one
            const destInputs = document.querySelectorAll('.destination-input');
            let targetInput = null;

            for (let input of destInputs) {
                if (input.value.trim() === '') {
                    targetInput = input;
                    break;
                }
            }

            if (!targetInput) {
                addDestinationInput();
                const newInputs = document.querySelectorAll('.destination-input');
                targetInput = newInputs[newInputs.length - 1];
            }

            targetInput.value = address;
            tempMarker.setPopupContent(`✅ Added: ${address.split(',')[0]}`);

            // Auto-close popup after 2 seconds
            setTimeout(() => map.removeLayer(tempMarker), 2000);
        } else {
            tempMarker.setPopupContent("❌ Could not find address here");
            setTimeout(() => map.removeLayer(tempMarker), 2000);
        }
    } catch (error) {
        console.error('Reverse geocoding error:', error);
        map.removeLayer(tempMarker);
    }
}


// ==================== Geocoding Autocomplete ====================

/**
 * Setup autocomplete for all existing address inputs
 */
function setupAutocompleteAll() {
    const inputs = [
        document.getElementById('startAddress'),
        ...document.querySelectorAll('.destination-input')
    ];

    inputs.forEach(input => setupAutocomplete(input));
}

/**
 * Setup autocomplete for a single input element
 */
function setupAutocomplete(input) {
    if (!input) return;

    const container = input.parentElement;
    const suggestionsList = document.createElement('div');
    suggestionsList.className = 'suggestions-list';
    container.appendChild(suggestionsList);

    // Debounced search function
    const performSearch = debounce(async (query) => {
        if (query.length < 3) {
            suggestionsList.style.display = 'none';
            return;
        }

        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`);
            const data = await response.json();

            if (data && data.length > 0) {
                renderSuggestions(data, suggestionsList, input);
            } else {
                suggestionsList.style.display = 'none';
            }
        } catch (error) {
            console.error('Autocomplete error:', error);
        }
    }, 300);

    // Event listeners
    input.addEventListener('input', (e) => performSearch(e.target.value));

    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            suggestionsList.style.display = 'none';
        }
    });

    // Handle focus
    input.addEventListener('focus', () => {
        if (input.value.length >= 3 && suggestionsList.innerHTML !== '') {
            suggestionsList.style.display = 'block';
        }
    });
}

/**
 * Render suggestion items
 */
function renderSuggestions(data, listElement, inputElement) {
    listElement.innerHTML = '';
    listElement.style.display = 'block';

    data.forEach(item => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';

        // Extract primary name and secondary address parts
        const mainText = item.display_name.split(',')[0];
        const subText = item.display_name.split(',').slice(1).join(',').trim();

        div.innerHTML = `
            <strong>${mainText}</strong>
            <small>${subText}</small>
        `;

        div.addEventListener('click', () => {
            inputElement.value = item.display_name;
            listElement.style.display = 'none';
        });

        listElement.appendChild(div);
    });
}

/**
 * Debounce utility
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

console.log('✅ GreenRoute frontend initialized');
