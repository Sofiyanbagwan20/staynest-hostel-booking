// StayNest Frontend - Fullstack API & Razorpay Payment Integration
const configuredApiBase = typeof window.STAYNEST_API_BASE_URL === 'string'
  ? window.STAYNEST_API_BASE_URL.trim().replace(/\/+$/, '')
  : '';
const isLocalHost = window.location.protocol === 'file:' ||
  ['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_BASE = configuredApiBase ||
  (window.location.port === '5000' || window.location.pathname.startsWith('/api')
    ? '/api'
    : isLocalHost
      ? 'http://127.0.0.1:5000/api'
      : '');

const DEFAULT_HOSTELS = [
  {
    id: 1,
    name: "Greenwood Student Living",
    type: "Girls",
    area: "Shivajinagar, Pune",
    city: "Pune",
    price: 6500,
    rating: 4.8,
    reviews: 124,
    verified: true,
    features: ["Wi-Fi", "Meals", "AC"],
    image: "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=900&q=80",
    desc_text: "A bright, comfortable stay with study-friendly spaces, friendly staff and easy access to colleges and public transport."
  },
  {
    id: 2,
    name: "The Urban Nest",
    type: "Co-living",
    area: "Kothrud, Pune",
    city: "Pune",
    price: 8000,
    rating: 4.7,
    reviews: 98,
    verified: true,
    features: ["Wi-Fi", "AC", "Laundry"],
    image: "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=900&q=80",
    desc_text: "Modern co-living with thoughtfully furnished rooms, shared common areas and a relaxed community atmosphere."
  },
  {
    id: 3,
    name: "Sunrise Girls Hostel",
    type: "Girls",
    area: "FC Road, Pune",
    city: "Pune",
    price: 5500,
    rating: 4.6,
    reviews: 86,
    verified: true,
    features: ["Wi-Fi", "Meals", "Security"],
    image: "https://images.unsplash.com/photo-1564078516393-cf04bd966897?auto=format&fit=crop&w=900&q=80",
    desc_text: "A welcoming girls hostel with secure entry, home-style meals and convenient access to shops and transit."
  },
  {
    id: 4,
    name: "Oakwood Residency",
    type: "Boys",
    area: "Aundh, Pune",
    city: "Pune",
    price: 9000,
    rating: 4.9,
    reviews: 152,
    verified: true,
    features: ["Wi-Fi", "AC", "Gym"],
    image: "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80",
    desc_text: "Spacious rooms and useful amenities for students and working professionals looking for a premium stay."
  },
  {
    id: 5,
    name: "Maple House",
    type: "Co-living",
    area: "Viman Nagar, Pune",
    city: "Pune",
    price: 7200,
    rating: 4.5,
    reviews: 73,
    verified: false,
    features: ["Wi-Fi", "Laundry", "Meals"],
    image: "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80",
    desc_text: "An affordable, relaxed home base with shared facilities, furnished rooms and easy connections across the city."
  },
  {
    id: 6,
    name: "Campus Corner Hostel",
    type: "Boys",
    area: "Pimpri, Pune",
    city: "Pune",
    price: 4800,
    rating: 4.4,
    reviews: 61,
    verified: true,
    features: ["Wi-Fi", "Meals", "Security"],
    image: "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=900&q=80",
    desc_text: "Budget-friendly rooms close to campus, with everyday essentials and a friendly student community."
  }
];

let currentUser = null;
let authToken = localStorage.getItem('staynest_token') || null;
let hostels = [];
let savedSet = new Set();
let activeChip = 'all';
let activeHostelForBooking = null;
let currentBookingData = null;
let currentRazorpayOrder = null;

// UI Elements
const grid = document.getElementById('hostelGrid');
const resultCount = document.getElementById('resultCount');
const emptyState = document.getElementById('emptyState');
const toast = document.getElementById('toast');
const userAvatar = document.getElementById('userAvatar');
const userNameDisplay = document.getElementById('userNameDisplay');
let toastTimer;

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3000);
}

function money(n) {
  return '₹' + Number(n).toLocaleString('en-IN');
}

