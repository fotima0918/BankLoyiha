let barChartInstance = null;
let pieChartInstance = null;

// Toast Notification
function showToast(message, isSuccess = true) {
    const toast = document.getElementById("toast");
    if(!toast) return;
    
    toast.textContent = message;
    toast.style.borderLeftColor = isSuccess ? "var(--primary)" : "#e74c3c";
    toast.classList.add("show");
    
    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}

// Load Dashboard Data (Charts and History)
async function loadDashboardData() {
    try {
        const [custRes, histRes] = await Promise.all([
            fetch("/api/customers"),
            fetch("/api/history")
        ]);
        
        const customers = await custRes.json();
        const history = await histRes.json();
        
        if (customers.error) {
            window.location.href = "/";
            return;
        }

        renderCharts(customers);
        renderHistory(history);
    } catch (error) {
        console.error("Error loading dashboard data", error);
    }
}

// Load Customers for the Customers Page
async function loadCustomersTable() {
    try {
        const res = await fetch("/api/customers");
        const customers = await res.json();
        
        if (customers.error) {
            window.location.href = "/";
            return;
        }

        const tbody = document.querySelector("#customers-table tbody");
        if(tbody) {
            tbody.innerHTML = "";
            customers.forEach(c => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><b>#${c.Id}</b></td>
                    <td>${c.FullName}</td>
                    <td><span class="badge" style="background: ${c.Gender === 'Erkak' ? 'rgba(52, 152, 219, 0.1)' : 'rgba(155, 89, 182, 0.1)'}; color: ${c.Gender === 'Erkak' ? '#2980b9' : '#8e44ad'}">${c.Gender}</span></td>
                    <td style="font-weight: 600; color: var(--primary-dark)">$${c.Balance.toLocaleString()}</td>
                    <td class="actions-cell">
                        <button class="action-btn edit-btn" onclick="openEditModal(${c.Id}, '${c.FullName.replace(/'/g, "\\'")}', '${c.Gender}', ${c.Balance})" title="Tahrirlash">✏️</button>
                        <button class="action-btn delete-btn" onclick="openDeleteModal(${c.Id}, '${c.FullName.replace(/'/g, "\\'")}')" title="O'chirish">🗑️</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error("Error loading customers", error);
    }
}

// ===== MODAL FUNCTIONS =====
let deleteCustomerId = null;

function openAddModal() {
    document.getElementById("modal-title").textContent = "Yangi mijoz qo'shish";
    document.getElementById("modal-submit-btn").textContent = "Qo'shish";
    document.getElementById("edit-customer-id").value = "";
    document.getElementById("input-fullname").value = "";
    document.getElementById("input-gender").value = "";
    document.getElementById("input-balance").value = "0";
    document.getElementById("customer-modal").classList.add("active");
}

function openEditModal(id, fullName, gender, balance) {
    document.getElementById("modal-title").textContent = "Mijozni tahrirlash";
    document.getElementById("modal-submit-btn").textContent = "Saqlash";
    document.getElementById("edit-customer-id").value = id;
    document.getElementById("input-fullname").value = fullName;
    document.getElementById("input-gender").value = gender;
    document.getElementById("input-balance").value = balance;
    document.getElementById("customer-modal").classList.add("active");
}

function closeModal() {
    document.getElementById("customer-modal").classList.remove("active");
}

function openDeleteModal(id, fullName) {
    deleteCustomerId = id;
    document.getElementById("delete-customer-name").textContent = fullName;
    document.getElementById("delete-modal").classList.add("active");
}

function closeDeleteModal() {
    document.getElementById("delete-modal").classList.remove("active");
    deleteCustomerId = null;
}

async function submitCustomerForm(e) {
    e.preventDefault();
    
    const customerId = document.getElementById("edit-customer-id").value;
    const fullName = document.getElementById("input-fullname").value.trim();
    const gender = document.getElementById("input-gender").value;
    const balance = document.getElementById("input-balance").value;
    const submitBtn = document.getElementById("modal-submit-btn");
    
    if (!fullName || !gender) {
        showToast("Barcha maydonlarni to'ldiring", false);
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Kuting...";

    try {
        const isEdit = customerId !== "";
        const url = isEdit ? `/api/customers/${customerId}` : "/api/customers";
        const method = isEdit ? "PUT" : "POST";

        const response = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                full_name: fullName,
                gender: gender,
                balance: parseInt(balance) || 0
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showToast(data.message, true);
            closeModal();
            loadCustomersTable();
        } else {
            showToast(data.message || "Xatolik yuz berdi", false);
        }
    } catch (error) {
        showToast("Server bilan ulanishda xatolik", false);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = customerId ? "Saqlash" : "Qo'shish";
    }
}