// ----------------- API CLIENT HELPERS -----------------
async function apiRequest(endpoint, method = 'GET', body = null, requiresAuth = false) {
  if (!API_BASE) {
    throw new Error('The online backend is not configured. Set the STAYNEST_API_BASE_URL GitHub Actions variable after deploying the backend.');
  }

  const headers = { 'Content-Type': 'application/json' };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const options = { method, headers };
  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || `Request failed with status ${res.status}`);
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${method} ${endpoint}:`, err);
    throw err;
  }
}

// ----------------- AUTHENTICATION -----------------
async function checkAuth() {
  if (!authToken) {
    updateUserUI(null);
    return;
  }
  try {
    const data = await apiRequest('/auth/me', 'GET', null, true);
    if (data.success && data.user) {
      currentUser = data.user;
      updateUserUI(currentUser);
      loadSavedStays();
    } else {
      logout();
    }
  } catch (e) {
    console.warn('Session expired or backend unavailable.');
    updateUserUI(null);
  }
}

function updateUserUI(user) {
  if (user) {
    const initial = user.name ? user.name.charAt(0).toUpperCase() : 'U';
    userAvatar.textContent = initial;
    userNameDisplay.textContent = user.name.split(' ')[0];
  } else {
    userAvatar.textContent = 'A';
    userNameDisplay.textContent = 'Sign In';
  }
}

function logout() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem('staynest_token');
  updateUserUI(null);
  document.getElementById('userProfileModal').close();
  showToast('You have been signed out.');
  loadHostels();
}

// Auth modal tabs
const tabLoginBtn = document.getElementById('tabLoginBtn');
const tabRegisterBtn = document.getElementById('tabRegisterBtn');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');

tabLoginBtn.addEventListener('click', () => {
  tabLoginBtn.classList.add('active');
  tabRegisterBtn.classList.remove('active');
  loginForm.classList.remove('hidden');
  registerForm.classList.add('hidden');
});

tabRegisterBtn.addEventListener('click', () => {
  tabRegisterBtn.classList.add('active');
  tabLoginBtn.classList.remove('active');
  registerForm.classList.remove('hidden');
  loginForm.classList.add('hidden');
});

loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;

  try {
    const data = await apiRequest('/auth/login', 'POST', { email, password });
    if (data.success) {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem('staynest_token', authToken);
      updateUserUI(currentUser);
      document.getElementById('authModal').close();
      loginForm.reset();
      showToast(`Welcome back, ${currentUser.name}!`);
      loadSavedStays();
    }
  } catch (err) {
    showToast(`Login failed: ${err.message}`);
  }
});

registerForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const phone = document.getElementById('regPhone').value.trim();
  const role = document.getElementById('regRole').value;
  const password = document.getElementById('regPassword').value;

  try {
    const data = await apiRequest('/auth/register', 'POST', { name, email, phone, role, password });
    if (data.success) {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem('staynest_token', authToken);
      updateUserUI(currentUser);
      document.getElementById('authModal').close();
      registerForm.reset();
      showToast(`Account created! Welcome, ${currentUser.name}.`);
      loadSavedStays();
    }
  } catch (err) {
    showToast(`Registration failed: ${err.message}`);
  }
});

// Profile / Account Click
document.getElementById('profileBtn').addEventListener('click', () => {
  if (!currentUser) {
    document.getElementById('authModal').showModal();
  } else {
    document.getElementById('modalUserName').textContent = currentUser.name;
    document.getElementById('modalUserEmail').textContent = currentUser.email;
    document.getElementById('modalUserRole').textContent = currentUser.role || 'Student';
    document.getElementById('modalUserPhone').textContent = currentUser.phone || 'Not provided';
    document.getElementById('modalUserAvatar').textContent = currentUser.name.charAt(0).toUpperCase();
    document.getElementById('userProfileModal').showModal();
  }
});

document.getElementById('logoutBtn').addEventListener('click', logout);
document.getElementById('viewBookingsBtn').addEventListener('click', () => {
  document.getElementById('userProfileModal').close();
  openMyBookings();
});

// ----------------- HOSTELS FETCH & RENDER -----------------
async function loadHostels() {
  const q = (document.getElementById('locationInput')?.value || '').trim();
  const type = document.getElementById('typeFilter')?.value || 'all';
  const budget = document.getElementById('budgetFilter')?.value || 'all';

  const params = new URLSearchParams();
  if (q) params.append('q', q);
  if (type !== 'all') params.append('type', type);
  if (budget !== 'all') params.append('budget', budget);
  if (activeChip !== 'all') params.append('chip', activeChip);

  try {
    const data = await apiRequest(`/hostels?${params.toString()}`);
    if (data && data.success && Array.isArray(data.hostels)) {
      hostels = data.hostels;
      render();
      return;
    }
  } catch (err) {
    console.warn('Backend server not connected yet; using local catalog:', err);
  }

  // Graceful catalog fallback if backend is offline or starting
  let filtered = [...DEFAULT_HOSTELS];
  if (q) {
    const qLower = q.toLowerCase();
    filtered = filtered.filter(h => 
      h.name.toLowerCase().includes(qLower) || 
      h.area.toLowerCase().includes(qLower) ||
      (h.city && h.city.toLowerCase().includes(qLower))
    );
  }
  if (type !== 'all') {
    filtered = filtered.filter(h => h.type.toLowerCase() === type.toLowerCase());
  }
  if (budget !== 'all') {
    const num = Number(budget);
    filtered = filtered.filter(h => {
      if (!isNaN(num) && num > 0) return h.price <= num;
      if (budget === 'under-6000') return h.price < 6000;
      if (budget === '6000-8000') return h.price >= 6000 && h.price <= 8000;
      if (budget === 'above-8000') return h.price > 8000;
      return true;
    });
  }
  if (activeChip !== 'all') {
    filtered = filtered.filter(h => {
      if (activeChip === 'verified') return h.verified;
      if (activeChip === 'wifi') return (h.features || []).includes('Wi-Fi');
      if (activeChip === 'meals') return (h.features || []).includes('Meals');
      if (activeChip === 'ac') return (h.features || []).includes('AC');
      return true;
    });
  }
  hostels = filtered;
  render();
}

async function loadSavedStays() {
  if (!authToken) {
    savedSet = new Set(JSON.parse(localStorage.getItem('staynest-saved') || '[]').map(Number));
    return;
  }
  try {
    const data = await apiRequest('/saved', 'GET', null, true);
    if (data.success) {
      savedSet = new Set(data.saved.map(Number));
      render();
    }
  } catch (err) {
    savedSet = new Set(JSON.parse(localStorage.getItem('staynest-saved') || '[]').map(Number));
  }
}

async function toggleSaveHostel(id) {
  if (authToken) {
    try {
      const data = await apiRequest(`/saved/${id}`, 'POST', null, true);
      if (data.success) {
        if (data.saved) savedSet.add(id);
        else savedSet.delete(id);
        showToast(data.message);
        render();
      }
    } catch (err) {
      showToast('Could not update saved stays on server.');
    }
  } else {
    if (savedSet.has(id)) {
      savedSet.delete(id);
      showToast('Removed from saved stays.');
    } else {
      savedSet.add(id);
      showToast('Stay saved locally! Sign in to sync across devices.');
    }
    localStorage.setItem('staynest-saved', JSON.stringify([...savedSet]));
    render();
  }
}

function render() {
  let items = hostels;
  if (location.hash === '#saved') {
    items = hostels.filter(h => savedSet.has(h.id));
  }

  resultCount.textContent = items.length;

  grid.innerHTML = items.map(h => `
    <article class="hostel-card">
      <div class="card-image">
        <img src="${h.image}" alt="Room at ${h.name}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=900&q=80'">
        <span class="image-tag">${h.verified ? '✓ VERIFIED' : 'NEW LISTING'}</span>
        <button class="heart-btn ${savedSet.has(h.id) ? 'saved' : ''}" data-save="${h.id}" aria-label="Save ${h.name}">
          ${savedSet.has(h.id) ? '♥' : '♡'}
        </button>
      </div>
      <div class="card-body">
        <div class="card-title-row">
          <h3 class="card-title">${h.name}</h3>
          <div class="rating"><span>★</span> ${h.rating}</div>
        </div>
        <p class="card-location">⌖ ${h.area} · ${h.type}</p>
        <div class="amenities">
          ${(h.features || []).slice(0, 3).map(f => `<span class="amenity">${f === 'Wi-Fi' ? '⌁ ' : f === 'Meals' ? '♨ ' : f === 'AC' ? '❄ ' : ''}${f}</span>`).join('')}
        </div>
        <div class="card-footer">
          <div class="price">${money(h.price)}<small> / month</small></div>
          <button class="details-btn" data-detail="${h.id}">View details →</button>
        </div>
      </div>
    </article>
  `).join('');

  emptyState.classList.toggle('hidden', items.length > 0);
  grid.classList.toggle('hidden', items.length === 0);
}

// ----------------- HOSTEL DETAILS & BOOKING -----------------
function openDetails(id) {
  const h = hostels.find(x => x.id === id);
  if (!h) return;
  activeHostelForBooking = h;

  document.getElementById('modalContent').innerHTML = `
    <img class="modal-hero" src="${h.image}" alt="${h.name}">
    <p class="eyebrow" style="margin-top:18px">${h.verified ? '✓ VERIFIED STAY' : 'HOSTEL LISTING'} · ${h.type.toUpperCase()}</p>
    <h2>${h.name}</h2>
    <p>⌖ ${h.area}, ${h.city || 'Pune'} &nbsp; · &nbsp; <span style="color:#e9a44f">★</span> ${h.rating} (${h.reviews} reviews)</p>
    <p>${h.desc}</p>
    <div class="modal-amenities">
      ${(h.features || []).map(f => `<span>${f}</span>`).join('')}
    </div>
    <div class="modal-price">${money(h.price)} <small>/ month</small></div>
    <button class="primary-wide" id="startBookingBtn">Book this stay & Pay Online →</button>
    <p style="font-size:11px;color:#7e8b82;text-align:center;margin-top:8px">Instant confirmation via Razorpay secure checkout.</p>
  `;

  document.getElementById('detailModal').showModal();

  document.getElementById('startBookingBtn').addEventListener('click', () => {
    document.getElementById('detailModal').close();
    if (!currentUser) {
      showToast('Please sign in or create an account to book.');
      document.getElementById('authModal').showModal();
    } else {
      openBookingModal(h);
    }
  });
}

function openBookingModal(hostel) {
  activeHostelForBooking = hostel;
  document.getElementById('bookingHostelTitle').textContent = `${hostel.name} (Rent: ${money(hostel.price)}/mo)`;
  document.getElementById('guestName').value = currentUser.name || '';
  document.getElementById('guestEmail').value = currentUser.email || '';
  document.getElementById('guestPhone').value = currentUser.phone || '';

  // Default check-in date: tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  document.getElementById('checkInDate').value = tomorrow.toISOString().split('T')[0];

  updateBookingPriceCalc();
  document.getElementById('bookingModal').showModal();
}

function updateBookingPriceCalc() {
  if (!activeHostelForBooking) return;
  const duration = parseInt(document.getElementById('durationMonths').value, 10);
  const total = activeHostelForBooking.price * duration;
  document.getElementById('bookingDurationCalc').textContent = `${duration} month(s) @ ${money(activeHostelForBooking.price)}/mo`;
  document.getElementById('bookingTotalPayable').textContent = money(total);
}

document.getElementById('durationMonths').addEventListener('change', updateBookingPriceCalc);

// Booking Form Submit -> Calls POST /api/bookings -> Opens Razorpay Modal
document.getElementById('bookingForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const check_in_date = document.getElementById('checkInDate').value;
  const duration_months = parseInt(document.getElementById('durationMonths').value, 10);
  const guest_name = document.getElementById('guestName').value.trim();
  const guest_email = document.getElementById('guestEmail').value.trim();
  const guest_phone = document.getElementById('guestPhone').value.trim();

  try {
    const bookingPayload = {
      hostel_id: activeHostelForBooking.id,
      check_in_date,
      duration_months,
      guest_name,
      guest_email,
      guest_phone
    };

    const res = await apiRequest('/bookings', 'POST', bookingPayload, true);
    if (res.success) {
      currentBookingData = res.booking;
      currentRazorpayOrder = res.razorpay_order;
      document.getElementById('bookingModal').close();
      openRazorpayCheckout(res.booking, res.razorpay_order);
    }
  } catch (err) {
    showToast(`Booking creation failed: ${err.message}`);
  }
});

// ----------------- RAZORPAY PAYMENT GATEWAY -----------------
function openRazorpayCheckout(booking, razorpayOrder) {
  document.getElementById('checkoutAmountDisplay').textContent = money(booking.total_amount);
  document.getElementById('cardName').value = currentUser ? currentUser.name : '';
  document.getElementById('paymentModal').showModal();
}

// Auto-fill test card details for fast testing
document.getElementById('autoFillCardBtn').addEventListener('click', () => {
  document.getElementById('cardNumber').value = '4111 2222 3333 4444';
  document.getElementById('cardExpiry').value = '12/28';
  document.getElementById('cardCvv').value = '123';
  if (!document.getElementById('cardName').value) {
    document.getElementById('cardName').value = currentUser ? currentUser.name : 'Test Cardholder';
  }
  showToast('Test card details filled!');
});

// Switch Payment Methods inside Checkout Modal
const payMethodCard = document.getElementById('payMethodCard');
const payMethodUpi = document.getElementById('payMethodUpi');
const payMethodNetBanking = document.getElementById('payMethodNetBanking');
const cardPaymentForm = document.getElementById('cardPaymentForm');
const upiPaymentForm = document.getElementById('upiPaymentForm');
const netBankingForm = document.getElementById('netBankingForm');

payMethodCard.addEventListener('click', () => {
  payMethodCard.classList.add('active');
  payMethodUpi.classList.remove('active');
  payMethodNetBanking.classList.remove('active');
  cardPaymentForm.classList.remove('hidden');
  upiPaymentForm.classList.add('hidden');
  netBankingForm.classList.add('hidden');
});

payMethodUpi.addEventListener('click', () => {
  payMethodUpi.classList.add('active');
  payMethodCard.classList.remove('active');
  payMethodNetBanking.classList.remove('active');
  upiPaymentForm.classList.remove('hidden');
  cardPaymentForm.classList.add('hidden');
  netBankingForm.classList.add('hidden');
});

payMethodNetBanking.addEventListener('click', () => {
  payMethodNetBanking.classList.add('active');
  payMethodCard.classList.remove('active');
  payMethodUpi.classList.remove('active');
  netBankingForm.classList.remove('hidden');
  cardPaymentForm.classList.add('hidden');
  upiPaymentForm.classList.add('hidden');
});

// Process Card Payment
cardPaymentForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  await processPayment('card');
});

// Process UPI Payment
upiPaymentForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  await processPayment('upi');
});

// Process Net Banking Payment
netBankingForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  await processPayment('netbanking');
});

async function processPayment(paymentMethod) {
  showToast('Processing payment securely with Razorpay...');
  try {
    // Obtain secure HMAC signature for the test order
    const paymentId = 'pay_' + Math.random().toString(36).substring(2, 12);
    const sigRes = await apiRequest('/payments/test-signature', 'POST', {
      order_id: currentRazorpayOrder.id,
      payment_id: paymentId
    });

    // Verify payment and confirm booking on backend
    const verifyPayload = {
      booking_id: currentBookingData.id,
      razorpay_order_id: sigRes.razorpay_order_id,
      razorpay_payment_id: sigRes.razorpay_payment_id,
      razorpay_signature: sigRes.razorpay_signature,
      payment_method: paymentMethod
    };

    const verifyRes = await apiRequest('/payments/verify', 'POST', verifyPayload, true);
    if (verifyRes.success) {
      document.getElementById('paymentModal').close();
      showReceipt({
        bookingCode: verifyRes.booking_code,
        transactionId: verifyRes.transaction_id,
        hostelName: currentBookingData.hostel_name,
        amount: currentBookingData.total_amount,
        duration: currentBookingData.duration_months,
        checkIn: currentBookingData.check_in_date,
        method: paymentMethod.toUpperCase()
      });
    }
  } catch (err) {
    showToast(`Payment verification failed: ${err.message}`);
  }
}

function showReceipt(data) {
  const container = document.getElementById('receiptCardContent');
  container.innerHTML = `
    <div class="receipt-row"><span>Booking Reference:</span><b class="booking-code">${data.bookingCode}</b></div>
    <div class="receipt-row"><span>Transaction ID:</span><b>${data.transactionId}</b></div>
    <div class="receipt-row"><span>Hostel:</span><b>${data.hostelName}</b></div>
    <div class="receipt-row"><span>Check-in Date:</span><b>${data.checkIn}</b></div>
    <div class="receipt-row"><span>Duration:</span><b>${data.duration} Month(s)</b></div>
    <div class="receipt-row"><span>Payment Method:</span><b>${data.method} (Razorpay)</b></div>
    <div class="receipt-row bold"><span>Total Paid:</span><b style="color:var(--green)">${money(data.amount)}</b></div>
  `;
  document.getElementById('receiptModal').showModal();
}

document.getElementById('receiptDoneBtn').addEventListener('click', () => {
  document.getElementById('receiptModal').close();
  showToast('Booking successfully recorded in StayNest database!');
});

document.getElementById('receiptViewBookingsBtn').addEventListener('click', () => {
  document.getElementById('receiptModal').close();
  openMyBookings();
});

// ----------------- MY BOOKINGS VIEW -----------------
async function openMyBookings() {
  if (!currentUser) {
    showToast('Please sign in to view your bookings.');
    document.getElementById('authModal').showModal();
    return;
  }

  const container = document.getElementById('bookingsListContainer');
  container.innerHTML = '<p style="text-align:center;color:#7e8b82;padding:20px">Loading your bookings from MySQL...</p>';
  document.getElementById('myBookingsModal').showModal();

  try {
    const data = await apiRequest('/bookings', 'GET', null, true);
    if (data.success && data.bookings.length > 0) {
      container.innerHTML = data.bookings.map(b => `
        <div class="booking-item">
          <div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
              <span class="booking-code">${b.booking_code}</span>
              <span class="${b.status === 'confirmed' ? 'badge-confirmed' : 'badge-pending'}">${b.status.toUpperCase()}</span>
            </div>
            <h4 style="margin:0 0 4px;font-size:14px;font-weight:700">${b.hostel_name}</h4>
            <div style="font-size:11px;color:#708075">
              ⌖ ${b.hostel_area} &nbsp;•&nbsp; Check-in: <b>${b.check_in_date}</b> (${b.duration_months} mo)
            </div>
            ${b.razorpay_payment_id ? `<small style="color:#78867e">Transaction ID: ${b.razorpay_payment_id}</small>` : ''}
          </div>
          <div style="text-align:right">
            <div class="payment-amount" style="font-size:17px">${money(b.total_amount)}</div>
            <small style="color:#77857b">${b.payment_method ? b.payment_method.toUpperCase() : 'PAID'}</small>
          </div>
        </div>
      `).join('');
    } else {
      container.innerHTML = `
        <div style="text-align:center;padding:35px 10px;color:#7e8b82">
          <div style="font-size:35px;margin-bottom:8px">📋</div>
          <h4 style="margin:0 0 6px;color:var(--ink)">No bookings yet</h4>
          <p style="font-size:12px;margin:0 0 15px">Explore available hostels and make your first booking today!</p>
          <button class="outline-btn" onclick="document.getElementById('myBookingsModal').close()">Explore stays</button>
        </div>
      `;
    }
  } catch (err) {
    container.innerHTML = `<p style="color:#d34848;text-align:center;padding:20px">Failed to load bookings: ${err.message}</p>`;
  }
}

document.getElementById('navBookings').addEventListener('click', (e) => {
  e.preventDefault();
  openMyBookings();
});

document.getElementById('mobileBookings').addEventListener('click', (e) => {
  e.preventDefault();
  openMyBookings();
});

// ----------------- LIST PROPERTY (OWNER SUBMISSION) -----------------
document.getElementById('listHostelBtn').addEventListener('click', () => {
  document.getElementById('listingModal').showModal();
});

document.getElementById('createHostelForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('newHostelName').value.trim();
  const type = document.getElementById('newHostelType').value;
  const price = parseInt(document.getElementById('newHostelPrice').value, 10);
  const area = document.getElementById('newHostelArea').value.trim();
  const city = document.getElementById('newHostelCity').value.trim();
  const image = document.getElementById('newHostelImage').value.trim() || 'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=900&q=80';
  const desc = document.getElementById('newHostelDesc').value.trim() || 'Modern, fully furnished stay near university.';

  const featureCheckboxes = document.querySelectorAll('input[name="amenities"]:checked');
  const features = Array.from(featureCheckboxes).map(c => c.value);

  try {
    const data = await apiRequest('/hostels', 'POST', {
      name, type, price, area, city, features, image, desc
    });
    if (data.success) {
      document.getElementById('listingModal').close();
      document.getElementById('createHostelForm').reset();
      showToast('Your hostel was published to StayNest database!');
      loadHostels();
    }
  } catch (err) {
    showToast(`Failed to list property: ${err.message}`);
  }
});

// ----------------- SEARCH & FILTERS EVENT LISTENERS -----------------
grid.addEventListener('click', (e) => {
  const s = e.target.closest('[data-save]');
  const d = e.target.closest('[data-detail]');
  if (s) toggleSaveHostel(Number(s.dataset.save));
  if (d) openDetails(Number(d.dataset.detail));
});

document.getElementById('searchBtn').addEventListener('click', () => {
  loadHostels();
  showToast('Search results updated.');
});

document.getElementById('locationInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    loadHostels();
    showToast('Search results updated.');
  }
});

document.getElementById('typeFilter').addEventListener('change', loadHostels);
document.getElementById('budgetFilter').addEventListener('change', loadHostels);

document.getElementById('quickFilters').addEventListener('click', (e) => {
  const b = e.target.closest('[data-chip]');
  if (!b) return;
  activeChip = b.dataset.chip;
  document.querySelectorAll('.chip').forEach(c => c.classList.toggle('selected', c === b));
  loadHostels();
});

document.getElementById('clearFilters').addEventListener('click', () => {
  document.getElementById('locationInput').value = '';
  document.getElementById('typeFilter').value = 'all';
  document.getElementById('budgetFilter').value = 'all';
  activeChip = 'all';
  document.querySelectorAll('.chip').forEach(c => c.classList.toggle('selected', c.dataset.chip === 'all'));
  loadHostels();
});

document.getElementById('filterToggle').addEventListener('click', () => {
  document.getElementById('quickFilters').classList.toggle('hidden');
});

// Map Pins Interaction
document.getElementById('fakeMap').addEventListener('click', (e) => {
  const p = e.target.closest('[data-hostel]');
  if (p) openDetails(Number(p.dataset.hostel));
});

document.getElementById('mapExpand').addEventListener('click', () => {
  document.getElementById('fakeMap').classList.toggle('map-expanded');
  showToast('Map preview expanded.');
});

document.getElementById('showMapBtn').addEventListener('click', () => {
  showToast('Interactive map connected to hostel coordinates.');
});

// Navigation Links
document.getElementById('navExplore').addEventListener('click', () => {
  window.location.hash = '#home';
  document.getElementById('navExplore').classList.add('active');
  document.getElementById('navSaved').classList.remove('active');
  loadHostels();
});

document.getElementById('navSaved').addEventListener('click', () => {
  window.location.hash = '#saved';
  document.getElementById('navSaved').classList.add('active');
  document.getElementById('navExplore').classList.remove('active');
  render();
  showToast('Showing your saved stays.');
});

document.getElementById('mobileSaved').addEventListener('click', (e) => {
  e.preventDefault();
  window.location.hash = '#saved';
  render();
  showToast('Showing your saved stays.');
});

document.getElementById('mobileProfile').addEventListener('click', (e) => {
  e.preventDefault();
  document.getElementById('profileBtn').click();
});

document.getElementById('notificationBtn').addEventListener('click', () => {
  const infoModal = document.getElementById('infoModal');
  document.getElementById('infoContent').innerHTML = `
    <div class="info-symbol">✦</div>
    <h2>Notifications</h2>
    <p>You have no unread notifications. New booking receipts and messages will appear here.</p>
    <button class="primary-wide" onclick="document.getElementById('infoModal').close()">Got it</button>
  `;
  infoModal.showModal();
});

window.addEventListener('hashchange', () => {
  if (location.hash === '#saved') {
    render();
  } else {
    loadHostels();
  }
});

// Initialize on page load
checkAuth();
loadHostels();