async function confirmDelete() {
    if (!deleteCustomerId) return;
    
    const btn = document.getElementById("btn-confirm-delete");
    btn.disabled = true;
    btn.textContent = "Kuting...";

    try {
        const response = await fetch(`/api/customers/${deleteCustomerId}`, {
            method: "DELETE"
        });
        const data = await response.json();

        if (response.ok && data.success) {
            showToast(data.message, true);
            closeDeleteModal();
            loadCustomersTable();
        } else {
            showToast(data.message || "Xatolik yuz berdi", false);
        }
    } catch (error) {
        showToast("Server bilan ulanishda xatolik", false);
    } finally {
        btn.disabled = false;
        btn.textContent = "O'chirish";
    }
}

function renderHistory(history) {
    const tbody = document.querySelector("#history-table tbody");
    if(!tbody) return;
    
    tbody.innerHTML = "";
    
    if (history.length === 0) {
        tbody.innerHTML = "<tr><td colspan='4' style='text-align:center'>O'tkazmalar mavjud emas</td></tr>";
        return;
    }
    
    history.slice(0, 10).forEach(h => {
        const date = new Date(h.Date).toLocaleString("uz-UZ");
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td style="font-size: 0.85rem; color: var(--text-light)">${date}</td>
            <td>${h.SenderName}</td>
            <td>${h.ReceiverName}</td>
            <td style="font-weight: bold; color: #e67e22">$${h.Amount.toLocaleString()}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderCharts(data) {
    // Top 10 by balance
    const sorted = [...data].sort((a, b) => b.Balance - a.Balance).slice(0, 10);
    const names = sorted.map(c => c.FullName.split(' ')[0]);
    const balances = sorted.map(c => c.Balance);
    
    // Gender dist
    let maleCount = 0;
    let femaleCount = 0;
    data.forEach(c => {
        if(c.Gender === "Erkak") maleCount++;
        else if(c.Gender === "Ayol") femaleCount++;
    });

    // Bar Chart
    const barCtx = document.getElementById("barChart");
    if(barCtx) {
        if(barChartInstance) barChartInstance.destroy();
        barChartInstance = new Chart(barCtx, {
            type: "bar",
            data: {
                labels: names,
                datasets: [{
                    label: "Balans ($)",
                    data: balances,
                    backgroundColor: "rgba(46, 204, 113, 0.6)",
                    borderColor: "rgba(46, 204, 113, 1)",
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // Pie Chart
    const pieCtx = document.getElementById("pieChart");
    if(pieCtx) {
        if(pieChartInstance) pieChartInstance.destroy();
        pieChartInstance = new Chart(pieCtx, {
            type: "doughnut",
            data: {
                labels: ["Erkak", "Ayol"],
                datasets: [{
                    data: [maleCount, femaleCount],
                    backgroundColor: [
                        "rgba(52, 152, 219, 0.7)",
                        "rgba(155, 89, 182, 0.7)"
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }
}

async function transfer() {
    const fromId = document.getElementById("from-id").value;
    const toId = document.getElementById("to-id").value;
    const amount = document.getElementById("amount").value;
    const btn = document.querySelector(".transfer-form .btn");
    
    if(!fromId || !toId || !amount) {
        showToast("Barcha maydonlarni to'ldiring", false);
        return;
    }

    btn.textContent = "Kuting...";
    btn.disabled = true;

    try {
        const response = await fetch("/api/transfer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                from: parseInt(fromId),
                to: parseInt(toId),
                amount: parseInt(amount)
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast(data.message, true);
            // Clear inputs
            document.getElementById("from-id").value = "";
            document.getElementById("to-id").value = "";
            document.getElementById("amount").value = "";
            // Reload data
            loadDashboardData();
        } else {
            showToast(data.message || "Xatolik yuz berdi", false);
        }
    } catch (error) {
        showToast("Server bilan ulanishda xatolik", false);
    } finally {
        btn.textContent = "O'tkazish";
        btn.disabled = false;
    }
}
